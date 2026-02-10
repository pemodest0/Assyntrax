#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


def _load_series(path: Path, date_col: str = "date", value_col: str = "value") -> pd.DataFrame:
    df = pd.read_csv(path)
    if date_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"missing required columns in {path}: {date_col},{value_col}")
    out = df[[date_col, value_col]].copy()
    out.columns = ["date", "value"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["date", "value"]).sort_values("date")
    return out


def _load_monthly_rate(path: Path) -> pd.DataFrame:
    df = _load_series(path)
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp("M")
    out = df.groupby("date", as_index=False)["value"].mean()
    out.columns = ["date", "J"]
    return out


def _compute_liquidity_proxy(price: pd.Series, window: int = 3) -> pd.Series:
    ret = price.pct_change().abs()
    vol = ret.rolling(window=window, min_periods=max(2, window // 2)).mean()
    liq = 1.0 / (1e-6 + vol)
    liq = (liq - liq.median()) / (liq.std(ddof=0) + 1e-9)
    return liq


def _find_discount_series(raw_dir: Path) -> pd.DataFrame | None:
    # Try ABRAINC/FipeZap CSVs if they exist and contain desconto-like columns.
    candidates = list(raw_dir.glob("**/*.csv"))
    patt = re.compile(r"descont|deságio|desagio|spread", re.IGNORECASE)
    for p in candidates:
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = list(df.columns)
        date_cols = [c for c in cols if c.lower() in {"date", "data", "mes", "month"}]
        if not date_cols:
            continue
        disc_cols = [c for c in cols if patt.search(str(c))]
        if not disc_cols:
            continue
        dcol = date_cols[0]
        vcol = disc_cols[0]
        out = df[[dcol, vcol]].copy()
        out.columns = ["date", "D"]
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out["D"] = pd.to_numeric(out["D"], errors="coerce")
        out = out.dropna(subset=["date", "D"]).sort_values("date")
        if len(out) >= 24:
            out["date"] = out["date"].dt.to_period("M").dt.to_timestamp("M")
            return out.groupby("date", as_index=False)["D"].mean()
    return None


def _find_liquidity_series(raw_dir: Path) -> pd.DataFrame | None:
    # Try ABRAINC/FipeZap CSVs if they exist and contain duration/stock-like liquidity proxies.
    candidates = list(raw_dir.glob("**/*.csv"))
    patt = re.compile(r"duracao|dura[cç][aã]o|estoque|vendas.*estoque|giro", re.IGNORECASE)
    for p in candidates:
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = list(df.columns)
        date_cols = [c for c in cols if c.lower() in {"date", "data", "mes", "month"}]
        if not date_cols:
            continue
        liq_cols = [c for c in cols if patt.search(str(c))]
        if not liq_cols:
            continue
        dcol = date_cols[0]
        vcol = liq_cols[0]
        out = df[[dcol, vcol]].copy()
        out.columns = ["date", "L"]
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out["L"] = pd.to_numeric(out["L"], errors="coerce")
        out = out.dropna(subset=["date", "L"]).sort_values("date")
        if len(out) >= 24:
            out["date"] = out["date"].dt.to_period("M").dt.to_timestamp("M")
            return out.groupby("date", as_index=False)["L"].mean()
    return None


def _adequacy(df: pd.DataFrame, min_points: int = 60, max_gap_days: int = 62) -> dict:
    if df.empty:
        return {
            "status": "fail",
            "reason": "empty_dataset",
            "n_points": 0,
            "coverage_years": 0.0,
            "gap_ratio": 1.0,
        }
    dates = pd.to_datetime(df["date"])
    diffs = dates.diff().dt.days.dropna()
    gap_ratio = float((diffs > max_gap_days).mean()) if len(diffs) else 0.0
    coverage_years = float((dates.max() - dates.min()).days / 365.25)
    missing_ratio = float(df[["P", "L", "J"]].isna().mean().mean())
    status = "ok"
    reason = ""
    if len(df) < min_points:
        status = "fail"
        reason = f"n_points_below_min_{min_points}"
    elif coverage_years < 5:
        status = "watch"
        reason = "coverage_below_5y"
    elif gap_ratio > 0.2:
        status = "watch"
        reason = "high_gap_ratio"
    elif missing_ratio > 0.15:
        status = "watch"
        reason = "high_missing_ratio"
    return {
        "status": status,
        "reason": reason,
        "n_points": int(len(df)),
        "coverage_years": coverage_years,
        "gap_ratio": gap_ratio,
        "missing_ratio_core": missing_ratio,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build offline real-estate core dataset (P,L,J,D) from local files.")
    parser.add_argument("--normalized-dir", default="data/realestate/normalized")
    parser.add_argument("--raw-dir", default="data/raw/realestate")
    parser.add_argument("--outdir", default="data/realestate/core")
    parser.add_argument("--validation-outdir", default="results/validation/realestate_offline")
    parser.add_argument("--min-points", type=int, default=60)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    np.random.seed(args.seed)
    normalized_dir = Path(args.normalized_dir)
    raw_dir = Path(args.raw_dir)
    outdir = Path(args.outdir)
    validation_outdir = Path(args.validation_outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    validation_outdir.mkdir(parents=True, exist_ok=True)

    price_files = sorted(normalized_dir.glob("FipeZap_*_Total.csv"))
    if not price_files:
        summary = {"status": "fail", "reason": "no_price_files", "n_assets": 0}
        (validation_outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("[fail] no FipeZap_*_Total.csv found")
        return

    selic_path = normalized_dir / "SELIC_D_11.csv"
    if not selic_path.exists():
        summary = {"status": "fail", "reason": "missing_SELIC_D_11.csv", "n_assets": 0}
        (validation_outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("[fail] missing SELIC_D_11.csv")
        return

    rate = _load_monthly_rate(selic_path)
    global_liq = _find_liquidity_series(raw_dir)
    global_disc = _find_discount_series(raw_dir)

    rows: list[dict] = []
    for pf in price_files:
        asset_id = pf.stem
        price_df = _load_series(pf)
        price_df["date"] = price_df["date"].dt.to_period("M").dt.to_timestamp("M")
        price_monthly = price_df.groupby("date", as_index=False)["value"].mean()
        price_monthly.columns = ["date", "P"]

        frame = price_monthly.merge(rate, on="date", how="left")
        if global_liq is not None:
            frame = frame.merge(global_liq, on="date", how="left")
            liq_source = "official_proxy"
        else:
            frame["L"] = _compute_liquidity_proxy(frame["P"])
            liq_source = "price_vol_proxy"

        if global_disc is not None:
            frame = frame.merge(global_disc, on="date", how="left")
            disc_source = "official_discount"
        else:
            frame["D"] = np.nan
            disc_source = "missing"

        frame = frame.sort_values("date").reset_index(drop=True)
        frame.to_csv(outdir / f"{asset_id}_core.csv", index=False)

        adeq = _adequacy(frame, min_points=args.min_points)
        adeq.update(
            {
                "asset_id": asset_id,
                "liquidity_source": liq_source,
                "discount_source": disc_source,
                "has_D": bool(frame["D"].notna().any()),
            }
        )
        rows.append(adeq)

    adequacy_df = pd.DataFrame(rows).sort_values(["status", "asset_id"])
    adequacy_df.to_csv(validation_outdir / "adequacy.csv", index=False)

    ok_count = int((adequacy_df["status"] == "ok").sum())
    watch_count = int((adequacy_df["status"] == "watch").sum())
    fail_count = int((adequacy_df["status"] == "fail").sum())
    summary = {
        "status": "ok" if ok_count > 0 else "fail",
        "n_assets": int(len(adequacy_df)),
        "ok": ok_count,
        "watch": watch_count,
        "fail": fail_count,
        "min_points": int(args.min_points),
        "notes": [
            "P(t)=FipeZap price index (monthly).",
            "L(t)=official liquidity proxy if found, else price volatility proxy.",
            "J(t)=SELIC monthly mean.",
            "D(t)=official discount when available, otherwise missing (TODO).",
        ],
    }
    (validation_outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[ok] assets={summary['n_assets']} ok={ok_count} watch={watch_count} fail={fail_count}")


if __name__ == "__main__":
    main()

