#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

SECTOR_HINTS: dict[str, str] = {
    "SPY": "equities_us_broad",
    "QQQ": "equities_us_broad",
    "DIA": "equities_us_broad",
    "IWM": "equities_us_broad",
    "VTI": "equities_us_broad",
    "RSP": "equities_us_broad",
    "XLF": "equities_us_sectors",
    "XLB": "equities_us_sectors",
    "XLI": "equities_us_sectors",
    "XLK": "equities_us_sectors",
    "XLP": "equities_us_sectors",
    "XLRE": "equities_us_sectors",
    "XLU": "equities_us_sectors",
    "XLV": "equities_us_sectors",
    "XLY": "equities_us_sectors",
    "KRE": "equities_us_sectors",
    "TLT": "rates_credit",
    "IEF": "rates_credit",
    "SHY": "rates_credit",
    "LQD": "rates_credit",
    "HYG": "rates_credit",
    "TIP": "rates_credit",
    "VIX": "volatility",
    "^VIX": "volatility",
    "GLD": "metals",
    "SLV": "metals",
    "USO": "energy_commodities",
    "DBC": "broad_commodities",
    "DBA": "agri_commodities",
    "XLE": "energy_commodities",
    "XOP": "energy_commodities",
    "UUP": "fx",
    "FXE": "fx",
    "FXY": "fx",
}


def _load_group_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {}
    cols = {str(c).lower(): str(c) for c in df.columns}
    a_col = cols.get("asset") or cols.get("ticker") or cols.get("symbol")
    g_col = cols.get("group") or cols.get("sector") or cols.get("category")
    if not a_col or not g_col:
        return {}
    out: dict[str, str] = {}
    for _, r in df.iterrows():
        out[str(r[a_col]).strip()] = str(r[g_col]).strip()
    return out


def _infer_sector(asset: str, group_map: dict[str, str]) -> str:
    a = str(asset).strip().upper()
    if a in group_map:
        return str(group_map[a])
    if a in SECTOR_HINTS:
        return SECTOR_HINTS[a]
    if a.endswith("-USD"):
        return "crypto"
    if a.startswith("^"):
        return "indices_macro"
    if a.isalpha() and 1 <= len(a) <= 5:
        return "equities_us"
    return "unknown"


def _to_float(v: Any) -> float:
    try:
        x = float(v)
        if np.isfinite(x):
            return x
    except Exception:
        pass
    return float("nan")


def _behavior_bucket(regime: str, confidence: float, alerts: list[str]) -> str:
    r = str(regime).upper()
    low_conf = bool(np.isfinite(confidence) and confidence < 0.45)
    has_instability_alert = any(str(a).upper() in {"REGIME_INSTAVEL", "NO_STRUCTURE"} for a in alerts)
    if r in {"UNSTABLE", "NOISY"} or has_instability_alert:
        return "fragil"
    if r == "TRANSITION" or low_conf:
        return "transicao"
    return "estavel"


def _risk_score(regime: str, confidence: float, quality: float, alerts: list[str]) -> float:
    r = str(regime).upper()
    regime_risk = 1.0 if r in {"UNSTABLE", "NOISY"} else (0.6 if r == "TRANSITION" else 0.2)
    conf_risk = 1.0 - (confidence if np.isfinite(confidence) else 0.0)
    qual_risk = 1.0 - (quality if np.isfinite(quality) else (confidence if np.isfinite(confidence) else 0.0))
    alert_risk = min(1.0, 0.25 * len(alerts))
    score = 0.45 * regime_risk + 0.30 * conf_risk + 0.20 * qual_risk + 0.05 * alert_risk
    return float(max(0.0, min(1.0, score)))


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize per-asset and per-sector diagnostics from universe outputs.")
    ap.add_argument("--assets-dir", type=str, default="results/latest_graph_universe470_batch/assets")
    ap.add_argument("--tickers-file", type=str, default="results/universe_470/tickers_470.txt")
    ap.add_argument("--group-map", type=str, default="")
    ap.add_argument("--outdir", type=str, default="results/latest_graph_universe470_batch")
    args = ap.parse_args()

    assets_dir = ROOT / args.assets_dir
    outdir = ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    target_tickers: list[str] = []
    tf = ROOT / args.tickers_file
    if tf.exists():
        target_tickers = [x.strip() for x in tf.read_text(encoding="utf-8").splitlines() if x.strip()]
    target_set = set(target_tickers)

    group_map_path = ROOT / args.group_map if str(args.group_map).strip() else None
    if group_map_path is None:
        enriched = ROOT / "data" / "asset_groups_470_enriched.csv"
        fallback = ROOT / "data" / "asset_groups.csv"
        group_map_path = enriched if enriched.exists() else fallback
    group_map = _load_group_map(group_map_path)
    rows: list[dict[str, Any]] = []

    for p in sorted(assets_dir.glob("*_daily.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        asset = str(d.get("asset", "")).strip()
        if not asset:
            continue
        st = d.get("state") or {}
        mt = d.get("metrics") or {}
        alerts = [str(x) for x in (d.get("alerts") or [])]
        regime = str(st.get("label", "UNKNOWN")).upper()
        confidence = _to_float(st.get("confidence"))
        quality = _to_float(d.get("quality"))
        stay_prob = _to_float(mt.get("stay_prob"))
        escape_prob = _to_float(mt.get("escape_prob"))
        stretch_mu = _to_float(mt.get("stretch_mu"))
        stretch_frac_pos = _to_float(mt.get("stretch_frac_pos"))
        sector = _infer_sector(asset=asset, group_map=group_map)
        behavior = _behavior_bucket(regime=regime, confidence=confidence, alerts=alerts)
        risk = _risk_score(regime=regime, confidence=confidence, quality=quality, alerts=alerts)
        rows.append(
            {
                "asset": asset,
                "sector": sector,
                "timeframe": str(d.get("timeframe", "daily")),
                "asof": str(d.get("asof", "")),
                "regime": regime,
                "confidence": confidence,
                "quality": quality if np.isfinite(quality) else confidence,
                "stay_prob": stay_prob,
                "escape_prob": escape_prob,
                "stretch_mu": stretch_mu,
                "stretch_frac_pos": stretch_frac_pos,
                "alerts_n": int(len(alerts)),
                "alerts": "|".join(alerts) if alerts else "",
                "behavior": behavior,
                "risk_score": risk,
                "in_target_470": bool((not target_set) or (asset in target_set)),
            }
        )

    assets_df = pd.DataFrame(rows)
    if assets_df.empty:
        raise SystemExit("no asset diagnostics found")

    sector_df = (
        assets_df.groupby("sector", as_index=False)
        .agg(
            n_assets=("asset", "count"),
            confidence_mean=("confidence", "mean"),
            quality_mean=("quality", "mean"),
            risk_score_mean=("risk_score", "mean"),
            stay_prob_mean=("stay_prob", "mean"),
            escape_prob_mean=("escape_prob", "mean"),
            stretch_mu_mean=("stretch_mu", "mean"),
            alerts_mean=("alerts_n", "mean"),
        )
    )
    for label in ["STABLE", "TRANSITION", "UNSTABLE", "NOISY"]:
        by = assets_df.groupby("sector")["regime"].apply(lambda s: float((s == label).mean())).rename(f"share_{label.lower()}")
        sector_df = sector_df.merge(by, on="sector", how="left")
    for b in ["estavel", "transicao", "fragil"]:
        byb = assets_df.groupby("sector")["behavior"].apply(lambda s: float((s == b).mean())).rename(f"share_behavior_{b}")
        sector_df = sector_df.merge(byb, on="sector", how="left")
    sector_df = sector_df.sort_values(["risk_score_mean", "n_assets"], ascending=[False, False]).reset_index(drop=True)

    n_target = int(len(target_tickers)) if target_tickers else int(assets_df.shape[0])
    n_done = int(assets_df.shape[0])
    coverage = float(n_done / n_target) if n_target > 0 else 1.0
    mean_conf = float(assets_df["confidence"].mean()) if not assets_df.empty else float("nan")
    mean_risk = float(assets_df["risk_score"].mean()) if not assets_df.empty else float("nan")
    fragil_share = float((assets_df["behavior"] == "fragil").mean()) if not assets_df.empty else float("nan")

    if coverage >= 0.80 and mean_conf >= 0.60:
        maturity = "alto"
    elif coverage >= 0.40 and mean_conf >= 0.50:
        maturity = "intermediario"
    else:
        maturity = "em_construcao"

    top_fragil = assets_df.sort_values(["risk_score", "confidence"], ascending=[False, True]).head(15)
    top_estavel = assets_df.sort_values(["risk_score", "confidence"], ascending=[True, False]).head(15)

    assets_df.to_csv(outdir / "diagnostics_assets_daily.csv", index=False)
    sector_df.to_csv(outdir / "diagnostics_sectors_daily.csv", index=False)
    top_fragil.to_csv(outdir / "diagnostics_top_fragil.csv", index=False)
    top_estavel.to_csv(outdir / "diagnostics_top_estavel.csv", index=False)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "assets_target": n_target,
        "assets_processed": n_done,
        "coverage_pct": float(100.0 * coverage),
        "maturity_level": maturity,
        "metrics": {
            "confidence_mean": mean_conf,
            "risk_score_mean": mean_risk,
            "fragil_share": fragil_share,
            "stable_share": float((assets_df["regime"] == "STABLE").mean()),
            "transition_share": float((assets_df["regime"] == "TRANSITION").mean()),
            "unstable_share": float((assets_df["regime"] == "UNSTABLE").mean()),
        },
        "sectors": sector_df.to_dict(orient="records"),
        "files": {
            "assets_csv": str(outdir / "diagnostics_assets_daily.csv"),
            "sectors_csv": str(outdir / "diagnostics_sectors_daily.csv"),
            "top_fragil_csv": str(outdir / "diagnostics_top_fragil.csv"),
            "top_estavel_csv": str(outdir / "diagnostics_top_estavel.csv"),
        },
    }
    (outdir / "diagnostics_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("Diagnostico Diario - Universo de Ativos")
    lines.append(f"assets_processados: {n_done}/{n_target} ({100.0*coverage:.2f}%)")
    lines.append(f"patamar_modelo: {maturity}")
    lines.append(
        f"medias: confidence={mean_conf:.3f}, risk_score={mean_risk:.3f}, fragil_share={fragil_share:.3f}"
    )
    lines.append("")
    lines.append("Setores por risco medio (top 10):")
    for _, r in sector_df.head(10).iterrows():
        lines.append(
            f"- {r['sector']}: n={int(r['n_assets'])}, risk={float(r['risk_score_mean']):.3f}, "
            f"conf={float(r['confidence_mean']):.3f}, stable={float(r.get('share_stable', np.nan)):.2f}, "
            f"transition={float(r.get('share_transition', np.nan)):.2f}, unstable={float(r.get('share_unstable', np.nan)):.2f}"
        )
    lines.append("")
    lines.append("Top ativos mais frageis (top 10):")
    for _, r in top_fragil.head(10).iterrows():
        lines.append(
            f"- {r['asset']} ({r['sector']}): regime={r['regime']}, risk={float(r['risk_score']):.3f}, conf={float(r['confidence']):.3f}"
        )
    lines.append("")
    lines.append("Top ativos mais estaveis (top 10):")
    for _, r in top_estavel.head(10).iterrows():
        lines.append(
            f"- {r['asset']} ({r['sector']}): regime={r['regime']}, risk={float(r['risk_score']):.3f}, conf={float(r['confidence']):.3f}"
        )
    (outdir / "diagnostics_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": "ok", "assets_processed": n_done, "assets_target": n_target, "coverage_pct": 100.0 * coverage, "maturity_level": maturity}, ensure_ascii=False))


if __name__ == "__main__":
    main()
