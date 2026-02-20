#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class CandidateConfig:
    policy: str
    q_unstable: float
    q_transition: float
    q_confidence: float
    q_confidence_guarded: float
    q_score_balanced: float
    q_score_guarded: float
    confirm_n: int
    confirm_m: int
    min_alert_gap_days: int
    block_size: int

    def as_key(self) -> tuple[object, ...]:
        return (
            self.policy,
            round(self.q_unstable, 3),
            round(self.q_transition, 3),
            round(self.q_confidence, 3),
            round(self.q_confidence_guarded, 3),
            round(self.q_score_balanced, 3),
            round(self.q_score_guarded, 3),
            self.confirm_n,
            self.confirm_m,
            self.min_alert_gap_days,
            self.block_size,
        )


@dataclass
class ScoreWeights:
    w_draw10: float
    w_draw5: float
    w_tail10: float
    w_tail5: float
    w_precision: float
    w_false_alarm: float
    w_sig_rate: float


@dataclass
class QualityGates:
    max_false_alarm_l5_l10: float
    min_drawdown_recall_l10: float
    min_sig_rate_block_draw_l5_l10: float


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _parse_json_last_line(stdout: str) -> dict[str, object]:
    for ln in reversed(stdout.splitlines()):
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("{") and ln.endswith("}"):
            return json.loads(ln)
    raise RuntimeError("Could not parse JSON output from validator.")


def run_validation(
    cfg: CandidateConfig,
    out_root: Path,
    n_random: int,
    lookbacks: str,
    min_sector_assets: int,
    min_cal_days: int,
    min_test_days: int,
    two_layer_mode: str,
    seed_tag: int,
) -> Path:
    cmd = [
        sys.executable,
        "scripts/bench/event_study_validate_sectors.py",
        "--out-root",
        str(out_root),
        "--lookbacks",
        str(lookbacks),
        "--n-random",
        str(int(n_random)),
        "--random-baseline-method",
        "both",
        "--random-block-size",
        str(int(cfg.block_size)),
        "--min-sector-assets",
        str(int(min_sector_assets)),
        "--min-cal-days",
        str(int(min_cal_days)),
        "--min-test-days",
        str(int(min_test_days)),
        "--two-layer-mode",
        str(two_layer_mode),
        "--alert-policy",
        str(cfg.policy),
        "--q-unstable",
        f"{cfg.q_unstable:.6f}",
        "--q-transition",
        f"{cfg.q_transition:.6f}",
        "--q-confidence",
        f"{cfg.q_confidence:.6f}",
        "--q-confidence-guarded",
        f"{cfg.q_confidence_guarded:.6f}",
        "--q-score-balanced",
        f"{cfg.q_score_balanced:.6f}",
        "--q-score-guarded",
        f"{cfg.q_score_guarded:.6f}",
        "--confirm-n",
        str(int(cfg.confirm_n)),
        "--confirm-m",
        str(int(cfg.confirm_m)),
        "--min-alert-gap-days",
        str(int(cfg.min_alert_gap_days)),
    ]
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed_tag)
    res = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    payload = _parse_json_last_line(res.stdout)
    outdir = Path(str(payload["outdir"]))
    if not outdir.exists():
        raise RuntimeError(f"Validator outdir not found: {outdir}")
    return outdir


def evaluate_outdir(outdir: Path) -> dict[str, float]:
    p = outdir / "sector_metrics_summary.csv"
    if not p.exists():
        raise RuntimeError(f"Missing metrics file: {p}")
    df = pd.read_csv(p)
    motor = df[df["model"] == "motor"].copy()
    if motor.empty:
        raise RuntimeError("No motor rows in metrics.")

    def _mean(event: str, lb: int, col: str) -> float:
        s = motor[(motor["event_def"] == event) & (motor["lookback_days"] == lb)][col]
        return float(s.mean()) if not s.empty else float("nan")

    draw5 = _mean("drawdown20", 5, "recall")
    draw10 = _mean("drawdown20", 10, "recall")
    ret5 = _mean("ret_tail", 5, "recall")
    ret10 = _mean("ret_tail", 10, "recall")

    subset = motor[(motor["event_def"].isin(["drawdown20", "ret_tail"])) & (motor["lookback_days"].isin([5, 10]))]
    precision = float(subset["precision"].mean()) if not subset.empty else float("nan")
    false_alarm = float(subset["false_alarm_per_year"].mean()) if not subset.empty else float("nan")

    block_subset = motor[(motor["event_def"] == "drawdown20") & (motor["lookback_days"].isin([5, 10]))]
    p_block_min = float(block_subset["p_vs_random_recall_block"].min()) if not block_subset.empty else float("nan")
    p_block_med = float(block_subset["p_vs_random_recall_block"].median()) if not block_subset.empty else float("nan")
    sig_rate = (
        float((block_subset["p_vs_random_recall_block"] < 0.05).mean()) if not block_subset.empty else float("nan")
    )

    return {
        "drawdown_recall_l5": float(draw5),
        "drawdown_recall_l10": float(draw10),
        "ret_tail_recall_l5": float(ret5),
        "ret_tail_recall_l10": float(ret10),
        "precision_l5_l10": float(precision),
        "false_alarm_l5_l10": float(false_alarm),
        "p_block_min_draw_l5_l10": float(p_block_min),
        "p_block_med_draw_l5_l10": float(p_block_med),
        "sig_rate_block_draw_l5_l10": float(sig_rate),
    }


def compute_score(metrics: dict[str, float], weights: ScoreWeights) -> float:
    return float(
        weights.w_draw10 * np.nan_to_num(metrics.get("drawdown_recall_l10", np.nan))
        + weights.w_draw5 * np.nan_to_num(metrics.get("drawdown_recall_l5", np.nan))
        + weights.w_tail10 * np.nan_to_num(metrics.get("ret_tail_recall_l10", np.nan))
        + weights.w_tail5 * np.nan_to_num(metrics.get("ret_tail_recall_l5", np.nan))
        + weights.w_precision * np.nan_to_num(metrics.get("precision_l5_l10", np.nan))
        - weights.w_false_alarm * np.nan_to_num(metrics.get("false_alarm_l5_l10", np.nan))
        + weights.w_sig_rate * np.nan_to_num(metrics.get("sig_rate_block_draw_l5_l10", np.nan))
    )


def passes_gates(metrics: dict[str, float], gates: QualityGates) -> bool:
    fa = float(np.nan_to_num(metrics.get("false_alarm_l5_l10", np.nan), nan=1e9))
    draw10 = float(np.nan_to_num(metrics.get("drawdown_recall_l10", np.nan), nan=-1e9))
    sig = float(np.nan_to_num(metrics.get("sig_rate_block_draw_l5_l10", np.nan), nan=-1e9))
    return (
        (fa <= float(gates.max_false_alarm_l5_l10))
        and (draw10 >= float(gates.min_drawdown_recall_l10))
        and (sig >= float(gates.min_sig_rate_block_draw_l5_l10))
    )


def _load_profile(path: Path) -> tuple[CandidateConfig, QualityGates, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    params = payload.get("params", payload)
    gates_raw = payload.get("acceptance_gates", {})
    cfg = CandidateConfig(
        policy=str(params.get("alert_policy", "regime_entry_confirm")),
        q_unstable=float(params.get("q_unstable", 0.80)),
        q_transition=float(params.get("q_transition", 0.80)),
        q_confidence=float(params.get("q_confidence", 0.50)),
        q_confidence_guarded=float(params.get("q_confidence_guarded", 0.60)),
        q_score_balanced=float(params.get("q_score_balanced", 0.70)),
        q_score_guarded=float(params.get("q_score_guarded", 0.80)),
        confirm_n=int(params.get("confirm_n", 2)),
        confirm_m=int(params.get("confirm_m", 3)),
        min_alert_gap_days=int(params.get("min_alert_gap_days", 2)),
        block_size=int(params.get("random_block_size", 10)),
    )
    gates = QualityGates(
        max_false_alarm_l5_l10=float(gates_raw.get("max_false_alarm_l5_l10", 10.0)),
        min_drawdown_recall_l10=float(gates_raw.get("min_drawdown_recall_l10", 0.35)),
        min_sig_rate_block_draw_l5_l10=float(gates_raw.get("min_sig_rate_block_draw_l5_l10", 0.25)),
    )
    profile_version = str(payload.get("profile_version", ""))
    return cfg, gates, profile_version


def _sample_candidate(rng: random.Random, base: CandidateConfig | None = None) -> CandidateConfig:
    policies = ["regime_entry_confirm", "regime_balanced", "regime_guarded", "regime_auto"]
    if base is None or rng.random() < 0.35:
        policy = rng.choice(policies)
        q_unstable = rng.uniform(0.70, 0.92)
        q_transition = rng.uniform(0.68, 0.92)
        q_confidence = rng.uniform(0.35, 0.70)
        q_conf_guarded = rng.uniform(0.45, 0.80)
        q_score_balanced = rng.uniform(0.60, 0.88)
        q_score_guarded = rng.uniform(0.70, 0.93)
        confirm_m = rng.choice([2, 3, 4, 5])
        confirm_n = rng.randint(1, confirm_m)
        min_alert_gap_days = rng.choice([1, 2, 3, 4])
        block_size = rng.choice([5, 8, 10, 12, 15])
        return CandidateConfig(
            policy=policy,
            q_unstable=q_unstable,
            q_transition=q_transition,
            q_confidence=q_confidence,
            q_confidence_guarded=q_conf_guarded,
            q_score_balanced=q_score_balanced,
            q_score_guarded=q_score_guarded,
            confirm_n=confirm_n,
            confirm_m=confirm_m,
            min_alert_gap_days=min_alert_gap_days,
            block_size=block_size,
        )

    policy = base.policy if rng.random() < 0.70 else rng.choice(policies)
    q_unstable = float(np.clip(base.q_unstable + rng.uniform(-0.06, 0.06), 0.60, 0.95))
    q_transition = float(np.clip(base.q_transition + rng.uniform(-0.06, 0.06), 0.60, 0.95))
    q_confidence = float(np.clip(base.q_confidence + rng.uniform(-0.08, 0.08), 0.20, 0.90))
    q_conf_guarded = float(np.clip(base.q_confidence_guarded + rng.uniform(-0.08, 0.08), 0.20, 0.95))
    q_score_balanced = float(np.clip(base.q_score_balanced + rng.uniform(-0.07, 0.07), 0.50, 0.95))
    q_score_guarded = float(np.clip(base.q_score_guarded + rng.uniform(-0.07, 0.07), 0.50, 0.97))
    confirm_m = int(np.clip(base.confirm_m + rng.choice([-1, 0, 1]), 2, 6))
    confirm_n = int(np.clip(base.confirm_n + rng.choice([-1, 0, 1]), 1, confirm_m))
    min_alert_gap_days = int(np.clip(base.min_alert_gap_days + rng.choice([-1, 0, 1]), 0, 7))
    block_size = int(rng.choice([5, 8, 10, 12, 15]))
    return CandidateConfig(
        policy=policy,
        q_unstable=q_unstable,
        q_transition=q_transition,
        q_confidence=q_confidence,
        q_confidence_guarded=q_conf_guarded,
        q_score_balanced=q_score_balanced,
        q_score_guarded=q_score_guarded,
        confirm_n=confirm_n,
        confirm_m=confirm_m,
        min_alert_gap_days=min_alert_gap_days,
        block_size=block_size,
    )


def _baseline_config() -> CandidateConfig:
    return CandidateConfig(
        policy="regime_entry_confirm",
        q_unstable=0.80,
        q_transition=0.80,
        q_confidence=0.50,
        q_confidence_guarded=0.60,
        q_score_balanced=0.70,
        q_score_guarded=0.80,
        confirm_n=2,
        confirm_m=3,
        min_alert_gap_days=2,
        block_size=10,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Hyper simulation for sector alert motor parameters.")
    ap.add_argument("--n-sims", type=int, default=6, help="Number of random simulations after baseline.")
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--lookbacks", type=str, default="1,5,10,20")
    ap.add_argument("--search-n-random", type=int, default=80)
    ap.add_argument("--final-n-random", type=int, default=300)
    ap.add_argument("--min-sector-assets", type=int, default=10)
    ap.add_argument("--min-cal-days", type=int, default=252)
    ap.add_argument("--min-test-days", type=int, default=252)
    ap.add_argument("--two-layer-mode", type=str, default="on", choices=["on", "off"])
    ap.add_argument("--gate-mode", type=str, default="adaptive", choices=["fixed", "adaptive"])
    ap.add_argument("--out-root", type=str, default="results/hyper_sector_search")
    ap.add_argument("--baseline-profile-file", type=str, default="config/sector_alerts_profile.json")
    ap.add_argument("--require-gates", action="store_true", default=True)
    ap.add_argument("--no-require-gates", action="store_true")
    ap.add_argument("--w-draw10", type=float, default=0.50)
    ap.add_argument("--w-draw5", type=float, default=0.20)
    ap.add_argument("--w-tail10", type=float, default=0.15)
    ap.add_argument("--w-tail5", type=float, default=0.05)
    ap.add_argument("--w-precision", type=float, default=0.20)
    ap.add_argument("--w-false-alarm", type=float, default=0.03)
    ap.add_argument("--w-sig-rate", type=float, default=0.15)
    ap.add_argument("--gate-max-false-alarm", type=float, default=10.0)
    ap.add_argument("--gate-min-draw10", type=float, default=0.35)
    ap.add_argument("--gate-min-sig-rate", type=float, default=0.25)
    args = ap.parse_args()
    if bool(args.no_require_gates):
        args.require_gates = False

    rng = random.Random(int(args.seed))
    run_root = ROOT / str(args.out_root) / _ts_id()
    runs_root = run_root / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    weights = ScoreWeights(
        w_draw10=float(args.w_draw10),
        w_draw5=float(args.w_draw5),
        w_tail10=float(args.w_tail10),
        w_tail5=float(args.w_tail5),
        w_precision=float(args.w_precision),
        w_false_alarm=float(args.w_false_alarm),
        w_sig_rate=float(args.w_sig_rate),
    )
    gates = QualityGates(
        max_false_alarm_l5_l10=float(args.gate_max_false_alarm),
        min_drawdown_recall_l10=float(args.gate_min_draw10),
        min_sig_rate_block_draw_l5_l10=float(args.gate_min_sig_rate),
    )
    profile_version = ""
    profile_path = ROOT / str(args.baseline_profile_file)
    if profile_path.exists():
        try:
            base_cfg_from_profile, gates_from_profile, profile_version = _load_profile(profile_path)
            if float(args.gate_max_false_alarm) == 10.0 and float(args.gate_min_draw10) == 0.35 and float(args.gate_min_sig_rate) == 0.25:
                gates = gates_from_profile
            base_cfg = base_cfg_from_profile
        except Exception:
            base_cfg = _baseline_config()
    else:
        base_cfg = _baseline_config()

    history: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    champion_cfg = base_cfg
    champion_score = -1e18
    champion_outdir = Path()
    champion_passes_gates = False
    fallback_cfg = base_cfg
    fallback_score = -1e18
    fallback_outdir = Path()

    total = int(max(0, args.n_sims)) + 1
    prev_score = float("nan")

    for i in range(total):
        if i == 0:
            cfg = base_cfg
            tag = "baseline"
        else:
            cfg = _sample_candidate(rng=rng, base=champion_cfg)
            tries = 0
            while cfg.as_key() in seen and tries < 50:
                cfg = _sample_candidate(rng=rng, base=champion_cfg)
                tries += 1
            tag = f"sim_{i:03d}"
        seen.add(cfg.as_key())

        sim_out_root = runs_root / tag
        sim_out_root.mkdir(parents=True, exist_ok=True)

        outdir = run_validation(
            cfg=cfg,
            out_root=sim_out_root,
            n_random=int(args.search_n_random),
            lookbacks=str(args.lookbacks),
            min_sector_assets=int(args.min_sector_assets),
            min_cal_days=int(args.min_cal_days),
            min_test_days=int(args.min_test_days),
            two_layer_mode=str(args.two_layer_mode),
            seed_tag=int(args.seed + i),
        )
        metrics = evaluate_outdir(outdir)
        score = compute_score(metrics=metrics, weights=weights)
        pass_gate = passes_gates(metrics=metrics, gates=gates)
        better_than_prev = bool(np.isfinite(prev_score) and score > prev_score)
        better_than_champion_before = bool(score > champion_score)
        if score > fallback_score:
            fallback_cfg = cfg
            fallback_score = score
            fallback_outdir = outdir
        if bool(args.require_gates):
            can_promote = bool(pass_gate and (score > champion_score or not champion_passes_gates))
        else:
            can_promote = bool(score > champion_score)
        if can_promote:
            champion_cfg = cfg
            champion_score = score
            champion_outdir = outdir
            champion_passes_gates = bool(pass_gate)
        prev_score = score

        row: dict[str, object] = {
            "sim_index": i,
            "tag": tag,
            "outdir": str(outdir),
            "is_baseline": i == 0,
            "better_than_prev": better_than_prev,
            "better_than_champion_before": better_than_champion_before,
            "is_champion_after": cfg.as_key() == champion_cfg.as_key(),
            "passes_gates": bool(pass_gate),
            "policy": cfg.policy,
            "q_unstable": cfg.q_unstable,
            "q_transition": cfg.q_transition,
            "q_confidence": cfg.q_confidence,
            "q_confidence_guarded": cfg.q_confidence_guarded,
            "q_score_balanced": cfg.q_score_balanced,
            "q_score_guarded": cfg.q_score_guarded,
            "confirm_n": cfg.confirm_n,
            "confirm_m": cfg.confirm_m,
            "min_alert_gap_days": cfg.min_alert_gap_days,
            "block_size": cfg.block_size,
            **metrics,
            "score": float(score),
        }
        history.append(row)

        print(
            f"[{i+1}/{total}] {tag} policy={cfg.policy} score={score:.4f} "
            f"vs_prev={'+' if better_than_prev else '-'} vs_best={'+' if can_promote else '-'} "
            f"gates={'ok' if pass_gate else 'fail'}",
            flush=True,
        )

    if (not champion_outdir.exists()) and fallback_outdir.exists():
        champion_cfg = fallback_cfg
        champion_score = fallback_score
        champion_outdir = fallback_outdir
        champion_passes_gates = False

    final_root = run_root / "final_champion"
    final_root.mkdir(parents=True, exist_ok=True)
    final_outdir = run_validation(
        cfg=champion_cfg,
        out_root=final_root,
        n_random=int(args.final_n_random),
        lookbacks=str(args.lookbacks),
        min_sector_assets=int(args.min_sector_assets),
        min_cal_days=int(args.min_cal_days),
        min_test_days=int(args.min_test_days),
        two_layer_mode=str(args.two_layer_mode),
        seed_tag=int(args.seed + 9999),
    )
    final_metrics = evaluate_outdir(final_outdir)
    final_score = compute_score(metrics=final_metrics, weights=weights)
    final_pass_gate = passes_gates(metrics=final_metrics, gates=gates)

    hist_df = pd.DataFrame(history).sort_values("sim_index")
    hist_df.to_csv(run_root / "simulations.csv", index=False)

    champion_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "search": {
            "n_sims": int(args.n_sims),
            "search_n_random": int(args.search_n_random),
            "final_n_random": int(args.final_n_random),
            "lookbacks": str(args.lookbacks),
            "min_sector_assets": int(args.min_sector_assets),
            "seed": int(args.seed),
            "profile_version": profile_version,
            "baseline_profile_file": str(profile_path),
            "require_gates": bool(args.require_gates),
        },
        "weights": weights.__dict__,
        "gates": gates.__dict__,
        "champion_from_search": {
            "outdir": str(champion_outdir),
            "score": float(champion_score),
            "passes_gates": bool(champion_passes_gates),
            "config": champion_cfg.__dict__,
        },
        "champion_final_validation": {
            "outdir": str(final_outdir),
            "score": float(final_score),
            "passes_gates": bool(final_pass_gate),
            **final_metrics,
        },
    }
    (run_root / "best_config.json").write_text(json.dumps(champion_payload, indent=2), encoding="utf-8")
    promoted_profile = {
        "profile_version": f"sector_profile_auto_{_ts_id()}",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_run": str(final_outdir),
        "gate_mode": str(args.gate_mode),
        "params": {
            "lookbacks": str(args.lookbacks),
            "n_random": int(args.final_n_random),
            "random_baseline_method": "both",
            "random_block_size": int(champion_cfg.block_size),
            "min_sector_assets": int(args.min_sector_assets),
            "min_cal_days": int(args.min_cal_days),
            "min_test_days": int(args.min_test_days),
            "alert_policy": str(champion_cfg.policy),
            "two_layer_mode": str(args.two_layer_mode),
            "q_unstable": float(champion_cfg.q_unstable),
            "q_transition": float(champion_cfg.q_transition),
            "q_confidence": float(champion_cfg.q_confidence),
            "q_confidence_guarded": float(champion_cfg.q_confidence_guarded),
            "q_score_balanced": float(champion_cfg.q_score_balanced),
            "q_score_guarded": float(champion_cfg.q_score_guarded),
            "confirm_n": int(champion_cfg.confirm_n),
            "confirm_m": int(champion_cfg.confirm_m),
            "min_alert_gap_days": int(champion_cfg.min_alert_gap_days),
            "auto_candidates": "regime_entry_confirm,regime_balanced,regime_guarded",
        },
        "acceptance_gates": gates.__dict__,
    }
    (run_root / "champion_profile.json").write_text(json.dumps(promoted_profile, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("Hyper Simulation - Sector Alert Motor")
    lines.append(f"run_root: {run_root}")
    lines.append(f"n_sims: {int(args.n_sims)}")
    lines.append(f"search_n_random: {int(args.search_n_random)}")
    lines.append(f"final_n_random: {int(args.final_n_random)}")
    lines.append(f"min_cal_days: {int(args.min_cal_days)}")
    lines.append(f"min_test_days: {int(args.min_test_days)}")
    lines.append(f"two_layer_mode: {str(args.two_layer_mode)}")
    lines.append(f"gate_mode: {str(args.gate_mode)}")
    lines.append(f"require_gates: {bool(args.require_gates)}")
    lines.append(f"profile_version: {profile_version}")
    lines.append("weights:")
    for k, v in weights.__dict__.items():
        lines.append(f"- {k}: {float(v):.4f}")
    lines.append("gates:")
    for k, v in gates.__dict__.items():
        lines.append(f"- {k}: {float(v):.4f}")
    lines.append("")
    lines.append("Champion config:")
    for k, v in champion_cfg.__dict__.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append(f"Champion search score: {champion_score:.6f}")
    lines.append(f"Champion search passes gates: {champion_passes_gates}")
    lines.append("Champion final metrics:")
    lines.append(f"- score: {float(final_score):.6f}")
    lines.append(f"- passes_gates: {bool(final_pass_gate)}")
    for k, v in final_metrics.items():
        lines.append(f"- {k}: {float(v):.6f}")
    lines.append("")
    lines.append("Top 5 simulations by score:")
    top = hist_df.sort_values("score", ascending=False).head(5)
    for _, r in top.iterrows():
        lines.append(
            f"- sim={int(r['sim_index'])} tag={r['tag']} policy={r['policy']} "
            f"score={float(r['score']):.6f} recall_d10={float(r['drawdown_recall_l10']):.4f} "
            f"fa={float(r['false_alarm_l5_l10']):.4f}"
        )
    lines.append("")
    lines.append(f"Generated profile file: {run_root / 'champion_profile.json'}")
    (run_root / "report_hyper_simulation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "run_root": str(run_root),
                "champion_final_outdir": str(final_outdir),
                "champion_policy": champion_cfg.policy,
                "champion_score_search": float(champion_score),
                "champion_score_final": float(final_score),
                "champion_passes_gates": bool(final_pass_gate),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
