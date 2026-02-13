#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

NASDAQ_SCREENER_URL = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&download=true&limit=9999"
STOOQ_URL_TEMPLATE = "https://stooq.com/q/d/l/?s={symbol}&i={interval}"
NASDAQ_HIST_URL_TEMPLATE = (
    "https://api.nasdaq.com/api/quote/{symbol}/historical"
    "?assetclass=stocks&fromdate={start}&todate={end}&limit=9999&offset=0"
)
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nasdaq.com/market-activity/stocks/screener",
}


@dataclass
class TickerMeta:
    symbol: str
    sector: str
    market_cap: float | None
    country: str | None


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _http_get_text(url: str, timeout_sec: int = 40) -> str:
    req = Request(url, headers=HTTP_HEADERS)
    with urlopen(req, timeout=timeout_sec) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _http_get_json(url: str, timeout_sec: int = 40) -> dict[str, Any]:
    raw = _http_get_text(url, timeout_sec=timeout_sec)
    return json.loads(raw)


def _parse_market_cap(value: Any) -> float | None:
    if value is None:
        return None
    txt = str(value).strip().replace(",", "")
    if not txt:
        return None
    try:
        cap = float(txt)
    except ValueError:
        return None
    return cap if np.isfinite(cap) and cap > 0 else None


def _valid_symbol(symbol: str) -> bool:
    s = str(symbol).strip().upper()
    if not s:
        return False
    return re.fullmatch(r"[A-Z][A-Z0-9\.\-]{0,9}", s) is not None


def _is_equity_like_name(name: str) -> bool:
    n = str(name).strip().lower()
    if not n:
        return False
    banned = (
        "warrant",
        "rights",
        "right",
        "unit",
        "depositary",
        "preferred",
        "etf",
        "etn",
        "trust",
        "fund",
        "bond",
        "note",
    )
    if any(tok in n for tok in banned):
        return False
    allowed = (
        "common stock",
        "ordinary shares",
        "class a",
        "class b",
        "class c",
    )
    return any(tok in n for tok in allowed)


def _fetch_nasdaq_universe() -> pd.DataFrame:
    payload = _http_get_json(NASDAQ_SCREENER_URL)
    rows = payload.get("data", {}).get("rows", [])
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Nasdaq screener returned no rows.")
    df = pd.DataFrame(rows)
    req_cols = {"symbol", "name", "sector", "country", "marketCap"}
    missing = req_cols.difference(set(df.columns))
    if missing:
        raise RuntimeError(f"Nasdaq screener missing columns: {sorted(missing)}")
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df["sector"] = df["sector"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    df["market_cap_num"] = df["marketCap"].apply(_parse_market_cap)
    df = df[df["symbol"].apply(_valid_symbol)]
    df = df[df["name"].apply(_is_equity_like_name)]
    df = df[df["sector"].str.len() > 0]
    df = df[df["market_cap_num"].notna()]
    df = df.drop_duplicates(subset=["symbol"], keep="first")
    return df.reset_index(drop=True)


def _select_top_by_sector(
    universe: pd.DataFrame,
    top_per_sector: int,
    country: str | None,
    sectors_filter: set[str] | None,
) -> tuple[list[TickerMeta], pd.DataFrame]:
    df = universe.copy()
    if country:
        df = df[df["country"].str.lower() == country.lower()]
    if sectors_filter:
        wanted = {s.lower() for s in sectors_filter}
        df = df[df["sector"].str.lower().isin(wanted)]
    if df.empty:
        raise RuntimeError("No rows left after country/sector filters.")

    picks: list[TickerMeta] = []
    stats: list[dict[str, Any]] = []
    for sector, g in df.groupby("sector", dropna=False):
        gg = g.sort_values("market_cap_num", ascending=False).head(top_per_sector)
        stats.append(
            {
                "sector": str(sector),
                "available": int(g.shape[0]),
                "selected": int(gg.shape[0]),
                "market_cap_min_selected": float(gg["market_cap_num"].min()) if not gg.empty else None,
            }
        )
        for _, row in gg.iterrows():
            picks.append(
                TickerMeta(
                    symbol=str(row["symbol"]),
                    sector=str(row["sector"]),
                    market_cap=float(row["market_cap_num"]) if pd.notna(row["market_cap_num"]) else None,
                    country=str(row["country"]) if pd.notna(row["country"]) else None,
                )
            )
    picks = sorted(picks, key=lambda x: (x.sector, -(x.market_cap or 0.0), x.symbol))
    return picks, pd.DataFrame(stats).sort_values("sector").reset_index(drop=True)


def _to_stooq_symbol(symbol: str) -> str:
    return f"{symbol.strip().upper().replace('.', '-').lower()}.us"


def _download_stooq_csv(stooq_symbol: str, interval: str, timeout_sec: int = 40) -> pd.DataFrame:
    url = STOOQ_URL_TEMPLATE.format(symbol=stooq_symbol, interval=interval)
    txt = _http_get_text(url, timeout_sec=timeout_sec)
    if not txt.strip() or txt.lstrip().startswith("No data"):
        raise RuntimeError("no_data")
    df = pd.read_csv(io.StringIO(txt))
    cols = {str(c).strip().lower(): str(c) for c in df.columns}
    if "date" not in cols or "close" not in cols:
        raise RuntimeError("missing_date_close")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[cols["date"]], errors="coerce"),
            "price": pd.to_numeric(df[cols["close"]], errors="coerce"),
        }
    ).dropna()
    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if out.empty:
        raise RuntimeError("empty_after_parse")
    return out


def _download_nasdaq_csv(symbol: str, start: str, end: str, timeout_sec: int = 40) -> pd.DataFrame:
    sym = str(symbol).strip().upper()
    url = NASDAQ_HIST_URL_TEMPLATE.format(symbol=sym, start=start, end=end)
    req = Request(
        url,
        headers={
            "User-Agent": HTTP_HEADERS["User-Agent"],
            "Accept": HTTP_HEADERS["Accept"],
            "Referer": f"https://www.nasdaq.com/market-activity/stocks/{sym.lower()}/historical",
        },
    )
    with urlopen(req, timeout=timeout_sec) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    rows = payload.get("data", {}).get("tradesTable", {}).get("rows", [])
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("nasdaq_no_rows")

    records: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        d = str(row.get("date", "")).strip()
        c = str(row.get("close", "")).strip()
        if not d or not c:
            continue
        d_parsed = pd.to_datetime(d, format="%m/%d/%Y", errors="coerce")
        c_parsed = pd.to_numeric(c.replace("$", "").replace(",", ""), errors="coerce")
        if pd.isna(d_parsed) or pd.isna(c_parsed):
            continue
        records.append({"date": d_parsed, "price": float(c_parsed)})
    out = pd.DataFrame(records)
    if out.empty:
        raise RuntimeError("nasdaq_empty_after_parse")
    out = out.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return out


def _normalize_daily(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    out = df.copy()
    if start:
        out = out[out["date"] >= pd.Timestamp(start)]
    if end:
        out = out[out["date"] <= pd.Timestamp(end)]
    out = out.sort_values("date").reset_index(drop=True)
    out["price"] = out["price"].astype(float)
    out = out[out["price"] > 0.0].copy()
    out["log_price"] = np.log(out["price"])
    out["r"] = out["log_price"].diff()
    out = out.dropna(subset=["r"]).reset_index(drop=True)
    out["date"] = out["date"].dt.date.astype(str)
    return out[["date", "price", "log_price", "r"]]


def _download_one(
    meta: TickerMeta,
    out_dir: Path,
    interval: str,
    start: str | None,
    end: str | None,
    retries: int,
    sleep_ms: int,
) -> dict[str, Any]:
    stooq_symbol = _to_stooq_symbol(meta.symbol)
    last_err = ""
    source_used = "stooq"
    start_req = start or "2009-01-01"
    end_req = end or datetime.now(timezone.utc).date().isoformat()
    for attempt in range(retries):
        try:
            try:
                raw = _download_stooq_csv(stooq_symbol=stooq_symbol, interval=interval)
                source_used = "stooq"
            except Exception as stooq_exc:
                # Stooq often enforces daily hit limits. Fallback to Nasdaq endpoint.
                raw = _download_nasdaq_csv(symbol=meta.symbol, start=start_req, end=end_req)
                source_used = "nasdaq"
            norm = _normalize_daily(raw, start=start, end=end)
            if norm.empty:
                raise RuntimeError("empty_after_window")
            out_path = out_dir / f"{meta.symbol}.csv"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            norm.to_csv(out_path, index=False)
            return {
                "symbol": meta.symbol,
                "sector": meta.sector,
                "market_cap": meta.market_cap,
                "country": meta.country,
                "status": "ok",
                "rows": int(norm.shape[0]),
                "start": str(norm["date"].iloc[0]),
                "end": str(norm["date"].iloc[-1]),
                "file": str(out_path),
                "stooq_symbol": stooq_symbol,
                "source": source_used,
            }
        except (HTTPError, URLError, RuntimeError, ValueError) as exc:
            last_err = str(exc)
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
            time.sleep(0.4 * (attempt + 1))
    return {
        "symbol": meta.symbol,
        "sector": meta.sector,
        "market_cap": meta.market_cap,
        "country": meta.country,
        "status": "error",
        "rows": 0,
        "start": None,
        "end": None,
        "file": "",
        "stooq_symbol": stooq_symbol,
        "error": last_err,
    }


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser("Baixa series financeiras (Stooq) com universo setorial top-N por market cap.")
    parser.add_argument("--tickers", nargs="+", default=[], help="Tickers explicitos (NASDAQ/Yahoo style).")
    parser.add_argument("--top-per-sector", type=int, default=0, help="Seleciona top N por setor via Nasdaq screener.")
    parser.add_argument("--country", default="United States", help="Filtro de pais quando usar --top-per-sector.")
    parser.add_argument("--sectors", default="", help="Lista de setores separada por virgula (opcional).")
    parser.add_argument("--interval", default="d", choices=["d", "w", "m"], help="Intervalo no Stooq.")
    parser.add_argument("--start", default="2009-01-01", help="Data inicial YYYY-MM-DD.")
    parser.add_argument("--end", default=None, help="Data final YYYY-MM-DD (default: max disponivel).")
    parser.add_argument("--workers", type=int, default=8, help="Threads de download.")
    parser.add_argument("--retries", type=int, default=3, help="Tentativas por ticker.")
    parser.add_argument("--sleep-ms", type=int, default=0, help="Delay entre tentativas.")
    parser.add_argument("--max-assets", type=int, default=0, help="Limite global de ativos apos selecao (0 = sem limite).")
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw/finance/yfinance_daily"), help="Diretorio dos CSVs.")
    parser.add_argument("--results-dir", type=Path, default=Path("results/finance_download"), help="Pasta de relatorios.")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    run_id = _run_id()
    run_dir = args.results_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    sectors_filter = {s.strip() for s in str(args.sectors).split(",") if s.strip()} or None
    selected: list[TickerMeta] = []
    sector_stats = pd.DataFrame()

    if int(args.top_per_sector) > 0:
        universe = _fetch_nasdaq_universe()
        selected, sector_stats = _select_top_by_sector(
            universe=universe,
            top_per_sector=int(args.top_per_sector),
            country=str(args.country).strip() or None,
            sectors_filter=sectors_filter,
        )

    if args.tickers:
        for t in args.tickers:
            s = str(t).strip().upper()
            if not _valid_symbol(s):
                continue
            selected.append(TickerMeta(symbol=s, sector="manual", market_cap=None, country=None))

    dedup: dict[str, TickerMeta] = {}
    for item in selected:
        if item.symbol not in dedup:
            dedup[item.symbol] = item
    selected = list(dedup.values())

    if int(args.max_assets) > 0:
        selected = selected[: int(args.max_assets)]

    if not selected:
        raise SystemExit("Nenhum ticker selecionado. Use --tickers ou --top-per-sector > 0.")

    print(f"[finance] run_id={run_id}")
    print(f"[finance] selected_assets={len(selected)}")
    print(f"[finance] out_dir={args.out_dir}")

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
        futs = [
            ex.submit(
                _download_one,
                meta,
                Path(args.out_dir),
                str(args.interval),
                str(args.start) if args.start else None,
                str(args.end) if args.end else None,
                int(args.retries),
                int(args.sleep_ms),
            )
            for meta in selected
        ]
        for i, fut in enumerate(as_completed(futs), start=1):
            rec = fut.result()
            rows.append(rec)
            if rec.get("status") == "ok":
                print(f"[ok] {i}/{len(futs)} {rec['symbol']} rows={rec['rows']} range={rec['start']}..{rec['end']}")
            else:
                print(f"[err] {i}/{len(futs)} {rec['symbol']} ({rec.get('error', 'unknown')})")

    df = pd.DataFrame(rows).sort_values(["status", "sector", "symbol"]).reset_index(drop=True)
    ok_df = df[df["status"] == "ok"].copy()
    err_df = df[df["status"] != "ok"].copy()
    df.to_csv(run_dir / "download_manifest.csv", index=False)
    if not sector_stats.empty:
        sector_stats.to_csv(run_dir / "sector_selection.csv", index=False)
    if not err_df.empty:
        err_df.to_csv(run_dir / "download_failed.csv", index=False)

    summary = {
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "selected_assets": int(len(selected)),
        "ok_assets": int(ok_df.shape[0]),
        "failed_assets": int(err_df.shape[0]),
        "top_per_sector": int(args.top_per_sector),
        "country_filter": str(args.country),
        "sectors_filter": sorted(list(sectors_filter)) if sectors_filter else [],
        "start": str(args.start) if args.start else None,
        "end": str(args.end) if args.end else None,
        "out_dir": str(Path(args.out_dir)),
        "run_dir": str(run_dir),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[finance] ok_assets={summary['ok_assets']} failed={summary['failed_assets']}")
    print(f"[finance] summary={run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
