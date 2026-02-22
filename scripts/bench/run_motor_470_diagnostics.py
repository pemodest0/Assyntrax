#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = ROOT / "results" / "lab_corr_macro"
UNIVERSE_ROOT = ROOT / "results" / "latest_graph_universe470_batch"


@dataclass
class AlertMetrics:
    recall: float
    precision: float
    false_alarm_per_year: float
    mean_lead_days: float
    n_events: int
    n_alert_episodes: int


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _latest_run_dir(root: Path) -> Path:
    runs = sorted([p for p in root.iterdir() if p.is_dir() and p.name[:2] == "20"], key=lambda p: p.name)
    if not runs:
        raise FileNotFoundError(f"No run folders found under: {root}")
    return runs[-1]


def _safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        y = float(x)
    except (TypeError, ValueError):
        return default
    return y if np.isfinite(y) else default


def _to_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _zscore(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    mu = float(x.mean(skipna=True))
    sd = float(x.std(ddof=0, skipna=True))
    if (not np.isfinite(sd)) or sd <= 1e-12:
        return pd.Series(np.zeros(len(x), dtype=float), index=x.index)
    return ((x - mu) / sd).replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _apply_hysteresis(labels: list[str], min_persist: int) -> list[str]:
    if not labels:
        return []
    k = int(max(1, min_persist))
    current = labels[0]
    pending = ""
    cnt = 0
    out = [current]
    for raw in labels[1:]:
        if raw == current:
            pending = ""
            cnt = 0
            out.append(current)
            continue
        if raw == pending:
            cnt += 1
        else:
            pending = raw
            cnt = 1
        if cnt >= k:
            current = pending
            pending = ""
            cnt = 0
        out.append(current)
    return out


def _build_market_events(
    returns_wide_core: pd.DataFrame,
    dd_threshold: float = -0.08,
    cooldown_days: int = 20,
) -> tuple[pd.Series, list[pd.Timestamp]]:
    d = returns_wide_core.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date")
    cols = [c for c in d.columns if c != "date"]
    mkt_ret = d[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
    price = 100.0 * np.exp(mkt_ret.fillna(0.0).cumsum())
    dd20 = price / price.rolling(20, min_periods=20).max() - 1.0
    d["mkt_ret"] = mkt_ret
    d["dd20"] = dd20
    mask = d["dd20"] <= float(dd_threshold)
    idx = d.index[mask].to_list()
    dates = d.loc[mask, "date"].to_list()
    deduped: list[pd.Timestamp] = []
    last_i: int | None = None
    for dt, i in zip(dates, idx):
        if last_i is None or (int(i) - int(last_i)) > int(cooldown_days):
            deduped.append(pd.Timestamp(dt))
            last_i = int(i)
    return d.set_index("date")["mkt_ret"], deduped


def _eval_alerts(
    dates: pd.Series,
    alert: pd.Series,
    event_dates: list[pd.Timestamp],
    lookback_days: int,
    assoc_horizon_days: int = 20,
) -> AlertMetrics:
    dts = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    s_alert = pd.Series(alert.to_numpy(dtype=bool)).reset_index(drop=True)
    d2i = {d: i for i, d in enumerate(dts)}
    ev_idx = sorted([d2i[d] for d in pd.to_datetime(pd.Series(event_dates)).to_list() if d in d2i])

    detected = 0
    lead_days: list[int] = []
    for e in ev_idx:
        lo = max(0, e - int(lookback_days))
        hi = e - 1
        if hi >= lo:
            w = s_alert.iloc[lo : hi + 1]
            if bool(w.any()):
                detected += 1
                first_rel = int(np.argmax(w.to_numpy(dtype=bool)))
                first_idx = lo + first_rel
                lead_days.append(int(e - first_idx))

    starts = s_alert.to_numpy(dtype=bool) & (~s_alert.shift(1, fill_value=False).to_numpy(dtype=bool))
    ep_idx = np.where(starts)[0]
    good = 0
    for a in ep_idx:
        has_future_event = any((ev >= a + 1) and (ev <= a + int(assoc_horizon_days)) for ev in ev_idx)
        if has_future_event:
            good += 1
    n_ep = int(len(ep_idx))
    n_false = int(max(0, n_ep - good))
    years = max(1e-9, len(dts) / 252.0)
    return AlertMetrics(
        recall=float(detected / len(ev_idx)) if ev_idx else float("nan"),
        precision=float(good / n_ep) if n_ep > 0 else float("nan"),
        false_alarm_per_year=float(n_false / years),
        mean_lead_days=float(np.mean(lead_days)) if lead_days else float("nan"),
        n_events=int(len(ev_idx)),
        n_alert_episodes=n_ep,
    )


def _normal_two_sided_p(z: float) -> float:
    if not np.isfinite(z):
        return float("nan")
    return float(math.erfc(abs(float(z)) / math.sqrt(2.0)))


def _metric_key(row: pd.Series) -> tuple[float, float, float, float, float, float, int]:
    return (
        float(row["w_dp1"]),
        float(row["w_ddeff"]),
        float(row["w_overlap"]),
        float(row["q_hi"]),
        float(row["q_lo"]),
        float(row["q_transition"]),
        int(row["hysteresis_days"]),
    )


def _principal_eigvec_overlap(
    returns_wide_core: pd.DataFrame,
    window: int,
    min_cov: float,
    min_assets: int,
) -> pd.DataFrame:
    d = returns_wide_core.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date")
    dates = d["date"].to_list()
    ret = d.drop(columns=["date"])
    rows: list[dict[str, Any]] = []
    prev_vec: np.ndarray | None = None
    prev_cols: list[str] | None = None

    for i in range(window - 1, len(dates)):
        block = ret.iloc[i - window + 1 : i + 1]
        cov = block.notna().mean(axis=0)
        cols = cov[cov >= float(min_cov)].index.to_list()
        if len(cols) < int(min_assets):
            continue
        x = block[cols].dropna(how="any")
        if x.shape[0] < max(30, int(np.ceil(window * min_cov))):
            continue
        std = np.nanstd(x.to_numpy(dtype=float), axis=0)
        keep = std > 1e-12
        if int(np.sum(keep)) < int(min_assets):
            continue
        use_cols = np.asarray(cols)[keep].tolist()
        x2 = x[use_cols].to_numpy(dtype=float)
        corr = np.corrcoef(x2, rowvar=False)
        if not np.all(np.isfinite(corr)):
            continue
        w, v = np.linalg.eigh(corr)
        order = np.argsort(w)[::-1]
        v1 = np.real(v[:, order[0]]).astype(float)
        norm = float(np.linalg.norm(v1))
        if norm <= 1e-12:
            continue
        v1 = v1 / norm

        overlap = float("nan")
        if prev_vec is not None and prev_cols is not None:
            common = sorted(set(prev_cols).intersection(use_cols))
            if len(common) >= 3:
                idx_prev = [prev_cols.index(c) for c in common]
                idx_cur = [use_cols.index(c) for c in common]
                a = prev_vec[idx_prev]
                b = v1[idx_cur]
                na = float(np.linalg.norm(a))
                nb = float(np.linalg.norm(b))
                if na > 1e-12 and nb > 1e-12:
                    a = a / na
                    b = b / nb
                    overlap = float(abs(np.dot(a, b)))

        rows.append(
            {
                "date": pd.Timestamp(dates[i]).date().isoformat(),
                "window": int(window),
                "n_used": int(len(use_cols)),
                "eigvec_overlap_1d": overlap,
            }
        )
        prev_vec = v1
        prev_cols = use_cols
    return pd.DataFrame(rows)


def _classify_with_params(
    ts: pd.DataFrame,
    *,
    p_lo_q: float,
    p_hi_q: float,
    d_lo_q: float,
    d_hi_q: float,
    trans_q: float,
    hysteresis_days: int,
    w_dp1: float,
    w_ddeff: float,
    w_overlap: float,
) -> pd.DataFrame:
    d = ts.copy().sort_values("date")
    d["dp1_5"] = d["p1"].diff(5)
    d["ddeff_5"] = d["deff"].diff(5)
    d["ov_instability"] = 1.0 - pd.to_numeric(d.get("eigvec_overlap_1d"), errors="coerce")
    z_dp1 = _zscore(d["dp1_5"].abs())
    z_ddeff = _zscore(d["ddeff_5"].abs())
    z_ov = _zscore(d["ov_instability"])
    d["transition_score"] = float(w_dp1) * z_dp1 + float(w_ddeff) * z_ddeff + float(w_overlap) * z_ov

    p_lo = float(d["p1"].quantile(float(p_lo_q)))
    p_hi = float(d["p1"].quantile(float(p_hi_q)))
    de_lo = float(d["deff"].quantile(float(d_lo_q)))
    de_hi = float(d["deff"].quantile(float(d_hi_q)))
    tr_thr = float(d["transition_score"].quantile(float(trans_q)))

    raw: list[str] = []
    for _, r in d.iterrows():
        p1 = float(r["p1"])
        de = float(r["deff"])
        tr = float(r["transition_score"])
        if (p1 >= p_hi) and (de <= de_lo):
            raw.append("stress")
        elif (p1 <= p_lo) and (de >= de_hi):
            raw.append("dispersion")
        elif tr >= tr_thr:
            raw.append("transition")
        else:
            raw.append("stable")
    d["regime_raw"] = raw
    d["regime"] = _apply_hysteresis(raw, int(max(1, hysteresis_days)))
    d["alert"] = d["regime"].isin(["stress", "transition"])
    return d


def _score_config(m: AlertMetrics, m20: AlertMetrics) -> float:
    return float(
        0.45 * _safe_float(m.recall, 0.0)
        + 0.35 * _safe_float(m20.recall, 0.0)
        + 0.25 * _safe_float(m.precision, 0.0)
        - 0.03 * _safe_float(m.false_alarm_per_year, 0.0)
    )


def _read_asset_regime_file(path: Path, asof_date: pd.Timestamp) -> pd.DataFrame:
    d = pd.read_csv(path)
    if "regime" not in d.columns:
        return pd.DataFrame(columns=["date", "regime", "confidence"])
    conf = pd.to_numeric(d.get("confidence"), errors="coerce")
    n = int(len(d))
    if n <= 0:
        return pd.DataFrame(columns=["date", "regime", "confidence"])
    dates = pd.bdate_range(end=asof_date, periods=n)
    out = pd.DataFrame(
        {
            "date": dates,
            "regime": d["regime"].astype(str).to_numpy(),
            "confidence": conf.to_numpy(),
        }
    )
    return out


def _inspect_asset_regime_series(path: Path, asset: str) -> dict[str, Any]:
    d = pd.read_csv(path)
    n = int(len(d))
    out: dict[str, Any] = {
        "asset": asset,
        "n_rows": n,
        "has_t_column": int("t" in d.columns),
        "t_duplicate_count": 0,
        "t_gap_count": 0,
        "confidence_out_of_range_count": 0,
        "unknown_regime_count": 0,
        "series_short_lt_180": int(n < 180),
    }

    if "t" in d.columns:
        t = pd.to_numeric(d["t"], errors="coerce")
        out["t_duplicate_count"] = int(t.dropna().duplicated().sum())
        t_sorted = np.sort(t.dropna().astype(int).unique())
        if len(t_sorted) > 1:
            expected = int(t_sorted[-1] - t_sorted[0] + 1)
            out["t_gap_count"] = int(max(0, expected - len(t_sorted)))

    if "confidence" in d.columns:
        conf = pd.to_numeric(d["confidence"], errors="coerce")
        out["confidence_out_of_range_count"] = int(((conf < 0.0) | (conf > 1.0)).sum())

    if "regime" in d.columns:
        reg = d["regime"].astype(str).str.upper()
        valid = {"STABLE", "TRANSITION", "UNSTABLE", "NOISY"}
        out["unknown_regime_count"] = int((~reg.isin(valid)).sum())

    out["has_data_issue"] = int(
        (out["t_duplicate_count"] > 0)
        or (out["t_gap_count"] > 0)
        or (out["confidence_out_of_range_count"] > 0)
        or (out["unknown_regime_count"] > 0)
        or (out["series_short_lt_180"] > 0)
    )
    return out


def _switches_last(regimes: pd.Series, lookback: int) -> int:
    s = regimes.tail(int(max(1, lookback))).astype(str)
    if s.empty:
        return 0
    return int((s != s.shift(1)).sum() - 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Diagnostico completo: nucleo do motor + universo 470 ativos.")
    ap.add_argument("--lab-run-dir", type=str, default="")
    ap.add_argument("--universe-dir", type=str, default=str(UNIVERSE_ROOT))
    ap.add_argument("--policy-json", type=str, default="config/lab_corr_policy.json")
    ap.add_argument("--window", type=int, default=120)
    ap.add_argument("--event-dd-threshold", type=float, default=-0.08)
    ap.add_argument("--event-cooldown-days", type=int, default=20)
    ap.add_argument("--assoc-horizon-days", type=int, default=20)
    ap.add_argument("--out-root", type=str, default="results/motor_470_program")
    args = ap.parse_args()

    lab_run = ROOT / args.lab_run_dir if str(args.lab_run_dir).strip() else _latest_run_dir(LAB_ROOT)
    uni_dir = ROOT / str(args.universe_dir)
    outdir = ROOT / str(args.out_root) / _ts_id()
    outdir.mkdir(parents=True, exist_ok=True)

    # -------------------------------
    # MOTOR CORE
    # -------------------------------
    ts = pd.read_csv(lab_run / f"macro_timeseries_T{int(args.window)}.csv")
    ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
    ts = ts.dropna(subset=["date"]).sort_values("date")
    ts = ts[~ts["insufficient_universe"]].copy()

    returns_wide = pd.read_csv(lab_run / "returns_wide_core.csv")
    mkt_ret, event_dates = _build_market_events(
        returns_wide_core=returns_wide,
        dd_threshold=float(args.event_dd_threshold),
        cooldown_days=int(args.event_cooldown_days),
    )
    ts = ts.merge(mkt_ret.rename("mkt_ret").reset_index().rename(columns={"index": "date"}), on="date", how="left")
    ts["date_str"] = ts["date"].dt.date.astype(str)

    # rule-by-rule review from current classifier
    d_rule = ts.copy()
    d_rule["dp1_5"] = d_rule["p1"].diff(5)
    d_rule["ddeff_5"] = d_rule["deff"].diff(5)
    p1_lo = float(d_rule["p1"].quantile(0.20))
    p1_hi = float(d_rule["p1"].quantile(0.80))
    deff_lo = float(d_rule["deff"].quantile(0.20))
    deff_hi = float(d_rule["deff"].quantile(0.80))
    dp1_thr = float(d_rule["dp1_5"].abs().quantile(0.80))
    ddeff_thr = float(d_rule["ddeff_5"].abs().quantile(0.80))
    stress_mask = (d_rule["p1"] >= p1_hi) & (d_rule["deff"] <= deff_lo)
    disp_mask = (d_rule["p1"] <= p1_lo) & (d_rule["deff"] >= deff_hi)
    trans_mask = (d_rule["dp1_5"].abs() >= dp1_thr) | (d_rule["ddeff_5"].abs() >= ddeff_thr)
    fallback_stable = ~(stress_mask | disp_mask | trans_mask)

    rule_review = {
        "window": int(args.window),
        "n_rows": int(len(d_rule)),
        "thresholds": {
            "p1_q20": p1_lo,
            "p1_q80": p1_hi,
            "deff_q20": deff_lo,
            "deff_q80": deff_hi,
            "abs_dp1_5_q80": dp1_thr,
            "abs_ddeff_5_q80": ddeff_thr,
        },
        "rule_counts_raw": {
            "stress": int(stress_mask.sum()),
            "dispersion": int(disp_mask.sum()),
            "transition": int(trans_mask.sum()),
            "stable_fallback": int(fallback_stable.sum()),
        },
    }
    _to_json(outdir / "motor_rule_review.json", rule_review)

    # eigenvector overlap (60/120/252)
    overlaps = []
    for w in [60, 120, 252]:
        ov = _principal_eigvec_overlap(returns_wide_core=returns_wide, window=w, min_cov=0.98, min_assets=25)
        if not ov.empty:
            overlaps.append(ov)
    ov_all = pd.concat(overlaps, ignore_index=True) if overlaps else pd.DataFrame()
    if not ov_all.empty:
        ov_all.to_csv(outdir / "motor_eigvec_overlap.csv", index=False)
        ov_sum = (
            ov_all.groupby("window", as_index=False)["eigvec_overlap_1d"]
            .agg(["mean", "median", "min", "max"])
            .reset_index()
            .rename(columns={"index": "window"})
        )
        ov_sum.to_csv(outdir / "motor_eigvec_overlap_summary.csv", index=False)
    else:
        ov_sum = pd.DataFrame()

    # significance by window from bootstrap deltas
    sig_rows: list[dict[str, Any]] = []
    for w in [60, 120, 252]:
        p = lab_run / f"macro_timeseries_T{w}.csv"
        if not p.exists():
            continue
        x = pd.read_csv(p)
        x = x[~x["insufficient_universe"]].copy()
        if x.empty:
            continue
        x["delta_p1"] = pd.to_numeric(x["p1"], errors="coerce") - pd.to_numeric(x["p1_bootstrap"], errors="coerce")
        x["delta_deff"] = pd.to_numeric(x["deff_bootstrap"], errors="coerce") - pd.to_numeric(x["deff"], errors="coerce")
        for col in ["delta_p1", "delta_deff"]:
            s = pd.to_numeric(x[col], errors="coerce")
            mu = float(s.mean(skipna=True))
            sd = float(s.std(ddof=0, skipna=True))
            n_eff = int(s.notna().sum())
            se = (sd / math.sqrt(n_eff)) if (n_eff > 0 and np.isfinite(sd) and sd > 1e-12) else float("nan")
            mean_z = (mu / se) if (np.isfinite(se) and se > 1e-12) else float("nan")
            mean_p = _normal_two_sided_p(mean_z)
            z = (s / sd) if (np.isfinite(sd) and sd > 1e-12) else pd.Series(np.nan, index=s.index)
            pvals = z.apply(_normal_two_sided_p)
            last_valid = s.dropna()
            latest_delta = _safe_float(last_valid.iloc[-1] if len(last_valid) else np.nan)
            latest_z = (latest_delta / sd) if (np.isfinite(sd) and sd > 1e-12) else float("nan")
            sig_share = float((pvals[s.notna()] < 0.05).mean()) if n_eff > 0 else float("nan")
            sig_rows.append(
                {
                    "window": int(w),
                    "metric": str(col),
                    "n": n_eff,
                    "mean_delta": mu,
                    "std_delta": sd,
                    "significant_share_p_lt_0_05": sig_share,
                    "mean_z_vs_zero": _safe_float(mean_z),
                    "mean_pvalue_vs_zero": _safe_float(mean_p),
                    "latest_delta": latest_delta,
                    "latest_z": _safe_float(latest_z),
                    "latest_pvalue": _safe_float(_normal_two_sided_p(latest_z)),
                }
            )
    sig_df = pd.DataFrame(sig_rows)
    if not sig_df.empty:
        sig_df.to_csv(outdir / "motor_significance_by_window.csv", index=False)

    # tuning: thresholds/weights/hysteresis with event metrics
    ov120 = ov_all[ov_all["window"] == 120][["date", "eigvec_overlap_1d"]].copy() if not ov_all.empty else pd.DataFrame()
    if not ov120.empty:
        ov120["date"] = pd.to_datetime(ov120["date"], errors="coerce")
    tune_base = ts.copy()
    if not ov120.empty:
        tune_base = tune_base.merge(ov120, on="date", how="left")
    else:
        tune_base["eigvec_overlap_1d"] = np.nan
    tune_base["eigvec_overlap_1d"] = tune_base["eigvec_overlap_1d"].fillna(tune_base["eigvec_overlap_1d"].median())

    grid_rows: list[dict[str, Any]] = []
    weight_grid = [(0.50, 0.50, 0.00), (0.40, 0.40, 0.20), (0.35, 0.35, 0.30), (0.30, 0.30, 0.40)]
    q_hi_grid = [0.75, 0.80, 0.85]
    trans_q_grid = [0.70, 0.75, 0.80, 0.85]
    hys_grid = [2, 3, 5]

    for w_dp1, w_ddeff, w_ov in weight_grid:
        for q_hi in q_hi_grid:
            q_lo = 1.0 - q_hi
            for q_tr in trans_q_grid:
                for hys in hys_grid:
                    d_cfg = _classify_with_params(
                        tune_base,
                        p_lo_q=q_lo,
                        p_hi_q=q_hi,
                        d_lo_q=q_lo,
                        d_hi_q=q_hi,
                        trans_q=q_tr,
                        hysteresis_days=hys,
                        w_dp1=w_dp1,
                        w_ddeff=w_ddeff,
                        w_overlap=w_ov,
                    )
                    ev10 = _eval_alerts(
                        dates=d_cfg["date"],
                        alert=d_cfg["alert"],
                        event_dates=event_dates,
                        lookback_days=10,
                        assoc_horizon_days=int(args.assoc_horizon_days),
                    )
                    ev20 = _eval_alerts(
                        dates=d_cfg["date"],
                        alert=d_cfg["alert"],
                        event_dates=event_dates,
                        lookback_days=20,
                        assoc_horizon_days=int(args.assoc_horizon_days),
                    )
                    grid_rows.append(
                        {
                            "w_dp1": w_dp1,
                            "w_ddeff": w_ddeff,
                            "w_overlap": w_ov,
                            "q_hi": q_hi,
                            "q_lo": q_lo,
                            "q_transition": q_tr,
                            "hysteresis_days": hys,
                            "recall_l10": ev10.recall,
                            "recall_l20": ev20.recall,
                            "precision_l10": ev10.precision,
                            "false_alarm_l10": ev10.false_alarm_per_year,
                            "lead_l10": ev10.mean_lead_days,
                            "n_events": ev10.n_events,
                            "score": _score_config(ev10, ev20),
                        }
                    )
    grid_df = pd.DataFrame(grid_rows).sort_values("score", ascending=False).reset_index(drop=True)
    grid_df.to_csv(outdir / "motor_grid_search.csv", index=False)

    # current baseline line (existing policy-like behavior)
    d_base = _classify_with_params(
        tune_base,
        p_lo_q=0.20,
        p_hi_q=0.80,
        d_lo_q=0.20,
        d_hi_q=0.80,
        trans_q=0.80,
        hysteresis_days=3,
        w_dp1=0.5,
        w_ddeff=0.5,
        w_overlap=0.0,
    )
    b10 = _eval_alerts(d_base["date"], d_base["alert"], event_dates, lookback_days=10, assoc_horizon_days=int(args.assoc_horizon_days))
    b20 = _eval_alerts(d_base["date"], d_base["alert"], event_dates, lookback_days=20, assoc_horizon_days=int(args.assoc_horizon_days))

    # conservative/aggressive picks
    cons_pool = grid_df[(grid_df["recall_l10"] >= b10.recall) & (grid_df["false_alarm_l10"] <= b10.false_alarm_per_year)]
    if cons_pool.empty:
        cons_pool = grid_df[
            (grid_df["recall_l10"] >= max(0.0, b10.recall - 0.05))
            & (grid_df["false_alarm_l10"] <= (b10.false_alarm_per_year * 1.15))
        ]
    if cons_pool.empty:
        cons_pool = grid_df.sort_values(["false_alarm_l10", "precision_l10"], ascending=[True, False]).head(1)
    else:
        cons_pool = cons_pool.sort_values(["false_alarm_l10", "precision_l10", "score"], ascending=[True, False, False]).head(1)

    aggr_pool = grid_df.sort_values(
        ["recall_l10", "recall_l20", "precision_l10", "false_alarm_l10", "score"],
        ascending=[False, False, False, True, False],
    )
    if aggr_pool.empty:
        aggr_pool = grid_df.head(1)
    cons_key = _metric_key(cons_pool.iloc[0])
    aggr_row = None
    for _, row in aggr_pool.iterrows():
        if _metric_key(row) != cons_key:
            aggr_row = row
            break
    if aggr_row is None:
        aggr_row = aggr_pool.iloc[0]
    aggr_pool = pd.DataFrame([aggr_row])

    mode_rows = [
        {
            "mode": "baseline_current",
            "recall_l10": b10.recall,
            "recall_l20": b20.recall,
            "precision_l10": b10.precision,
            "false_alarm_l10": b10.false_alarm_per_year,
            "lead_l10": b10.mean_lead_days,
            "score": _score_config(b10, b20),
        },
        {"mode": "conservative", **cons_pool.iloc[0].to_dict()},
        {"mode": "aggressive", **aggr_pool.iloc[0].to_dict()},
    ]
    mode_df = pd.DataFrame(mode_rows)
    mode_df.to_csv(outdir / "motor_mode_comparison.csv", index=False)

    cons_prod_score = (
        0.45 * float(cons_pool.iloc[0]["recall_l10"])
        + 0.25 * float(cons_pool.iloc[0]["precision_l10"])
        + 0.30 * float(cons_pool.iloc[0]["recall_l20"])
        - 0.06 * float(cons_pool.iloc[0]["false_alarm_l10"])
    )
    aggr_prod_score = (
        0.45 * float(aggr_pool.iloc[0]["recall_l10"])
        + 0.25 * float(aggr_pool.iloc[0]["precision_l10"])
        + 0.30 * float(aggr_pool.iloc[0]["recall_l20"])
        - 0.06 * float(aggr_pool.iloc[0]["false_alarm_l10"])
    )
    best_mode = "conservative" if cons_prod_score >= aggr_prod_score else "aggressive"
    best_row = cons_pool.iloc[0] if best_mode == "conservative" else aggr_pool.iloc[0]
    final_policy = {
        "status": "ok",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "recommended_mode": best_mode,
        "recommended_params": {
            "w_dp1": float(best_row["w_dp1"]),
            "w_ddeff": float(best_row["w_ddeff"]),
            "w_overlap": float(best_row["w_overlap"]),
            "q_hi": float(best_row["q_hi"]),
            "q_lo": float(best_row["q_lo"]),
            "q_transition": float(best_row["q_transition"]),
            "hysteresis_days": int(best_row["hysteresis_days"]),
        },
        "expected_metrics_l10": {
            "recall": float(best_row["recall_l10"]),
            "precision": float(best_row["precision_l10"]),
            "false_alarm_per_year": float(best_row["false_alarm_l10"]),
            "mean_lead_days": float(best_row["lead_l10"]),
        },
        "baseline_metrics_l10": {
            "recall": b10.recall,
            "precision": b10.precision,
            "false_alarm_per_year": b10.false_alarm_per_year,
            "mean_lead_days": b10.mean_lead_days,
        },
        "mode_scores": {
            "conservative_production_score": float(cons_prod_score),
            "aggressive_production_score": float(aggr_prod_score),
        },
    }
    _to_json(outdir / "motor_policy_final.json", final_policy)

    # -------------------------------
    # UNIVERSE 470
    # -------------------------------
    diag = pd.read_csv(uni_dir / "diagnostics_assets_daily.csv")
    diag["asof"] = pd.to_datetime(diag["asof"], errors="coerce")
    diag = diag.sort_values(["asset", "asof"]).drop_duplicates(subset=["asset"], keep="last").reset_index(drop=True)
    target = diag[diag["in_target_470"].astype(bool)].copy()
    expected_assets = sorted(target["asset"].astype(str).tolist())
    asof = pd.Timestamp(target["asof"].max()) if not target.empty else pd.Timestamp.today()

    assets_dir = uni_dir / "assets"
    missing_regime_files = []
    enriched_rows: list[dict[str, Any]] = []
    series_consistency_rows: list[dict[str, Any]] = []

    for _, r in target.iterrows():
        a = str(r["asset"])
        fp = assets_dir / f"{a}_daily_regimes.csv"
        if not fp.exists():
            missing_regime_files.append(a)
            continue
        series_consistency_rows.append(_inspect_asset_regime_series(fp, a))
        rg = _read_asset_regime_file(fp, asof_date=asof)
        if rg.empty:
            missing_regime_files.append(a)
            continue
        reg_s = rg["regime"].astype(str)
        sw30 = _switches_last(reg_s, 30)
        sw90 = _switches_last(reg_s, 90)
        sw180 = _switches_last(reg_s, 180)
        unstable_share_90 = float(reg_s.tail(90).isin(["UNSTABLE", "NOISY"]).mean())
        transition_share_90 = float((reg_s.tail(90) == "TRANSITION").mean())

        conf = _safe_float(r.get("confidence"), 0.0)
        qual = _safe_float(r.get("quality"), 0.0)
        stay = _safe_float(r.get("stay_prob"), 0.0)
        esc = _safe_float(r.get("escape_prob"), 0.0)
        risk = _safe_float(r.get("risk_score"), 0.0)
        sensitivity = (
            0.45 * risk
            + 0.20 * esc
            + 0.20 * (1.0 - conf)
            + 0.10 * min(1.0, sw90 / 12.0)
            + 0.05 * unstable_share_90
        )
        stability = (
            0.40 * conf
            + 0.30 * stay
            + 0.20 * (1.0 - risk)
            + 0.10 * (1.0 - min(1.0, sw90 / 12.0))
        )

        enriched_rows.append(
            {
                "asset": a,
                "sector": str(r.get("sector", "")),
                "asof": pd.Timestamp(r["asof"]).date().isoformat() if pd.notna(r["asof"]) else "",
                "regime": str(r.get("regime", "")),
                "confidence": conf,
                "quality": qual,
                "stay_prob": stay,
                "escape_prob": esc,
                "risk_score": risk,
                "switches_30d": int(sw30),
                "switches_90d": int(sw90),
                "switches_180d": int(sw180),
                "transition_share_90d": transition_share_90,
                "unstable_share_90d": unstable_share_90,
                "sensitivity_score": float(np.clip(sensitivity, 0.0, 1.0)),
                "stability_score": float(np.clip(stability, 0.0, 1.0)),
            }
        )

    enriched = pd.DataFrame(enriched_rows)
    enriched.to_csv(outdir / "universe_asset_diagnostics_enriched.csv", index=False)

    top_sensitive = enriched.sort_values(["sensitivity_score", "risk_score"], ascending=[False, False]).head(50)
    top_stable = enriched.sort_values(["stability_score", "confidence"], ascending=[False, False]).head(50)
    top_sensitive.to_csv(outdir / "universe_top_sensitive.csv", index=False)
    top_stable.to_csv(outdir / "universe_top_stable.csv", index=False)

    series_consistency = pd.DataFrame(series_consistency_rows)
    if not series_consistency.empty:
        series_consistency.to_csv(outdir / "universe_series_consistency.csv", index=False)

    weak = enriched[
        (enriched["confidence"] < 0.40)
        | (enriched["quality"] < 0.40)
        | ((enriched["regime"].isin(["UNSTABLE", "NOISY"])) & (enriched["confidence"] < 0.55))
    ].copy()
    weak = weak.sort_values(["confidence", "risk_score"], ascending=[True, False])
    weak.to_csv(outdir / "universe_weak_signal_assets.csv", index=False)

    review_queue = weak[["asset", "sector", "asof", "regime", "confidence", "quality", "risk_score"]].copy()
    review_queue["review_reason"] = "weak_signal"
    if not series_consistency.empty:
        data_issues = series_consistency[series_consistency["has_data_issue"] > 0]["asset"].astype(str)
        if not data_issues.empty:
            add = enriched[enriched["asset"].isin(data_issues)][["asset", "sector", "asof", "regime", "confidence", "quality", "risk_score"]].copy()
            add["review_reason"] = "data_issue"
            review_queue = pd.concat([review_queue, add], ignore_index=True)
    review_queue = review_queue.drop_duplicates(subset=["asset", "review_reason"]).sort_values(
        ["review_reason", "confidence", "risk_score"], ascending=[True, True, False]
    )
    review_queue.to_csv(outdir / "universe_review_queue.csv", index=False)

    cov = {
        "expected_assets_target_470": int(len(expected_assets)),
        "diagnostics_assets_rows": int(len(target)),
        "diagnostics_unique_assets": int(target["asset"].nunique()),
        "assets_with_regime_file": int(len(enriched)),
        "assets_missing_regime_file": int(len(missing_regime_files)),
        "missing_regime_assets_sample": missing_regime_files[:25],
        "consistency_checks": {
            "confidence_in_0_1": int(((target["confidence"] >= 0) & (target["confidence"] <= 1)).sum()),
            "quality_in_0_1": int(((target["quality"] >= 0) & (target["quality"] <= 1)).sum()),
            "stay_plus_escape_close_to_1": int((np.abs(target["stay_prob"] + target["escape_prob"] - 1.0) <= 0.02).sum()),
            "valid_asof": int(target["asof"].notna().sum()),
        },
    }
    if not series_consistency.empty:
        cov["series_consistency"] = {
            "with_any_data_issue": int((series_consistency["has_data_issue"] > 0).sum()),
            "with_t_duplicates": int((series_consistency["t_duplicate_count"] > 0).sum()),
            "with_t_gaps": int((series_consistency["t_gap_count"] > 0).sum()),
            "with_confidence_out_of_range": int((series_consistency["confidence_out_of_range_count"] > 0).sum()),
            "with_unknown_regime": int((series_consistency["unknown_regime_count"] > 0).sum()),
            "short_series_lt_180": int((series_consistency["series_short_lt_180"] > 0).sum()),
        }
    _to_json(outdir / "universe_coverage_checks.json", cov)

    risk_lines = []
    risk_lines.append(f"assets_target_470={cov['expected_assets_target_470']}")
    risk_lines.append(f"assets_with_full_diagnostics={cov['assets_with_regime_file']}")
    risk_lines.append(f"assets_weak_signal={int(len(weak))}")
    risk_lines.append(f"mean_confidence={float(enriched['confidence'].mean()):.4f}")
    risk_lines.append(f"mean_risk_score={float(enriched['risk_score'].mean()):.4f}")
    risk_lines.append("")
    risk_lines.append("top_20_risk_assets:")
    for _, r in enriched.sort_values(["risk_score", "sensitivity_score"], ascending=[False, False]).head(20).iterrows():
        risk_lines.append(
            f"- {r['asset']} | setor={r['sector']} | regime={r['regime']} | "
            f"risk={float(r['risk_score']):.4f} | conf={float(r['confidence']):.4f} | sw90={int(r['switches_90d'])}"
        )
    (outdir / "universe_top_risks.txt").write_text("\n".join(risk_lines) + "\n", encoding="utf-8")

    # consolidated overview
    overview_lines = []
    overview_lines.append("# Motor + 470 ativos | diagnostico consolidado")
    overview_lines.append("")
    overview_lines.append("## Motor (nucleo)")
    overview_lines.append(f"- run_lab: `{lab_run}`")
    overview_lines.append(f"- eventos_drawdown20: {len(event_dates)}")
    overview_lines.append(f"- baseline_l10: recall={b10.recall:.4f}, precision={b10.precision:.4f}, false_alarm_ano={b10.false_alarm_per_year:.4f}, lead={b10.mean_lead_days:.2f}")
    overview_lines.append(
        f"- modo_recomendado: {best_mode} | recall_l10={float(best_row['recall_l10']):.4f} | "
        f"precision_l10={float(best_row['precision_l10']):.4f} | false_alarm_ano={float(best_row['false_alarm_l10']):.4f}"
    )
    if not sig_df.empty:
        s120 = sig_df[sig_df["window"] == int(args.window)]
        if not s120.empty:
            row = s120.iloc[0]
            overview_lines.append(
                f"- significancia_T{int(args.window)} ({row['metric']}): share_p<0.05={float(row['significant_share_p_lt_0_05']):.4f}"
            )
    overview_lines.append("")
    overview_lines.append("## Universo 470 ativos")
    overview_lines.append(f"- run_universe: `{uni_dir}`")
    overview_lines.append(f"- cobertura_alvo: {cov['expected_assets_target_470']}")
    overview_lines.append(f"- com_regime: {cov['assets_with_regime_file']} | faltando={cov['assets_missing_regime_file']}")
    overview_lines.append(f"- weak_signal_assets: {int(len(weak))}")
    if "series_consistency" in cov:
        sc = cov["series_consistency"]
        overview_lines.append(
            f"- series_data_issue_assets: {int(sc['with_any_data_issue'])} "
            f"(gaps={int(sc['with_t_gaps'])}, dup={int(sc['with_t_duplicates'])}, short={int(sc['short_series_lt_180'])})"
        )
    overview_lines.append(
        f"- medias: confidence={float(enriched['confidence'].mean()):.4f}, "
        f"risk={float(enriched['risk_score'].mean()):.4f}, switches90={float(enriched['switches_90d'].mean()):.2f}"
    )
    overview_lines.append("")
    overview_lines.append("## Proximos passos sugeridos")
    overview_lines.append("- aplicar policy final recomendada em ambiente de teste (sem produção direta).")
    overview_lines.append("- revisar manualmente os 20 ativos de maior risco e os assets de weak_signal.")
    overview_lines.append("- repetir este diagnostico diariamente e comparar tendencia de recall/false_alarm.")
    (outdir / "report_overview.md").write_text("\n".join(overview_lines) + "\n", encoding="utf-8")

    status = {
        "status": "ok",
        "outdir": str(outdir),
        "lab_run": str(lab_run),
        "universe_dir": str(uni_dir),
        "motor": {
            "n_events": int(len(event_dates)),
            "recommended_mode": best_mode,
            "baseline_recall_l10": b10.recall,
            "recommended_recall_l10": float(best_row["recall_l10"]),
            "baseline_false_alarm_l10": b10.false_alarm_per_year,
            "recommended_false_alarm_l10": float(best_row["false_alarm_l10"]),
        },
        "universe470": {
            "assets_target": int(cov["expected_assets_target_470"]),
            "assets_with_regime_file": int(cov["assets_with_regime_file"]),
            "assets_missing_regime_file": int(cov["assets_missing_regime_file"]),
            "weak_signal_assets": int(len(weak)),
        },
    }
    _to_json(outdir / "status.json", status)
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
