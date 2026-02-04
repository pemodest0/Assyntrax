#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import io
import pandas as pd
import requests


def fetch_csv(url: str) -> pd.DataFrame:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch real estate indicators (manual URLs).")
    parser.add_argument("--outdir", default="data/realestate")
    parser.add_argument("--bis-url", default="")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.bis_url:
        try:
            df = fetch_csv(args.bis_url)
            df.to_csv(outdir / "bis_housing.csv", index=False)
        except Exception:
            pass


if __name__ == "__main__":
    main()
