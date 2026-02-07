#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import date
from pathlib import Path
from typing import Iterable, List, Tuple
from urllib.parse import urlencode
from urllib.request import urlopen, Request

DEFAULT_FIPEZAP_URLS = [
    ("fipezap_serieshistoricas.xlsx", "https://downloads.fipe.org.br/indices/fipezap/fipezap-serieshistoricas.xlsx"),
    ("fipezap_historico.xlsx", "https://downloads.fipe.org.br/indices/fipezap/historico-fipezap-01.xlsx"),
]

# Conservative, widely used BCB SGS series ids
DEFAULT_BCB_IDS = [
    ("SELIC_D", 11),   # Selic diária
    ("IPCA_M", 433),   # IPCA
    ("INPC_M", 188),   # INPC
    ("IGPM_M", 189),   # IGP-M
]


def _chunked_year_ranges(start: int, end: int, span: int = 10) -> Iterable[Tuple[date, date]]:
    year = start
    while year <= end:
        s = date(year, 1, 1)
        e = date(min(year + span - 1, end), 12, 31)
        yield s, e
        year += span


def _fetch_bcb_series(series_id: int, start: int, end: int) -> List[dict]:
    rows: List[dict] = []
    for s, e in _chunked_year_ranges(start, end, span=10):
        query = urlencode({"formato": "json", "dataInicial": s.strftime("%d/%m/%Y"), "dataFinal": e.strftime("%d/%m/%Y")})
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados?{query}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Assyntrax)"})
        try:
            with urlopen(req) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            # fallback without date range
            fallback = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados?formato=json"
            req_fb = Request(fallback, headers={"User-Agent": "Mozilla/5.0 (Assyntrax)"})
            with urlopen(req_fb) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        rows.extend(payload)
    return rows


def _write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "valor"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"data": row.get("data"), "valor": row.get("valor")})


def _extract_excel_sheets(xlsx_path: Path, outdir: Path) -> None:
    try:
        import pandas as pd
    except Exception:
        return
    outdir.mkdir(parents=True, exist_ok=True)
    try:
        xls = pd.ExcelFile(xlsx_path)
    except Exception:
        return
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in sheet).strip("_")
        df.to_csv(outdir / f"{safe}.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="data/raw/realestate", help="Base output dir for downloads")
    parser.add_argument("--bcb-start-year", type=int, default=2000)
    parser.add_argument("--bcb-end-year", type=int, default=date.today().year)
    parser.add_argument("--bcb-ids", default="", help="Comma-separated list of id:name or id (e.g. 11:SELIC_D,433:IPCA_M)")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # FipeZap downloads
    fipezap_dir = outdir / "fipezap"
    fipezap_dir.mkdir(parents=True, exist_ok=True)
    def download(url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Assyntrax)"} )
        with urlopen(req) as resp, dest.open("wb") as f:
            f.write(resp.read())

    for fname, url in DEFAULT_FIPEZAP_URLS:
        dest = fipezap_dir / fname
        if not dest.exists():
            download(url, dest)
        _extract_excel_sheets(dest, fipezap_dir / "sheets")

    # BCB SGS downloads
    bcb_dir = outdir / "bcb"
    bcb_dir.mkdir(parents=True, exist_ok=True)
    series = list(DEFAULT_BCB_IDS)
    if args.bcb_ids:
        series = []
        for token in args.bcb_ids.split(","):
            token = token.strip()
            if ":" in token:
                sid, name = token.split(":", 1)
                series.append((name.strip(), int(sid.strip())))
            else:
                series.append((f"SERIE_{token}", int(token)))

    for name, sid in series:
        rows = _fetch_bcb_series(sid, args.bcb_start_year, args.bcb_end_year)
        _write_csv(bcb_dir / f"{name}_{sid}.csv", rows)


if __name__ == "__main__":
    main()
