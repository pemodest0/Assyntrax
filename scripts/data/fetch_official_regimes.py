#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


def fetch_fred_series(series_id: str, api_key: str) -> pd.DataFrame:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    obs = data.get("observations", [])
    rows = []
    for o in obs:
        rows.append({"date": o["date"], series_id: o["value"]})
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.dropna(subset=["date"])


def fetch_cboe_vix() -> pd.DataFrame:
    url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    # CBOE format uses DATE column
    date_col = "DATE" if "DATE" in df.columns else df.columns[0]
    close_col = "CLOSE" if "CLOSE" in df.columns else df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.rename(columns={date_col: "date", close_col: "VIX"})
    df["VIX"] = pd.to_numeric(df["VIX"], errors="coerce")
    return df[["date", "VIX"]].dropna()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch official regime proxies (NBER, NFCI, VIX).")
    parser.add_argument("--outdir", default="results/official_regimes")
    parser.add_argument("--fred-key", default=os.environ.get("FRED_API_KEY", ""))
    args = parser.parse_args()

    if not args.fred_key:
        raise SystemExit("Missing FRED_API_KEY. Set env var or pass --fred-key.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    usrec = fetch_fred_series("USREC", args.fred_key)
    nfci = fetch_fred_series("NFCI", args.fred_key)
    vix = fetch_cboe_vix()

    # Merge all
    df = usrec.merge(nfci, on="date", how="outer").merge(vix, on="date", how="outer")
    df = df.sort_values("date").reset_index(drop=True)

    # Regime labels
    df["macro_regime"] = df["USREC"].map(lambda x: "RECESSION" if x == 1 else "EXPANSION")
    df["stress_regime"] = df["NFCI"].map(lambda x: "STRESS" if x > 0 else "NORMAL")
    df["vol_regime"] = pd.cut(
        df["VIX"],
        bins=[-1, 15, 25, 40, 200],
        labels=["LOW", "MED", "HIGH", "EXTREME"],
    )

    df.to_csv(outdir / "official_regimes.csv", index=False)

    meta = {
        "generated_at": datetime.utcnow().isoformat(),
        "sources": {
            "USREC": "FRED / NBER recession indicator",
            "NFCI": "FRED / Chicago Fed Financial Conditions Index",
            "VIX": "CBOE VIX daily prices",
        },
    }
    (outdir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[ok] wrote {outdir}/official_regimes.csv")


if __name__ == "__main__":
    main()
