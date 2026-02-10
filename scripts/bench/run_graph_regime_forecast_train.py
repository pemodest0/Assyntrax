#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.graph.core import local_divergence  # noqa: E402
from engine.graph.embedding import estimate_embedding_params, takens_embed  # noqa: E402
from engine.graph.graph_builder import knn_edges, normalize_counts, transition_counts  # noqa: E402
from engine.graph.labels import compute_confidence, compute_graph_quality, compute_thresholds, label_state  # noqa: E402
from engine.graph.metastable import metastable_regimes  # noqa: E402


def load_series(path: Path, timeframe: str) -> pd.Series:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    if "close" in df.columns:
        col = "close"
    elif "price" in df.columns:
        col = "price"
    else:
        col = df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, col]).sort_values(date_col)
    if timeframe == "weekly":
        series = df.set_index(date_col)[col].astype(float).resample("W").last().dropna()
        if "r" in df.columns:
            r_series = df.set_index(date_col)["r"].astype(float).resample("W").last().dropna()
            series.attrs["returns"] = r_series
    else:
        series = df.set_index(date_col)[col].astype(float)
        if "r" in df.columns:
            r_series = df.set_index(date_col)["r"].astype(float)
            series.attrs["returns"] = r_series
    return series


def make_dataset(series: pd.Series, target: str, horizon: int, n_lags: int = 5):
    values = series.values.astype(float)
    dates = series.index
    eps = 1e-12
    if target == "log_return":
        ret_series = series.attrs.get("returns")
        if isinstance(ret_series, pd.Series):
            ret_series = ret_series.reindex(dates).astype(float)
            y_base = ret_series.values
        else:
            safe_vals = np.clip(values, eps, None)
            with np.errstate(divide="ignore", invalid="ignore"):
                y_base = np.diff(np.log(safe_vals))
            y_base = np.concatenate([[np.nan], y_base])
    else:
        y_base = values

    X = []
    y = []
    t = []
    for i in range(n_lags, len(values) - horizon):
        if target == "log_return":
            if isinstance(ret_series, pd.Series):
                lag_slice = y_base[i - n_lags : i]
                feats = lag_slice
            else:
                lag_slice = values[i - n_lags : i]
                safe_slice = np.clip(lag_slice, eps, None)
                with np.errstate(divide="ignore", invalid="ignore"):
                    lag_ret = np.diff(np.log(safe_slice))
                lag_ret = np.concatenate([[np.nan], lag_ret])
                feats = lag_ret
        else:
            lag_slice = values[i - n_lags : i]
            feats = lag_slice
        X.append(feats)
        y.append(y_base[i + horizon])
        t.append(dates[i])
    X = np.asarray(X)
    y = np.asarray(y)
    t = np.asarray(t)
    if X.size == 0:
        return X, y, t
    mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
    return X[mask], y[mask], t[mask]


def _metrics(y_true: np.ndarray, y_pred: np.ndarray, scale: float) -> Dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred)) if y_true.size else float("nan")
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred))) if y_true.size else float("nan")
    mase = float(mae / max(scale, 1e-8)) if y_true.size else float("nan")
    # directional accuracy (only meaningful for returns)
    dir_acc = float(np.mean(np.sign(y_true) == np.sign(y_pred))) if y_true.size else float("nan")
    return {"mae": mae, "rmse": rmse, "mase": mase, "dir_acc": dir_acc}


def _year_slices(index: pd.DatetimeIndex) -> List[int]:
    return sorted(set(index.year))


def _fit_arima(y_train: np.ndarray, steps: int):
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except Exception:
        return None
    try:
        model = ARIMA(y_train, order=(1, 0, 0))
        fit = model.fit()
        pred = fit.forecast(steps=steps)
        return np.asarray(pred)
    except Exception:
        return None


def _fit_xgboost(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray):
    try:
        import xgboost as xgb
    except Exception:
        return None
    try:
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=7,
        )
        model.fit(X_train, y_train)
        return model.predict(X_test)
    except Exception:
        return None


def _build_regimes_for_test(
    series: pd.Series,
    train_end: pd.Timestamp,
    timeframe: str,
    m: int,
    tau: int,
    n_micro: int,
    n_regimes: int,
    k_nn: int,
    theiler: int,
    alpha: float,
    method: str,
) -> Tuple[pd.DatetimeIndex, List[str]]:
    train = series[series.index <= train_end]
    full = series
    if len(train) < (m - 1) * tau + 5:
        return full.index, ["NOISY"] * len(full.index)

    train_values = train.values.astype(float)
    emb_train = takens_embed(train_values, m=m, tau=tau)
    n_clusters = min(n_micro, max(2, len(emb_train) // 5))
    n_clusters = min(n_clusters, len(emb_train))
    km = KMeans(n_clusters=n_clusters, random_state=7, n_init=10)
    train_labels = km.fit_predict(emb_train)
    centroids = km.cluster_centers_

    counts = transition_counts(train_labels)
    p_matrix = normalize_counts(counts, alpha=alpha)
    micro_regime = metastable_regimes(p_matrix, n_regimes=n_regimes, seed=7, method=method)

    emb_full = takens_embed(full.values.astype(float), m=m, tau=tau)
    aligned_index = full.index[(m - 1) * tau :]
    nn = NearestNeighbors(n_neighbors=1).fit(centroids)
    micro_full = nn.kneighbors(emb_full, return_distance=False).ravel()

    conf_full = compute_confidence(p_matrix, micro_regime, micro_full)
    stretch, frac_pos = local_divergence(emb_full, theiler=theiler)
    if stretch.size > 0:
        lo = float(np.quantile(stretch, 0.05))
        hi = float(np.quantile(stretch, 0.95))
        stretch = np.clip(stretch, lo, hi)
    stretch_mu = np.pad(stretch, (0, 1), mode="edge")
    stretch_frac = np.pad(frac_pos, (0, 1), mode="edge")

    train_mask = aligned_index <= train_end
    escape_train = 1.0 - conf_full[train_mask]
    thresholds = compute_thresholds(
        escape_train,
        stretch_mu[train_mask],
        stretch_frac[train_mask],
        conf_full[train_mask],
        timeframe=timeframe,
    )
    edges = knn_edges(centroids, k=k_nn)
    quality = compute_graph_quality(len(centroids), edges, np.bincount(train_labels, minlength=len(centroids)), p_matrix, {})

    labels = []
    for c, s, f in zip(conf_full, stretch_mu, stretch_frac):
        if quality["score"] < 0.3:
            labels.append("NOISY")
        else:
            labels.append(label_state(float(c), float(s), float(1.0 - c), float(f), thresholds))

    # pad to full length (embedding shortens)
    pad_len = len(full.index) - len(aligned_index)
    if pad_len > 0:
        labels = ["NOISY"] * pad_len + labels
    return full.index, labels


def run_backtest(
    series: pd.Series,
    target: str,
    horizon: int,
    method: str,
    timeframe: str,
    m: int,
    tau: int,
    n_micro: int,
    n_regimes: int,
    k_nn: int,
    theiler: int,
    alpha: float,
    models_to_run: List[str],
    sector_model_map: Dict[tuple, str] | None = None,
    sector_group: str | None = None,
    best_model_map: Dict[tuple, str] | None = None,
    best_model_top2_map: Dict[tuple, tuple[str, str]] | None = None,
    asset_name: str | None = None,
    purge: int = -1,
    embargo: int = -1,
) -> Dict[str, any]:
    X, y, t = make_dataset(series, target=target, horizon=horizon, n_lags=5)
    if len(t) < 50:
        return {"by_year": {}, "predictions": []}

    years = _year_slices(pd.to_datetime(t))
    out_years = {}
    predictions = []

    for i in range(1, len(years)):
        year = years[i]
        train_end = pd.Timestamp(year=year - 1, month=12, day=31)
        train_mask = t <= train_end
        test_mask = (pd.to_datetime(t).year == year)
        if not train_mask.any() or not test_mask.any():
            continue

        # purge/embargo to avoid label leakage across boundary
        purge_n = horizon if purge < 0 else purge
        embargo_n = horizon if embargo < 0 else embargo
        if purge_n > 0:
            train_idx = np.where(train_mask)[0]
            if len(train_idx) > purge_n:
                train_mask[train_idx[-purge_n:]] = False
        if embargo_n > 0:
            test_idx = np.where(test_mask)[0]
            if len(test_idx) > embargo_n:
                test_mask[test_idx[:embargo_n]] = False

        X_train, y_train = X[train_mask], y[train_mask]
        X_test, y_test = X[test_mask], y[test_mask]
        t_test = t[test_mask]
        if X_train.size == 0 or X_test.size == 0:
            continue
        train_ok = np.isfinite(X_train).all(axis=1) & np.isfinite(y_train)
        test_ok = np.isfinite(X_test).all(axis=1) & np.isfinite(y_test)
        X_train, y_train = X_train[train_ok], y_train[train_ok]
        X_test, y_test = X_test[test_ok], y_test[test_ok]
        t_test = t_test[test_ok]
        if X_train.size == 0 or X_test.size == 0:
            continue

        scale = float(np.mean(np.abs(np.diff(y_train)))) if len(y_train) > 1 else 1.0

        # regime labels for test period
        _, labels = _build_regimes_for_test(
            series,
            train_end=train_end,
            timeframe=timeframe,
            m=m,
            tau=tau,
            n_micro=n_micro,
            n_regimes=n_regimes,
            k_nn=k_nn,
            theiler=theiler,
            alpha=alpha,
            method=method,
        )
        label_series = pd.Series(labels, index=series.index)
        label_test = label_series.loc[pd.to_datetime(t_test)].values

        # models
        models: Dict[str, np.ndarray] = {}
        if "naive" in models_to_run:
            models["naive"] = np.full_like(y_test, y_train[-1])
        if "ridge" in models_to_run:
            models["ridge"] = Ridge(alpha=1.0).fit(X_train, y_train).predict(X_test)
        if "gbrt" in models_to_run:
            models["gbrt"] = GradientBoostingRegressor(random_state=7).fit(X_train, y_train).predict(X_test)
        if "rf" in models_to_run:
            models["rf"] = RandomForestRegressor(n_estimators=200, random_state=7).fit(X_train, y_train).predict(X_test)
        if "arima" in models_to_run:
            arima_pred = _fit_arima(y_train, len(y_test))
            if arima_pred is not None:
                models["arima"] = arima_pred
        if "xgb" in models_to_run:
            xgb_pred = _fit_xgboost(X_train, y_train, X_test)
            if xgb_pred is not None:
                models["xgb"] = xgb_pred

        year_summary = {"overall": {}, "by_regime": {}}

        for name, pred in models.items():
            year_summary["overall"][name] = _metrics(y_test, pred, scale)
            by_reg = {}
            for reg in np.unique(label_test):
                mask = label_test == reg
                by_reg[str(reg)] = _metrics(y_test[mask], pred[mask], scale)
            year_summary["by_regime"][name] = by_reg

            for dt, y_t, y_p, reg in zip(t_test, y_test, pred, label_test):
                predictions.append(
                    {
                        "date": str(dt),
                        "year": int(year),
                        "target": target,
                        "horizon": horizon,
                        "model": name,
                        "y_true": float(y_t),
                        "y_pred": float(y_p),
                        "regime": str(reg),
                    }
                )

        # auto model per sector/regime
        if sector_model_map and sector_group:
            auto_pred = []
            for reg, y_t in zip(label_test, y_test):
                key = (sector_group, timeframe, str(horizon), str(reg))
                model_name = sector_model_map.get(key)
                if model_name not in models:
                    # fallback: best overall by mase
                    best_model = None
                    best_mase = None
                    for name, pred in models.items():
                        met = _metrics(y_test, pred, scale)
                        if best_mase is None or met["mase"] < best_mase:
                            best_mase = met["mase"]
                            best_model = name
                    model_name = best_model or "naive"
                auto_pred.append(models[model_name][len(auto_pred)])
            auto_pred = np.asarray(auto_pred)
            year_summary["overall"]["auto_sector"] = _metrics(y_test, auto_pred, scale)
            by_reg = {}
            for reg in np.unique(label_test):
                mask = label_test == reg
                by_reg[str(reg)] = _metrics(y_test[mask], auto_pred[mask], scale)
            year_summary["by_regime"]["auto_sector"] = by_reg

            for dt, y_t, y_p, reg in zip(t_test, y_test, auto_pred, label_test):
                predictions.append(
                    {
                        "date": str(dt),
                        "year": int(year),
                        "target": target,
                        "horizon": horizon,
                        "model": "auto_sector",
                        "y_true": float(y_t),
                        "y_pred": float(y_p),
                        "regime": str(reg),
                    }
                )

        # auto model per asset/regime (best_models_by_regime)
        if best_model_map and asset_name:
            auto_pred = []
            for reg in label_test:
                key = (asset_name, timeframe, str(horizon), str(reg))
                model_name = best_model_map.get(key)
                if model_name not in models:
                    best_model = None
                    best_mase = None
                    for name, pred in models.items():
                        met = _metrics(y_test, pred, scale)
                        if best_mase is None or met["mase"] < best_mase:
                            best_mase = met["mase"]
                            best_model = name
                    model_name = best_model or "naive"
                auto_pred.append(models[model_name][len(auto_pred)])
            auto_pred = np.asarray(auto_pred)
            year_summary["overall"]["auto_best"] = _metrics(y_test, auto_pred, scale)
            by_reg = {}
            for reg in np.unique(label_test):
                mask = label_test == reg
                by_reg[str(reg)] = _metrics(y_test[mask], auto_pred[mask], scale)
            year_summary["by_regime"]["auto_best"] = by_reg

            for dt, y_t, y_p, reg in zip(t_test, y_test, auto_pred, label_test):
                predictions.append(
                    {
                        "date": str(dt),
                        "year": int(year),
                        "target": target,
                        "horizon": horizon,
                        "model": "auto_best",
                        "y_true": float(y_t),
                        "y_pred": float(y_p),
                        "regime": str(reg),
                    }
                )

        # auto ensemble of top2 per asset/regime
        if best_model_top2_map and asset_name:
            auto_pred = []
            for reg in label_test:
                key = (asset_name, timeframe, str(horizon), str(reg))
                pair = best_model_top2_map.get(key)
                model_a, model_b = (pair if pair else (None, None))
                if model_a not in models:
                    best_model = None
                    best_mase = None
                    for name, pred in models.items():
                        met = _metrics(y_test, pred, scale)
                        if best_mase is None or met["mase"] < best_mase:
                            best_mase = met["mase"]
                            best_model = name
                    model_a = best_model or "naive"
                if model_b not in models:
                    model_b = model_a
                pred_a = models[model_a][len(auto_pred)]
                pred_b = models[model_b][len(auto_pred)]
                auto_pred.append(0.5 * (pred_a + pred_b))
            auto_pred = np.asarray(auto_pred)
            year_summary["overall"]["auto_best_ens"] = _metrics(y_test, auto_pred, scale)
            by_reg = {}
            for reg in np.unique(label_test):
                mask = label_test == reg
                by_reg[str(reg)] = _metrics(y_test[mask], auto_pred[mask], scale)
            year_summary["by_regime"]["auto_best_ens"] = by_reg

            for dt, y_t, y_p, reg in zip(t_test, y_test, auto_pred, label_test):
                predictions.append(
                    {
                        "date": str(dt),
                        "year": int(year),
                        "target": target,
                        "horizon": horizon,
                        "model": "auto_best_ens",
                        "y_true": float(y_t),
                        "y_pred": float(y_p),
                        "regime": str(reg),
                    }
                )

        out_years[str(year)] = year_summary

    return {"by_year": out_years, "predictions": predictions}


def main() -> None:
    parser = argparse.ArgumentParser(description="Formal backtest by regime and asset (multi-horizon).")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers")
    parser.add_argument("--timeframes", default="daily,weekly")
    parser.add_argument("--data-dir", default="data/raw/finance/yfinance_daily")
    parser.add_argument("--outdir", default="results/latest_graph/forecast_backtest")
    parser.add_argument("--method", default="spectral", choices=["spectral", "pcca"])
    parser.add_argument("--m", type=int, default=3)
    parser.add_argument("--tau", type=int, default=1)
    parser.add_argument("--auto-embed", action="store_true")
    parser.add_argument("--tau-method", default="ami", choices=["ami", "acf"])
    parser.add_argument("--m-method", default="cao", choices=["cao", "fnn"])
    parser.add_argument("--n-micro", type=int, default=200)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=10)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument(
        "--horizons",
        type=str,
        default="",
        help="Override horizons list (comma-separated, applies to all timeframes).",
    )
    parser.add_argument(
        "--models",
        type=str,
        default="naive,ridge,gbrt,rf,arima,xgb",
        help="Comma-separated model list (naive,ridge,gbrt,rf,arima,xgb).",
    )
    parser.add_argument(
        "--purge",
        type=int,
        default=-1,
        help="Remove Ãºltimas N amostras do treino (default -1 = horizon).",
    )
    parser.add_argument(
        "--embargo",
        type=int,
        default=-1,
        help="Ignora primeiras N amostras do teste (default -1 = horizon).",
    )
    parser.add_argument(
        "--use-sector-models",
        action="store_true",
        help="Use sector_best_models.csv to auto-pick model per regime.",
    )
    parser.add_argument(
        "--use-best-models",
        action="store_true",
        help="Use best_models_by_regime.csv to auto-pick model per asset/regime.",
    )
    parser.add_argument(
        "--use-best-ensemble",
        action="store_true",
        help="Use best_models_by_regime_top2.csv to build an ensemble per asset/regime.",
    )
    parser.add_argument(
        "--sector-models",
        default="results/forecast_suite/sector_best_models.csv",
        help="CSV with best model per sector/regime/horizon.",
    )
    parser.add_argument(
        "--best-models",
        default="results/forecast_suite/best_models_by_regime.csv",
        help="CSV with best model per asset/regime/horizon.",
    )
    parser.add_argument(
        "--best-models-top2",
        default="results/forecast_suite/best_models_by_regime_top2.csv",
        help="CSV with top2 models per asset/regime/horizon.",
    )
    parser.add_argument(
        "--asset-groups",
        default="data/asset_groups.csv",
        help="CSV mapping asset -> group.",
    )
    args = parser.parse_args()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)

    if args.horizons:
        try:
            override = [int(h.strip()) for h in args.horizons.split(",") if h.strip()]
        except ValueError:
            override = []
    else:
        override = []

    horizons = {
        "daily": override or [1, 5, 20, 252],
        "weekly": override or [1, 4, 12, 52],
    }

    models_to_run = [m.strip() for m in args.models.split(",") if m.strip()]
    allowed_models = {"naive", "ridge", "gbrt", "rf", "arima", "xgb"}
    models_to_run = [m for m in models_to_run if m in allowed_models]
    if not models_to_run:
        models_to_run = ["naive"]

    sector_model_map = None
    asset_to_group = None
    best_model_map = None
    best_model_top2_map = None
    if args.use_sector_models:
        sector_path = Path(args.sector_models)
        group_path = Path(args.asset_groups)
        if sector_path.exists() and group_path.exists():
            sector_df = pd.read_csv(sector_path)
            sector_model_map = {}
            for _, row in sector_df.iterrows():
                sector_model_map[(str(row["group"]), str(row["tf"]), str(row["horizon"]), str(row["regime"]))] = str(
                    row["best_model"]
                )
            asset_groups = pd.read_csv(group_path)
            asset_to_group = dict(zip(asset_groups["asset"], asset_groups["group"]))

    if args.use_best_models:
        best_path = Path(args.best_models)
        if best_path.exists():
            best_df = pd.read_csv(best_path)
            best_model_map = {}
            for _, row in best_df.iterrows():
                best_model_map[(str(row["asset"]), str(row["tf"]), str(row["horizon"]), str(row["regime"]))] = str(
                    row["best_model"]
                )

    if args.use_best_ensemble:
        top2_path = Path(args.best_models_top2)
        if top2_path.exists():
            top2_df = pd.read_csv(top2_path)
            best_model_top2_map = {}
            for _, row in top2_df.iterrows():
                best_model_top2_map[
                    (str(row["asset"]), str(row["tf"]), str(row["horizon"]), str(row["regime"]))
                ] = (str(row["best_model"]), str(row["second_model"]))

    for ticker in tickers:
        csv_path = data_dir / f"{ticker}.csv"
        if not csv_path.exists():
            continue
        for tf in tfs:
            series = load_series(csv_path, tf)
            if args.auto_embed:
                m_use, tau_use = estimate_embedding_params(series.values, tau_method=args.tau_method, m_method=args.m_method)
            else:
                m_use, tau_use = args.m, args.tau

            asset_dir = outdir / ticker / tf
            asset_dir.mkdir(parents=True, exist_ok=True)

            for target in ["close", "log_return"]:
                for horizon in horizons.get(tf, [1]):
                    result = run_backtest(
                        series=series,
                        target=target,
                        horizon=horizon,
                        method=args.method,
                        timeframe=tf,
                        m=m_use,
                        tau=tau_use,
                        n_micro=args.n_micro,
                        n_regimes=args.n_regimes,
                        k_nn=args.k_nn,
                        theiler=args.theiler,
                        alpha=args.alpha,
                        models_to_run=models_to_run,
                        sector_model_map=sector_model_map,
                        sector_group=(asset_to_group.get(ticker) if asset_to_group else None),
                        best_model_map=best_model_map,
                        best_model_top2_map=best_model_top2_map,
                        asset_name=ticker,
                        purge=args.purge,
                        embargo=args.embargo,
                    )
                    out_path = asset_dir / f"{ticker}_{tf}_{target}_h{horizon}.json"
                    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

            latest = {
                "dates": [d.strftime("%Y-%m-%d") for d in series.tail(30).index],
                "values": [float(v) for v in series.tail(30).values],
                "last": float(series.iloc[-1]),
            }
            (asset_dir / f"{ticker}_{tf}_latest.json").write_text(json.dumps(latest, indent=2), encoding="utf-8")

    print("[ok] forecast backtest complete")


if __name__ == "__main__":
    main()

