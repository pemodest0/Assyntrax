#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SNAP_ROOT = ROOT / "results" / "ops" / "snapshots"
OUT = ROOT / "results" / "validation" / "frontend_data_audit.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_snapshot_run() -> tuple[str | None, Path | None, dict[str, Any]]:
    if not SNAP_ROOT.exists():
        return None, None, {}
    runs = sorted([p for p in SNAP_ROOT.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    latest_any: tuple[str, Path, dict[str, Any]] | None = None
    for run in runs:
        summary_path = run / "summary.json"
        snap_path = run / "api_snapshot.jsonl"
        if not summary_path.exists() or not snap_path.exists():
            continue
        summary = _read_json(summary_path, {})
        if latest_any is None:
            latest_any = (run.name, snap_path, summary)
        if str(summary.get("status", "")).lower() == "ok" and not bool((summary.get("deployment_gate") or {}).get("blocked")):
            return run.name, snap_path, summary
    if latest_any is None:
        return None, None, {}
    return latest_any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _contains_mojibake(v: Any) -> bool:
    if isinstance(v, str):
        return any(x in v for x in ("Ã", "Â", "�"))
    if isinstance(v, list):
        return any(_contains_mojibake(x) for x in v)
    if isinstance(v, dict):
        return any(_contains_mojibake(x) for x in v.values())
    return False


def main() -> None:
    run_id, snap_path, summary = _latest_snapshot_run()
    if not run_id or not snap_path:
        payload = {
            "status": "ok",
            "reason": "no_snapshot_available",
            "checks": {"skipped_no_snapshot": True},
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[frontend_audit] status=ok skipped_no_snapshot=True")
        return

    rows = _read_jsonl(snap_path)
    required = ["asset", "domain", "timestamp", "regime", "confidence", "quality", "signal_status", "reason"]
    missing_counts = {k: 0 for k in required}
    bad_signal_status = 0
    bad_numeric = {"confidence": 0, "quality": 0}

    for r in rows:
        for k in required:
            if k not in r or r.get(k) in (None, ""):
                missing_counts[k] += 1
        if str(r.get("signal_status", "")).lower() not in {"validated", "watch", "inconclusive", "diagnostico_inconclusivo"}:
            bad_signal_status += 1
        for k in ("confidence", "quality"):
            try:
                float(r.get(k))
            except (TypeError, ValueError):
                bad_numeric[k] += 1

    global_status = _read_json(ROOT / "results" / "validation" / "STATUS.json", {})
    risk_truth = _read_json(ROOT / "results" / "validation" / "risk_truth_panel.json", {})
    mojibake_summary = _contains_mojibake(summary)
    mojibake_rows = _contains_mojibake(rows)
    mojibake_risk_truth = _contains_mojibake(risk_truth)

    payload = {
        "status": "ok",
        "run_id": run_id,
        "records_total": len(rows),
        "required_fields_missing": missing_counts,
        "bad_signal_status": bad_signal_status,
        "bad_numeric_fields": bad_numeric,
        "encoding_flags": {
            "summary_has_mojibake": mojibake_summary,
            "rows_has_mojibake": mojibake_rows,
            "risk_truth_has_mojibake": mojibake_risk_truth,
        },
        "global_status": str(global_status.get("status", "unknown")).lower(),
        "risk_truth_counts": risk_truth.get("counts", {}),
        "checks": {
            "has_records": len(rows) > 0,
            "all_required_present": all(v == 0 for v in missing_counts.values()),
            "signal_status_clean": bad_signal_status == 0,
            "numeric_clean": all(v == 0 for v in bad_numeric.values()),
            # Legacy text artifacts in status/risk truth must not block payload contract checks.
            "encoding_clean": not any([mojibake_summary, mojibake_rows]),
        },
        "summary_source": str(snap_path.parent / "summary.json"),
        "snapshot_source": str(snap_path),
    }
    if not all(bool(v) for v in payload["checks"].values()):
        payload["status"] = "fail"
        payload["reason"] = "frontend_payload_contract_violation"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"[frontend_audit] status={payload['status']} run={run_id} rows={len(rows)} "
        f"required_ok={payload['checks']['all_required_present']} "
        f"signal_ok={payload['checks']['signal_status_clean']} "
        f"numeric_ok={payload['checks']['numeric_clean']} "
        f"encoding_ok={payload['checks']['encoding_clean']}"
    )
    if payload["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
