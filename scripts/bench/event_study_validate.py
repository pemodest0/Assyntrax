#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class EvalResult:
    recall: float
    precision: float
    false_alarm_per_year: float
    mean_lead_days: float
    coincident_rate: float
    n_events: int
    n_alert_days: int
    n_false_alert_days: int


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _read_tickers(path: Path) -> list[str]:
    return [x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _load_returns_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    if "date" not in df.columns:
        return None
    out = df[["date"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    if "r" in df.columns:
        out["ret"] = pd.to_numeric(df["r"], errors="coerce")
    elif "price" in df.columns:
        p = pd.to_numeric(df["price"], errors="coerce")
        out["ret"] = np.log(p / p.shift(1))
    else:
        return None
    out = out.dropna(subset=["date", "ret"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")
    return out


def build_reference_series(tickers: list[str], prices_dir: Path) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for t in tickers:
        df = _load_returns_csv(prices_dir / f"{t}.csv")
        if df is None or df.empty:
            continue
        s = df.set_index("date")["ret"].rename(t)
        parts.append(s.to_frame())
    if not parts:
        raise RuntimeError("No return series available to build reference market.")
    m = pd.concat(parts, axis=1, join="outer", sort=False).sort_index()
    ref = pd.DataFrame(index=m.index)
    ref["ret"] = m.mean(axis=1, skipna=True)
    ref["n_assets"] = m.notna().sum(axis=1)
    ref = ref.dropna(subset=["ret"])
    ref["price"] = 100.0 * np.exp(ref["ret"].cumsum())
    ref["vol20"] = ref["ret"].rolling(20, min_periods=20).std() * np.sqrt(252.0)
    ref["dd20"] = ref["price"] / ref["price"].rolling(20, min_periods=20).max() - 1.0
    ref = ref.reset_index().rename(columns={"index": "date"})
    return ref


def build_motor_daily_series(tickers: list[str], assets_dir: Path, prices_dir: Path) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for t in tickers:
        rg_path = assets_dir / f"{t}_daily_regimes.csv"
        px_path = prices_dir / f"{t}.csv"
        if not rg_path.exists() or not px_path.exists():
            continue
        try:
            rg = pd.read_csv(rg_path)
        except Exception:
            continue
        if rg.empty or "regime" not in rg.columns or "confidence" not in rg.columns:
            continue
        px = _load_returns_csv(px_path)
        if px is None or px.empty:
            continue
        dates = px["date"].to_list()
        n_rg = int(len(rg))
        if n_rg <= 0 or len(dates) < n_rg:
            continue
        date_aligned = dates[-n_rg:]
        d = pd.DataFrame(
            {
                "date": date_aligned,
                "asset": t,
                "regime": rg["regime"].astype(str).to_numpy(),
                "confidence": pd.to_numeric(rg["confidence"], errors="coerce").to_numpy(),
            }
        ).dropna(subset=["date", "confidence"])
        rows.append(d)
    if not rows:
        raise RuntimeError("No regime history found in assets folder.")

    panel = pd.concat(rows, axis=0, ignore_index=True)
    panel["is_transition"] = (panel["regime"] == "TRANSITION").astype(float)
    panel["is_unstable"] = panel["regime"].isin(["UNSTABLE", "NOISY"]).astype(float)
    panel["is_alert_regime"] = panel["regime"].isin(["TRANSITION", "UNSTABLE", "NOISY"]).astype(float)
    panel["confidence"] = panel["confidence"].clip(0.0, 1.0)

    agg = (
        panel.groupby("date", as_index=False)
        .agg(
            n_assets=("asset", "count"),
            share_transition=("is_transition", "mean"),
            share_unstable=("is_unstable", "mean"),
            share_alert_regime=("is_alert_regime", "mean"),
            mean_confidence=("confidence", "mean"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    agg["motor_score"] = (
        0.60 * agg["share_transition"] + 1.00 * agg["share_unstable"] + 0.40 * (1.0 - agg["mean_confidence"])
    )
    return agg


def _dedupe_events(event_dates: list[pd.Timestamp], event_pos: list[int], cooldown_days: int = 20) -> list[pd.Timestamp]:
    out: list[pd.Timestamp] = []
    last_pos: int | None = None
    pairs = sorted(zip(event_dates, event_pos), key=lambda x: int(x[1]))
    for d, p in pairs:
        if last_pos is None or (int(p) - int(last_pos)) > int(cooldown_days):
            out.append(pd.Timestamp(d))
            last_pos = int(p)
    return out


def build_event_dates(ref: pd.DataFrame, test_start: pd.Timestamp, ret_q01: float) -> dict[str, list[pd.Timestamp]]:
    x = ref.copy().sort_values("date")
    x["event_ret_tail"] = x["ret"] <= float(ret_q01)
    x["event_dd20"] = x["dd20"] <= -0.08
    out: dict[str, list[pd.Timestamp]] = {}
    for name, col in [("ret_tail", "event_ret_tail"), ("drawdown20", "event_dd20")]:
        mask = (x["date"] >= test_start) & (x[col].fillna(False))
        dates = x.loc[mask, "date"].tolist()
        pos = x.index[mask].tolist()
        out[name] = _dedupe_events(dates, pos, cooldown_days=20)
    return out


def evaluate_alerts(
    dates: pd.Series,
    alert: pd.Series,
    event_dates: list[pd.Timestamp],
    lookback_days: int,
    assoc_horizon_days: int = 20,
) -> EvalResult:
    dts = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    s_alert = pd.Series(alert.to_numpy(dtype=bool)).reset_index(drop=True)
    date_to_idx = {d: i for i, d in enumerate(dts)}
    event_idx = sorted([date_to_idx[d] for d in pd.to_datetime(pd.Series(event_dates)).tolist() if d in date_to_idx])

    detected = 0
    coincident = 0
    lead_days: list[int] = []
    for e in event_idx:
        lo = max(0, e - int(lookback_days))
        hi = e - 1
        if hi >= lo:
            w_pre = s_alert.iloc[lo : hi + 1]
            if bool(w_pre.any()):
                detected += 1
                first_rel = int(np.argmax(w_pre.to_numpy(dtype=bool)))
                first_idx = lo + first_rel
                lead_days.append(int(e - first_idx))
        co_lo = e
        co_hi = min(len(s_alert) - 1, e + 2)
        if co_hi >= co_lo and bool(s_alert.iloc[co_lo : co_hi + 1].any()):
            coincident += 1

    alert_days_idx = np.where(s_alert.to_numpy(dtype=bool))[0]
    # Precision/false alarm are episode-based (entry alerts), avoiding distortion from long alert streaks.
    starts_mask = s_alert.to_numpy(dtype=bool) & (~s_alert.shift(1, fill_value=False).to_numpy(dtype=bool))
    alert_episode_idx = np.where(starts_mask)[0]
    good_alerts = 0
    for a in alert_episode_idx:
        has_future_event = any((ev >= a + 1) and (ev <= a + int(assoc_horizon_days)) for ev in event_idx)
        if has_future_event:
            good_alerts += 1
    n_alert_episodes = int(len(alert_episode_idx))
    n_false_episodes = int(max(0, n_alert_episodes - good_alerts))
    years = max(1e-9, len(dts) / 252.0)

    return EvalResult(
        recall=float(detected / len(event_idx)) if event_idx else float("nan"),
        precision=float(good_alerts / n_alert_episodes) if n_alert_episodes > 0 else float("nan"),
        false_alarm_per_year=float(n_false_episodes / years),
        mean_lead_days=float(np.mean(lead_days)) if lead_days else float("nan"),
        coincident_rate=float(coincident / len(event_idx)) if event_idx else float("nan"),
        n_events=int(len(event_idx)),
        n_alert_days=int(len(alert_days_idx)),
        n_false_alert_days=n_false_episodes,
    )


def random_baseline_distribution(
    dates: pd.Series,
    n_alert_days: int,
    event_dates: list[pd.Timestamp],
    lookback_days: int,
    n_boot: int = 1000,
    seed: int = 7,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = np.arange(len(dates))
    out: list[dict[str, float]] = []
    for _ in range(int(n_boot)):
        pick = rng.choice(idx, size=min(n_alert_days, len(idx)), replace=False)
        a = np.zeros(len(dates), dtype=bool)
        a[pick] = True
        ev = evaluate_alerts(dates=dates, alert=pd.Series(a), event_dates=event_dates, lookback_days=lookback_days)
        out.append(
            {
                "recall": ev.recall,
                "precision": ev.precision,
                "false_alarm_per_year": ev.false_alarm_per_year,
                "mean_lead_days": ev.mean_lead_days,
            }
        )
    return pd.DataFrame(out)


def _format_metric(x: float) -> str:
    if pd.isna(x):
        return "nan"
    return f"{x:.4f}"


def _entry_alert(signal: pd.Series) -> pd.Series:
    s = pd.Series(signal).fillna(False).astype(bool)
    return s & (~s.shift(1, fill_value=False))


def _confirm_n_of_m(signal: pd.Series, n: int = 2, m: int = 3) -> pd.Series:
    s = pd.Series(signal).fillna(False).astype(int)
    return (s.rolling(m, min_periods=m).sum() >= int(n)).astype(bool)


def build_alert_series(cal: pd.DataFrame, test: pd.DataFrame, policy: str) -> tuple[pd.Series, dict[str, float]]:
    policy = str(policy).strip().lower()
    out: dict[str, float] = {}

    if policy == "score_q80":
        thr = float(cal["motor_score"].quantile(0.80))
        out["motor_q"] = thr
        return (test["motor_score"] >= thr).astype(bool), out

    if policy == "score_q90":
        thr = float(cal["motor_score"].quantile(0.90))
        out["motor_q"] = thr
        return (test["motor_score"] >= thr).astype(bool), out

    if policy == "regime_entry":
        q_unstable = float(cal["share_unstable"].quantile(0.80))
        q_transition = float(cal["share_transition"].quantile(0.80))
        q_conf = float(cal["mean_confidence"].quantile(0.50))
        raw = (test["share_unstable"] >= q_unstable) | (
            (test["share_transition"] >= q_transition) & (test["mean_confidence"] >= q_conf)
        )
        out["share_unstable_q80"] = q_unstable
        out["share_transition_q80"] = q_transition
        out["mean_confidence_q50"] = q_conf
        return _entry_alert(raw), out

    if policy == "regime_balanced":
        q_unstable = float(cal["share_unstable"].quantile(0.80))
        q_transition = float(cal["share_transition"].quantile(0.80))
        q_conf = float(cal["mean_confidence"].quantile(0.50))
        q_score = float(cal["motor_score"].quantile(0.70))
        raw = (
            ((test["share_unstable"] >= q_unstable) & (test["motor_score"] >= q_score))
            | (
                (test["share_transition"] >= q_transition)
                & (test["mean_confidence"] >= q_conf)
                & (test["motor_score"] >= q_score)
            )
        )
        confirmed = _confirm_n_of_m(raw, n=2, m=3)
        out["share_unstable_q80"] = q_unstable
        out["share_transition_q80"] = q_transition
        out["mean_confidence_q50"] = q_conf
        out["motor_q70"] = q_score
        out["confirm_n"] = 2.0
        out["confirm_m"] = 3.0
        return _entry_alert(confirmed), out

    if policy == "regime_guarded":
        q_unstable = float(cal["share_unstable"].quantile(0.80))
        q_transition = float(cal["share_transition"].quantile(0.80))
        q_conf = float(cal["mean_confidence"].quantile(0.60))
        q_score = float(cal["motor_score"].quantile(0.80))
        raw = (
            ((test["share_unstable"] >= q_unstable) & (test["motor_score"] >= q_score))
            | (
                (test["share_transition"] >= q_transition)
                & (test["mean_confidence"] >= q_conf)
                & (test["motor_score"] >= q_score)
            )
        )
        confirmed = _confirm_n_of_m(raw, n=2, m=3)
        out["share_unstable_q80"] = q_unstable
        out["share_transition_q80"] = q_transition
        out["mean_confidence_q60"] = q_conf
        out["motor_q80"] = q_score
        out["confirm_n"] = 2.0
        out["confirm_m"] = 3.0
        return _entry_alert(confirmed), out

    raise ValueError(f"Unknown alert policy: {policy}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate if motor anticipates stress events with causal setup.")
    ap.add_argument("--tickers-file", type=str, default="results/universe_470/tickers_470.txt")
    ap.add_argument("--assets-dir", type=str, default="results/latest_graph_universe470_batch/assets")
    ap.add_argument("--prices-dir", type=str, default="data/raw/finance/yfinance_daily")
    ap.add_argument("--calibration-end", type=str, default="2019-12-31")
    ap.add_argument("--test-start", type=str, default="2020-01-01")
    ap.add_argument("--lookbacks", type=str, default="1,5,10,20")
    ap.add_argument("--out-root", type=str, default="results/event_study")
    ap.add_argument("--n-random", type=int, default=1000)
    ap.add_argument("--skip-plots", action="store_true", help="Skip PNG charts to speed up/headless runs.")
    ap.add_argument("--verbose", action="store_true", help="Print progress to stderr.")
    ap.add_argument(
        "--alert-policy",
        type=str,
        default="regime_entry",
        choices=["regime_entry", "regime_balanced", "regime_guarded", "score_q80", "score_q90"],
        help="How to create motor alert days from aggregate diagnostics.",
    )
    args = ap.parse_args()

    def log(msg: str) -> None:
        if args.verbose:
            print(msg, file=sys.stderr, flush=True)

    log("step: read_tickers")
    tickers = _read_tickers(ROOT / args.tickers_file)
    assets_dir = ROOT / args.assets_dir
    prices_dir = ROOT / args.prices_dir
    calibration_end = pd.to_datetime(args.calibration_end)
    test_start = pd.to_datetime(args.test_start)
    lookbacks = [int(x.strip()) for x in str(args.lookbacks).split(",") if x.strip()]

    outdir = ROOT / args.out_root / _ts_id()
    outdir.mkdir(parents=True, exist_ok=True)

    log("step: build_reference_series")
    ref = build_reference_series(tickers=tickers, prices_dir=prices_dir)
    log("step: build_motor_daily_series")
    motor = build_motor_daily_series(tickers=tickers, assets_dir=assets_dir, prices_dir=prices_dir)

    log("step: merge_and_split")
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
        raise RuntimeError("Calibration/test split produced empty sample. Adjust dates.")

    log("step: thresholds")
    ret_q01 = float(cal["ret"].quantile(0.01))
    vol_q95 = float(cal["vol20"].dropna().quantile(0.95))
    motor_q80 = float(cal["motor_score"].quantile(0.80))

    log("step: events")
    events = build_event_dates(ref=df[["date", "ret", "dd20"]], test_start=test_start, ret_q01=ret_q01)

    test = test.copy()
    alert_motor, alert_meta = build_alert_series(cal=cal, test=test, policy=args.alert_policy)
    test["alert_motor"] = alert_motor
    test["alert_vol95"] = test["vol20"] >= vol_q95
    test["alert_ret1"] = test["ret"] <= ret_q01

    metrics_rows: list[dict[str, object]] = []
    events_rows: list[dict[str, object]] = []

    log("step: metrics_loop")
    for ev_name, ev_dates in events.items():
        for L in lookbacks:
            motor_ev = evaluate_alerts(test["date"], test["alert_motor"], ev_dates, lookback_days=L)
            b1_ev = evaluate_alerts(test["date"], test["alert_vol95"], ev_dates, lookback_days=L)
            b2_ev = evaluate_alerts(test["date"], test["alert_ret1"], ev_dates, lookback_days=L)
            rnd = random_baseline_distribution(
                dates=test["date"],
                n_alert_days=int(test["alert_motor"].sum()),
                event_dates=ev_dates,
                lookback_days=L,
                n_boot=int(args.n_random),
                seed=7 + L,
            )
            rnd_recall_mean = float(rnd["recall"].mean())
            rnd_recall_p95 = float(rnd["recall"].quantile(0.95))
            p_vs_random = float((rnd["recall"] >= motor_ev.recall).mean()) if np.isfinite(motor_ev.recall) else float("nan")

            metrics_rows.extend(
                [
                    {
                        "event_def": ev_name,
                        "lookback_days": L,
                        "model": "motor",
                        "recall": motor_ev.recall,
                        "precision": motor_ev.precision,
                        "false_alarm_per_year": motor_ev.false_alarm_per_year,
                        "mean_lead_days": motor_ev.mean_lead_days,
                        "coincident_rate": motor_ev.coincident_rate,
                        "n_events": motor_ev.n_events,
                        "n_alert_days": motor_ev.n_alert_days,
                        "n_false_alert_days": motor_ev.n_false_alert_days,
                        "p_vs_random_recall": p_vs_random,
                        "random_recall_mean": rnd_recall_mean,
                        "random_recall_p95": rnd_recall_p95,
                    },
                    {
                        "event_def": ev_name,
                        "lookback_days": L,
                        "model": "baseline_vol95",
                        "recall": b1_ev.recall,
                        "precision": b1_ev.precision,
                        "false_alarm_per_year": b1_ev.false_alarm_per_year,
                        "mean_lead_days": b1_ev.mean_lead_days,
                        "coincident_rate": b1_ev.coincident_rate,
                        "n_events": b1_ev.n_events,
                        "n_alert_days": b1_ev.n_alert_days,
                        "n_false_alert_days": b1_ev.n_false_alert_days,
                        "p_vs_random_recall": float("nan"),
                        "random_recall_mean": rnd_recall_mean,
                        "random_recall_p95": rnd_recall_p95,
                    },
                    {
                        "event_def": ev_name,
                        "lookback_days": L,
                        "model": "baseline_ret1",
                        "recall": b2_ev.recall,
                        "precision": b2_ev.precision,
                        "false_alarm_per_year": b2_ev.false_alarm_per_year,
                        "mean_lead_days": b2_ev.mean_lead_days,
                        "coincident_rate": b2_ev.coincident_rate,
                        "n_events": b2_ev.n_events,
                        "n_alert_days": b2_ev.n_alert_days,
                        "n_false_alert_days": b2_ev.n_false_alert_days,
                        "p_vs_random_recall": float("nan"),
                        "random_recall_mean": rnd_recall_mean,
                        "random_recall_p95": rnd_recall_p95,
                    },
                ]
            )

        d = test[["date", "alert_motor"]].copy().reset_index(drop=True)
        d_idx = {pd.Timestamp(x): i for i, x in enumerate(pd.to_datetime(d["date"]))}
        for ev in ev_dates:
            ev_ts = pd.Timestamp(ev)
            if ev_ts not in d_idx:
                continue
            i = d_idx[ev_ts]
            i1 = i - 1
            lo5 = max(0, i - 5)
            hi5 = i - 1
            alert_1d = bool(i1 >= 0 and bool(d.loc[i1, "alert_motor"]))
            w5 = d.loc[lo5:hi5].copy() if hi5 >= lo5 else d.iloc[0:0].copy()
            first5 = w5[w5["alert_motor"]]
            first5_date = pd.to_datetime(first5["date"]).iloc[0] if not first5.empty else pd.NaT
            events_rows.append(
                {
                    "event_def": ev_name,
                    "event_date": ev_ts.date().isoformat(),
                    "alert_1d_before": alert_1d,
                    "alert_week_before": bool(w5["alert_motor"].any()) if not w5.empty else False,
                    "first_alert_in_week": first5_date.date().isoformat() if pd.notna(first5_date) else "",
                    "lead_days_week": int(i - d_idx[pd.Timestamp(first5_date)]) if pd.notna(first5_date) else "",
                }
            )

    metrics_df = pd.DataFrame(metrics_rows)
    events_df = pd.DataFrame(events_rows)
    test.to_csv(outdir / "motor_score_timeseries.csv", index=False)
    metrics_df.to_csv(outdir / "metrics_summary.csv", index=False)
    events_df.to_csv(outdir / "events_with_first_alert.csv", index=False)

    # Tradeoff curve: vary threshold quantiles for motor score.
    log("step: tradeoff")
    trade_rows: list[dict[str, object]] = []
    quantiles = np.linspace(0.60, 0.95, 15)
    for ev_name, ev_dates in events.items():
        for L in lookbacks:
            for q in quantiles:
                thr = float(cal["motor_score"].quantile(float(q)))
                alert_q = test["motor_score"] >= thr
                ev_q = evaluate_alerts(test["date"], alert_q, ev_dates, lookback_days=L)
                trade_rows.append(
                    {
                        "event_def": ev_name,
                        "lookback_days": L,
                        "threshold_quantile": float(q),
                        "threshold_value": thr,
                        "recall": ev_q.recall,
                        "false_alarm_per_year": ev_q.false_alarm_per_year,
                        "precision": ev_q.precision,
                    }
                )
    trade_df = pd.DataFrame(trade_rows)
    trade_df.to_csv(outdir / "detection_false_alarm_tradeoff.csv", index=False)

    # Text report (focus on L=1 and L=5 as requested)
    log("step: write_report")
    lines: list[str] = []
    lines.append("Event Study Validation - Motor de Regimes")
    lines.append(f"generated_at_utc: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"calibration_end: {calibration_end.date().isoformat()}")
    lines.append(f"test_start: {test_start.date().isoformat()}")
    lines.append("")
    lines.append("Thresholds (calibration):")
    lines.append(f"- ret_q01: {ret_q01:.6f}")
    lines.append(f"- vol20_q95: {vol_q95:.6f}")
    lines.append(f"- motor_q80: {motor_q80:.6f}")
    lines.append(f"- alert_policy: {args.alert_policy}")
    for k, v in sorted(alert_meta.items()):
        lines.append(f"- {k}: {v:.6f}")
    lines.append("")
    lines.append("Resumo principal (L=1 e L=5):")
    for ev_name in sorted(events.keys()):
        lines.append(f"Evento: {ev_name}")
        for L in [1, 5]:
            m = metrics_df[(metrics_df["event_def"] == ev_name) & (metrics_df["lookback_days"] == L) & (metrics_df["model"] == "motor")]
            b1 = metrics_df[(metrics_df["event_def"] == ev_name) & (metrics_df["lookback_days"] == L) & (metrics_df["model"] == "baseline_vol95")]
            b2 = metrics_df[(metrics_df["event_def"] == ev_name) & (metrics_df["lookback_days"] == L) & (metrics_df["model"] == "baseline_ret1")]
            if m.empty:
                continue
            rm = m.iloc[0]
            rb1 = b1.iloc[0] if not b1.empty else None
            rb2 = b2.iloc[0] if not b2.empty else None
            lines.append(
                f"- L={L} motor: recall={_format_metric(float(rm['recall']))}, precision={_format_metric(float(rm['precision']))}, "
                f"false_alarm/ano={_format_metric(float(rm['false_alarm_per_year']))}, lead_medio={_format_metric(float(rm['mean_lead_days']))}, "
                f"p_vs_random={_format_metric(float(rm['p_vs_random_recall']))}"
            )
            if rb1 is not None:
                lines.append(
                    f"  baseline_vol95: recall={_format_metric(float(rb1['recall']))}, false_alarm/ano={_format_metric(float(rb1['false_alarm_per_year']))}"
                )
            if rb2 is not None:
                lines.append(
                    f"  baseline_ret1: recall={_format_metric(float(rb2['recall']))}, false_alarm/ano={_format_metric(float(rb2['false_alarm_per_year']))}"
                )
        lines.append("")

    # Binary conclusion rule for anticipation
    lines.append("Conclusao simples:")
    for ev_name in sorted(events.keys()):
        m1 = metrics_df[(metrics_df["event_def"] == ev_name) & (metrics_df["lookback_days"] == 1) & (metrics_df["model"] == "motor")]
        m5 = metrics_df[(metrics_df["event_def"] == ev_name) & (metrics_df["lookback_days"] == 5) & (metrics_df["model"] == "motor")]
        if m1.empty or m5.empty:
            continue
        r1 = float(m1.iloc[0]["recall"])
        r5 = float(m5.iloc[0]["recall"])
        p5 = float(m5.iloc[0]["p_vs_random_recall"])
        if np.isfinite(r5) and r5 > 0.5 and np.isfinite(p5) and p5 < 0.05:
            txt = "ha evidencia de antecipacao na semana anterior"
        elif np.isfinite(r1) and r1 > 0.4:
            txt = "antecipa alguns casos em 1 dia, mas evidencia moderada"
        else:
            txt = "nao ha evidencia forte de antecipacao"
        lines.append(f"- {ev_name}: {txt}.")

    (outdir / "report_event_study.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Plots are optional and non-blocking for report generation.
    if not args.skip_plots:
        log("step: plots")
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        try:
            fig, ax = plt.subplots(figsize=(14, 5))
            ax.plot(test["date"], test["motor_score"], lw=1.2, label="motor_score")
            ax.axhline(motor_q80, color="tab:orange", lw=1.0, ls="--", label="threshold_q80")
            for ev_name, ev_dates in events.items():
                for d in ev_dates:
                    ax.axvline(d, color=("tab:red" if ev_name == "ret_tail" else "tab:purple"), alpha=0.15, lw=0.8)
            ax.set_title("Motor Score vs Events (Test Window)")
            ax.legend(loc="upper right")
            ax.grid(alpha=0.2)
            fig.tight_layout()
            fig.savefig(outdir / "motor_score_vs_events.png", dpi=140)
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(8, 6))
            for ev_name in sorted(trade_df["event_def"].unique()):
                for L in [1, 5]:
                    d = trade_df[(trade_df["event_def"] == ev_name) & (trade_df["lookback_days"] == L)].sort_values("threshold_quantile")
                    if d.empty:
                        continue
                    ax.plot(d["false_alarm_per_year"], d["recall"], marker="o", ms=2.5, lw=1.0, label=f"{ev_name} L={L}")
            ax.set_xlabel("false_alarm_per_year")
            ax.set_ylabel("recall")
            ax.set_title("Detection vs False Alarm Tradeoff")
            ax.grid(alpha=0.25)
            ax.legend(loc="best", fontsize=8)
            fig.tight_layout()
            fig.savefig(outdir / "tradeoff_detection_false_alarm.png", dpi=140)
            plt.close(fig)
        except Exception as exc:
            (outdir / "plot_error.txt").write_text(str(exc), encoding="utf-8")

    log("step: write_config")
    cfg = {
        "tickers_file": str(ROOT / args.tickers_file),
        "assets_dir": str(assets_dir),
        "prices_dir": str(prices_dir),
        "calibration_end": calibration_end.date().isoformat(),
        "test_start": test_start.date().isoformat(),
        "lookbacks": lookbacks,
        "n_random": int(args.n_random),
        "alert_policy": str(args.alert_policy),
        "alert_meta": {k: float(v) for k, v in alert_meta.items()},
    }
    (outdir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    log("step: done")

    print(
        json.dumps(
            {
                "status": "ok",
                "outdir": str(outdir),
                "n_days_test": int(len(test)),
                "n_events_ret_tail": int(len(events.get("ret_tail", []))),
                "n_events_drawdown20": int(len(events.get("drawdown20", []))),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
