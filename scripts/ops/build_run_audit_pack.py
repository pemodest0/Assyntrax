#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _git_hash() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build audit package for a daily run.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--max-assets", type=int, default=80)
    parser.add_argument("--snapshots-root", default="results/ops/snapshots")
    parser.add_argument("--daily-root", default="results/ops/daily")
    args = parser.parse_args()

    snap_dir = ROOT / args.snapshots_root / args.run_id
    daily_dir = ROOT / args.daily_root / args.run_id
    out = snap_dir / "audit_pack.json"

    snap_summary = _read_json(snap_dir / "summary.json", {})
    daily_summary = _read_json(daily_dir / "summary.json", {})
    diff_summary = _read_json(ROOT / "results/ops/diff/summary.json", {})
    global_status = _read_json(ROOT / "results/validation/STATUS.json", {})
    if not global_status:
        global_status = _read_json(ROOT / "results/validation/VERDICT.json", {})
    adequacy = _read_json(ROOT / "results/validation/data_adequacy/summary.json", {})
    gates_cfg = _read_json(ROOT / "config/validation_gates.json", {})
    prod_cfg = _read_json(ROOT / "config/production_gate.v1.json", {})
    protocol = _read_json(ROOT / "config/v1_protocol.json", {})

    caveats = [
        "Nao e previsao de preco; e classificacao de regime e risco.",
        "Backtests e simulacoes nao garantem resultado futuro.",
        "Sinais inconclusivos devem ser tratados como diagnostico sem acao.",
        "Metricas podem variar por cobertura e qualidade de dados por dominio.",
        "Gates e thresholds sao versionados e devem ser auditados por run_id.",
    ]

    payload = {
        "status": "ok",
        "run_id": args.run_id,
        "version": "audit_pack.v1",
        "reproducibility": {
            "seed": args.seed,
            "max_assets": args.max_assets,
            "git_commit_hash": _git_hash(),
            "snapshot_sha256": _file_sha256(snap_dir / "api_snapshot.jsonl"),
        },
        "coverage": {
            "snapshot_n_assets": snap_summary.get("n_assets"),
            "validated_signals": snap_summary.get("validated_signals"),
            "watch_signals": snap_summary.get("watch_signals"),
            "inconclusive_signals": snap_summary.get("inconclusive_signals"),
            "validated_ratio": snap_summary.get("validated_ratio"),
            "data_adequacy": adequacy.get("counts", {}),
        },
        "thresholds": {
            "validation_gates": gates_cfg,
            "production_gate": prod_cfg,
            "protocol_goals": protocol.get("goals", {}),
            "drift_guardrails": protocol.get("drift_guardrails", {}),
        },
        "deployment": {
            "snapshot_summary": snap_summary,
            "daily_summary": daily_summary,
            "diff_summary": diff_summary,
            "global_status": global_status.get("status", "unknown"),
        },
        "sources": {
            "snapshot": str(snap_dir / "api_snapshot.jsonl"),
            "snapshot_summary": str(snap_dir / "summary.json"),
            "daily_summary": str(daily_dir / "summary.json"),
            "diff_summary": "results/ops/diff/summary.json",
            "status": "results/validation/STATUS.json",
        },
        "caveats": caveats,
    }

    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[audit_pack] ok run={args.run_id} out={out}")


if __name__ == "__main__":
    main()
