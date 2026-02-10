#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate snapshot rows against output contract.")
    parser.add_argument("--snapshot", type=str, required=True)
    parser.add_argument("--contract", type=str, default="config/output_contract.v1.json")
    parser.add_argument("--out", type=str, default="results/validation/contract_check.json")
    args = parser.parse_args()

    snapshot_path = ROOT / args.snapshot
    contract = _read_json(ROOT / args.contract)
    required = list(contract.get("required_fields") or [])
    statuses = set(
        str(x).lower()
        for x in (
            contract.get("allowed_status")
            or contract.get("allowed_signal_status")
            or contract.get("status_values")
            or []
        )
    )
    status_field = str(contract.get("status_field") or "status")

    payload: dict[str, Any] = {
        "status": "ok",
        "snapshot": str(snapshot_path),
        "contract": str(ROOT / args.contract),
        "n_rows": 0,
        "missing_required": {},
        "invalid_status_rows": 0,
    }

    if not snapshot_path.exists():
        payload["status"] = "fail"
        payload["reason"] = f"missing_snapshot: {snapshot_path}"
    else:
        missing: dict[str, int] = {k: 0 for k in required}
        bad_status = 0
        n = 0
        with snapshot_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                n += 1
                try:
                    row = json.loads(line)
                except Exception:
                    payload["status"] = "fail"
                    payload["reason"] = "invalid_jsonl_line"
                    continue
                for k in required:
                    if k not in row:
                        missing[k] += 1
                st = str(row.get(status_field, row.get("signal_status", ""))).lower()
                if statuses and st not in statuses:
                    bad_status += 1
        payload["n_rows"] = n
        payload["missing_required"] = {k: v for k, v in missing.items() if v > 0}
        payload["invalid_status_rows"] = bad_status
        if payload["missing_required"] or bad_status > 0:
            payload["status"] = "fail"
            payload["reason"] = "contract_violation"

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"[contract_check] status={payload['status']} rows={payload.get('n_rows', 0)} "
        f"missing={len(payload.get('missing_required', {}))} bad_status={payload.get('invalid_status_rows', 0)}"
    )
    if payload["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
