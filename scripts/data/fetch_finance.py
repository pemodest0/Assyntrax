#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests


def fetch_fred(series_id: str, api_key: str) -> pd.DataFrame:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": api_key, "file_type": "json"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("observations", [])
    rows = [{"date": o["date"], series_id: o["value"]} for o in data]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.dropna(subset=["date"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch finance macro series (FRED).")
    parser.add_argument("--outdir", default="data/finance")
    parser.add_argument("--fred-key", required=True)
    parser.add_argument("--series", default="DFF,DTB3,DTB6,SP500,VIXCLS,DEXUSEU")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    series_list = [s.strip() for s in args.series.split(",") if s.strip()]

    for sid in series_list:
        df = fetch_fred(sid, args.fred_key)
        df.to_csv(outdir / f"{sid}.csv", index=False)


if __name__ == "__main__":
    main()
