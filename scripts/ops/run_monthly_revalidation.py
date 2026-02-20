#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _parse_json_last_line(stdout: str) -> dict[str, object]:
    for ln in reversed(stdout.splitlines()):
        ln = ln.strip()
        if ln.startswith("{") and ln.endswith("}"):
            return json.loads(ln)
    raise RuntimeError("Could not parse JSON output from command.")


def _run(cmd: list[str]) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    return _parse_json_last_line(proc.stdout)


def main() -> None:
    ap = argparse.ArgumentParser(description="Monthly revalidation orchestrator for sector alert motor.")
    ap.add_argument("--profile-file", type=str, default="config/sector_alerts_profile.json")
    ap.add_argument("--hyper-n-sims", type=int, default=20)
    ap.add_argument("--hyper-search-n-random", type=int, default=60)
    ap.add_argument("--hyper-final-n-random", type=int, default=300)
    ap.add_argument("--hyper-min-cal-days", type=int, default=252)
    ap.add_argument("--hyper-min-test-days", type=int, default=252)
    ap.add_argument("--hyper-two-layer-mode", type=str, default="on", choices=["on", "off"])
    ap.add_argument("--hyper-min-alert-gap-days", type=int, default=2)
    ap.add_argument("--hyper-gate-mode", type=str, default="adaptive", choices=["fixed", "adaptive"])
    ap.add_argument("--walkforward-start-year", type=int, default=2020)
    ap.add_argument("--walkforward-end-year", type=int, default=2025)
    ap.add_argument("--walkforward-n-random", type=int, default=120)
    ap.add_argument("--walkforward-gate-mode", type=str, default="adaptive", choices=["fixed", "adaptive"])
    ap.add_argument("--min-improve-mean-score", type=float, default=0.01)
    ap.add_argument("--min-pass-rate-delta", type=float, default=0.00)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--out-root", type=str, default="results/monthly_revalidation")
    ap.add_argument("--seed", type=int, default=101)
    args = ap.parse_args()

    profile_path = ROOT / str(args.profile_file)
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    run_root = ROOT / str(args.out_root) / _ts_id()
    run_root.mkdir(parents=True, exist_ok=True)

    hyper_cmd = [
        sys.executable,
        "scripts/bench/hyper_simulate_sector_alerts.py",
        "--n-sims",
        str(int(args.hyper_n_sims)),
        "--search-n-random",
        str(int(args.hyper_search_n_random)),
        "--final-n-random",
        str(int(args.hyper_final_n_random)),
        "--min-cal-days",
        str(int(args.hyper_min_cal_days)),
        "--min-test-days",
        str(int(args.hyper_min_test_days)),
        "--two-layer-mode",
        str(args.hyper_two_layer_mode),
        "--min-alert-gap-days",
        str(int(args.hyper_min_alert_gap_days)),
        "--gate-mode",
        str(args.hyper_gate_mode),
        "--baseline-profile-file",
        str(profile_path),
        "--seed",
        str(int(args.seed)),
        "--out-root",
        str((run_root / "hyper").relative_to(ROOT)),
    ]
    hyper_payload = _run(hyper_cmd)
    hyper_root = Path(str(hyper_payload["run_root"]))
    champion_profile = hyper_root / "champion_profile.json"
    best_config = json.loads((hyper_root / "best_config.json").read_text(encoding="utf-8"))

    wf_base_cmd = [
        sys.executable,
        "scripts/bench/walkforward_sector_stability.py",
        "--profile-file",
        str(profile_path),
        "--start-year",
        str(int(args.walkforward_start_year)),
        "--end-year",
        str(int(args.walkforward_end_year)),
        "--n-random",
        str(int(args.walkforward_n_random)),
        "--gate-mode",
        str(args.walkforward_gate_mode),
        "--out-root",
        str((run_root / "walkforward_baseline").relative_to(ROOT)),
    ]
    wf_base_payload = _run(wf_base_cmd)
    wf_base_summary = json.loads(Path(str(wf_base_payload["summary_file"])).read_text(encoding="utf-8"))

    wf_new_cmd = [
        sys.executable,
        "scripts/bench/walkforward_sector_stability.py",
        "--profile-file",
        str(champion_profile),
        "--start-year",
        str(int(args.walkforward_start_year)),
        "--end-year",
        str(int(args.walkforward_end_year)),
        "--n-random",
        str(int(args.walkforward_n_random)),
        "--gate-mode",
        str(args.walkforward_gate_mode),
        "--out-root",
        str((run_root / "walkforward_candidate").relative_to(ROOT)),
    ]
    wf_new_payload = _run(wf_new_cmd)
    wf_new_summary = json.loads(Path(str(wf_new_payload["summary_file"])).read_text(encoding="utf-8"))

    delta_score = float(wf_new_summary["mean_score"]) - float(wf_base_summary["mean_score"])
    delta_pass = float(wf_new_summary["pass_rate"]) - float(wf_base_summary["pass_rate"])
    candidate_passes = bool(best_config["champion_final_validation"]["passes_gates"])
    promote_decision = bool(
        candidate_passes
        and (delta_score >= float(args.min_improve_mean_score))
        and (delta_pass >= float(args.min_pass_rate_delta))
    )

    promoted = False
    backup_file = ""
    if promote_decision and bool(args.promote):
        backup = profile_path.with_name(f"{profile_path.stem}.backup_{_ts_id()}{profile_path.suffix}")
        shutil.copy2(profile_path, backup)
        shutil.copy2(champion_profile, profile_path)
        promoted = True
        backup_file = str(backup)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_file": str(profile_path),
        "hyper_run_root": str(hyper_root),
        "champion_profile": str(champion_profile),
        "candidate_passes_gates": candidate_passes,
        "hyper_min_cal_days": int(args.hyper_min_cal_days),
        "hyper_min_test_days": int(args.hyper_min_test_days),
        "hyper_two_layer_mode": str(args.hyper_two_layer_mode),
        "hyper_min_alert_gap_days": int(args.hyper_min_alert_gap_days),
        "hyper_gate_mode": str(args.hyper_gate_mode),
        "baseline_walkforward": wf_base_summary,
        "candidate_walkforward": wf_new_summary,
        "delta_mean_score": float(delta_score),
        "delta_pass_rate": float(delta_pass),
        "walkforward_gate_mode": str(args.walkforward_gate_mode),
        "min_improve_mean_score": float(args.min_improve_mean_score),
        "min_pass_rate_delta": float(args.min_pass_rate_delta),
        "promote_decision": promote_decision,
        "promoted": promoted,
        "backup_file": backup_file,
    }
    (run_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("Monthly Revalidation Summary")
    lines.append(f"run_root: {run_root}")
    lines.append(f"candidate_passes_gates: {candidate_passes}")
    lines.append(f"delta_mean_score: {delta_score:.6f}")
    lines.append(f"delta_pass_rate: {delta_pass:.6f}")
    lines.append(f"walkforward_gate_mode: {str(args.walkforward_gate_mode)}")
    lines.append(f"decision: {'promote' if promote_decision else 'keep_baseline'}")
    lines.append(f"promoted_now: {promoted}")
    if backup_file:
        lines.append(f"backup_file: {backup_file}")
    (run_root / "report_monthly_revalidation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "run_root": str(run_root),
                "summary_file": str(run_root / "summary.json"),
                "promote_decision": promote_decision,
                "promoted": promoted,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
