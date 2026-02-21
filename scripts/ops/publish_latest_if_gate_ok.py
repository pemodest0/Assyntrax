#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> None:
    ap = argparse.ArgumentParser(description="Only allow publish if latest ops gate is green.")
    ap.add_argument("--ops-root", type=str, default="results/ops/runs")
    ap.add_argument("--out", type=str, default="results/ops/publish/latest_publish_decision.json")
    args = ap.parse_args()

    ops_root = ROOT / args.ops_root
    latest = _read_json(ops_root / "latest_run.json")
    run_id = str(latest.get("run_id", "")).strip()
    run_path = Path(str(latest.get("path", "")).strip()) if latest.get("path") else Path()

    decision = {
        "status": "blocked",
        "run_id": run_id,
        "publish_allowed": False,
        "reasons": ["latest_run_missing"],
    }

    if run_id and run_path.exists():
        gate = _read_json(run_path / "publish_gate.json")
        allowed = bool(gate.get("publish_allowed", False))
        reasons = gate.get("blocked_reasons", []) if isinstance(gate, dict) else []
        decision = {
            "status": "ok" if allowed else "blocked",
            "run_id": run_id,
            "publish_allowed": allowed,
            "reasons": reasons if reasons else ([] if allowed else ["gate_blocked"]),
            "run_path": str(run_path),
        }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(decision, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False))
    if not decision["publish_allowed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
