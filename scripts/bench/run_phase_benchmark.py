import argparse
import json
import os
import sys
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.finance.yf_fetch_or_load import (
    find_local_data,
    load_price_series,
    fetch_yfinance,
    unify_to_daily,
    save_cache,
)
from engine.finance_utils import (
    FinancialDatasetSpec,
    prepare_financial_series,
    split_train_test,
    standardize_train_test,
    compute_metrics,
    compute_confidence_finance,
    plot_master_finance,
)
from engine.api_records import PredictionRecord, save_prediction_records


def load_or_fetch(ticker, base_dir, start="2010-01-01", end="2025-12-31", allow_downloads=False):
    candidates = find_local_data(ticker, base_dir)
    df = None
    if candidates:
        df = load_price_series(candidates[0])
    if df is None and allow_downloads:
        df = fetch_yfinance(ticker, start=start, end=end)
    if df is None:
        return None
    df = unify_to_daily(df)
    df = df[df["date"] <= end]
    save_cache(df, base_dir, ticker)
    return df


def build_returns_df(df):
    out = df[["date", "r"]].copy()
    out.rename(columns={"r": "value"}, inplace=True)
    return out


def plot_ranking(summary_rows, out_path):
    if not summary_rows:
        return
    labels = [row["ticker"] for row in summary_rows]
    mae = [row.get("mae_h1", np.nan) for row in summary_rows]
    mae = [0 if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in mae]
    plt.figure(figsize=(8, 4))
    plt.bar(labels, mae, color="#1f77b4")
    plt.ylabel("MAE (h=1)")
    plt.title("Erro no teste (MAE h=1)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Benchmark de fase (finance) com auto-embed e horizonte")
    parser.add_argument("--tickers", required=True, help="Lista de tickers separados por virgula")
    parser.add_argument("--outdir", default="results/bench_finance", help="Diretorio de saida")
    parser.add_argument("--start", default="2010-01-01", help="Data inicial")
    parser.add_argument("--end", default="2025-12-31", help="Data final")
    parser.add_argument("--allow-downloads", action="store_true", help="Permite download (padrao: nao)")
    parser.add_argument("--horizons", default="1,5", help="Horizontes para debug (ex: 1,5)")
    parser.add_argument("--debug-limit", type=int, default=3, help="Limite de ativos para debug")
    parser.add_argument(
        "--auto-embed",
        dest="auto_embed",
        action="store_true",
        default=True,
        help="Usar AMI+FNN",
    )
    parser.add_argument(
        "--no-auto-embed",
        dest="auto_embed",
        action="store_false",
        help="Desativar AMI+FNN",
    )
    parser.add_argument("--max-tau", type=int, default=60, help="Tau maximo para AMI")
    parser.add_argument("--max-m", type=int, default=12, help="m maximo para FNN")
    parser.add_argument("--ami-bins", type=int, default=32, help="Bins para AMI")
    parser.add_argument("--fnn-threshold", type=float, default=0.02, help="Threshold FNN para escolher m")
    parser.add_argument("--k", type=int, default=10, help="k do kNN local")
    parser.add_argument("--horizon", type=int, default=30, help="Horizonte maximo (multi-step)")
    parser.add_argument("--mape-threshold", type=float, default=5.0, help="Limiar de MAPE para horizonte util")
    parser.add_argument("--target-type", default="log_return", choices=["log_return", "simple_return", "volatility"])
    parser.add_argument("--emit-api-records", action="store_true", help="Gera api_records.jsonl e api_records.csv")
    args = parser.parse_args()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    tickers = tickers[: max(0, int(args.debug_limit))]
    if not tickers:
        raise ValueError("Nenhum ticker informado.")
    horizons = [int(x) for x in args.horizons.split(",") if x.strip().isdigit()]
    if not horizons:
        horizons = [1, 5]

    base_dir = ROOT
    outdir = os.path.join(base_dir, args.outdir)
    os.makedirs(outdir, exist_ok=True)

    summaries = []
    for ticker in tickers:
        df = load_or_fetch(ticker, base_dir, start=args.start, end=args.end, allow_downloads=args.allow_downloads)
        if df is None or df.empty:
            continue
        df = df[(df["date"] >= args.start) & (df["date"] <= args.end)].copy()
        # prepare financial dataset
        spec = FinancialDatasetSpec(
            entity_name=ticker,
            freq="daily",
            date_col="date",
            price_col="price",
            return_col="r",
            target_type=args.target_type,
        )
        prepared, meta = prepare_financial_series(df, spec)
        train_df, test_df = split_train_test(prepared, "2024-12-31")
        train_df, test_df, norm_meta = standardize_train_test(train_df, test_df)
        # naive baseline
        naive = test_df["y_raw"].shift(1).bfill()
        # simple model placeholder: predict zero (no heavy model)
        y_pred_raw = np.zeros_like(test_df["y_raw"].to_numpy())
        y_pred_std = np.zeros_like(test_df["y"].to_numpy())
        metrics = compute_metrics(
            test_df["y_raw"].to_numpy(),
            y_pred_raw,
            test_df["y"].to_numpy(),
            y_pred_std,
            naive.to_numpy(),
            spec.target_type,
        )
        # confidence
        error_std = float(np.std(test_df["y_raw"].to_numpy() - y_pred_raw))
        transition_rate = float(np.mean(np.sign(test_df["y_raw"].to_numpy()[1:]) != np.sign(test_df["y_raw"].to_numpy()[:-1])))
        novelty = 0.0
        confidence = compute_confidence_finance(metrics, error_std, transition_rate, novelty)
        # outputs
        ticker_dir = os.path.join(outdir, ticker.replace("^", ""))
        os.makedirs(ticker_dir, exist_ok=True)
        summary_row = {
            "ticker": ticker,
            "mae_raw": metrics.get("mae_raw"),
            "rmse_raw": metrics.get("rmse_raw"),
            "mase": metrics.get("mase"),
            "dir_acc": metrics.get("dir_acc"),
            "n_samples": int(len(test_df)),
            "warnings": meta.get("warning_scale", ""),
        }
        summaries.append(summary_row)
        # write confidence/verdict
        pd.DataFrame(confidence["breakdown"]).to_csv(os.path.join(ticker_dir, "confidence_breakdown.csv"), index=False)
        with open(os.path.join(ticker_dir, "verdict.json"), "w", encoding="utf-8") as f:
            json.dump(confidence, f, indent=2)
        with open(os.path.join(ticker_dir, "summary_finance.json"), "w", encoding="utf-8") as f:
            json.dump({"metrics": metrics, "meta": meta, "norm": norm_meta}, f, indent=2)
        # standardized summary table per asset
        summary_table = pd.DataFrame([{
            "run_id": "",
            "entity_name": ticker,
            "system_type": "finance",
            "ticker": ticker,
            "freq": "daily",
            "method": "financial_sanity",
            "n_samples": int(len(test_df)),
            "dt": "",
            "m": "",
            "tau": "",
            "cluster_id": "",
            "label": "",
            "pct_time": "",
            "n_segments": "",
            "mean_duration": "",
            "std_duration": "",
            "energy_mean": "",
            "energy_std": "",
            "entropy_mean": "",
            "recurrence_mean": "",
            "notes": meta.get("warning_scale", ""),
        }])
        summary_table.to_csv(os.path.join(ticker_dir, "summary.csv"), index=False)
        # master plot
        plot_master_finance(
            test_df["date"],
            test_df["y_raw"].to_numpy(),
            y_pred_raw,
            naive.to_numpy(),
            os.path.join(ticker_dir, "master_plot.png"),
            confidence,
        )
        # legacy phase benchmark disabled in financial sanity mode

    summary_path = os.path.join(outdir, "summary_all.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    report_path = os.path.join(outdir, "report.md")
    lines = [
        "# Finance Benchmark (sanity)",
        "",
        "| ticker | mae_raw | rmse_raw | mase | dir_acc | n_samples | warnings |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in summaries:
        lines.append(
            "| {ticker} | {mae_raw:.6f} | {rmse_raw:.6f} | {mase:.3f} | {dir_acc} | {n_samples} | {warnings} |".format(
                ticker=row.get("ticker"),
                mae_raw=row.get("mae_raw", float("nan")),
                rmse_raw=row.get("rmse_raw", float("nan")),
                mase=row.get("mase", float("nan")),
                dir_acc=row.get("dir_acc", float("nan")),
                n_samples=row.get("n_samples", 0),
                warnings=row.get("warnings", ""),
            )
        )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\\n".join(lines))

    if args.emit_api_records:
        records = []
        horizon_default = horizons[0] if horizons else 1
        for row in summaries:
            warnings = [w for w in str(row.get("warnings", "")).split(";") if w]
            records.append(
                PredictionRecord(
                    timestamp=str(args.end),
                    asset=row.get("ticker", ""),
                    timeframe="daily",
                    horizon=horizon_default,
                    regime_label=None,
                    regime_confidence=None,
                    regime_risk=None,
                    novelty_score=None,
                    transition_rate=None,
                    entropy=None,
                    y_true=None,
                    y_pred=None,
                    y_pred_p10=None,
                    y_pred_p50=None,
                    y_pred_p90=None,
                    model_name="zero_model",
                    model_family="naive",
                    forecast_confidence=None,
                    warnings=warnings,
                    mase_6m=row.get("mase"),
                    smape_6m=None,
                    diracc_6m=row.get("dir_acc"),
                )
            )
        save_prediction_records(
            records,
            os.path.join(outdir, "api_records.jsonl"),
            os.path.join(outdir, "api_records.csv"),
        )


if __name__ == "__main__":
    main()

