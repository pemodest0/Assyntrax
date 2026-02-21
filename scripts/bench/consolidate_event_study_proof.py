#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _event_detect_vector(
    dates: pd.Series,
    alert: pd.Series,
    event_dates: list[pd.Timestamp],
    lookback_days: int,
) -> list[int]:
    dts = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    s_alert = pd.Series(alert.to_numpy(dtype=bool)).reset_index(drop=True)
    d2i = {d: i for i, d in enumerate(dts)}
    ev_idx = sorted([d2i[d] for d in pd.to_datetime(pd.Series(event_dates)).tolist() if d in d2i])
    out: list[int] = []
    for e in ev_idx:
        lo = max(0, e - int(lookback_days))
        hi = e - 1
        hit = False
        if hi >= lo:
            hit = bool(s_alert.iloc[lo : hi + 1].any())
        out.append(1 if hit else 0)
    return out


def _binom_two_sided_p(k: int, n: int) -> float:
    if n <= 0:
        return float("nan")
    p = 0.5
    kk = min(k, n - k)
    cdf = 0.0
    for i in range(0, kk + 1):
        cdf += math.comb(n, i) * (p**i) * ((1 - p) ** (n - i))
    return float(min(1.0, 2.0 * cdf))


def _mcnemar_exact(a: list[int], b: list[int]) -> dict[str, float]:
    b_only = 0
    c_only = 0
    for x, y in zip(a, b):
        if x == 1 and y == 0:
            b_only += 1
        elif x == 0 and y == 1:
            c_only += 1
    n = b_only + c_only
    p = _binom_two_sided_p(min(b_only, c_only), n) if n > 0 else float("nan")
    return {"pvalue": p, "motor_only": float(b_only), "base_only": float(c_only)}


def _score(row: pd.Series) -> float:
    return float(
        0.40 * float(row.get("drawdown_l10_recall", 0.0))
        + 0.30 * float(row.get("drawdown_l20_recall", 0.0))
        + 0.15 * float(row.get("ret_tail_l10_recall", 0.0))
        + 0.10 * float(row.get("ret_tail_l20_recall", 0.0))
        - 0.03 * float(row.get("drawdown_l10_false_alarm", 0.0))
        - 0.02 * float(row.get("ret_tail_l10_false_alarm", 0.0))
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Consolidate event study runs into a single proof report.")
    ap.add_argument("--raw-root", type=str, default="results/event_study_proof_raw")
    ap.add_argument("--limit-runs", type=int, default=8)
    ap.add_argument("--out-root", type=str, default="results/event_study_proof")
    args = ap.parse_args()

    raw_root = ROOT / args.raw_root
    runs = sorted([p for p in raw_root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)[: int(args.limit_runs)]
    rows: list[dict[str, Any]] = []
    sig_rows: list[dict[str, Any]] = []
    seen_policy: set[str] = set()

    for run in runs[::-1]:
        cfg_path = run / "config.json"
        met_path = run / "metrics_summary.csv"
        ts_path = run / "motor_score_timeseries.csv"
        ev_path = run / "events_with_first_alert.csv"
        if not (cfg_path.exists() and met_path.exists() and ts_path.exists() and ev_path.exists()):
            continue

        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        policy = str(cfg.get("alert_policy", "")).strip()
        if not policy or policy in seen_policy:
            continue
        seen_policy.add(policy)

        met = pd.read_csv(met_path)
        ts = pd.read_csv(ts_path)
        ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
        evdf = pd.read_csv(ev_path)
        event_dates: dict[str, list[pd.Timestamp]] = {}
        if not evdf.empty:
            for ev_name, g in evdf.groupby("event_def"):
                d = pd.to_datetime(g["event_date"], errors="coerce").dropna().sort_values().unique().tolist()
                event_dates[str(ev_name)] = [pd.Timestamp(x) for x in d]

        for _, r in met[met["model"] == "motor"].iterrows():
            ev = str(r["event_def"])
            L = int(r["lookback_days"])
            b1 = met[(met["event_def"] == ev) & (met["lookback_days"] == L) & (met["model"] == "baseline_vol95")]
            b2 = met[(met["event_def"] == ev) & (met["lookback_days"] == L) & (met["model"] == "baseline_ret1")]
            rows.append(
                {
                    "policy": policy,
                    "run_id": run.name,
                    "event_def": ev,
                    "lookback_days": L,
                    "motor_recall": float(r["recall"]),
                    "motor_precision": float(r["precision"]),
                    "motor_false_alarm_per_year": float(r["false_alarm_per_year"]),
                    "motor_mean_lead_days": float(r["mean_lead_days"]),
                    "p_vs_random_recall": float(r["p_vs_random_recall"]) if np.isfinite(float(r["p_vs_random_recall"])) else float("nan"),
                    "baseline_vol95_recall": float(b1.iloc[0]["recall"]) if not b1.empty else float("nan"),
                    "baseline_ret1_recall": float(b2.iloc[0]["recall"]) if not b2.empty else float("nan"),
                }
            )

            if ev in event_dates and len(event_dates[ev]) > 0:
                det_m = _event_detect_vector(ts["date"], ts["alert_motor"].astype(bool), event_dates[ev], lookback_days=L)
                det_v = _event_detect_vector(ts["date"], ts["alert_vol95"].astype(bool), event_dates[ev], lookback_days=L)
                det_r = _event_detect_vector(ts["date"], ts["alert_ret1"].astype(bool), event_dates[ev], lookback_days=L)
                mv = _mcnemar_exact(det_m, det_v)
                mr = _mcnemar_exact(det_m, det_r)
                sig_rows.append(
                    {
                        "policy": policy,
                        "run_id": run.name,
                        "event_def": ev,
                        "lookback_days": L,
                        "p_mcnemar_motor_vs_vol95": mv["pvalue"],
                        "p_mcnemar_motor_vs_ret1": mr["pvalue"],
                        "motor_only_vs_vol95": mv["motor_only"],
                        "vol95_only_vs_motor": mv["base_only"],
                        "motor_only_vs_ret1": mr["motor_only"],
                        "ret1_only_vs_motor": mr["base_only"],
                    }
                )

    outdir = ROOT / args.out_root / _ts_id()
    outdir.mkdir(parents=True, exist_ok=True)

    long_df = pd.DataFrame(rows).sort_values(["policy", "event_def", "lookback_days"]).reset_index(drop=True)
    sig_df = pd.DataFrame(sig_rows).sort_values(["policy", "event_def", "lookback_days"]).reset_index(drop=True)
    long_df.to_csv(outdir / "policy_metrics_long.csv", index=False)
    sig_df.to_csv(outdir / "policy_significance_event_level.csv", index=False)

    # wide ranking
    rank_rows: list[dict[str, Any]] = []
    for pol, g in long_df.groupby("policy"):
        def get(ev: str, L: int, col: str) -> float:
            x = g[(g["event_def"] == ev) & (g["lookback_days"] == L)]
            return float(x.iloc[0][col]) if not x.empty else float("nan")

        rr = {
            "policy": pol,
            "drawdown_l10_recall": get("drawdown20", 10, "motor_recall"),
            "drawdown_l20_recall": get("drawdown20", 20, "motor_recall"),
            "ret_tail_l10_recall": get("ret_tail", 10, "motor_recall"),
            "ret_tail_l20_recall": get("ret_tail", 20, "motor_recall"),
            "drawdown_l10_false_alarm": get("drawdown20", 10, "motor_false_alarm_per_year"),
            "ret_tail_l10_false_alarm": get("ret_tail", 10, "motor_false_alarm_per_year"),
            "drawdown_l10_p_random": get("drawdown20", 10, "p_vs_random_recall"),
            "drawdown_l20_p_random": get("drawdown20", 20, "p_vs_random_recall"),
            "ret_tail_l10_p_random": get("ret_tail", 10, "p_vs_random_recall"),
            "ret_tail_l20_p_random": get("ret_tail", 20, "p_vs_random_recall"),
        }
        rr["score"] = _score(pd.Series(rr))
        rank_rows.append(rr)

    rank_df = pd.DataFrame(rank_rows).sort_values("score", ascending=False).reset_index(drop=True)
    rank_df.to_csv(outdir / "policy_rank.csv", index=False)

    best = rank_df.iloc[0].to_dict() if not rank_df.empty else {}
    best_policy = str(best.get("policy", ""))
    best_drawdown_strong = bool(
        best
        and float(best.get("drawdown_l10_recall", 0.0)) > 0.0
        and float(best.get("drawdown_l20_recall", 0.0)) > 0.0
        and (
            float(best.get("drawdown_l10_p_random", 1.0)) < 0.05
            or float(best.get("drawdown_l20_p_random", 1.0)) < 0.05
        )
    )
    best_ret_strong = bool(
        best
        and float(best.get("ret_tail_l10_recall", 0.0)) > 0.0
        and float(best.get("ret_tail_l20_recall", 0.0)) > 0.0
        and (
            float(best.get("ret_tail_l10_p_random", 1.0)) < 0.05
            or float(best.get("ret_tail_l20_p_random", 1.0)) < 0.05
        )
    )
    if best_drawdown_strong and best_ret_strong:
        verdict = "ANTECIPA com evidencia estatistica forte"
    elif best_drawdown_strong or best_ret_strong:
        verdict = "ANTECIPA parcialmente com evidencia forte em um tipo de evento"
    else:
        verdict = "Sem evidencia estatistica forte; sinal operacional presente"

    lines = []
    lines.append("Consolidado de Prova - Event Study")
    lines.append(f"melhor_politica: {best_policy}")
    lines.append(f"veredito_final: {verdict}")
    lines.append("")
    lines.append("Ranking:")
    for _, r in rank_df.iterrows():
        lines.append(
            f"- {r['policy']}: score={float(r['score']):.4f} | "
            f"dd_l10={float(r['drawdown_l10_recall']):.3f} p={float(r['drawdown_l10_p_random']):.3f} | "
            f"dd_l20={float(r['drawdown_l20_recall']):.3f} p={float(r['drawdown_l20_p_random']):.3f} | "
            f"rt_l10={float(r['ret_tail_l10_recall']):.3f} p={float(r['ret_tail_l10_p_random']):.3f} | "
            f"rt_l20={float(r['ret_tail_l20_recall']):.3f} p={float(r['ret_tail_l20_p_random']):.3f}"
        )
    (outdir / "report_event_study_proof_final.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    status = {
        "status": "ok",
        "outdir": str(outdir),
        "policies": rank_df["policy"].tolist(),
        "best_policy": best_policy,
        "verdict": verdict,
    }
    (outdir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
