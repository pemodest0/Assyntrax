#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter, Retry


def fetch_dgs2(start: str, end: str, out: Path):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2&start_date={start}&end_date={end}"
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502,503,504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(resp.content)
    print(f"Salvo {out} ({len(resp.content)} bytes)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=str, help='YYYY-MM-DD')
    parser.add_argument('--end', type=str, help='YYYY-MM-DD')
    parser.add_argument('--out', type=str, default='dados/brutos/market_data/DGS2.csv')
    args = parser.parse_args()
    end = args.end or datetime.utcnow().strftime('%Y-%m-%d')
    if args.start:
        start = args.start
    else:
        start = (datetime.utcnow() - timedelta(days=int(25*365.25))).strftime('%Y-%m-%d')
    fetch_dgs2(start, end, Path(args.out))
