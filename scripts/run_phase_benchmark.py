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

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.yf_fetch_or_load import find_local_data, load_price_series, fetch_yfinance, unify_to_daily, save_cache
from spa.diagnostics_phase import run_for_group


def load_or_fetch(ticker, base_dir, start="2010-01-01", end="2025-12-31"):
    candidates = find_local_data(ticker, base_dir)
    df = None
    if candidates:
        df = load_price_series(candidates[0])
    if df is None:
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
    mape = [row.get("mape_2025", np.nan) for row in summary_rows]
    mape = [0 if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in mape]
    plt.figure(figsize=(8, 4))
    plt.bar(labels, mape, color="#1f77b4")
    plt.ylabel("MAPE (%)")
    plt.title("MAPE no teste (2025)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Benchmark de fase (finance) com auto-embed e horizonte")
    parser.add_argument("--tickers", required=True, help="Lista de tickers separados por virgula")
    parser.add_argument("--outdir", default="results/bench_finance", help="Diretorio de saida")
    parser.add_argument("--start", default="2010-01-01", help="Data inicial")
    parser.add_argument("--end", default="2025-12-31", help="Data final")
    parser.add_argument("--auto-embed", action="store_true", default=True, help="Usar AMI+FNN")
    parser.add_argument("--max-tau", type=int, default=60, help="Tau maximo para AMI")
    parser.add_argument("--max-m", type=int, default=12, help="m maximo para FNN")
    parser.add_argument("--ami-bins", type=int, default=32, help="Bins para AMI")
    parser.add_argument("--fnn-threshold", type=float, default=0.02, help="Threshold FNN para escolher m")
    parser.add_argument("--k", type=int, default=10, help="k do kNN local")
    parser.add_argument("--horizon", type=int, default=30, help="Horizonte maximo (multi-step)")
    parser.add_argument("--mape-threshold", type=float, default=5.0, help="Limiar de MAPE para horizonte util")
    args = parser.parse_args()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        raise ValueError("Nenhum ticker informado.")

    base_dir = ROOT
    outdir = os.path.join(base_dir, args.outdir)
    os.makedirs(outdir, exist_ok=True)

    summaries = []
    for ticker in tickers:
        df = load_or_fetch(ticker, base_dir, start=args.start, end=args.end)
        if df is None or df.empty:
            continue
        df = df[(df["date"] >= args.start) & (df["date"] <= args.end)].copy()
        ret_df = build_returns_df(df)
        ret_df["_group"] = ticker
        ticker_dir = os.path.join(outdir, ticker.replace("^", ""))
        os.makedirs(ticker_dir, exist_ok=True)
        summary = run_for_group(
            ret_df,
            ticker,
            "date",
            "value",
            ticker_dir,
            tau=4,
            m=4,
            k=args.k,
            auto_embed=args.auto_embed,
            max_tau=args.max_tau,
            max_m=args.max_m,
            ami_bins=args.ami_bins,
            fnn_threshold=args.fnn_threshold,
            horizon=args.horizon,
            mape_threshold=args.mape_threshold,
        )
        if summary:
            summary["ticker"] = ticker
            summaries.append(summary)

    summary_path = os.path.join(outdir, "summary_all.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)

    summary_rows = []
    for s in summaries:
        mape_2025 = None
        if s.get("test_year") == 2025:
            mape_2025 = s.get("metrics", {}).get("mape")
        summary_rows.append({"ticker": s.get("ticker"), "mape_2025": mape_2025})

    plot_ranking(summary_rows, os.path.join(outdir, "ranking_mape.png"))


if __name__ == "__main__":
    main()
