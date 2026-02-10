#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    msg = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, msg.strip()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily validation orchestrator for production gating.")
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--max-assets", type=int, default=80)
    parser.add_argument("--run-id", type=str, default=datetime.now(timezone.utc).strftime("%Y%m%d"))
    parser.add_argument("--outdir", type=str, default="results/ops/daily")
    args = parser.parse_args()

    run_dir = ROOT / args.outdir / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        ["python", "scripts/bench/validation/run_product_pipeline.py", "--seed", str(args.seed), "--max-assets", str(args.max_assets)],
        [
            "python",
            "scripts/bench/validation/04_universe_mini.py",
            "--outdir",
            "results/validation/universe_mini_full",
            "--seed",
            str(args.seed),
            "--max-assets",
            str(args.max_assets),
        ],
        [
            "python",
            "scripts/bench/validation/10_calibrate_switch_targets.py",
            "--universe-dir",
            "results/validation/universe_mini_full",
            "--outdir",
            "results/validation/calibration_full",
        ],
        [
            "python",
            "scripts/bench/validation/11_metric_uncertainty_ci.py",
            "--outdir",
            "results/validation/uncertainty_full",
            "--seed",
            str(args.seed),
        ],
    ]

    logs: list[dict[str, Any]] = []
    ok = True
    for i, cmd in enumerate(steps, start=1):
        code, tail = _run(cmd)
        logs.append({"step": i, "cmd": " ".join(cmd), "code": code, "tail": tail[-2000:]})
        if code != 0:
            ok = False
            break

    (run_dir / "execution_log.json").write_text(json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8")

    verdict = _read_json(ROOT / "results/validation/VERDICT.json")
    universe = _read_json(ROOT / "results/validation/universe_mini_full/universe_report.json")
    uncertainty = _read_json(ROOT / "results/validation/uncertainty_full/summary.json")
    validated = _read_json(ROOT / "results/validated/latest/summary.json")
    ablation = _read_json(ROOT / "results/validation/ablation/ablation_report.json")
    adaptive = _read_json(ROOT / "results/validation/adaptive_gates/summary.json")
    risk_utility = _read_json(ROOT / "results/validation/risk_utility/summary.json")
    adequacy = _read_json(ROOT / "results/validation/data_adequacy/summary.json")
    hist_metrics = _read_json(ROOT / "results/validation/historical_shifts/metrics.json")
    hist_verdict = _read_json(ROOT / "results/validation/historical_shifts/VERDICT.json")
    realestate_offline = _read_json(ROOT / "results/validation/realestate_offline/summary.json")

    success_rate = 0.0
    counts = (universe.get("counts") or {})
    total = float(counts.get("total") or 0)
    if total > 0:
        success_rate = float((counts.get("ok") or 0) / total)

    protocol = _read_json(ROOT / "config/v1_protocol.json")
    goals = protocol.get("goals") or {}
    min_success = float(goals.get("min_universe_success_rate", 0.8))
    min_stability = float(goals.get("min_stability_score", 0.55))
    stability = float((verdict.get("scores") or {}).get("stability_score") or 0.0)

    checks = {
        "pipeline_ok": ok,
        "verdict_pass": str(verdict.get("status", "")).lower() == "pass",
        "universe_success_ok": success_rate >= min_success,
        "stability_ok": stability >= min_stability,
        "ablation_ok": str(ablation.get("status", "")).lower() == "ok",
        "adaptive_gates_ok": str(adaptive.get("status", "")).lower() == "ok",
        "risk_utility_ok": str(risk_utility.get("status", "")).lower() == "ok",
        "data_adequacy_ok": str(adequacy.get("status", "")).lower() == "ok",
        "pseudo_bifurcation_ok": not bool(hist_metrics.get("pseudo_bifurcation_flag", False)),
        "historical_shifts_ok": str(hist_verdict.get("status", "")).lower() in {"pass", "neutral"},
        "realestate_offline_ok": str(realestate_offline.get("status", "")).lower() == "ok",
    }
    status = "ok" if all(checks.values()) else "fail"

    summary = {
        "status": status,
        "run_id": args.run_id,
        "seed": args.seed,
        "max_assets": args.max_assets,
        "checks": checks,
        "metrics": {
            "stability_score": stability,
            "universe_success_rate": success_rate,
            "validated_ratio": validated.get("validated_ratio"),
            "conservative_ci_confidence": ((uncertainty.get("conservative_overall_metrics") or {}).get("mean_confidence") or {}).get("conservative_value"),
            "conservative_ci_quality": ((uncertainty.get("conservative_overall_metrics") or {}).get("mean_quality") or {}).get("conservative_value"),
            "ablation_status": ablation.get("status"),
            "adaptive_validated_count": ((adaptive.get("counts") or {}).get("validated")),
            "risk_utility_mean_dd_avoidance": risk_utility.get("mean_drawdown_avoidance"),
            "data_adequacy_ok_count": ((adequacy.get("counts") or {}).get("ok")),
            "pseudo_bifurcation_flag": bool(hist_metrics.get("pseudo_bifurcation_flag", False)),
            "historical_status": hist_verdict.get("status"),
            "realestate_assets_ok": realestate_offline.get("ok"),
            "realestate_assets_fail": realestate_offline.get("fail"),
        },
        "sources": {
            "verdict": "results/validation/VERDICT.json",
            "universe_report": "results/validation/universe_mini_full/universe_report.json",
            "uncertainty": "results/validation/uncertainty_full/summary.json",
            "validated_summary": "results/validated/latest/summary.json",
            "realestate_offline": "results/validation/realestate_offline/summary.json",
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"[daily_validation] status={status} "
        f"stability={stability:.3f} success_rate={success_rate:.3f} "
        f"validated_ratio={float(validated.get('validated_ratio') or 0.0):.3f}"
    )
    if status != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
