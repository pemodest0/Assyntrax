#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bench import event_study_validate as es  # noqa: E402


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt(x: float | None, d: int = 4) -> str:
    if x is None or not np.isfinite(float(x)):
        return "nan"
    return f"{float(x):.{d}f}"


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
    # two-sided exact binomial by tail doubling around min(k, n-k)
    kk = min(k, n - k)
    cdf = 0.0
    for i in range(0, kk + 1):
        cdf += math.comb(n, i) * (p**i) * ((1 - p) ** (n - i))
    return float(min(1.0, 2.0 * cdf))


def _mcnemar_exact(a: list[int], b: list[int]) -> dict[str, float]:
    if len(a) != len(b) or not a:
        return {"pvalue": float("nan"), "b_motor_only": float("nan"), "c_baseline_only": float("nan")}
    b_motor_only = 0
    c_baseline_only = 0
    for x, y in zip(a, b):
        if x == 1 and y == 0:
            b_motor_only += 1
        elif x == 0 and y == 1:
            c_baseline_only += 1
    n = b_motor_only + c_baseline_only
    p = _binom_two_sided_p(min(b_motor_only, c_baseline_only), n) if n > 0 else float("nan")
    return {"pvalue": p, "b_motor_only": float(b_motor_only), "c_baseline_only": float(c_baseline_only)}


def _score_row(row: pd.Series) -> float:
    return float(
        0.40 * float(row["drawdown_l10_recall"])
        + 0.25 * float(row["drawdown_l20_recall"])
        + 0.15 * float(row["ret_tail_l10_recall"])
        + 0.10 * float(row["ret_tail_l20_recall"])
        - 0.06 * float(row["drawdown_l10_false_alarm"])
        - 0.04 * float(row["ret_tail_l10_false_alarm"])
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Prova estatistica reforcada para estudo de eventos.")
    ap.add_argument("--tickers-file", type=str, default="results/universe_470/tickers_470.txt")
    ap.add_argument("--assets-dir", type=str, default="results/latest_graph_universe470_batch/assets")
    ap.add_argument("--prices-dir", type=str, default="data/raw/finance/yfinance_daily")
    ap.add_argument("--calibration-end", type=str, default="2019-12-31")
    ap.add_argument("--test-start", type=str, default="2020-01-01")
    ap.add_argument("--lookbacks", type=str, default="1,5,10,20")
    ap.add_argument("--policies", type=str, default="regime_entry,regime_balanced,regime_guarded,score_q80,score_q90")
    ap.add_argument("--n-random", type=int, default=3000)
    ap.add_argument("--out-root", type=str, default="results/event_study_proof")
    args = ap.parse_args()

    tickers = es._read_tickers(ROOT / args.tickers_file)
    calibration_end = pd.to_datetime(args.calibration_end)
    test_start = pd.to_datetime(args.test_start)
    lookbacks = [int(x.strip()) for x in str(args.lookbacks).split(",") if x.strip()]
    policies = [x.strip() for x in str(args.policies).split(",") if x.strip()]

    outdir = ROOT / args.out_root / _ts_id()
    outdir.mkdir(parents=True, exist_ok=True)

    ref = es.build_reference_series(tickers=tickers, prices_dir=ROOT / args.prices_dir)
    motor = es.build_motor_daily_series(tickers=tickers, assets_dir=ROOT / args.assets_dir, prices_dir=ROOT / args.prices_dir)
    df = pd.merge(
        motor,
        ref[["date", "ret", "price", "vol20", "dd20", "n_assets"]],
        on="date",
        how="inner",
        suffixes=("_motor", "_ref"),
    ).sort_values("date")
    df = df[df["date"] >= pd.to_datetime("2018-01-01")].reset_index(drop=True)

    cal = df[df["date"] <= calibration_end].copy()
    test = df[df["date"] >= test_start].copy()
    if cal.empty or test.empty:
        raise RuntimeError("calibration/test split empty")

    ret_q01 = float(cal["ret"].quantile(0.01))
    vol_q95 = float(cal["vol20"].dropna().quantile(0.95))
    events = es.build_event_dates(ref=df[["date", "ret", "dd20"]], test_start=test_start, ret_q01=ret_q01)

    policy_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    sig_rows: list[dict[str, Any]] = []

    for policy in policies:
        t = test.copy()
        alert_motor, alert_meta = es.build_alert_series(cal=cal, test=t, policy=policy)
        t["alert_motor"] = alert_motor
        t["alert_vol95"] = t["vol20"] >= vol_q95
        t["alert_ret1"] = t["ret"] <= ret_q01
        motor_alert_episodes = int(es._entry_alert(t["alert_motor"]).sum())

        # Evaluate each event def and lookback
        policy_metric: dict[str, Any] = {"policy": policy}
        for ev_name, ev_dates in events.items():
            for L in lookbacks:
                motor_ev = es.evaluate_alerts(t["date"], t["alert_motor"], ev_dates, lookback_days=L)
                b1_ev = es.evaluate_alerts(t["date"], t["alert_vol95"], ev_dates, lookback_days=L)
                b2_ev = es.evaluate_alerts(t["date"], t["alert_ret1"], ev_dates, lookback_days=L)
                rnd = es.random_baseline_distribution(
                    dates=t["date"],
                    n_alert_days=motor_alert_episodes,
                    event_dates=ev_dates,
                    lookback_days=L,
                    n_boot=int(args.n_random),
                    seed=101 + L,
                )
                p_vs_random = float((rnd["recall"] >= motor_ev.recall).mean()) if np.isfinite(motor_ev.recall) else float("nan")

                metric_rows.append(
                    {
                        "policy": policy,
                        "event_def": ev_name,
                        "lookback_days": int(L),
                        "motor_recall": float(motor_ev.recall),
                        "motor_precision": float(motor_ev.precision),
                        "motor_false_alarm_per_year": float(motor_ev.false_alarm_per_year),
                        "motor_lead_days": float(motor_ev.mean_lead_days),
                        "baseline_vol95_recall": float(b1_ev.recall),
                        "baseline_ret1_recall": float(b2_ev.recall),
                        "p_vs_random_recall": p_vs_random,
                        "random_recall_mean": float(rnd["recall"].mean()),
                        "random_recall_p95": float(rnd["recall"].quantile(0.95)),
                    }
                )

                if ev_name == "drawdown20":
                    policy_metric[f"drawdown_l{L}_recall"] = float(motor_ev.recall)
                    policy_metric[f"drawdown_l{L}_false_alarm"] = float(motor_ev.false_alarm_per_year)
                    policy_metric[f"drawdown_l{L}_p_random"] = p_vs_random
                if ev_name == "ret_tail":
                    policy_metric[f"ret_tail_l{L}_recall"] = float(motor_ev.recall)
                    policy_metric[f"ret_tail_l{L}_false_alarm"] = float(motor_ev.false_alarm_per_year)
                    policy_metric[f"ret_tail_l{L}_p_random"] = p_vs_random

                # Event-level significance vs simple baselines (McNemar exact)
                det_m = _event_detect_vector(t["date"], t["alert_motor"], ev_dates, lookback_days=L)
                det_v = _event_detect_vector(t["date"], t["alert_vol95"], ev_dates, lookback_days=L)
                det_r = _event_detect_vector(t["date"], t["alert_ret1"], ev_dates, lookback_days=L)
                sig_mv = _mcnemar_exact(det_m, det_v)
                sig_mr = _mcnemar_exact(det_m, det_r)
                sig_rows.append(
                    {
                        "policy": policy,
                        "event_def": ev_name,
                        "lookback_days": int(L),
                        "p_mcnemar_motor_vs_vol95": float(sig_mv["pvalue"]),
                        "p_mcnemar_motor_vs_ret1": float(sig_mr["pvalue"]),
                        "motor_only_vs_vol95": float(sig_mv["b_motor_only"]),
                        "vol95_only_vs_motor": float(sig_mv["c_baseline_only"]),
                        "motor_only_vs_ret1": float(sig_mr["b_motor_only"]),
                        "ret1_only_vs_motor": float(sig_mr["c_baseline_only"]),
                    }
                )

        # Keep alert thresholds metadata
        for k, v in alert_meta.items():
            policy_metric[f"meta_{k}"] = float(v)
        policy_rows.append(policy_metric)

    metrics_df = pd.DataFrame(metric_rows)
    sig_df = pd.DataFrame(sig_rows)
    policy_df = pd.DataFrame(policy_rows)
    if not policy_df.empty:
        # Ensure required columns exist for scoring
        for col in [
            "drawdown_l10_recall",
            "drawdown_l20_recall",
            "ret_tail_l10_recall",
            "ret_tail_l20_recall",
            "drawdown_l10_false_alarm",
            "ret_tail_l10_false_alarm",
        ]:
            if col not in policy_df.columns:
                policy_df[col] = np.nan
        policy_df["score"] = policy_df.apply(_score_row, axis=1)
        policy_df = policy_df.sort_values("score", ascending=False).reset_index(drop=True)

    metrics_df.to_csv(outdir / "policy_metrics_long.csv", index=False)
    sig_df.to_csv(outdir / "policy_significance_event_level.csv", index=False)
    policy_df.to_csv(outdir / "policy_rank.csv", index=False)

    best = policy_df.iloc[0].to_dict() if not policy_df.empty else {}
    best_policy = str(best.get("policy", ""))
    best_metrics = metrics_df[metrics_df["policy"] == best_policy].copy() if best_policy else pd.DataFrame()
    best_metrics.to_csv(outdir / "best_policy_metrics.csv", index=False)

    # Final verdict
    verdict_lines: list[str] = []
    if best_policy:
        # Focus on drawdown L10/L20 criteria
        def _pick(df: pd.DataFrame, ev: str, L: int) -> dict[str, Any]:
            x = df[(df["event_def"] == ev) & (df["lookback_days"] == L)]
            return x.iloc[0].to_dict() if not x.empty else {}

        d10 = _pick(best_metrics, "drawdown20", 10)
        d20 = _pick(best_metrics, "drawdown20", 20)
        r10 = _pick(best_metrics, "ret_tail", 10)
        r20 = _pick(best_metrics, "ret_tail", 20)
        cond_recall = (
            d10
            and d20
            and (float(d10["motor_recall"]) > max(float(d10["baseline_vol95_recall"]), float(d10["baseline_ret1_recall"])))
            and (float(d20["motor_recall"]) > max(float(d20["baseline_vol95_recall"]), float(d20["baseline_ret1_recall"])))
        )
        cond_false = bool(d10 and d20 and float(d10["motor_false_alarm_per_year"]) <= 30.0 and float(d20["motor_false_alarm_per_year"]) <= 30.0)
        cond_random = bool(d10 and d20 and (float(d10["p_vs_random_recall"]) < 0.05 or float(d20["p_vs_random_recall"]) < 0.05))

        if cond_recall and cond_false and cond_random:
            verdict = "ANTEcipa com evidencia estatistica forte"
        elif cond_recall and cond_false:
            verdict = "Tem sinal operacional, mas sem evidencia estatistica forte"
        else:
            verdict = "Nao ha evidencia forte de antecipacao no protocolo atual"

        verdict_lines.append(f"politica_escolhida={best_policy}")
        verdict_lines.append(f"veredito={verdict}")
        verdict_lines.append(
            "drawdown_L10: "
            f"recall={_fmt(_safe(best_metrics, 'drawdown20', 10, 'motor_recall'))}, "
            f"precision={_fmt(_safe(best_metrics, 'drawdown20', 10, 'motor_precision'))}, "
            f"false_alarm={_fmt(_safe(best_metrics, 'drawdown20', 10, 'motor_false_alarm_per_year'))}, "
            f"p_random={_fmt(_safe(best_metrics, 'drawdown20', 10, 'p_vs_random_recall'))}"
        )
        verdict_lines.append(
            "drawdown_L20: "
            f"recall={_fmt(_safe(best_metrics, 'drawdown20', 20, 'motor_recall'))}, "
            f"precision={_fmt(_safe(best_metrics, 'drawdown20', 20, 'motor_precision'))}, "
            f"false_alarm={_fmt(_safe(best_metrics, 'drawdown20', 20, 'motor_false_alarm_per_year'))}, "
            f"p_random={_fmt(_safe(best_metrics, 'drawdown20', 20, 'p_vs_random_recall'))}"
        )
        verdict_lines.append(
            "ret_tail_L10: "
            f"recall={_fmt(_safe(best_metrics, 'ret_tail', 10, 'motor_recall'))}, "
            f"precision={_fmt(_safe(best_metrics, 'ret_tail', 10, 'motor_precision'))}, "
            f"false_alarm={_fmt(_safe(best_metrics, 'ret_tail', 10, 'motor_false_alarm_per_year'))}, "
            f"p_random={_fmt(_safe(best_metrics, 'ret_tail', 10, 'p_vs_random_recall'))}"
        )
        verdict_lines.append(
            "ret_tail_L20: "
            f"recall={_fmt(_safe(best_metrics, 'ret_tail', 20, 'motor_recall'))}, "
            f"precision={_fmt(_safe(best_metrics, 'ret_tail', 20, 'motor_precision'))}, "
            f"false_alarm={_fmt(_safe(best_metrics, 'ret_tail', 20, 'motor_false_alarm_per_year'))}, "
            f"p_random={_fmt(_safe(best_metrics, 'ret_tail', 20, 'p_vs_random_recall'))}"
        )
    else:
        verdict_lines.append("sem_resultado")

    (outdir / "report_event_study_proof.txt").write_text("\n".join(verdict_lines) + "\n", encoding="utf-8")

    status = {
        "status": "ok",
        "outdir": str(outdir),
        "best_policy": best_policy,
        "n_policies": int(len(policies)),
        "n_rows_metrics": int(metrics_df.shape[0]),
        "n_rows_significance": int(sig_df.shape[0]),
    }
    (outdir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))


def _safe(df: pd.DataFrame, ev: str, L: int, col: str) -> float | None:
    x = df[(df["event_def"] == ev) & (df["lookback_days"] == L)]
    if x.empty or col not in x.columns:
        return None
    v = x.iloc[0][col]
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if np.isfinite(f) else None


if __name__ == "__main__":
    main()
