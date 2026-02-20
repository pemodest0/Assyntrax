#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run(cmd: list[str]) -> None:
    print("[run] " + " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=REPO)


def _default_tickers_csv() -> str:
    base = REPO / "data/raw/finance/yfinance_daily"
    if not base.exists():
        return ""
    tickers = sorted(p.stem for p in base.glob("*.csv") if p.is_file())
    return ",".join(tickers)


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
        run(["python3", "scripts/data/fetch_finance.py", "--fred-key", args.fred_key])
    run(["python3", "scripts/data/fetch_logistics.py"])
    run(["python3", "scripts/data/fetch_realestate.py"])

    tickers = args.tickers
    if not tickers:
        tickers = _default_tickers_csv()
        if not tickers:
            raise RuntimeError("No tickers found in data/raw/finance/yfinance_daily and --tickers was not provided.")

    cmd = ["python3", "scripts/bench/run_graph_regime_universe.py", "--tickers", tickers, "--timeframes", args.timeframes, "--mode", args.mode, "--outdir", args.outdir]
    if args.auto_embed:
        cmd.append("--auto-embed")
        cmd.extend(["--tau-method", args.tau_method, "--m-method", args.m_method])
    run(cmd)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"[error] command failed: {exc}")
        sys.exit(1)
