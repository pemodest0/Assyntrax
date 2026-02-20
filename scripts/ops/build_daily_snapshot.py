#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_adequacy_map(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for _, r in df.iterrows():
        aid = str(r.get("asset_id", "")).strip()
        if not aid:
            continue
        out[aid] = {
            "status": str(r.get("status", "unknown")).lower(),
            "source_type": str(r.get("source_type", "")).lower(),
            "source_name": str(r.get("source_name", "")),
            "coverage_years": pd.to_numeric(pd.Series([r.get("coverage_years")]), errors="coerce").iloc[0],
        }
    return out


def _infer_domain(group: str) -> str:
    g = (group or "").lower()
    if g in {"realestate", "imobiliario", "real_estate"}:
        return "realestate"
    if g in {"energy", "ons_grid", "logistics_energy"}:
        return "energy"
    return "finance"


def _apply_hysteresis(statuses: list[str], promote_days: int, degrade_days: int) -> list[str]:
    if not statuses:
        return statuses
    order = {"inconclusive": 0, "watch": 1, "validated": 2}
    out = [statuses[0]]
    current = statuses[0]
    candidate: str | None = None
    streak = 0
    for i in range(1, len(statuses)):
        s = statuses[i]
        if s == current:
            candidate = None
            streak = 0
            out.append(current)
            continue
        if candidate != s:
            candidate = s
            streak = 1
        else:
            streak += 1

        need = promote_days if order.get(s, 0) > order.get(current, 0) else degrade_days
        if streak >= max(1, need):
            current = s
            candidate = None
            streak = 0
        out.append(current)
    return out


def _instability_score(conf: float | None, qual: float | None) -> float | None:
    if conf is None or qual is None:
        return None
    # Conservative and deterministic score in [0,1].
    raw = ((1.0 - conf) + (1.0 - qual)) / 2.0
    return float(max(0.0, min(1.0, raw)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build daily API snapshot with conservative CI gate.")
    parser.add_argument("--run-id", type=str, default=datetime.now(timezone.utc).strftime("%Y%m%d"))
    parser.add_argument("--outdir", type=str, default="results/ops/snapshots")
    parser.add_argument("--source-status", type=str, default="results/validated/latest/asset_status.csv")
    parser.add_argument("--uncertainty", type=str, default="results/validation/uncertainty_full/summary.json")
    parser.add_argument("--gate-config", type=str, default="config/validation_gates.json")
    parser.add_argument("--production-gate", type=str, default="config/production_gate.v1.json")
    parser.add_argument("--protocol", type=str, default="config/v1_protocol.json")
    args = parser.parse_args()

    outdir = ROOT / args.outdir / args.run_id
    outdir.mkdir(parents=True, exist_ok=True)

    src = ROOT / args.source_status
    if not src.exists():
        summary = {"status": "fail", "reason": f"missing_source_status: {src}"}
        (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[snapshot] fail missing source {src}")
        return

    df = pd.read_csv(src)
    gate_cfg = _read_json(ROOT / args.gate_config)
    production_gate = _read_json(ROOT / args.production_gate)
    protocol = _read_json(ROOT / args.protocol)
    unc = _read_json(ROOT / args.uncertainty)

    conservative = unc.get("conservative_overall_metrics") or {}
    ci_conf = float(((conservative.get("mean_confidence") or {}).get("conservative_value")) or 0.55)
    ci_qual = float(((conservative.get("mean_quality") or {}).get("conservative_value")) or 0.35)

    fallback_conf = float(((protocol.get("production_gate") or {}).get("fallback_min_confidence")) or 0.55)
    fallback_qual = float(((protocol.get("production_gate") or {}).get("fallback_min_quality")) or 0.35)
    # Conservative CI is applied as a system-health guardrail, not per-asset hard threshold.
    min_conf_global = fallback_conf
    min_qual_global = fallback_qual

    domain_cfg = (gate_cfg.get("domains") or {})
    prod_domain_cfg = production_gate.get("domains") or {}
    prod_defaults = production_gate.get("defaults") or {}
    src_by_domain = production_gate.get("source_type_by_domain") or {}

    adequacy = _read_json(ROOT / "results" / "validation" / "data_adequacy" / "summary.json")
    adequacy_map = _read_adequacy_map(ROOT / "results" / "validation" / "data_adequacy" / "data_adequacy_by_asset.csv")
    adequacy_ok = str(adequacy.get("status", "")).lower() == "ok"

    out_rows = []
    for _, r in df.iterrows():
        asset = str(r.get("asset", ""))
        group = str(r.get("group", "unknown"))
        domain = _infer_domain(group)
        asset_adequacy = adequacy_map.get(asset, {})
        asset_adequacy_ok = str(asset_adequacy.get("status", "unknown")) == "ok"
        dcfg = domain_cfg.get(domain, {})
        min_conf = max(float(dcfg.get("min_confidence", 0.0)), min_conf_global)
        min_qual = max(float(dcfg.get("min_quality", 0.0)), min_qual_global)

        conf = pd.to_numeric(pd.Series([r.get("confidence")]), errors="coerce").iloc[0]
        qual = pd.to_numeric(pd.Series([r.get("quality")]), errors="coerce").iloc[0]
        # Keep payload numeric when one metric exists and the other is missing.
        if pd.isna(qual) and not pd.isna(conf):
            qual = conf
        if pd.isna(conf) and not pd.isna(qual):
            conf = qual
        regime = str(r.get("regime", "INCONCLUSIVE"))

        pdcfg = prod_domain_cfg.get(domain, {})
        vcfg = pdcfg.get("validated") or prod_defaults.get("validated") or {}
        wcfg = pdcfg.get("watch") or prod_defaults.get("watch") or {}
        min_conf_v = float(vcfg.get("min_confidence", 0.6))
        min_qual_v = float(vcfg.get("min_quality", 0.7))
        min_conf_w = float(wcfg.get("min_confidence", 0.45))
        min_qual_w = float(wcfg.get("min_quality", 0.55))

        if not asset_adequacy_ok or regime == "INCONCLUSIVE" or pd.isna(conf) or pd.isna(qual):
            signal_status = "inconclusive"
            reason = "data_adequacy_or_regime_inconclusive"
        elif float(conf) >= min_conf_v and float(qual) >= min_qual_v and float(conf) >= min_conf and float(qual) >= min_qual:
            signal_status = "validated"
            reason = "gate_ok"
        elif float(conf) >= min_conf_w and float(qual) >= min_qual_w:
            signal_status = "watch"
            reason = "watch_zone"
        else:
            signal_status = "inconclusive"
            reason = "below_production_gate"

        instability = _instability_score(None if pd.isna(conf) else float(conf), None if pd.isna(qual) else float(qual))
        out_rows.append(
            {
                "asset": asset,
                "group": group,
                "domain": domain,
                "timeframe": str(r.get("timeframe", "daily")).lower(),
                "timestamp": str(r.get("timestamp", "")),
                "regime": regime,
                "confidence": None if pd.isna(conf) else float(conf),
                "quality": None if pd.isna(qual) else float(qual),
                "instability_score": instability,
                "status": signal_status,
                "signal_status": signal_status,
                "reason": reason,
                "run_id": args.run_id,
                "data_adequacy": "ok" if asset_adequacy_ok else "fail",
                "source_type": str(asset_adequacy.get("source_type") or src_by_domain.get(domain, "proxy")),
                "source_name": str(asset_adequacy.get("source_name") or "unknown"),
                "min_conf_required": min_conf,
                "min_quality_required": min_qual,
            }
        )

    out_df = pd.DataFrame(out_rows)
    hcfg = production_gate.get("defaults", {}).get("hysteresis", {})
    promote_days = int(hcfg.get("promote_days", 2))
    degrade_days = int(hcfg.get("degrade_days", 2))
    if not out_df.empty:
        out_df = out_df.sort_values(["asset", "timeframe", "timestamp"]).reset_index(drop=True)
        for (asset, tf), idx in out_df.groupby(["asset", "timeframe"]).groups.items():
            seq = out_df.loc[list(idx), "signal_status"].astype(str).tolist()
            out_df.loc[list(idx), "signal_status"] = _apply_hysteresis(seq, promote_days, degrade_days)

        out_df["reason"] = out_df.apply(
            lambda x: (
                "gate_ok"
                if x["signal_status"] == "validated"
                else ("watch_zone" if x["signal_status"] == "watch" else x["reason"])
            ),
            axis=1,
        )
        # Keep legacy field and enforce canonical status field side-by-side.
        out_df["status"] = out_df["signal_status"]
    out_df.to_csv(outdir / "snapshot.csv", index=False)
    out_rows_final = out_df.to_dict(orient="records")

    with (outdir / "api_snapshot.jsonl").open("w", encoding="utf-8") as f:
        for row in out_rows_final:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    ci_health_ok = bool(ci_conf >= fallback_conf and ci_qual >= fallback_qual)

    summary = {
        "status": "ok",
        "run_id": args.run_id,
        "n_assets": int(out_df.shape[0]),
        "validated_signals": int((out_df["signal_status"] == "validated").sum()),
        "watch_signals": int((out_df["signal_status"] == "watch").sum()),
        "inconclusive_signals": int((out_df["signal_status"] == "inconclusive").sum()),
        "validated_ratio": float((out_df["signal_status"] == "validated").mean()) if out_df.shape[0] else 0.0,
        "conservative_floors": {
            "confidence_asset_gate": min_conf_global,
            "quality_asset_gate": min_qual_global,
            "confidence_ci_lower": ci_conf,
            "quality_ci_lower": ci_qual,
            "ci_health_ok": ci_health_ok,
        },
        "data_adequacy": {
            "status": "ok" if adequacy_ok else "fail",
            "assets_ok": int((out_df["data_adequacy"] == "ok").sum()) if out_df.shape[0] else 0,
            "assets_fail": int((out_df["data_adequacy"] == "fail").sum()) if out_df.shape[0] else 0,
        },
        "contract": {"name": "output_contract.v1", "version": "v1.0.0"},
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"[snapshot] ok assets={summary['n_assets']} "
        f"validated={summary['validated_signals']} watch={summary['watch_signals']} "
        f"inconclusive={summary['inconclusive_signals']}"
    )


if __name__ == "__main__":
    main()
