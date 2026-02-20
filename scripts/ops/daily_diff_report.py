#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_two_dirs(root: Path) -> list[Path]:
    dirs = [d for d in root.iterdir() if d.is_dir()]
    dirs = sorted(dirs, key=lambda p: p.name)
    return dirs[-2:]


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare latest snapshots and build drift/block report.")
    parser.add_argument("--snapshots-root", type=str, default="results/ops/snapshots")
    parser.add_argument("--daily-root", type=str, default="results/ops/daily")
    parser.add_argument("--protocol", type=str, default="config/v1_protocol.json")
    parser.add_argument("--outdir", type=str, default="results/ops/diff")
    args = parser.parse_args()

    snap_root = ROOT / args.snapshots_root
    daily_root = ROOT / args.daily_root
    outdir = ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    snaps = _latest_two_dirs(snap_root) if snap_root.exists() else []
    dailies = _latest_two_dirs(daily_root) if daily_root.exists() else []
    if len(snaps) < 2 or len(dailies) < 2:
        payload = {"status": "fail", "reason": "need_at_least_two_runs_for_diff"}
        (outdir / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[diff] fail need at least two runs")
        return

    prev_snap, cur_snap = snaps[0], snaps[1]
    prev_daily, cur_daily = dailies[0], dailies[1]

    prev_df = pd.read_csv(prev_snap / "snapshot.csv")
    cur_df = pd.read_csv(cur_snap / "snapshot.csv")
    merged = prev_df.merge(cur_df, on="asset", how="outer", suffixes=("_prev", "_cur"))
    merged["status_changed"] = merged["signal_status_prev"] != merged["signal_status_cur"]
    merged["regime_changed"] = merged["regime_prev"] != merged["regime_cur"]
    merged["confidence_delta"] = pd.to_numeric(merged["confidence_cur"], errors="coerce") - pd.to_numeric(
        merged["confidence_prev"], errors="coerce"
    )
    merged["quality_delta"] = pd.to_numeric(merged["quality_cur"], errors="coerce") - pd.to_numeric(
        merged["quality_prev"], errors="coerce"
    )
    merged.to_csv(outdir / "asset_diff.csv", index=False)

    prev_sum = _read_json(prev_snap / "summary.json")
    cur_sum = _read_json(cur_snap / "summary.json")
    prev_daily_sum = _read_json(prev_daily / "summary.json")
    cur_daily_sum = _read_json(cur_daily / "summary.json")
    protocol = _read_json(ROOT / args.protocol)
    guard = protocol.get("drift_guardrails") or {}

    prev_stab = _to_float((prev_daily_sum.get("metrics") or {}).get("stability_score"))
    cur_stab = _to_float((cur_daily_sum.get("metrics") or {}).get("stability_score"))
    prev_sr = _to_float((prev_daily_sum.get("metrics") or {}).get("universe_success_rate"))
    cur_sr = _to_float((cur_daily_sum.get("metrics") or {}).get("universe_success_rate"))
    prev_vr = _to_float(prev_sum.get("validated_ratio"))
    cur_vr = _to_float(cur_sum.get("validated_ratio"))

    drop_stab = prev_stab - cur_stab
    drop_sr = prev_sr - cur_sr
    drop_vr = prev_vr - cur_vr

    block = False
    reasons: list[str] = []
    if drop_stab > float(guard.get("max_stability_drop", 0.08)):
        block = True
        reasons.append("stability_drop_exceeds_guardrail")
    if drop_sr > float(guard.get("max_success_rate_drop", 0.10)):
        block = True
        reasons.append("universe_success_rate_drop_exceeds_guardrail")
    if drop_vr > float(guard.get("max_valid_signal_ratio_drop", 0.15)):
        block = True
        reasons.append("validated_signal_ratio_drop_exceeds_guardrail")

    summary = {
        "status": "ok",
        "prev_run": prev_snap.name,
        "cur_run": cur_snap.name,
        "changes": {
            "assets_total": int(merged.shape[0]),
            "status_changed": int(merged["status_changed"].sum()),
            "regime_changed": int(merged["regime_changed"].sum()),
        },
        "drift": {
            "stability_prev": prev_stab,
            "stability_cur": cur_stab,
            "stability_drop": drop_stab,
            "success_rate_prev": prev_sr,
            "success_rate_cur": cur_sr,
            "success_rate_drop": drop_sr,
            "validated_ratio_prev": prev_vr,
            "validated_ratio_cur": cur_vr,
            "validated_ratio_drop": drop_vr,
        },
        "deployment_gate": {
            "blocked": block,
            "reasons": reasons,
        },
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # Persist deployment gate decision inside current snapshot summary so API can select latest valid run.
    cur_summary_path = cur_snap / "summary.json"
    cur_summary = _read_json(cur_summary_path)
    cur_summary["deployment_gate"] = summary["deployment_gate"]
    cur_summary_path.write_text(json.dumps(cur_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"[diff] ok blocked={block} "
        f"status_changed={summary['changes']['status_changed']} regime_changed={summary['changes']['regime_changed']}"
    )


if __name__ == "__main__":
    main()
