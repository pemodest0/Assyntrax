#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _find_price_file(prices_dir: Path, ticker: str) -> tuple[Path | None, str | None]:
    candidates = [ticker]
    if ticker.startswith("^"):
        candidates.append(ticker[1:])
    else:
        candidates.append("^" + ticker)
    for symbol in candidates:
        path = prices_dir / f"{symbol}.csv"
        if path.exists():
            return path, symbol
    return None, None


def _load_returns(path: Path, business_days_only: bool) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" not in df.columns or "r" not in df.columns:
        return pd.DataFrame(columns=["date", "r"])
    out = df[["date", "r"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["r"] = pd.to_numeric(out["r"], errors="coerce")
    out = out.dropna(subset=["date", "r"]).sort_values("date").drop_duplicates("date", keep="last")
    if business_days_only:
        out = out[out["date"].dt.dayofweek < 5]
    out["date"] = out["date"].dt.date.astype(str)
    return out.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build local finance pack (panel_long_sector + universe_fixed).")
    ap.add_argument("--prices-dir", type=str, default="data/raw/finance/yfinance_daily")
    ap.add_argument("--asset-groups", type=str, default="data/asset_groups.csv")
    ap.add_argument("--results-dir", type=str, default="results/finance_download")
    ap.add_argument("--business-days-only", type=int, default=1)
    ap.add_argument("--min-rows", type=int, default=252)
    args = ap.parse_args()

    prices_dir = ROOT / args.prices_dir
    groups_path = ROOT / args.asset_groups
    results_dir = ROOT / args.results_dir
    if not prices_dir.exists():
        raise SystemExit(f"prices dir not found: {prices_dir}")
    if not groups_path.exists():
        raise SystemExit(f"asset groups not found: {groups_path}")

    run_id = f"local_pack_{_run_id()}"
    outdir = results_dir / run_id
    outdir.mkdir(parents=True, exist_ok=True)

    groups = pd.read_csv(groups_path)
    if "asset" not in groups.columns or "group" not in groups.columns:
        raise SystemExit("asset_groups.csv must have columns: asset, group")

    panel_parts: list[pd.DataFrame] = []
    universe_rows: list[dict[str, Any]] = []
    missing: list[str] = []
    skipped_low_rows: list[str] = []

    for _, row in groups.iterrows():
        ticker = str(row["asset"]).strip()
        sector = str(row["group"]).strip()
        if not ticker:
            continue
        price_path, source_symbol = _find_price_file(prices_dir, ticker)
        if price_path is None:
            missing.append(ticker)
            continue
        rets = _load_returns(price_path, business_days_only=bool(int(args.business_days_only)))
        if rets.empty or int(rets.shape[0]) < int(args.min_rows):
            skipped_low_rows.append(ticker)
            continue
        rets["ticker"] = ticker
        rets["sector"] = sector
        panel_parts.append(rets[["date", "ticker", "sector", "r"]])
        universe_rows.append(
            {
                "ticker": ticker,
                "sector": sector,
                "source_file": str(price_path),
                "source_symbol": str(source_symbol),
                "n_rows": int(rets.shape[0]),
                "start": str(rets["date"].iloc[0]),
                "end": str(rets["date"].iloc[-1]),
            }
        )

    if not panel_parts:
        raise SystemExit("no valid assets found to build panel")

    panel = pd.concat(panel_parts, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)
    universe = pd.DataFrame(universe_rows).sort_values(["sector", "ticker"]).reset_index(drop=True)

    panel.to_csv(outdir / "panel_long_sector.csv", index=False)
    universe.to_csv(outdir / "universe_fixed.csv", index=False)

    meta = {
        "run_id": run_id,
        "outdir": str(outdir),
        "prices_dir": str(prices_dir),
        "asset_groups": str(groups_path),
        "business_days_only": bool(int(args.business_days_only)),
        "min_rows": int(args.min_rows),
        "panel_rows": int(panel.shape[0]),
        "assets_ok": int(universe.shape[0]),
        "assets_missing": int(len(missing)),
        "assets_skipped_low_rows": int(len(skipped_low_rows)),
        "missing_tickers": missing,
        "skipped_low_rows_tickers": skipped_low_rows,
        "period_start": str(panel["date"].min()),
        "period_end": str(panel["date"].max()),
    }
    (outdir / "build_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
