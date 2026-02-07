#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def extract_total(src: Path, outdir: Path) -> Path:
    df = pd.read_csv(src, header=None)
    header_idx = df.index[df[1].astype(str).str.strip().eq("Data")]
    if header_idx.empty:
        raise ValueError(f"header row not found in {src.name}")
    hr = int(header_idx[0])
    headers = df.iloc[hr].tolist()
    try:
        total_col = headers.index("Total")
    except ValueError:
        raise ValueError(f"Total column not found in {src.name}")
    data = df.iloc[hr + 1 :].copy()
    data = data[[1, total_col]]
    data.columns = ["date", "value"]
    data = data.dropna(subset=["date"])
    data["date"] = pd.to_datetime(data["date"], errors="coerce").dt.date
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["date", "value"])

    outdir.mkdir(parents=True, exist_ok=True)
    name = src.stem.replace(" ", "_")
    dest = outdir / f"FipeZap_{name}_Total.csv"
    data.to_csv(dest, index=False)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", default="data/realestate/normalized")
    args = parser.parse_args()

    dest = extract_total(Path(args.input), Path(args.outdir))
    print(f"[ok] wrote {dest}")


if __name__ == "__main__":
    main()
