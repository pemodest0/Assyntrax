#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_last_line(stdout: str) -> dict[str, object]:
    for ln in reversed(stdout.splitlines()):
        ln = ln.strip()
        if ln.startswith("{") and ln.endswith("}"):
            return json.loads(ln)
    raise RuntimeError("Could not parse JSON output.")


def _load_profile(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    params = payload.get("params", payload) if isinstance(payload, dict) else {}
    if not isinstance(params, dict):
        params = {}
    return {
        "profile_version": str(payload.get("profile_version", "")) if isinstance(payload, dict) else "",
        "params": params,
    }


def _mean_metric(df: pd.DataFrame, event_def: str, lookback: int, model: str, col: str) -> float:
    s = df[(df["event_def"] == event_def) & (df["lookback_days"] == int(lookback)) & (df["model"] == model)][col]
    return float(s.mean()) if not s.empty else float("nan")


def _count_levels(path: Path) -> dict[str, int]:
    df = pd.read_csv(path)
    if "alert_level" not in df.columns:
        return {"verde": 0, "amarelo": 0, "vermelho": 0}
    vc = df["alert_level"].astype(str).str.lower().value_counts().to_dict()
    return {
        "verde": int(vc.get("verde", 0)),
        "amarelo": int(vc.get("amarelo", 0)),
        "vermelho": int(vc.get("vermelho", 0)),
    }


def _safe(v: float) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0.0
    return x if np.isfinite(x) else 0.0


def _append_worklog(entry: dict[str, object]) -> None:
    out_jsonl = ROOT / "results/codex/worklog.jsonl"
    out_latest = ROOT / "results/codex/worklog_latest.json"
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_latest.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    out_latest.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_mode(
    *,
    mode_name: str,
    profile_file: Path,
    out_root: Path,
    n_random: int,
    lookbacks: str,
) -> dict[str, object]:
    loaded = _load_profile(profile_file)
    p = loaded["params"]
    cmd = [
        sys.executable,
        "scripts/bench/event_study_validate_sectors.py",
        "--out-root",
        str(out_root / mode_name),
        "--lookbacks",
        str(lookbacks),
        "--n-random",
        str(int(n_random)),
        "--random-baseline-method",
        str(p.get("random_baseline_method", "both")),
        "--random-block-size",
        str(int(p.get("random_block_size", 8))),
        "--min-sector-assets",
        str(int(p.get("min_sector_assets", 10))),
        "--min-cal-days",
        str(int(p.get("min_cal_days", 252))),
        "--min-test-days",
        str(int(p.get("min_test_days", 252))),
        "--alert-policy",
        str(p.get("alert_policy", "regime_entry_confirm")),
        "--two-layer-mode",
        str(p.get("two_layer_mode", "on")),
        "--q-unstable",
        str(float(p.get("q_unstable", 0.80))),
        "--q-transition",
        str(float(p.get("q_transition", 0.80))),
        "--q-confidence",
        str(float(p.get("q_confidence", 0.50))),
        "--q-confidence-guarded",
        str(float(p.get("q_confidence_guarded", 0.60))),
        "--q-score-balanced",
        str(float(p.get("q_score_balanced", 0.70))),
        "--q-score-guarded",
        str(float(p.get("q_score_guarded", 0.80))),
        "--confirm-n",
        str(int(p.get("confirm_n", 2))),
        "--confirm-m",
        str(int(p.get("confirm_m", 3))),
        "--min-alert-gap-days",
        str(int(p.get("min_alert_gap_days", 2))),
        "--auto-candidates",
        str(p.get("auto_candidates", "regime_entry_confirm,regime_balanced,regime_guarded")),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout)[-1500:])
    payload = _json_last_line(proc.stdout)
    mode_outdir = Path(str(payload["outdir"]))
    metrics = pd.read_csv(mode_outdir / "sector_metrics_summary.csv")
    levels = _count_levels(mode_outdir / "sector_alert_levels_latest.csv")
    d10 = _mean_metric(metrics, "drawdown20", 10, "motor", "recall")
    d20 = _mean_metric(metrics, "drawdown20", 20, "motor", "recall")
    d30 = _mean_metric(metrics, "drawdown20", 30, "motor", "recall")
    p10 = _mean_metric(metrics, "drawdown20", 10, "motor", "precision")
    fa10 = _mean_metric(metrics, "drawdown20", 10, "motor", "false_alarm_per_year")
    ret10 = _mean_metric(metrics, "ret_tail", 10, "motor", "recall")
    utility_score = (
        0.50 * _safe(d10)
        + 0.20 * _safe(d20)
        + 0.10 * _safe(ret10)
        + 0.15 * _safe(p10)
        - 0.03 * _safe(fa10)
    )
    return {
        "mode": mode_name,
        "profile_file": str(profile_file),
        "profile_version": str(loaded["profile_version"]),
        "outdir": str(mode_outdir),
        "drawdown_recall_l10": float(d10),
        "drawdown_recall_l20": float(d20),
        "drawdown_recall_l30": float(d30),
        "ret_tail_recall_l10": float(ret10),
        "drawdown_precision_l10": float(p10),
        "drawdown_false_alarm_l10": float(fa10),
        "utility_score": float(utility_score),
        "levels_verde": int(levels["verde"]),
        "levels_amarelo": int(levels["amarelo"]),
        "levels_vermelho": int(levels["vermelho"]),
    }


def _write_csv_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerows(rows)


def _build_7d_summary(history_path: Path, out_path: Path) -> dict[str, object]:
    if not history_path.exists():
        payload = {"status": "no_history"}
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload
    df = pd.read_csv(history_path)
    if df.empty:
        payload = {"status": "empty_history"}
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload
    df["run_ts_utc"] = pd.to_datetime(df["run_ts_utc"], errors="coerce")
    df = df.sort_values("run_ts_utc")
    result: dict[str, object] = {"status": "ok", "modes": {}}
    for mode in sorted(df["mode"].unique()):
        sub = df[df["mode"] == mode].tail(7)
        result["modes"][mode] = {
            "n_days": int(len(sub)),
            "mean_drawdown_recall_l10": float(sub["drawdown_recall_l10"].mean()),
            "mean_drawdown_recall_l20": float(sub["drawdown_recall_l20"].mean()),
            "mean_drawdown_recall_l30": float(sub["drawdown_recall_l30"].mean()),
            "mean_false_alarm_l10": float(sub["drawdown_false_alarm_l10"].mean()),
            "mean_precision_l10": float(sub["drawdown_precision_l10"].mean()),
            "mean_utility_score": float(sub["utility_score"].mean()),
        }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Run and compare useful mode vs aggressive mode, storing daily history.")
    ap.add_argument("--profile-useful", type=str, default="config/sector_alerts_profile_useful.json")
    ap.add_argument("--profile-aggressive", type=str, default="config/sector_alerts_profile_aggressive97.json")
    ap.add_argument("--n-random", type=int, default=20)
    ap.add_argument("--lookbacks", type=str, default="10,20,30")
    ap.add_argument("--out-root", type=str, default="results/dual_mode_compare")
    args = ap.parse_args()

    run_id = _ts_id()
    run_root = ROOT / str(args.out_root) / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    useful = _run_mode(
        mode_name="useful",
        profile_file=ROOT / str(args.profile_useful),
        out_root=run_root / "runs",
        n_random=int(args.n_random),
        lookbacks=str(args.lookbacks),
    )
    aggressive = _run_mode(
        mode_name="aggressive97",
        profile_file=ROOT / str(args.profile_aggressive),
        out_root=run_root / "runs",
        n_random=int(args.n_random),
        lookbacks=str(args.lookbacks),
    )
    rows = [useful, aggressive]
    results_df = pd.DataFrame(rows)
    results_df.to_csv(run_root / "mode_results.csv", index=False)

    if float(aggressive["drawdown_recall_l30"]) >= 0.97:
        winner = "aggressive97"
        winner_reason = "bateu meta 97% em 30 dias"
    else:
        winner = "useful" if float(useful["utility_score"]) >= float(aggressive["utility_score"]) else "aggressive97"
        winner_reason = "melhor equilibrio utilidade (recall + precisao - falso alerta)"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "n_random": int(args.n_random),
        "lookbacks": str(args.lookbacks),
        "winner_mode": winner,
        "winner_reason": winner_reason,
        "target97_hit": bool(float(aggressive["drawdown_recall_l30"]) >= 0.97),
        "modes": rows,
    }
    (run_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    hist_rows: list[dict[str, object]] = []
    run_ts = datetime.now(timezone.utc).isoformat()
    for row in rows:
        hist_rows.append({"run_id": run_id, "run_ts_utc": run_ts, **row})
    hist_path = ROOT / str(args.out_root) / "history.csv"
    _write_csv_rows(hist_path, hist_rows)

    summary_7d = _build_7d_summary(
        history_path=hist_path,
        out_path=ROOT / str(args.out_root) / "summary_7d.json",
    )

    lines: list[str] = []
    lines.append("Comparacao de Modos - Util x Agressivo 97")
    lines.append(f"run_id: {run_id}")
    lines.append(f"winner: {winner}")
    lines.append(f"motivo: {winner_reason}")
    lines.append("")
    for row in rows:
        lines.append(f"modo: {row['mode']}")
        lines.append(f"- recall L10: {float(row['drawdown_recall_l10']):.4f}")
        lines.append(f"- recall L20: {float(row['drawdown_recall_l20']):.4f}")
        lines.append(f"- recall L30: {float(row['drawdown_recall_l30']):.4f}")
        lines.append(f"- precision L10: {float(row['drawdown_precision_l10']):.4f}")
        lines.append(f"- falso alerta L10/ano: {float(row['drawdown_false_alarm_l10']):.4f}")
        lines.append(f"- utility_score: {float(row['utility_score']):.4f}")
        lines.append(
            f"- niveis: verde={int(row['levels_verde'])}, amarelo={int(row['levels_amarelo'])}, vermelho={int(row['levels_vermelho'])}"
        )
        lines.append("")
    lines.append("Resumo 7 dias (historico acumulado):")
    lines.append(json.dumps(summary_7d, ensure_ascii=False))
    (run_root / "report_dual_mode.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    _append_worklog(
        {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "kind": "result",
            "title": "Comparacao util vs agressivo executada",
            "summary": (
                f"winner={winner}, target97_hit={bool(summary['target97_hit'])}, "
                f"useful_l10={useful['drawdown_recall_l10']:.3f}, aggressive_l30={aggressive['drawdown_recall_l30']:.3f}"
            ),
            "artifacts": [str(run_root), str(run_root / "summary.json"), str(hist_path)],
            "tags": ["dual_mode", "useful", "aggressive97", "comparison"],
            "metrics": {
                "target97_hit": bool(summary["target97_hit"]),
                "winner_mode": winner,
                "useful_recall_l10": float(useful["drawdown_recall_l10"]),
                "aggressive_recall_l30": float(aggressive["drawdown_recall_l30"]),
                "useful_false_alarm_l10": float(useful["drawdown_false_alarm_l10"]),
                "aggressive_false_alarm_l10": float(aggressive["drawdown_false_alarm_l10"]),
            },
        }
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "run_root": str(run_root),
                "winner_mode": winner,
                "target97_hit": bool(summary["target97_hit"]),
                "history_file": str(hist_path),
                "summary_7d_file": str(ROOT / str(args.out_root) / "summary_7d.json"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
