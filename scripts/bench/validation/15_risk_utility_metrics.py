#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "risk_utility"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_price(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    cols = {str(c).lower(): str(c) for c in df.columns}
    dc = cols.get("date") or cols.get("data") or cols.get("datetime") or cols.get("timestamp")
    if dc is None:
        raise ValueError(f"missing date col in {path.name}")
    value_col = cols.get("close") or cols.get("adj_close") or cols.get("value") or cols.get("price") or cols.get("valor")
    if value_col is None:
        raise ValueError(f"missing close/value col in {path.name}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[dc], errors="coerce"),
            "price": pd.to_numeric(df[value_col], errors="coerce"),
        }
    ).dropna()
    return out.sort_values("date").drop_duplicates("date")


def _load_vix_regimes(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    need = {"date", "label", "confidence", "quality"}
    if not need.issubset(set(df.columns)):
        raise ValueError("vix_regimes missing required columns")
    out = df[list(need)].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["confidence"] = pd.to_numeric(out["confidence"], errors="coerce")
    out["quality"] = pd.to_numeric(out["quality"], errors="coerce")
    out = out.dropna().sort_values("date")
    return out


def _metrics(r: np.ndarray) -> dict[str, float]:
    ann = 252.0
    mu = float(np.mean(r))
    sd = float(np.std(r, ddof=1)) if r.size > 1 else 0.0
    eq = np.exp(np.cumsum(r))
    peak = np.maximum.accumulate(eq)
    dd = eq / np.maximum(peak, 1e-12) - 1.0
    mdd = float(dd.min())
    ar = float(np.exp(mu * ann) - 1.0)
    av = float(sd * math.sqrt(ann))
    sharpe = float((mu * ann) / (sd * math.sqrt(ann) + 1e-12))
    return {
        "total_return": float(eq[-1] - 1.0),
        "annualized_return": ar,
        "annualized_vol": av,
        "sharpe": sharpe,
        "max_drawdown": mdd,
    }


def _build_exposure(regime: pd.Series, conf: pd.Series, quality: pd.Series) -> np.ndarray:
    emap = {"stable": 1.0, "transition": 0.5, "unstable": 0.0}
    out = []
    for lbl, c, q in zip(regime.astype(str), conf.to_numpy(dtype=float), quality.to_numpy(dtype=float)):
        l = lbl.lower()
        ex = emap.get(l, 0.5)
        if c < 0.55 or q < 0.35:
            ex = 0.5
        out.append(ex)
    arr = np.asarray(out, dtype=float)
    # 3-day hysteresis.
    for i in range(2, len(arr)):
        if arr[i] != arr[i - 1] and arr[i] != arr[i - 2]:
            arr[i] = arr[i - 1]
    return arr


def _lead_time(vix: pd.Series, signal: np.ndarray) -> float:
    idx = np.argsort(-vix.to_numpy(dtype=float))[:20]
    idx = np.sort(idx)
    leads = []
    for i in idx:
        j = i
        while j >= 0 and signal[j] < 0.8:
            j -= 1
        if j >= 0:
            leads.append(i - j)
    return float(np.mean(leads)) if leads else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser(description="Risk utility metrics: drawdown avoidance, regime metrics, lead-time.")
    parser.add_argument("--vix-regimes", type=str, default=str(ROOT / "results" / "validation" / "realworld_vix" / "vix_regimes.csv"))
    parser.add_argument("--assets-dir", type=str, default=str(ROOT / "data" / "raw" / "finance" / "yfinance_daily"))
    parser.add_argument("--assets", type=str, default="SPY,QQQ,IWM,GLD,TLT,BTC-USD")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        vix_reg = _load_vix_regimes(Path(args.vix_regimes))
    except Exception as exc:
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": str(exc)})
        print(f"[risk_utility] fail {exc}")
        return

    vix_price_path = None
    for cand in ["^VIX.csv", "VIX.csv", "^vix.csv", "vix.csv"]:
        p = Path(args.assets_dir) / cand
        if p.exists():
            vix_price_path = p
            break
    if vix_price_path is None:
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": "vix_price_file_missing"})
        print("[risk_utility] fail vix file")
        return
    try:
        vix_px = _load_price(vix_price_path).rename(columns={"price": "vix"})
    except Exception as exc:
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": f"vix_price_missing: {exc}"})
        print("[risk_utility] fail vix price")
        return

    assets = [a.strip() for a in args.assets.split(",") if a.strip()]
    rows: list[dict[str, Any]] = []
    for asset in assets:
        p = Path(args.assets_dir) / f"{asset}.csv"
        if not p.exists():
            continue
        try:
            price = _load_price(p).rename(columns={"price": "asset_price"})
        except Exception:
            continue
        df = price.merge(vix_reg, on="date", how="inner").merge(vix_px, on="date", how="left")
        if df.shape[0] < 400:
            continue
        r = np.log(df["asset_price"]).diff().fillna(0.0).to_numpy(dtype=float)
        exposure_a = np.ones(len(df), dtype=float)
        exposure_c = _build_exposure(df["label"], df["confidence"], df["quality"])
        m_a = _metrics(exposure_a * r)
        m_c = _metrics(exposure_c * r)

        by_regime = []
        for rg, rgdf in df.assign(ret=r).groupby(df["label"].astype(str).str.lower()):
            rr = rgdf["ret"].to_numpy(dtype=float)
            if rr.size < 20:
                continue
            by_regime.append(
                {
                    "regime": rg,
                    "n": int(rr.size),
                    "annualized_vol": float(np.std(rr, ddof=1) * np.sqrt(252.0)),
                    "max_drawdown_proxy": float(np.min(np.exp(np.cumsum(rr)) / np.maximum.accumulate(np.exp(np.cumsum(rr))) - 1.0)),
                }
            )
        lead = _lead_time(df["vix"], (exposure_c < 1.0).astype(float))
        rows.append(
            {
                "asset": asset,
                "n_points": int(df.shape[0]),
                "drawdown_avoidance": float(abs(m_a["max_drawdown"]) - abs(m_c["max_drawdown"])),
                "delta_sharpe": float(m_c["sharpe"] - m_a["sharpe"]),
                "lead_time_days_top_vix": None if np.isnan(lead) else float(lead),
                "metrics_A": m_a,
                "metrics_C": m_c,
                "regime_conditioned": by_regime,
            }
        )

    if not rows:
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": "no_assets_processed"})
        print("[risk_utility] fail no assets")
        return

    detail = pd.DataFrame(
        [
            {
                "asset": r["asset"],
                "n_points": r["n_points"],
                "drawdown_avoidance": r["drawdown_avoidance"],
                "delta_sharpe": r["delta_sharpe"],
                "lead_time_days_top_vix": r["lead_time_days_top_vix"],
            }
            for r in rows
        ]
    )
    detail.to_csv(outdir / "risk_utility_by_asset.csv", index=False)

    summary = {
        "status": "ok",
        "n_assets": len(rows),
        "mean_drawdown_avoidance": float(detail["drawdown_avoidance"].mean()),
        "mean_delta_sharpe": float(detail["delta_sharpe"].mean()),
        "mean_lead_time_days_top_vix": float(detail["lead_time_days_top_vix"].dropna().mean()) if detail["lead_time_days_top_vix"].notna().any() else None,
        "assets_positive_drawdown_avoidance": int((detail["drawdown_avoidance"] > 0).sum()),
        "assets_positive_delta_sharpe": int((detail["delta_sharpe"] > 0).sum()),
    }
    _json_dump(outdir / "risk_utility_report.json", {"summary": summary, "assets": rows})
    _json_dump(outdir / "summary.json", summary)
    print(
        f"[risk_utility] assets={summary['n_assets']} "
        f"mean_dd_avoid={summary['mean_drawdown_avoidance']:.4f} "
        f"mean_delta_sharpe={summary['mean_delta_sharpe']:.4f}"
    )


if __name__ == "__main__":
    main()
