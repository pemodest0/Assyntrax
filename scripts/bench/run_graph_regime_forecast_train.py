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

from graph_engine.core import local_divergence  # noqa: E402
from graph_engine.embedding import estimate_embedding_params, takens_embed  # noqa: E402
from graph_engine.graph_builder import knn_edges, normalize_counts, transition_counts  # noqa: E402
from graph_engine.labels import compute_confidence, compute_graph_quality, compute_thresholds, label_state  # noqa: E402
from graph_engine.metastable import metastable_regimes  # noqa: E402


def load_series(path: Path, timeframe: str) -> pd.Series:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    col = "close" if "close" in df.columns else df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, col]).sort_values(date_col)
    if timeframe == "weekly":
        series = df.set_index(date_col)[col].astype(float).resample("W").last().dropna()
    else:
        series = df.set_index(date_col)[col].astype(float)
    return series


def make_dataset(series: pd.Series, target: str, horizon: int, n_lags: int = 5):
    values = series.values.astype(float)
    dates = series.index
    if target == "log_return":
        y_base = np.diff(np.log(values))
        y_base = np.concatenate([[0.0], y_base])
    else:
        y_base = values

    X = []
    y = []
    t = []
    for i in range(n_lags, len(values) - horizon):
        lag_slice = values[i - n_lags : i]
        if target == "log_return":
            lag_ret = np.diff(np.log(lag_slice))
            lag_ret = np.concatenate([[0.0], lag_ret])
            feats = lag_ret
        else:
            feats = lag_slice
        X.append(feats)
        y.append(y_base[i + horizon])
        t.append(dates[i])
    return np.asarray(X), np.asarray(y), np.asarray(t)


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
    km = KMeans(n_clusters=min(n_micro, max(20, len(emb_train) // 5)), random_state=7, n_init=10)
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
    thresholds = compute_thresholds(escape_train, stretch_mu[train_mask], stretch_frac[train_mask])
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
    m: int,
    tau: int,
    n_micro: int,
    n_regimes: int,
    k_nn: int,
    theiler: int,
    alpha: float,
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

        X_train, y_train = X[train_mask], y[train_mask]
        X_test, y_test = X[test_mask], y[test_mask]
        t_test = t[test_mask]

        scale = float(np.mean(np.abs(np.diff(y_train)))) if len(y_train) > 1 else 1.0

        # regime labels for test period
        _, labels = _build_regimes_for_test(
            series,
            train_end=train_end,
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
        models["naive"] = np.full_like(y_test, y_train[-1])
        models["ridge"] = Ridge(alpha=1.0).fit(X_train, y_train).predict(X_test)
        models["gbrt"] = GradientBoostingRegressor(random_state=7).fit(X_train, y_train).predict(X_test)
        models["rf"] = RandomForestRegressor(n_estimators=200, random_state=7).fit(X_train, y_train).predict(X_test)
        arima_pred = _fit_arima(y_train, len(y_test))
        if arima_pred is not None:
            models["arima"] = arima_pred
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
    args = parser.parse_args()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)

    horizons = {
        "daily": [1, 5, 20, 252],
        "weekly": [1, 4, 12, 52],
    }

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
                        m=m_use,
                        tau=tau_use,
                        n_micro=args.n_micro,
                        n_regimes=args.n_regimes,
                        k_nn=args.k_nn,
                        theiler=args.theiler,
                        alpha=args.alpha,
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
