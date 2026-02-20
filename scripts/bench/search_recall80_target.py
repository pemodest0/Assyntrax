#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_last_line(stdout: str) -> dict[str, object]:
    for ln in reversed(stdout.splitlines()):
        ln = ln.strip()
        if ln.startswith("{") and ln.endswith("}"):
            return json.loads(ln)
    raise RuntimeError("Could not parse JSON line from validator output.")


def _mean_metric(df: pd.DataFrame, event_def: str, lookback: int, model: str, col: str) -> float:
    s = df[(df["event_def"] == event_def) & (df["lookback_days"] == int(lookback)) & (df["model"] == model)][col]
    return float(s.mean()) if not s.empty else float("nan")


def _load_profile_params(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    params = payload.get("params", payload) if isinstance(payload, dict) else {}
    return dict(params) if isinstance(params, dict) else {}


def _build_cases(max_cases: int) -> list[dict[str, object]]:
    # Ordered from aggressive to conservative for faster hit of 80% recall target.
    base: list[dict[str, object]] = [
        {"tag": "entry_1of2_gap0_fast", "policy": "regime_entry_confirm", "confirm_n": 1, "confirm_m": 2, "gap": 0, "two_layer": "off"},
        {"tag": "entry_1of3_gap0_fast", "policy": "regime_entry_confirm", "confirm_n": 1, "confirm_m": 3, "gap": 0, "two_layer": "off"},
        {"tag": "entry_2of3_gap0_fast", "policy": "regime_entry_confirm", "confirm_n": 2, "confirm_m": 3, "gap": 0, "two_layer": "off"},
        {"tag": "entry_1of2_gap1_fast", "policy": "regime_entry_confirm", "confirm_n": 1, "confirm_m": 2, "gap": 1, "two_layer": "off"},
        {"tag": "entry_1of3_gap1_fast", "policy": "regime_entry_confirm", "confirm_n": 1, "confirm_m": 3, "gap": 1, "two_layer": "off"},
        {"tag": "auto_1of3_gap0_fast", "policy": "regime_auto", "confirm_n": 1, "confirm_m": 3, "gap": 0, "two_layer": "off"},
        {"tag": "auto_1of2_gap1_fast", "policy": "regime_auto", "confirm_n": 1, "confirm_m": 2, "gap": 1, "two_layer": "off"},
        {"tag": "entry_3of3_gap3_confirm", "policy": "regime_entry_confirm", "confirm_n": 3, "confirm_m": 3, "gap": 3, "two_layer": "on"},
        {"tag": "entry_3of3_gap5_confirm", "policy": "regime_entry_confirm", "confirm_n": 3, "confirm_m": 3, "gap": 5, "two_layer": "on"},
        {"tag": "entry_2of3_gap3_confirm", "policy": "regime_entry_confirm", "confirm_n": 2, "confirm_m": 3, "gap": 3, "two_layer": "on"},
    ]
    return base[: max(1, int(max_cases))]


def _append_worklog(entry: dict[str, object]) -> None:
    out = ROOT / "results/codex/worklog.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    (ROOT / "results/codex/worklog_latest.json").write_text(
        json.dumps(entry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Search configs aiming recall >= 80% for sector event study.")
    ap.add_argument("--profile-file", type=str, default="config/sector_alerts_profile.json")
    ap.add_argument("--event-def", type=str, default="drawdown20")
    ap.add_argument("--lookback", type=int, default=10)
    ap.add_argument("--target-recall", type=float, default=0.80)
    ap.add_argument("--n-random", type=int, default=40)
    ap.add_argument("--max-cases", type=int, default=10)
    ap.add_argument("--out-root", type=str, default="results/recall80_search")
    args = ap.parse_args()

    params = _load_profile_params(ROOT / str(args.profile_file))
    q_unstable = float(params.get("q_unstable", 0.80))
    q_transition = float(params.get("q_transition", 0.80))
    q_confidence = float(params.get("q_confidence", 0.50))
    q_confidence_guarded = float(params.get("q_confidence_guarded", 0.60))
    q_score_balanced = float(params.get("q_score_balanced", 0.70))
    q_score_guarded = float(params.get("q_score_guarded", 0.80))
    random_block_size = int(params.get("random_block_size", 8))
    auto_candidates = str(params.get("auto_candidates", "regime_entry_confirm,regime_balanced,regime_guarded"))

    run_root = ROOT / str(args.out_root) / _ts_id()
    run_root.mkdir(parents=True, exist_ok=True)
    cases = _build_cases(max_cases=int(args.max_cases))
    rows: list[dict[str, object]] = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['tag']}", flush=True)
        cmd = [
            sys.executable,
            "scripts/bench/event_study_validate_sectors.py",
            "--out-root",
            str(run_root / "runs" / str(case["tag"])),
            "--n-random",
            str(int(args.n_random)),
            "--random-baseline-method",
            "both",
            "--random-block-size",
            str(int(random_block_size)),
            "--alert-policy",
            str(case["policy"]),
            "--two-layer-mode",
            str(case["two_layer"]),
            "--confirm-n",
            str(int(case["confirm_n"])),
            "--confirm-m",
            str(int(case["confirm_m"])),
            "--min-alert-gap-days",
            str(int(case["gap"])),
            "--q-unstable",
            str(q_unstable),
            "--q-transition",
            str(q_transition),
            "--q-confidence",
            str(q_confidence),
            "--q-confidence-guarded",
            str(q_confidence_guarded),
            "--q-score-balanced",
            str(q_score_balanced),
            "--q-score-guarded",
            str(q_score_guarded),
            "--auto-candidates",
            str(auto_candidates),
            "--min-sector-assets",
            "10",
            "--min-cal-days",
            "252",
            "--min-test-days",
            "252",
        ]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            rows.append(
                {
                    "tag": case["tag"],
                    "status": "error",
                    "policy": case["policy"],
                    "stderr_tail": (proc.stderr or proc.stdout)[-500:],
                }
            )
            continue
        payload = _json_last_line(proc.stdout)
        outdir = Path(str(payload["outdir"]))
        df = pd.read_csv(outdir / "sector_metrics_summary.csv")
        model = "motor"
        recall = _mean_metric(df, str(args.event_def), int(args.lookback), model, "recall")
        precision = _mean_metric(df, str(args.event_def), int(args.lookback), model, "precision")
        false_alarm = _mean_metric(df, str(args.event_def), int(args.lookback), model, "false_alarm_per_year")
        p_block = _mean_metric(df, str(args.event_def), int(args.lookback), model, "p_vs_random_recall_block")
        score = float(0.70 * recall + 0.15 * precision - 0.03 * false_alarm)
        rows.append(
            {
                "tag": case["tag"],
                "status": "ok",
                "policy": case["policy"],
                "two_layer_mode": case["two_layer"],
                "confirm_n": int(case["confirm_n"]),
                "confirm_m": int(case["confirm_m"]),
                "min_alert_gap_days": int(case["gap"]),
                "event_def": str(args.event_def),
                "lookback": int(args.lookback),
                "recall": float(recall),
                "precision": float(precision),
                "false_alarm_per_year": float(false_alarm),
                "p_block": float(p_block),
                "target_hit": bool(pd.notna(recall) and float(recall) >= float(args.target_recall)),
                "score": float(score),
                "outdir": str(outdir),
            }
        )

    df_all = pd.DataFrame(rows)
    df_all.to_csv(run_root / "search_results.csv", index=False)
    ok = df_all[df_all["status"] == "ok"].copy()
    if not ok.empty:
        ok = ok.sort_values(["target_hit", "score", "recall"], ascending=[False, False, False])
        best = ok.iloc[0].to_dict()
    else:
        best = {}

    report_lines: list[str] = []
    report_lines.append("Recall 80 Target Search")
    report_lines.append(f"run_root: {run_root}")
    report_lines.append(f"target_recall: {float(args.target_recall):.3f}")
    report_lines.append(f"event_def: {str(args.event_def)}")
    report_lines.append(f"lookback: {int(args.lookback)}")
    report_lines.append(f"n_random: {int(args.n_random)}")
    report_lines.append(f"cases: {int(len(cases))}")
    hit_count = int(ok["target_hit"].sum()) if not ok.empty else 0
    report_lines.append(f"target_hits: {hit_count}")
    if best:
        report_lines.append("best:")
        report_lines.append(f"- tag: {best.get('tag')}")
        report_lines.append(f"- policy: {best.get('policy')}")
        report_lines.append(f"- recall: {float(best.get('recall', float('nan'))):.4f}")
        report_lines.append(f"- false_alarm_per_year: {float(best.get('false_alarm_per_year', float('nan'))):.4f}")
        report_lines.append(f"- precision: {float(best.get('precision', float('nan'))):.4f}")
        report_lines.append(f"- p_block: {float(best.get('p_block', float('nan'))):.4f}")
        report_lines.append(f"- target_hit: {bool(best.get('target_hit', False))}")
        report_lines.append(f"- outdir: {best.get('outdir')}")
    (run_root / "report_recall80.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": str(run_root),
        "target_recall": float(args.target_recall),
        "event_def": str(args.event_def),
        "lookback": int(args.lookback),
        "n_random": int(args.n_random),
        "cases": int(len(cases)),
        "target_hits": hit_count,
        "best": best,
    }
    (run_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    _append_worklog(
        {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "kind": "result",
            "title": "Recall 80 target search executed",
            "summary": (
                f"hits={hit_count}/{len(cases)}, "
                f"best={best.get('tag', '')}, recall={best.get('recall', None)}"
            ),
            "artifacts": [str(run_root), str(run_root / "summary.json"), str(run_root / "search_results.csv")],
            "tags": ["recall80", "search", "motor", "sectors"],
            "metrics": {
                "target_recall": float(args.target_recall),
                "target_hits": int(hit_count),
                "best_recall": best.get("recall", None),
                "best_false_alarm_per_year": best.get("false_alarm_per_year", None),
                "best_score": best.get("score", None),
            },
        }
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "run_root": str(run_root),
                "target_hits": hit_count,
                "best_tag": best.get("tag", ""),
                "best_recall": best.get("recall", None),
                "best_false_alarm_per_year": best.get("false_alarm_per_year", None),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
