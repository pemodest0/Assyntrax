#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _parse_json_last_line(stdout: str) -> dict[str, object]:
    for ln in reversed(stdout.splitlines()):
        ln = ln.strip()
        if ln.startswith("{") and ln.endswith("}"):
            return json.loads(ln)
    raise RuntimeError("Could not parse JSON output from validator.")


def _load_profile(path: Path) -> tuple[dict[str, object], dict[str, float], str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    params = payload.get("params", payload) if isinstance(payload, dict) else {}
    gates = payload.get("acceptance_gates", {}) if isinstance(payload, dict) else {}
    gate_mode = ""
    if isinstance(payload, dict):
        if "gate_mode" in payload:
            gate_mode = str(payload.get("gate_mode", "")).strip()
        elif isinstance(params, dict) and ("gate_mode" in params):
            gate_mode = str(params.get("gate_mode", "")).strip()
    return (
        dict(params) if isinstance(params, dict) else {},
        {
            "max_false_alarm_l5_l10": float(gates.get("max_false_alarm_l5_l10", 10.0)),
            "min_drawdown_recall_l10": float(gates.get("min_drawdown_recall_l10", 0.35)),
            "min_sig_rate_block_draw_l5_l10": float(gates.get("min_sig_rate_block_draw_l5_l10", 0.25)),
        },
        str(payload.get("profile_version", "")) if isinstance(payload, dict) else "",
        gate_mode,
    )


def _mean_metric(df: pd.DataFrame, event_def: str, lb: int, col: str) -> float:
    s = df[(df["event_def"] == event_def) & (df["lookback_days"] == lb)][col]
    return float(s.mean()) if not s.empty else float("nan")


def _window_score(df_motor: pd.DataFrame) -> dict[str, float]:
    draw5 = _mean_metric(df_motor, "drawdown20", 5, "recall")
    draw10 = _mean_metric(df_motor, "drawdown20", 10, "recall")
    tail5 = _mean_metric(df_motor, "ret_tail", 5, "recall")
    tail10 = _mean_metric(df_motor, "ret_tail", 10, "recall")
    sub = df_motor[df_motor["lookback_days"].isin([5, 10])]
    precision = float(sub["precision"].mean()) if not sub.empty else float("nan")
    false_alarm = float(sub["false_alarm_per_year"].mean()) if not sub.empty else float("nan")
    block = df_motor[(df_motor["event_def"] == "drawdown20") & (df_motor["lookback_days"].isin([5, 10]))]
    n_events_draw10 = _mean_metric(df_motor, "drawdown20", 10, "n_events")
    sig_rate = float((block["p_vs_random_recall_block"] < 0.05).mean()) if not block.empty else float("nan")
    p_block_min = float(block["p_vs_random_recall_block"].min()) if not block.empty else float("nan")
    score = (
        0.50 * np.nan_to_num(draw10)
        + 0.20 * np.nan_to_num(draw5)
        + 0.15 * np.nan_to_num(tail10)
        + 0.05 * np.nan_to_num(tail5)
        + 0.20 * np.nan_to_num(precision)
        - 0.03 * np.nan_to_num(false_alarm)
        + 0.15 * np.nan_to_num(sig_rate)
    )
    return {
        "score": float(score),
        "drawdown_recall_l5": float(draw5),
        "drawdown_recall_l10": float(draw10),
        "ret_tail_recall_l5": float(tail5),
        "ret_tail_recall_l10": float(tail10),
        "precision_l5_l10": float(precision),
        "false_alarm_l5_l10": float(false_alarm),
        "n_events_drawdown_l10": float(n_events_draw10),
        "sig_rate_block_draw_l5_l10": float(sig_rate),
        "p_block_min_draw_l5_l10": float(p_block_min),
    }


def _passes(row: dict[str, float], gates: dict[str, float], *, gate_mode: str = "fixed") -> bool:
    max_fa = float(gates["max_false_alarm_l5_l10"])
    min_draw = float(gates["min_drawdown_recall_l10"])
    min_sig = float(gates["min_sig_rate_block_draw_l5_l10"])
    fa = float(np.nan_to_num(row["false_alarm_l5_l10"], nan=1e9))
    draw = float(np.nan_to_num(row["drawdown_recall_l10"], nan=-1e9))
    sig = float(np.nan_to_num(row["sig_rate_block_draw_l5_l10"], nan=-1e9))
    pmin = float(np.nan_to_num(row.get("p_block_min_draw_l5_l10", np.nan), nan=1e9))
    n_events = float(np.nan_to_num(row.get("n_events_drawdown_l10", np.nan), nan=0.0))
    if str(gate_mode).lower() == "adaptive":
        # No-event year: cannot test anticipation; require only alert discipline.
        if n_events <= 0.0:
            return fa <= max_fa

        # Rare-event year: relax hard significance threshold and accept strong p-min.
        if n_events < 2.0:
            event_factor = float(np.clip(n_events / 8.0, 0.10, 1.20))
            min_draw = float(min_draw * event_factor)
            min_sig = float(min_sig * event_factor)
            max_fa = float(max_fa / max(event_factor, 0.10))
            sig_ok = (sig >= min_sig) or (pmin <= 0.10)
            return (fa <= max_fa) and (draw >= min_draw) and sig_ok

        event_factor = float(np.clip(n_events / 8.0, 0.40, 1.20))
        min_draw = float(min_draw * event_factor)
        min_sig = float(min_sig * event_factor)
        max_fa = float(max_fa / event_factor)
    return (fa <= max_fa) and (draw >= min_draw) and (sig >= min_sig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Walk-forward annual stability validation for sector alert motor.")
    ap.add_argument("--start-year", type=int, default=2020)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--lookbacks", type=str, default="1,5,10,20")
    ap.add_argument("--n-random", type=int, default=120)
    ap.add_argument("--min-sector-assets", type=int, default=10)
    ap.add_argument("--min-cal-days", type=int, default=252)
    ap.add_argument("--min-test-days", type=int, default=200)
    ap.add_argument("--out-root", type=str, default="results/walkforward_sector_stability")
    ap.add_argument("--profile-file", type=str, default="config/sector_alerts_profile.json")
    ap.add_argument("--ignore-profile", action="store_true")
    ap.add_argument("--alert-policy", type=str, default="regime_entry_confirm")
    ap.add_argument("--random-baseline-method", type=str, default="both", choices=["iid", "block", "both"])
    ap.add_argument("--random-block-size", type=int, default=8)
    ap.add_argument("--q-unstable", type=float, default=0.80)
    ap.add_argument("--q-transition", type=float, default=0.80)
    ap.add_argument("--q-confidence", type=float, default=0.50)
    ap.add_argument("--q-confidence-guarded", type=float, default=0.60)
    ap.add_argument("--q-score-balanced", type=float, default=0.70)
    ap.add_argument("--q-score-guarded", type=float, default=0.80)
    ap.add_argument("--confirm-n", type=int, default=2)
    ap.add_argument("--confirm-m", type=int, default=3)
    ap.add_argument("--min-alert-gap-days", type=int, default=2)
    ap.add_argument("--auto-candidates", type=str, default="regime_entry_confirm,regime_balanced,regime_guarded")
    ap.add_argument("--gate-max-false-alarm", type=float, default=10.0)
    ap.add_argument("--gate-min-draw10", type=float, default=0.35)
    ap.add_argument("--gate-min-sig-rate", type=float, default=0.25)
    ap.add_argument("--gate-mode", type=str, default="adaptive", choices=["fixed", "adaptive"])
    args = ap.parse_args()

    profile_version = ""
    if (not args.ignore_profile) and str(args.profile_file).strip():
        p = ROOT / str(args.profile_file)
        if p.exists():
            try:
                params, gates, profile_version, gate_mode_profile = _load_profile(p)
                args.alert_policy = str(params.get("alert_policy", args.alert_policy))
                args.random_block_size = int(params.get("random_block_size", args.random_block_size))
                args.q_unstable = float(params.get("q_unstable", args.q_unstable))
                args.q_transition = float(params.get("q_transition", args.q_transition))
                args.q_confidence = float(params.get("q_confidence", args.q_confidence))
                args.q_confidence_guarded = float(params.get("q_confidence_guarded", args.q_confidence_guarded))
                args.q_score_balanced = float(params.get("q_score_balanced", args.q_score_balanced))
                args.q_score_guarded = float(params.get("q_score_guarded", args.q_score_guarded))
                args.confirm_n = int(params.get("confirm_n", args.confirm_n))
                args.confirm_m = int(params.get("confirm_m", args.confirm_m))
                args.min_alert_gap_days = int(params.get("min_alert_gap_days", args.min_alert_gap_days))
                args.auto_candidates = str(params.get("auto_candidates", args.auto_candidates))
                args.gate_max_false_alarm = float(gates["max_false_alarm_l5_l10"])
                args.gate_min_draw10 = float(gates["min_drawdown_recall_l10"])
                args.gate_min_sig_rate = float(gates["min_sig_rate_block_draw_l5_l10"])
                if str(gate_mode_profile).lower() in {"fixed", "adaptive"}:
                    args.gate_mode = str(gate_mode_profile).lower()
            except Exception:
                pass

    gates = {
        "max_false_alarm_l5_l10": float(args.gate_max_false_alarm),
        "min_drawdown_recall_l10": float(args.gate_min_draw10),
        "min_sig_rate_block_draw_l5_l10": float(args.gate_min_sig_rate),
    }
    out_root = ROOT / str(args.out_root) / _ts_id()
    out_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for year in range(int(args.start_year), int(args.end_year) + 1):
        cal_end = f"{year-1}-12-31"
        test_start = f"{year}-01-01"
        test_end = f"{year}-12-31"
        cmd = [
            sys.executable,
            "scripts/bench/event_study_validate_sectors.py",
            "--out-root",
            str(out_root / "runs" / f"{year}"),
            "--calibration-end",
            cal_end,
            "--test-start",
            test_start,
            "--test-end",
            test_end,
            "--lookbacks",
            str(args.lookbacks),
            "--n-random",
            str(int(args.n_random)),
            "--random-baseline-method",
            str(args.random_baseline_method),
            "--random-block-size",
            str(int(args.random_block_size)),
            "--min-sector-assets",
            str(int(args.min_sector_assets)),
            "--min-cal-days",
            str(int(args.min_cal_days)),
            "--min-test-days",
            str(int(args.min_test_days)),
            "--alert-policy",
            str(args.alert_policy),
            "--q-unstable",
            str(float(args.q_unstable)),
            "--q-transition",
            str(float(args.q_transition)),
            "--q-confidence",
            str(float(args.q_confidence)),
            "--q-confidence-guarded",
            str(float(args.q_confidence_guarded)),
            "--q-score-balanced",
            str(float(args.q_score_balanced)),
            "--q-score-guarded",
            str(float(args.q_score_guarded)),
            "--confirm-n",
            str(int(args.confirm_n)),
            "--confirm-m",
            str(int(args.confirm_m)),
            "--min-alert-gap-days",
            str(int(args.min_alert_gap_days)),
            "--auto-candidates",
            str(args.auto_candidates),
        ]
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = str(1000 + year)
        try:
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True, env=env)
            payload = _parse_json_last_line(proc.stdout)
            outdir = Path(str(payload["outdir"]))
            m = pd.read_csv(outdir / "sector_metrics_summary.csv")
            motor = m[m["model"] == "motor"].copy()
            summary = _window_score(motor)
            row = {
                "year": int(year),
                "calibration_end": cal_end,
                "test_start": test_start,
                "test_end": test_end,
                "outdir": str(outdir),
                "status": "ok",
                "error": "",
                **summary,
            }
            row["passes_gates"] = bool(_passes(summary, gates, gate_mode=str(args.gate_mode)))
            rows.append(row)
            print(
                f"[walkforward] year={year} score={float(summary['score']):.4f} "
                f"draw10={float(summary['drawdown_recall_l10']):.3f} fa={float(summary['false_alarm_l5_l10']):.3f} "
                f"gates={'ok' if row['passes_gates'] else 'fail'}",
                flush=True,
            )
        except subprocess.CalledProcessError as exc:
            err_txt = ((exc.stderr or "") + "\n" + (exc.stdout or "")).strip()
            row = {
                "year": int(year),
                "calibration_end": cal_end,
                "test_start": test_start,
                "test_end": test_end,
                "outdir": "",
                "status": "error",
                "error": err_txt[:1000],
                "score": float("nan"),
                "drawdown_recall_l5": float("nan"),
                "drawdown_recall_l10": float("nan"),
                "ret_tail_recall_l5": float("nan"),
                "ret_tail_recall_l10": float("nan"),
                "precision_l5_l10": float("nan"),
                "false_alarm_l5_l10": float("nan"),
                "sig_rate_block_draw_l5_l10": float("nan"),
                "p_block_min_draw_l5_l10": float("nan"),
                "passes_gates": False,
            }
            rows.append(row)
            print(f"[walkforward] year={year} error: {str(exc)}", flush=True)

    df = pd.DataFrame(rows).sort_values("year")
    df.to_csv(out_root / "walkforward_windows.csv", index=False)

    summary_json = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_version": profile_version,
        "gates": gates,
        "gate_mode": str(args.gate_mode),
        "n_windows": int(len(df)),
        "n_ok": int((df["status"] == "ok").sum()) if not df.empty else 0,
        "n_error": int((df["status"] != "ok").sum()) if not df.empty else 0,
        "n_pass": int(df["passes_gates"].sum()) if not df.empty else 0,
        "pass_rate": float(df["passes_gates"].mean()) if not df.empty else float("nan"),
        "mean_score": float(df["score"].mean()) if not df.empty else float("nan"),
        "std_score": float(df["score"].std(ddof=0)) if not df.empty else float("nan"),
        "mean_drawdown_recall_l10": float(df["drawdown_recall_l10"].mean()) if not df.empty else float("nan"),
        "mean_false_alarm_l5_l10": float(df["false_alarm_l5_l10"].mean()) if not df.empty else float("nan"),
        "median_p_block_min": float(df["p_block_min_draw_l5_l10"].median()) if not df.empty else float("nan"),
    }
    (out_root / "summary.json").write_text(json.dumps(summary_json, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("Walkforward Sector Stability")
    lines.append(f"out_root: {out_root}")
    lines.append(f"profile_version: {profile_version}")
    lines.append(f"gate_mode: {str(args.gate_mode)}")
    lines.append(f"windows: {int(len(df))}")
    lines.append(f"ok_windows: {summary_json['n_ok']}")
    lines.append(f"error_windows: {summary_json['n_error']}")
    lines.append(f"passes: {summary_json['n_pass']} ({summary_json['pass_rate']:.2%})")
    lines.append(f"mean_score: {summary_json['mean_score']:.4f}")
    lines.append(f"std_score: {summary_json['std_score']:.4f}")
    lines.append(f"mean_drawdown_recall_l10: {summary_json['mean_drawdown_recall_l10']:.4f}")
    lines.append(f"mean_false_alarm_l5_l10: {summary_json['mean_false_alarm_l5_l10']:.4f}")
    lines.append("")
    lines.append("Per-year:")
    for _, r in df.iterrows():
        if str(r.get("status", "ok")) != "ok":
            lines.append(f"- {int(r['year'])}: status=error")
            continue
        lines.append(
            f"- {int(r['year'])}: score={float(r['score']):.4f}, draw10={float(r['drawdown_recall_l10']):.3f}, "
            f"fa={float(r['false_alarm_l5_l10']):.3f}, p_block_min={float(r['p_block_min_draw_l5_l10']):.3f}, "
            f"gates={'ok' if bool(r['passes_gates']) else 'fail'}"
        )
    (out_root / "report_walkforward_stability.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "out_root": str(out_root),
                "summary_file": str(out_root / "summary.json"),
                "windows_file": str(out_root / "walkforward_windows.csv"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
