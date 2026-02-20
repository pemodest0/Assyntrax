#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


SECTOR_PROXIES: dict[str, str] = {
    "XLB": "materials",
    "XLE": "energy",
    "XLF": "financials",
    "XLI": "industrials",
    "XLK": "technology",
    "XLP": "consumer_staples",
    "XLRE": "real_estate",
    "XLU": "utilities",
    "XLV": "health_care",
    "XLY": "consumer_discretionary",
}


@dataclass
class InferResult:
    group: str
    source: str
    proxy: str
    corr: float
    n_obs: int


def _read_list(path: Path) -> list[str]:
    return [x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _load_base_map(paths: list[Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in paths:
        if not p.exists():
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = {str(c).lower(): str(c) for c in df.columns}
        a_col = cols.get("asset") or cols.get("ticker") or cols.get("symbol")
        g_col = cols.get("group") or cols.get("sector") or cols.get("category")
        if not a_col or not g_col:
            continue
        for _, r in df.iterrows():
            a = str(r[a_col]).strip()
            g = str(r[g_col]).strip()
            if a and g:
                out[a] = g
    return out


def _load_returns(path: Path, start_date: str) -> pd.Series | None:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    if "date" not in df.columns:
        return None
    if "r" in df.columns:
        val_col = "r"
    elif "price" in df.columns:
        val_col = "price"
    else:
        return None
    d = df[["date", val_col]].copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date", val_col]).sort_values("date")
    d = d[d["date"] >= pd.to_datetime(start_date)]
    if d.empty:
        return None
    if val_col == "price":
        px = pd.to_numeric(d["price"], errors="coerce")
        rets = np.log(px / px.shift(1))
        d["ret"] = rets
        d = d.dropna(subset=["ret"])
        s = pd.Series(d["ret"].to_numpy(dtype=float), index=d["date"])
    else:
        s = pd.Series(pd.to_numeric(d["r"], errors="coerce").to_numpy(dtype=float), index=d["date"]).dropna()
    if s.empty:
        return None
    return s


def _infer_group(
    ticker: str,
    base_map: dict[str, str],
    proxy_returns: dict[str, pd.Series],
    ticker_returns: pd.Series | None,
    min_obs: int,
    min_corr: float,
) -> InferResult:
    t = str(ticker).strip()
    if t in base_map:
        return InferResult(group=base_map[t], source="base_map", proxy="", corr=float("nan"), n_obs=0)
    if t.endswith("-USD"):
        return InferResult(group="crypto", source="rule_crypto", proxy="", corr=float("nan"), n_obs=0)
    if t.startswith("^"):
        return InferResult(group="indices_macro", source="rule_index", proxy="", corr=float("nan"), n_obs=0)

    if ticker_returns is None:
        return InferResult(group="equities_us_other", source="fallback_no_data", proxy="", corr=float("nan"), n_obs=0)

    best_proxy = ""
    best_group = "equities_us_other"
    best_corr = -2.0
    best_n = 0
    for px, grp in SECTOR_PROXIES.items():
        pr = proxy_returns.get(px)
        if pr is None or pr.empty:
            continue
        m = pd.concat([ticker_returns.rename("a"), pr.rename("b")], axis=1, join="inner").dropna()
        n = int(m.shape[0])
        if n < min_obs:
            continue
        corr = float(m["a"].corr(m["b"]))
        if not np.isfinite(corr):
            continue
        if corr > best_corr:
            best_corr = corr
            best_proxy = px
            best_group = grp
            best_n = n
    if best_proxy and best_corr >= min_corr:
        return InferResult(group=best_group, source="proxy_corr", proxy=best_proxy, corr=best_corr, n_obs=best_n)
    if best_proxy:
        return InferResult(group="equities_us_other", source="proxy_corr_low", proxy=best_proxy, corr=best_corr, n_obs=best_n)
    return InferResult(group="equities_us_other", source="fallback_no_proxy", proxy="", corr=float("nan"), n_obs=0)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build enriched sector map for the 470-asset universe.")
    ap.add_argument("--tickers-file", type=str, default="results/universe_470/tickers_470.txt")
    ap.add_argument("--prices-dir", type=str, default="data/raw/finance/yfinance_daily")
    ap.add_argument("--base-map", type=str, default="data/asset_groups.csv")
    ap.add_argument("--extra-map", type=str, default="results/finance_download/local_pack_20260218T060240Z/universe_fixed.csv")
    ap.add_argument("--start-date", type=str, default="2018-01-01")
    ap.add_argument("--min-obs", type=int, default=252)
    ap.add_argument("--min-corr", type=float, default=0.15)
    ap.add_argument("--out", type=str, default="data/asset_groups_470_enriched.csv")
    args = ap.parse_args()

    tickers = _read_list(ROOT / args.tickers_file)
    prices_dir = ROOT / args.prices_dir
    base_map = _load_base_map([ROOT / args.base_map, ROOT / args.extra_map])

    proxy_returns: dict[str, pd.Series] = {}
    for px in SECTOR_PROXIES:
        proxy_returns[px] = _load_returns(prices_dir / f"{px}.csv", start_date=args.start_date)

    rows: list[dict[str, object]] = []
    for t in tickers:
        s = _load_returns(prices_dir / f"{t}.csv", start_date=args.start_date)
        infer = _infer_group(
            ticker=t,
            base_map=base_map,
            proxy_returns=proxy_returns,
            ticker_returns=s,
            min_obs=int(args.min_obs),
            min_corr=float(args.min_corr),
        )
        rows.append(
            {
                "asset": t,
                "group": infer.group,
                "source": infer.source,
                "proxy": infer.proxy,
                "corr": infer.corr if np.isfinite(infer.corr) else "",
                "n_obs": infer.n_obs,
            }
        )

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["asset", "group", "source", "proxy", "corr", "n_obs"])
        w.writeheader()
        w.writerows(rows)

    df = pd.DataFrame(rows)
    counts = df["group"].value_counts(dropna=False).to_dict()
    print({"status": "ok", "assets": int(df.shape[0]), "groups": counts, "out": str(out)})


if __name__ == "__main__":
    main()
