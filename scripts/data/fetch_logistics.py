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
    parser = argparse.ArgumentParser(description="Fetch logistics indicators (manual URLs).")
    parser.add_argument("--outdir", default="data/logistics")
    parser.add_argument("--gscpi-url", default="https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.csv")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        df = fetch_csv(args.gscpi_url)
        df.to_csv(outdir / "gscpi.csv", index=False)
    except Exception:
        # keep script robust; handle failures upstream
        pass


if __name__ == "__main__":
    main()
