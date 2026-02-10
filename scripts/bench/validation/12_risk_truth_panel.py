#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = ROOT / "results" / "validation"
DEFAULT_OUT = DEFAULT_ROOT / "risk_truth_panel.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_float(x: Any) -> float | None:
    try:
        return float(x)
    except Exception:
        return None


def _safe_bool(x: Any) -> bool:
    s = str(x).strip().lower()
    if s in {"1", "true", "yes", "y"}:
        return True
    if s in {"0", "false", "no", "n", ""}:
        return False
    return bool(x)


def _risk_status(conf: float | None, quality: float | None, transition: float | None) -> str:
    if conf is None or quality is None or transition is None:
        return "inconclusive"
    if conf >= 0.70 and quality >= 0.80 and transition <= 0.35:
        return "validated"
    if conf >= 0.55 and quality >= 0.70 and transition <= 0.50:
        return "watch"
    return "inconclusive"


def build_panel(root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    adaptive_map: dict[str, dict[str, Any]] = {}
    thresholds_map: dict[str, dict[str, Any]] = {}
    adequacy_map: dict[str, dict[str, Any]] = {}
    hybrid_map: dict[str, dict[str, Any]] = {}

    adaptive_csv = root / "adaptive_gates" / "latest_status.csv"
    if adaptive_csv.exists():
        try:
            adf = pd.read_csv(adaptive_csv)
            for _, r in adf.iterrows():
                asset = str(r.get("asset", "")).strip()
                if not asset:
                    continue
                adaptive_map[asset] = {
                    "status_hysteresis": str(r.get("status_hysteresis", "inconclusive")).lower(),
                    "status_raw": str(r.get("status_raw", "inconclusive")).lower(),
                    "confidence": _safe_float(r.get("confidence")),
                    "quality": _safe_float(r.get("quality")),
                    "transition": _safe_float(r.get("transition")),
                    "instability_score": _safe_float(r.get("instability_score")),
                    "changepoint_flag": _safe_bool(r.get("changepoint_flag", False)),
                    "regime_age_days": _safe_float(r.get("regime_age_days")),
                    "hazard_score": _safe_float(r.get("hazard_score")),
                    "status_reason": str(r.get("status_reason", "")),
                }
        except Exception:
            adaptive_map = {}

    thr_csv = root / "adaptive_gates" / "adaptive_thresholds.csv"
    if thr_csv.exists():
        try:
            tdf = pd.read_csv(thr_csv)
            if not tdf.empty:
                tdf = tdf.sort_values(["asset", "run_id"]).groupby("asset", as_index=False).tail(1)
                for _, r in tdf.iterrows():
                    asset = str(r.get("asset", "")).strip()
                    if not asset:
                        continue
                    hp = _safe_float(r.get("history_points"))
                    thresholds_map[asset] = {
                        "thr_conf": _safe_float(r.get("thr_conf")),
                        "thr_quality": _safe_float(r.get("thr_quality")),
                        "thr_transition": _safe_float(r.get("thr_transition")),
                        "thr_instability": _safe_float(r.get("thr_instability")),
                        "thr_changepoint_delta": _safe_float(r.get("thr_changepoint_delta")),
                        "history_points": int(hp) if hp is not None else 0,
                    }
        except Exception:
            thresholds_map = {}

    adequacy_csv = root / "data_adequacy" / "data_adequacy_by_asset.csv"
    if adequacy_csv.exists():
        try:
            adq = pd.read_csv(adequacy_csv)
            for _, r in adq.iterrows():
                aid = str(r.get("asset_id", "")).strip()
                if not aid:
                    continue
                n_points = _safe_float(r.get("n_points"))
                max_gap = _safe_float(r.get("max_gap_days"))
                adequacy_map[aid] = {
                    "status": str(r.get("status", "unknown")),
                    "coverage_years": _safe_float(r.get("coverage_years")),
                    "n_points": int(n_points) if n_points is not None else 0,
                    "max_gap_days": int(max_gap) if max_gap is not None else 0,
                    "inferred_freq": str(r.get("inferred_freq", "")),
                    "source_type": str(r.get("source_type", "proxy")).lower(),
                    "source_name": str(r.get("source_name", "unknown")),
                    "reason": "" if str(r.get("reason", "")).lower() == "nan" else str(r.get("reason", "")),
                }
        except Exception:
            adequacy_map = {}

    hybrid_csv = root / "hybrid_risk" / "hybrid_status_by_asset.csv"
    if hybrid_csv.exists():
        try:
            hdf = pd.read_csv(hybrid_csv)
            for _, r in hdf.iterrows():
                aid = str(r.get("asset_id", "")).strip()
                if not aid:
                    continue
                hybrid_map[aid] = {
                    "hybrid_status": str(r.get("hybrid_status", "")).lower(),
                    "hybrid_reason": str(r.get("reason", "")),
                    "ews_score": _safe_float(r.get("ews_score")),
                    "var95_hist": _safe_float(r.get("var95_hist")),
                    "ewma_sigma": _safe_float(r.get("ewma_sigma")),
                }
        except Exception:
            hybrid_map = {}

    # Universe-level micro metrics.
    master_csv = root / "universe_mini_full" / "master_summary.csv"
    if master_csv.exists():
        df = pd.read_csv(master_csv)
        for _, r in df.iterrows():
            asset = str(r.get("asset_id", ""))
            conf = _safe_float(r.get("mean_confidence"))
            qual = _safe_float(r.get("mean_quality"))
            trans = _safe_float(r.get("pct_transition"))
            base_status = _risk_status(conf, qual, trans)
            adp = adaptive_map.get(asset)
            final_status = adp["status_hysteresis"] if adp else base_status
            thr = thresholds_map.get(asset, {})
            adequacy = adequacy_map.get(asset, {})
            hybrid = hybrid_map.get(asset, {})
            entries.append(
                {
                    "asset_id": asset,
                    "scope": "universe_mini_full",
                    "micro": {
                        "mean_confidence": conf,
                        "mean_quality": qual,
                        "pct_transition": trans,
                    },
                    "macro": {},
                    "operational": {},
                    "gates": {
                        "status_reason": (adp or {}).get("status_reason"),
                        "changepoint_flag": (adp or {}).get("changepoint_flag"),
                        "regime_age_days": (adp or {}).get("regime_age_days"),
                        "hazard_score": (adp or {}).get("hazard_score"),
                        "hybrid_status": hybrid.get("hybrid_status"),
                        "hybrid_reason": hybrid.get("hybrid_reason"),
                        "hybrid_ews_score": hybrid.get("ews_score"),
                        "hybrid_var95_hist": hybrid.get("var95_hist"),
                        "hybrid_ewma_sigma": hybrid.get("ewma_sigma"),
                        "thresholds": thr,
                        "data_adequacy": adequacy,
                        "source_type": adequacy.get("source_type", "proxy"),
                        "source_name": adequacy.get("source_name", "unknown"),
                    },
                    "risk_truth_status": final_status,
                    "status_raw": adp["status_raw"] if adp else base_status,
                }
            )

    # Historical macro metrics (VIX/SPY/QQQ or any historical_shifts_* folder).
    for p in sorted(root.glob("historical_shifts*/metrics.json")):
        m = _read_json(p) or {}
        asset = str(m.get("asset", p.parent.name))
        macro = {
            "hit_rate_macro": _safe_float(m.get("hit_rate_macro")),
            "density_ratio_macro": _safe_float(m.get("density_ratio_macro")),
            "macro_block_rate_per_year": _safe_float(m.get("macro_block_rate_per_year")),
            "micro_switch_rate": _safe_float(m.get("micro_switch_rate")),
            "pseudo_bifurcation_flag": _safe_bool(m.get("pseudo_bifurcation_flag", False)),
        }
        existing = next((e for e in entries if e["asset_id"] == asset), None)
        if existing is None:
            entries.append(
                {
                    "asset_id": asset,
                    "scope": p.parent.name,
                    "micro": {},
                    "macro": macro,
                    "operational": {},
                    "risk_truth_status": "inconclusive",
                    "source_type": "proxy",
                }
            )
        else:
            existing["macro"].update(macro)

    # Operational metrics from realworld_vix test.
    rw = _read_json(root / "realworld_vix" / "metrics.json") or {}
    if rw:
        op = {
            "max_drawdown_A": _safe_float((rw.get("metrics_A") or {}).get("max_drawdown")),
            "max_drawdown_C": _safe_float((rw.get("metrics_C") or {}).get("max_drawdown")),
            "sharpe_A": _safe_float((rw.get("metrics_A") or {}).get("sharpe")),
            "sharpe_C": _safe_float((rw.get("metrics_C") or {}).get("sharpe")),
            "time_in_market_C": _safe_float((rw.get("metrics_C") or {}).get("time_in_market")),
        }
        # Attach to SPY when available.
        target = next((e for e in entries if e["asset_id"].upper() == "SPY"), None)
        if target is None:
            entries.append(
                {
                    "asset_id": "SPY",
                    "scope": "realworld_vix",
                    "micro": {},
                    "macro": {},
                    "operational": op,
                    "risk_truth_status": "inconclusive",
                    "source_type": "proxy",
                }
            )
        else:
            target["operational"].update(op)

    # Recompute status using best available micro keys unless adaptive status exists.
    for e in entries:
        if str(e.get("risk_truth_status", "")).lower() in {"validated", "watch", "inconclusive"}:
            continue
        micro = e.get("micro", {})
        status = _risk_status(
            _safe_float(micro.get("mean_confidence")),
            _safe_float(micro.get("mean_quality")),
            _safe_float(micro.get("pct_transition")),
        )
        e["risk_truth_status"] = status

    n = len(entries)
    validated = sum(1 for e in entries if e["risk_truth_status"] == "validated")
    watch = sum(1 for e in entries if e["risk_truth_status"] == "watch")
    inconclusive = n - validated - watch

    global_verdict = _read_json(root / "VERDICT.json") or {}
    out = {
        "status": "ok",
        "root": str(root),
        "global_validation_verdict": global_verdict.get("status"),
        "adaptive_thresholds_available": bool(thresholds_map),
        "data_adequacy_available": bool(adequacy_map),
        "hybrid_risk_available": bool(hybrid_map),
        "counts": {
            "assets": n,
            "validated": validated,
            "watch": watch,
            "inconclusive": inconclusive,
        },
        "entries": entries,
        "source_counts": {
            "official": int(sum(1 for e in entries if str((e.get("gates") or {}).get("source_type", e.get("source_type", "proxy"))).lower() == "official")),
            "proxy": int(sum(1 for e in entries if str((e.get("gates") or {}).get("source_type", e.get("source_type", "proxy"))).lower() != "official")),
        },
        "notes": [
            "Risk truth status uses adaptive gates with hysteresis when available.",
            "Macro and operational evidence are attached when available.",
            "API/dashboard should expose only validated/watch by default.",
        ],
    }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build consolidated risk truth panel for API/dashboard.")
    parser.add_argument("--root", type=str, default=str(DEFAULT_ROOT))
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = parser.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    payload = build_panel(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"risk_truth_panel ok | assets={payload['counts']['assets']} "
        f"validated={payload['counts']['validated']} watch={payload['counts']['watch']} "
        f"inconclusive={payload['counts']['inconclusive']}"
    )


if __name__ == "__main__":
    main()
