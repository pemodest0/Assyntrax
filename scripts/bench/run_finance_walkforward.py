#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from spa.finance_utils import (
    ExperimentSpec,
    FinancialDatasetSpec,
    compute_confidence_finance,
    compute_metrics,
    prepare_financial_series,
    standardize_train_test,
)
from spa.api_records import PredictionRecord, save_prediction_records
from spa.forecasting.forecasters import ARIMAForecaster, NaivePersistenceForecaster, XGBoostForecaster
from spa.forecasting.regime_gating import select_model_for_regime
from spa.models.takens_knn import TakensKNN
from spa.sanity import ensure_sorted_dates, split_hash, validate_time_split
from scripts.finance.yf_fetch_or_load import find_local_data, load_price_series, unify_to_daily


def to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.set_index("date").sort_index()
    weekly = df["price"].resample("W-FRI").last().dropna().to_frame()
    weekly = weekly.reset_index()
    return unify_to_daily(weekly)


def load_local_series(ticker: str) -> pd.DataFrame | None:
    base_dir = ROOT
    cache_dir = base_dir / "data" / "raw" / "finance" / "yfinance_daily"
    candidates = []
    if cache_dir.exists():
        for suffix in (ticker, ticker.replace("^", "")):
            cand = cache_dir / f"{suffix}.csv"
            if cand.exists():
                candidates.append(cand)

    candidates += find_local_data(ticker, base_dir)
    if ticker.startswith("^"):
        candidates += find_local_data(ticker.replace("^", ""), base_dir)

    for candidate in candidates:
        df = load_price_series(candidate)
        if df is not None:
            return unify_to_daily(df)
    return None


def build_dataset(ticker: str, freq: str, target_type: str) -> Tuple[pd.DataFrame, Dict[str, object]] | None:
    df = load_local_series(ticker)
    if df is None or df.empty:
        return None
    if freq == "weekly":
        df = to_weekly(df)
    spec = FinancialDatasetSpec(
        entity_name=ticker,
        freq=freq,
        price_col="price",
        target_type=target_type,
        vol_window=12 if freq == "weekly" else 20,
    )
    prepared, meta = prepare_financial_series(df, spec)
    prepared = prepared.dropna(subset=["y_raw"]).reset_index(drop=True)
    return prepared, meta


def predict_knn_train(values: np.ndarray, horizon: int, train_end: int, tau: int = 2, m: int = 4, k: int = 10) -> np.ndarray:
    pred = np.full_like(values, np.nan, dtype=float)
    min_len = (m - 1) * tau + horizon + 1
    if len(values) <= min_len or train_end <= (m - 1) * tau:
        return pred
    model = TakensKNN(tau=tau, m=m, k=k)
    if not model.fit(values, train_end):
        return pred
    for i in range((m - 1) * tau, len(values) - horizon):
        state = np.array([values[i - j * tau] for j in range(m)], dtype=float)
        pred_val = model.predict_1step(state)
        if pred_val is None:
            continue
        pred[i + horizon] = pred_val
    return pred


def _compute_transition_rate(values: np.ndarray) -> float:
    if values.size < 3:
        return 0.0
    window = max(3, int(values.size * 0.1))
    recent = values[-window:]
    signs = np.sign(recent)
    return float(np.mean(signs[1:] != signs[:-1]))


def _compute_novelty(last_val: float, mean: float, std: float) -> float:
    if std == 0 or not np.isfinite(last_val):
        return 0.0
    z = abs((last_val - mean) / std)
    return float(np.clip(z / 3.0, 0.0, 1.0))


def _compute_backtest(y_true: np.ndarray, y_pred: np.ndarray, freq: str, allow_short: bool, cost: float) -> Dict[str, float]:
    if y_true.size == 0:
        return {}
    if allow_short:
        signal = np.sign(y_pred)
    else:
        signal = (y_pred > 0).astype(float)
    trades = np.abs(np.diff(signal, prepend=signal[:1]))
    strat_ret = signal * y_true - cost * trades
    equity = np.cumprod(1.0 + strat_ret)
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    ann = 252 if freq == "daily" else 52
    ret_mean = float(np.mean(strat_ret))
    ret_std = float(np.std(strat_ret)) if float(np.std(strat_ret)) != 0 else 1.0
    sharpe = float((ret_mean / ret_std) * math.sqrt(ann))
    return {
        "total_return": float(equity[-1] - 1.0),
        "max_drawdown": float(drawdown.min()),
        "sharpe": sharpe,
        "hit_rate": float(np.mean(strat_ret > 0)),
    }


def _save_plot_hist(values: Iterable[float], out_path: Path, title: str, xlabel: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist([v for v in values if np.isfinite(v)], bins=20, color="#2563eb", alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def _retrain_schedule(start: pd.Timestamp, end: pd.Timestamp, frequency: str) -> List[pd.Timestamp]:
    if frequency == "monthly":
        dates = pd.date_range(start, end, freq="MS")
    elif frequency == "quarterly":
        dates = pd.date_range(start, end, freq="QS")
    else:
        dates = pd.date_range(start, end, freq="YS")
    return [pd.Timestamp(d) for d in dates if d <= end]


def simulate_production(
    spec: ExperimentSpec,
    outdir: Path,
    start_date: str,
    end_date: str,
    allow_short: bool,
    cost_bps: float,
) -> pd.DataFrame:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    rows: List[Dict[str, object]] = []

    for ticker in spec.universe:
        prepared_meta = build_dataset(ticker, spec.freq, spec.target_type)
        if prepared_meta is None:
            continue
        df, meta = prepared_meta
        dates = pd.to_datetime(df["date"])
        y_raw = df["y_raw"].to_numpy()

        schedule = _retrain_schedule(start, end, spec.retrain_frequency)
        if not schedule:
            continue

        for idx, retrain_date in enumerate(schedule):
            next_date = schedule[idx + 1] if idx + 1 < len(schedule) else end
            train_mask = dates <= retrain_date
            test_mask = (dates > retrain_date) & (dates <= next_date)
            if not train_mask.any() or not test_mask.any():
                continue
            train_df = df.loc[train_mask, ["date", "y"]]
            test_df = df.loc[test_mask, ["date", "y"]]
            train_std, test_std, stats = standardize_train_test(train_df, test_df)

            train_end_idx = int(np.where(train_mask)[0].max())
            for horizon in spec.horizons:
                y_target = df["y_raw"].shift(-horizon)
                y_target_std = ((y_target - stats["mean"]) / stats["std"]).to_numpy()
                motor_pred = predict_knn_train(y_raw, horizon, train_end_idx)
                motor_pred_series = pd.Series(motor_pred, index=df.index)
                mask_eval = test_mask & y_target.notna() & motor_pred_series.notna()
                if not mask_eval.any():
                    continue

                y_true_raw = y_target[mask_eval].to_numpy()
                y_true_std = y_target_std[mask_eval.to_numpy()]
                pred_motor_raw = motor_pred_series[mask_eval].to_numpy()
                pred_motor_std = (pred_motor_raw - stats["mean"]) / stats["std"]
                naive_pred_raw = df.loc[mask_eval, "y_raw"].to_numpy()

                metrics = compute_metrics(
                    y_true_raw,
                    pred_motor_raw,
                    y_true_std,
                    pred_motor_std,
                    naive_pred_raw,
                    spec.target_type,
                )
                backtest = _compute_backtest(
                    y_true_raw,
                    pred_motor_raw,
                    spec.freq,
                    allow_short,
                    cost_bps,
                )
                rows.append(
                    {
                        "ticker": ticker,
                        "freq": spec.freq,
                        "target_type": spec.target_type,
                        "retrain_date": retrain_date.date().isoformat(),
                        "test_end": next_date.date().isoformat(),
                        "horizon": horizon,
                        "n_test": int(len(y_true_raw)),
                        "mae_raw": metrics["mae_raw"],
                        "rmse_raw": metrics["rmse_raw"],
                        "mase": metrics["mase"],
                        "dir_acc": metrics.get("dir_acc", float("nan")),
                        "backtest_total_return": backtest.get("total_return"),
                        "backtest_max_drawdown": backtest.get("max_drawdown"),
                        "backtest_sharpe": backtest.get("sharpe"),
                        "backtest_hit_rate": backtest.get("hit_rate"),
                    }
                )

    prod_df = pd.DataFrame(rows)
    prod_path = outdir / "production_metrics.csv"
    prod_df.to_csv(prod_path, index=False)
    return prod_df


def run_walk_forward(spec: ExperimentSpec, outdir: Path, allow_short: bool, cost_bps: float, top_plots: int) -> Tuple[pd.DataFrame, Dict[str, object]]:
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    outdir.mkdir(parents=True, exist_ok=True)
    plot_dir = outdir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, object]] = []
    registry_path = ROOT / "results" / "model_perf_registry.csv"
    if registry_path.exists():
        registry_df = pd.read_csv(registry_path)
    else:
        registry_df = pd.DataFrame(
            columns=[
                "asset",
                "timeframe",
                "regime_label",
                "model_name",
                "model_family",
                "horizon",
                "year_test",
                "mase",
                "mae",
                "rmse",
                "dir_acc",
            ]
        )
    warnings_all: List[str] = []

    for ticker in spec.universe:
        prepared_meta = build_dataset(ticker, spec.freq, spec.target_type)
        if prepared_meta is None:
            continue
        df, meta = prepared_meta
        ensure_sorted_dates(df["date"])
        dates = pd.to_datetime(df["date"])
        y_raw = df["y_raw"].to_numpy()

        for year in range(spec.start_year + 1, spec.end_year + 1):
            train_mask = (dates.dt.year >= spec.start_year) & (dates.dt.year <= year - 1)
            test_mask = dates.dt.year == year
            if not train_mask.any() or not test_mask.any():
                continue
            train_end = pd.Timestamp(f"{year - 1}-12-31")
            test_start = pd.Timestamp(f"{year}-01-01")
            test_end = pd.Timestamp(f"{year}-12-31")
            validate_time_split(dates, train_mask, test_mask, train_end=train_end, test_start=test_start, test_end=test_end)

            train_df = df.loc[train_mask, ["date", "y"]]
            test_df = df.loc[test_mask, ["date", "y"]]
            train_std, test_std, stats = standardize_train_test(train_df, test_df)
            y_std = pd.Series(index=df.index, dtype=float)
            y_std.loc[train_df.index] = train_std["y"].values
            y_std.loc[test_df.index] = test_std["y"].values

            last_test_val = df.loc[test_mask, "y_raw"].iloc[-1]
            novelty = _compute_novelty(last_test_val, stats["mean"], stats["std"])
            transition_rate = _compute_transition_rate(df.loc[test_mask, "y_raw"].to_numpy())
            regime_label = "global"
            regime_conf = float(np.clip(1.0 - novelty, 0.0, 1.0))
            decision = select_model_for_regime(
                registry_df,
                ticker,
                spec.freq,
                regime_label,
                regime_conf,
                novelty,
            )

            year_rows: List[Dict[str, object]] = []
            train_end_idx = int(np.where(train_mask)[0].max())
            for horizon in spec.horizons:
                y_target = df["y_raw"].shift(-horizon)
                y_target_std = y_std.shift(-horizon)

                naive_pred = df["y_raw"].copy()
                motor_pred = predict_knn_train(y_raw, horizon, train_end_idx)
                motor_pred_series = pd.Series(motor_pred, index=df.index)

                train_forecast_df = df.loc[train_mask, ["y_raw"]].rename(columns={"y_raw": "y"})
                test_forecast_df = df.loc[test_mask, ["y_raw"]].rename(columns={"y_raw": "y"})

                forecasters = [
                    NaivePersistenceForecaster(y_col="y"),
                    ARIMAForecaster(y_col="y"),
                    XGBoostForecaster(y_col="y"),
                ]
                model_preds: Dict[str, Dict[str, object]] = {}
                for fc in forecasters:
                    try:
                        fc.fit(train_forecast_df)
                        pred, p10, p50, p90 = fc.predict(test_forecast_df, horizon)
                        pred_series = pd.Series(pred, index=test_forecast_df.index)
                        model_preds[fc.model_name] = {
                            "family": fc.model_family,
                            "pred": pred_series,
                            "p10": p10,
                            "p50": p50,
                            "p90": p90,
                        }
                    except Exception:
                        continue

                model_preds["takens_knn"] = {
                    "family": "knn",
                    "pred": motor_pred_series.loc[test_mask],
                    "p10": None,
                    "p50": None,
                    "p90": None,
                }

                selected_model = decision.selected_model
                selected_metrics = None
                selected_pred_series = None

                for model_name, info in model_preds.items():
                    pred_series = info["pred"]
                    mask_eval = test_mask & y_target.notna() & pred_series.notna()
                    if not mask_eval.any():
                        continue
                    y_true_raw = y_target[mask_eval].to_numpy()
                    y_true_std = y_target_std[mask_eval].to_numpy()
                    pred_raw = pred_series[mask_eval].to_numpy()
                    pred_std = (pred_raw - stats["mean"]) / stats["std"]
                    pred_naive_raw = naive_pred[mask_eval].to_numpy()

                    metrics = compute_metrics(
                        y_true_raw,
                        pred_raw,
                        y_true_std,
                        pred_std,
                        pred_naive_raw,
                        spec.target_type,
                    )

                    new_row = pd.DataFrame(
                        [
                            {
                                "asset": ticker,
                                "timeframe": spec.freq,
                                "regime_label": regime_label,
                                "model_name": model_name,
                                "model_family": info.get("family", ""),
                                "horizon": horizon,
                                "year_test": year,
                                "mase": metrics.get("mase"),
                                "mae": metrics.get("mae_raw"),
                                "rmse": metrics.get("rmse_raw"),
                                "dir_acc": metrics.get("dir_acc"),
                            }
                        ]
                    )
                    if registry_df.empty:
                        registry_df = new_row
                    else:
                        registry_df = pd.concat([registry_df, new_row], ignore_index=True)

                    if model_name == selected_model:
                        selected_metrics = metrics
                        selected_pred_series = pred_series

                if selected_metrics is None or selected_pred_series is None:
                    continue

                mask_eval = test_mask & y_target.notna() & selected_pred_series.notna()
                if not mask_eval.any():
                    continue

                y_true_raw = y_target[mask_eval].to_numpy()
                pred_selected_raw = selected_pred_series[mask_eval].to_numpy()
                error_std = float(np.std(y_true_raw - pred_selected_raw) / (np.std(train_df["y"].to_numpy()) + 1e-9))
                error_std = float(np.clip(error_std, 0.0, 1.0))

                verdict = compute_confidence_finance(selected_metrics, error_std, transition_rate, novelty)
                warnings = []
                if meta.get("warning_scale"):
                    warnings.append(meta["warning_scale"])
                if selected_metrics.get("mase", float("nan")) >= 1 or selected_metrics.get("mase", float("nan")) != selected_metrics.get("mase", float("nan")):
                    warnings.append("MASE_FRACO")
                if "dir_acc" in selected_metrics and selected_metrics["dir_acc"] < 0.52:
                    warnings.append("DIRECAO_FRACA")
                if novelty > 0.7:
                    warnings.append("FORA_DISTRIBUICAO")
                if transition_rate > 0.3:
                    warnings.append("REGIME_INSTAVEL")
                if len(y_true_raw) < 20:
                    warnings.append("POUCOS_PONTOS")
                warnings.extend(decision.warnings)

                backtest = _compute_backtest(
                    y_true_raw,
                    pred_selected_raw,
                    spec.freq,
                    allow_short,
                    cost_bps,
                )

                row = {
                    "run_id": run_id,
                    "ticker": ticker,
                    "freq": spec.freq,
                    "target_type": spec.target_type,
                    "year_test": year,
                    "horizon": horizon,
                    "n_test": int(len(y_true_raw)),
                    "mae_raw": selected_metrics["mae_raw"],
                    "rmse_raw": selected_metrics["rmse_raw"],
                    "mase": selected_metrics["mase"],
                    "dir_acc": selected_metrics.get("dir_acc", float("nan")),
                    "gain_vs_naive": float(1.0 - selected_metrics["mase"]) if np.isfinite(selected_metrics["mase"]) else float("nan"),
                    "confidence_score": verdict["score"],
                    "confidence_level": verdict["level"],
                    "action": verdict["action"],
                    "warnings": ";".join(warnings),
                    "split_hash": split_hash(np.where(train_mask)[0], np.where(mask_eval)[0]),
                    "novelty": novelty,
                    "transition_rate": transition_rate,
                    "error_std": error_std,
                    "selected_model": selected_model,
                    "use_forecast_bool": decision.use_forecast_bool,
                    "forecast_confidence": decision.forecast_confidence,
                    "backtest_total_return": backtest.get("total_return"),
                    "backtest_max_drawdown": backtest.get("max_drawdown"),
                    "backtest_sharpe": backtest.get("sharpe"),
                    "backtest_hit_rate": backtest.get("hit_rate"),
                }
                rows.append(row)
                year_rows.append(row)
                warnings_all.extend(warnings)

            if year_rows:
                best = sorted(year_rows, key=lambda r: (r["mase"] if np.isfinite(r["mase"]) else 999.0))[0]
                for row in rows:
                    if (
                        row["ticker"] == ticker
                        and row["year_test"] == year
                        and row["horizon"] == best["horizon"]
                    ):
                        row["best_horizon_flag"] = True

    results = pd.DataFrame(rows)
    if not results.empty and "best_horizon_flag" not in results.columns:
        results["best_horizon_flag"] = False

    warnings_counts = pd.Series(warnings_all).value_counts().to_dict()
    overview = {
        "run_id": run_id,
        "spec": asdict(spec),
        "n_rows": int(len(results)),
        "warnings_top": warnings_counts,
    }

    if not results.empty:
        agg = results.groupby("ticker").agg(
            mean_mase=("mase", "mean"),
            pct_mase_lt_1=("mase", lambda x: float(np.mean(x < 1))),
            mean_dir_acc=("dir_acc", "mean"),
            pct_dir_acc_gt_052=("dir_acc", lambda x: float(np.mean(x > 0.52))),
            stability_mase=("mase", "std"),
            best_year_mase=("mase", "min"),
            worst_year_mase=("mase", "max"),
        )
        overview["by_ticker"] = agg.reset_index().to_dict(orient="records")

        global_good = float(np.mean(agg["pct_mase_lt_1"] > 0.5)) if not agg.empty else 0.0
        global_dir = float(np.mean(agg["pct_dir_acc_gt_052"] > 0.5)) if not agg.empty else 0.0
        if global_good > 0.6 and global_dir > 0.6:
            verdict = "SIM"
        elif global_good < 0.3 or global_dir < 0.3:
            verdict = "NAO"
        else:
            verdict = "DEPENDE"
        overview["global_verdict"] = verdict
        overview["global_good_pct"] = global_good
        overview["global_dir_pct"] = global_dir

        _save_plot_hist(results["mase"], plot_dir / "hist_mase.png", "Distribuicao de MASE", "MASE")
        if "dir_acc" in results.columns:
            _save_plot_hist(results["dir_acc"], plot_dir / "hist_dir_acc.png", "Distribuicao de Dir Acc", "Dir Acc")

        top_tickers = (
            results.groupby("ticker")["mase"].mean().sort_values().head(top_plots).index.tolist()
        )
        for ticker in top_tickers:
            sub = results[results["ticker"] == ticker]
            pivot = sub.pivot_table(index="year_test", columns="horizon", values="mase", aggfunc="mean")
            if pivot.empty:
                continue
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(7, 4))
            for horizon in pivot.columns:
                ax.plot(pivot.index, pivot[horizon], marker="o", label=f"h{horizon}")
            ax.set_title(f"{ticker} MASE por ano")
            ax.set_xlabel("Ano")
            ax.set_ylabel("MASE")
            ax.legend()
            fig.tight_layout()
            fig.savefig(plot_dir / f"{ticker}_mase_by_year.png", dpi=140)
            plt.close(fig)

    registry_df.to_csv(registry_path, index=False)
    return results, overview


def main() -> None:
    parser = argparse.ArgumentParser(description="Walk-forward financeiro (sem download).")
    parser.add_argument("--tickers", default="SPY,^VIX,GLD")
    parser.add_argument("--freq", default="daily", choices=["daily", "weekly"])
    parser.add_argument("--target-type", default="log_return", choices=["log_return", "simple_return", "volatility"])
    parser.add_argument("--horizons", default="1,5,20")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=datetime.utcnow().year)
    parser.add_argument("--retrain-frequency", default="yearly", choices=["yearly", "quarterly", "monthly"])
    parser.add_argument("--outdir", default="results/finance_walkforward")
    parser.add_argument("--allow-short", action="store_true")
    parser.add_argument("--cost-bps", type=float, default=0.0005)
    parser.add_argument("--top-plots", type=int, default=3)
    parser.add_argument("--simulate-prod", action="store_true")
    parser.add_argument("--prod-start", default=None)
    parser.add_argument("--prod-end", default=None)
    parser.add_argument("--emit-api-records", action="store_true", help="Gera api_records.jsonl e api_records.csv")
    args = parser.parse_args()

    universe = [t.strip() for t in args.tickers.split(",") if t.strip()]
    horizons = [int(h.strip()) for h in args.horizons.split(",") if h.strip()]
    spec = ExperimentSpec(
        universe=universe,
        freq=args.freq,
        target_type=args.target_type,
        horizons=horizons,
        start_year=args.start_year,
        end_year=args.end_year,
        retrain_frequency=args.retrain_frequency,
        models_to_compare=("naive", "motor"),
    )

    outdir = Path(args.outdir)
    results, overview = run_walk_forward(spec, outdir, args.allow_short, args.cost_bps, args.top_plots)

    csv_path = outdir / "walkforward_results.csv"
    results.to_csv(csv_path, index=False)

    overview_path = outdir / "overview.json"
    overview_path.write_text(json.dumps(overview, indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = outdir / "report.md"
    lines = [
        "# Walk-forward Finance Report",
        "",
        f"run_id: {overview.get('run_id')}",
        f"freq: {spec.freq}",
        f"target_type: {spec.target_type}",
        f"years: {spec.start_year}..{spec.end_year}",
        "",
    ]
    if "global_verdict" in overview:
        lines.append(f"veredito_global: {overview['global_verdict']}")
        lines.append(f"pct_tickers_mase_lt_1: {overview.get('global_good_pct')}")
        lines.append(f"pct_tickers_dir_acc_gt_052: {overview.get('global_dir_pct')}")
        lines.append("")

    if not results.empty:
        sample = results.head(10)
        lines.append("## Exemplo de linhas")
        lines.append(sample.to_csv(index=False))
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] resultados: {csv_path}")
    print(f"[OK] overview: {overview_path}")
    print(f"[OK] report: {report_path}")

    if args.emit_api_records:
        records = []
        if not results.empty:
            for _, row in results.iterrows():
                warnings = [w for w in str(row.get("warnings", "")).split(";") if w]
                records.append(
                    PredictionRecord(
                        timestamp=f"{int(row['year_test'])}-12-31",
                        asset=row.get("ticker", ""),
                        timeframe=row.get("freq", ""),
                        horizon=int(row.get("horizon")) if not pd.isna(row.get("horizon")) else None,
                        regime_label=None,
                        regime_confidence=None,
                        regime_risk=None,
                        novelty_score=row.get("novelty"),
                        transition_rate=row.get("transition_rate"),
                        entropy=None,
                        y_true=None,
                        y_pred=None,
                        y_pred_p10=None,
                        y_pred_p50=None,
                        y_pred_p90=None,
                        model_name=row.get("selected_model", ""),
                        model_family="ensemble",
                        forecast_confidence=float(row.get("forecast_confidence", 0.0)) if row.get("forecast_confidence") is not None else None,
                        warnings=warnings,
                        mase_6m=row.get("mase"),
                        smape_6m=None,
                        diracc_6m=row.get("dir_acc"),
                    )
                )
        save_prediction_records(
            records,
            outdir / "api_records.jsonl",
            outdir / "api_records.csv",
        )

    if args.simulate_prod:
        prod_start = args.prod_start or f"{args.end_year}-01-01"
        prod_end = args.prod_end or f"{args.end_year}-12-31"
        prod_df = simulate_production(
            spec,
            outdir,
            prod_start,
            prod_end,
            args.allow_short,
            args.cost_bps,
        )
        print(f"[OK] production metrics: {outdir / 'production_metrics.csv'} ({len(prod_df)} linhas)")


if __name__ == "__main__":
    main()
