#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run(cmd: str) -> None:
    print(f"[run] {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=REPO)


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily data fetch + graph engine pipeline.")
    parser.add_argument("--fred-key", default=os.environ.get("FRED_API_KEY", ""))
    parser.add_argument("--tickers", default="")
    parser.add_argument("--timeframes", default="daily,weekly")
    parser.add_argument("--mode", default="fast", choices=["fast", "heavy"])
    parser.add_argument("--outdir", default="results/latest_graph")
    parser.add_argument("--auto-embed", action="store_true")
    parser.add_argument("--tau-method", default="ami", choices=["ami", "acf"])
    parser.add_argument("--m-method", default="cao", choices=["cao", "fnn"])
    args = parser.parse_args()

    if args.fred_key:
        run(f"python3 scripts/data/fetch_finance.py --fred-key {args.fred_key}")
    run("python3 scripts/data/fetch_logistics.py")
    run("python3 scripts/data/fetch_realestate.py")

    tickers = args.tickers
    if not tickers:
        # default: use existing yfinance tickers
        tickers = "$(ls data/raw/finance/yfinance_daily | sed 's/\\.csv$//' | paste -sd, -)"

    cmd = [
        "python3 scripts/bench/run_graph_regime_universe.py",
        f"--tickers \"{tickers}\"",
        f"--timeframes {args.timeframes}",
        f"--mode {args.mode}",
        f"--outdir {args.outdir}",
    ]
    if args.auto_embed:
        cmd.append("--auto-embed")
        cmd.append(f"--tau-method {args.tau_method}")
        cmd.append(f"--m-method {args.m_method}")
    run(" ".join(cmd))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"[error] command failed: {exc}")
        sys.exit(1)
