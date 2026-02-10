#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.graph.core import run_graph_engine  # noqa: E402
from engine.graph.embedding import estimate_embedding_params  # noqa: E402


def load_series(path: Path, timeframe: str) -> pd.Series:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    if "price" in df.columns:
        col = "price"
    elif "close" in df.columns:
        col = "close"
    else:
        col = df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, col]).sort_values(date_col)
    series = df.set_index(date_col)[col].astype(float)
    if timeframe == "weekly":
        series = series.resample("W").last().dropna()
    return series


def load_official(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])


def engine_labels(series: pd.Series, m: int, tau: int, n_micro: int, n_regimes: int, k_nn: int, theiler: int, alpha: float, method: str) -> Tuple[pd.Series, pd.Series, pd.Series]:
    result = run_graph_engine(
        series.values.astype(float),
        m=m,
        tau=tau,
        n_micro=n_micro,
        n_regimes=n_regimes,
        k_nn=k_nn,
        theiler=theiler,
        alpha=alpha,
        seed=7,
        method=method,
    )
    # Align labels with series index (embedding shortens)
    offset = (m - 1) * tau
    idx = series.index[offset:]
    labels = pd.Series(result.state_labels, index=idx)
    confidence = pd.Series(result.confidence, index=idx)
    quality_score = result.quality.get("score", np.nan)
    quality = pd.Series([quality_score] * len(idx), index=idx)
    return labels, confidence, quality


def agreement(a: np.ndarray, b: np.ndarray) -> Dict[str, float]:
    if len(a) == 0:
        return {"agree": 0.0, "n": 0}
    agree = float(np.mean(a == b))
    return {"agree": agree, "n": int(len(a))}


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    if len(y_true) == 0:
        return {
            "n": 0,
            "accuracy": 0.0,
            "balanced_accuracy": 0.0,
            "f1": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "mcc": 0.0,
        }
    accuracy = float(np.mean(y_true == y_pred))
    return {
        "n": int(len(y_true)),
        "accuracy": accuracy,
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
    }


def score_metrics(y_true: np.ndarray, y_score: np.ndarray) -> Dict[str, float]:
    if len(y_true) == 0:
        return {"n": 0, "roc_auc": 0.0, "pr_auc": 0.0}
    try:
        roc_auc = float(roc_auc_score(y_true, y_score))
    except ValueError:
        roc_auc = 0.0
    try:
        pr_auc = float(average_precision_score(y_true, y_score))
    except ValueError:
        pr_auc = 0.0
    return {"n": int(len(y_true)), "roc_auc": roc_auc, "pr_auc": pr_auc}


def change_points(series: pd.Series) -> pd.DatetimeIndex:
    if series.empty:
        return pd.DatetimeIndex([])
    return series.index[series != series.shift(1)]


def smooth_binary(series: pd.Series, min_run: int) -> pd.Series:
    if min_run <= 1:
        return series
    values = series.values.copy()
    n = len(values)
    i = 0
    while i < n:
        j = i + 1
        while j < n and values[j] == values[i]:
            j += 1
        run_len = j - i
        if run_len < min_run:
            # flip short run to neighbor if possible
            left = values[i - 1] if i > 0 else None
            right = values[j] if j < n else None
            if left is not None:
                values[i:j] = left
            elif right is not None:
                values[i:j] = right
        i = j
    return pd.Series(values, index=series.index)


def apply_cooldown(series: pd.Series, cooldown: int) -> pd.Series:
    if cooldown <= 0:
        return series
    values = series.values.copy()
    last_on = -cooldown - 1
    for i, val in enumerate(values):
        if val == 1:
            if i - last_on <= cooldown:
                values[i] = 0
            else:
                last_on = i
    return pd.Series(values, index=series.index)

def entropy_from_labels(labels: List[str]) -> Dict[str, float]:
    if not labels:
        return {"shannon": 0.0}
    counts = {}
    total = 0
    for lbl in labels:
        if lbl is None:
            continue
        counts[lbl] = counts.get(lbl, 0) + 1
        total += 1
    if total == 0:
        return {"shannon": 0.0}
    probs = np.array([c / total for c in counts.values()], dtype=float)
    shannon = float(-np.sum(probs * np.log(probs + 1e-12)))
    return {"shannon": shannon}


def build_mode_unstable(
    labels: pd.Series,
    confidence: pd.Series,
    quality: float,
    window: int,
    conf_floor: float,
    quality_floor: float,
) -> pd.Series:
    values = labels.values
    n = len(values)
    flags = np.zeros(n, dtype=int)
    # change rate (rolling)
    changes = (labels != labels.shift(1)).astype(int).values
    roll = pd.Series(changes, index=labels.index).rolling(window, min_periods=1).mean().values
    for i in range(n):
        start = max(0, i - window + 1)
        recent_labels = values[start : i + 1].tolist()
        prior_start = max(0, i - 2 * window + 1)
        prior_end = max(0, i - window)
        prior_labels = values[prior_start:prior_end].tolist()
        recent_entropy = entropy_from_labels(recent_labels).get("shannon", 0.0)
        prior_entropy = entropy_from_labels(prior_labels).get("shannon", 0.0)
        delta = float(recent_entropy - prior_entropy) if prior_labels else 0.0
        recent_change_rate = float(roll[i])
        change_rate = float(np.mean(changes[: i + 1])) if i > 0 else float(changes[i])

        local_flags = 0
    if recent_change_rate > 0.35 or change_rate > 0.30:
        local_flags += 1
    if abs(delta) > 0.10 and recent_change_rate > 0.04:
        local_flags += 1
        if confidence.iloc[i] < conf_floor:
            local_flags += 1
        if quality < quality_floor:
            local_flags += 1
        flags[i] = local_flags

    # MODE_UNSTABLE mirrors engine: >=2 flags AND low quality
    # Proxy for MODE_UNSTABLE: allow either low quality + >=2 flags,
    # or stronger multi-flag condition, or sharp recent flipping with low confidence.
    recent_change = pd.Series(flags, index=labels.index).rolling(window, min_periods=1).mean().values
    mode_unstable = (
        ((flags >= 2) & (quality < quality_floor))
        | (flags >= 3)
        | ((recent_change > 0.4) & (confidence.values < conf_floor))
    ).astype(int)
    return pd.Series(mode_unstable, index=labels.index)


def build_consensus_signal(
    labels: pd.Series,
    confidence: pd.Series,
    quality: float,
    window: int,
    conf_floor: float,
    quality_floor: float,
    change_rate_threshold: float,
    entropy_delta_threshold: float,
    min_votes: int,
) -> pd.Series:
    values = labels.values
    n = len(values)
    votes = np.zeros(n, dtype=int)
    changes = (labels != labels.shift(1)).astype(int).values
    change_rate = pd.Series(changes, index=labels.index).rolling(window, min_periods=1).mean().values
    for i in range(n):
        start = max(0, i - window + 1)
        recent_labels = values[start : i + 1].tolist()
        prior_start = max(0, i - 2 * window + 1)
        prior_end = max(0, i - window)
        prior_labels = values[prior_start:prior_end].tolist()
        recent_entropy = entropy_from_labels(recent_labels).get("shannon", 0.0)
        prior_entropy = entropy_from_labels(prior_labels).get("shannon", 0.0)
        delta_entropy = float(recent_entropy - prior_entropy) if prior_labels else 0.0

        local_votes = 0
        if values[i] == "UNSTABLE":
            local_votes += 1
        if values[i] == "TRANSITION":
            local_votes += 1
        if change_rate[i] >= change_rate_threshold:
            local_votes += 1
        if delta_entropy >= entropy_delta_threshold:
            local_votes += 1
        if confidence.iloc[i] <= conf_floor:
            local_votes += 1
        if quality < quality_floor:
            local_votes += 1
        votes[i] = local_votes

    consensus = (votes >= min_votes).astype(int)
    return pd.Series(consensus, index=labels.index)


def turn_hit_rate(proxy_changes: pd.DatetimeIndex, engine_changes: pd.DatetimeIndex, window_days: int) -> Dict[str, float]:
    if len(proxy_changes) == 0:
        return {"hits": 0, "total": 0, "hit_rate": 0.0, "false_alarms": 0, "false_alarm_rate": 0.0}
    hits = 0
    for dt in proxy_changes:
        start = dt - pd.Timedelta(window_days, unit="D")
        end = dt + pd.Timedelta(window_days, unit="D")
        if ((engine_changes >= start) & (engine_changes <= end)).any():
            hits += 1
    total = len(proxy_changes)
    hit_rate = hits / total if total else 0.0
    false_alarms = 0
    for dt in engine_changes:
        start = dt - pd.Timedelta(window_days, unit="D")
        end = dt + pd.Timedelta(window_days, unit="D")
        if not ((proxy_changes >= start) & (proxy_changes <= end)).any():
            false_alarms += 1
    false_alarm_rate = false_alarms / max(len(engine_changes), 1)
    return {
        "hits": int(hits),
        "total": int(total),
        "hit_rate": float(hit_rate),
        "false_alarms": int(false_alarms),
        "false_alarm_rate": float(false_alarm_rate),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare graph regimes to official proxies.")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers")
    parser.add_argument("--timeframes", default="daily")
    parser.add_argument("--data-dir", default="data/raw/finance/yfinance_daily")
    parser.add_argument("--official", default="results/official_regimes/official_regimes.csv")
    parser.add_argument("--proxy-mode", default="official", choices=["official", "market"])
    parser.add_argument("--vix-asset", default="^VIX")
    parser.add_argument("--vix-quantile", type=float, default=0.9)
    parser.add_argument("--vol-window", type=int, default=20)
    parser.add_argument("--vol-quantile", type=float, default=0.9)
    parser.add_argument("--drawdown-window", type=int, default=60)
    parser.add_argument("--drawdown-threshold", type=float, default=-0.1)
    parser.add_argument("--outdir", default="results/official_regimes/compare")
    parser.add_argument("--method", default="spectral", choices=["spectral", "pcca"])
    parser.add_argument("--m", type=int, default=3)
    parser.add_argument("--tau", type=int, default=1)
    parser.add_argument("--auto-embed", action="store_true")
    parser.add_argument("--tau-method", default="ami", choices=["ami", "acf"])
    parser.add_argument("--m-method", default="cao", choices=["cao", "fnn"])
    parser.add_argument("--n-micro", type=int, default=200)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=10)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--max-lag", type=int, default=8, help="Max lag (in periods) to test")
    parser.add_argument("--turn-window", type=int, default=5, help="Window in days for turning point matching")
    parser.add_argument(
        "--risk-mode",
        default="unstable_transition",
        choices=["unstable_transition", "unstable_only", "score", "mode_unstable", "consensus", "rare_events", "balanced_events"],
    )
    parser.add_argument("--min-confidence", type=float, default=0.0)
    parser.add_argument("--min-quality", type=float, default=0.0)
    parser.add_argument("--mode-unstable-conf", type=float, default=0.3)
    parser.add_argument("--mode-unstable-quality", type=float, default=0.6)
    parser.add_argument("--consensus-min-votes", type=int, default=3)
    parser.add_argument("--consensus-change-rate", type=float, default=0.18)
    parser.add_argument("--consensus-entropy-delta", type=float, default=0.08)
    parser.add_argument("--rare-min-run", type=int, default=7)
    parser.add_argument("--rare-change-rate", type=float, default=0.25)
    parser.add_argument("--rare-confidence", type=float, default=0.35)
    parser.add_argument("--rare-quality", type=float, default=0.55)
    parser.add_argument("--balanced-min-votes", type=int, default=2)
    parser.add_argument("--balanced-change-rate", type=float, default=0.14)
    parser.add_argument("--balanced-entropy-delta", type=float, default=0.06)
    parser.add_argument("--balanced-confidence", type=float, default=0.45)
    parser.add_argument("--balanced-quality", type=float, default=0.55)
    parser.add_argument("--min-run", type=int, default=1, help="Require consecutive risk run length")
    parser.add_argument("--cooldown", type=int, default=0, help="Cooldown periods between risk signals")
    parser.add_argument("--auto-smoothing", action="store_true", help="Auto-tune min_run/cooldown to reduce false alarms")
    parser.add_argument("--score-window", type=int, default=8, help="Rolling window for regime change-rate in score mode")
    parser.add_argument(
        "--score-thresholds",
        default="0.8,0.9,0.95",
        help="Comma-separated quantiles for score->binary conversion (score mode)",
    )
    args = parser.parse_args()

    if args.auto_smoothing and args.min_run == 1 and args.cooldown == 0:
        if args.risk_mode == "unstable_only":
            args.min_run = 2
            args.cooldown = 3
        else:
            args.min_run = 3
            args.cooldown = 5

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip()]
    score_thresholds = [float(x) for x in args.score_thresholds.split(",") if x.strip()]

    official = None
    if args.proxy_mode == "official":
        official_path = Path(args.official)
        if not official_path.exists():
            raise SystemExit("official_regimes.csv not found. Run fetch_official_regimes.py first.")
        official = load_official(official_path)
        official = official.set_index("date")

    vix_series = None
    if args.proxy_mode == "market":
        vix_path = Path(args.data_dir) / f"{args.vix_asset}.csv"
        if vix_path.exists():
            vix_series = load_series(vix_path, "daily")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    results = {}

    for ticker in tickers:
        csv_path = Path(args.data_dir) / f"{ticker}.csv"
        if not csv_path.exists():
            continue
        for tf in tfs:
            series = load_series(csv_path, tf)
            if args.auto_embed:
                m_use, tau_use = estimate_embedding_params(series.values, tau_method=args.tau_method, m_method=args.m_method)
            else:
                m_use, tau_use = args.m, args.tau

            labels, confidence, quality = engine_labels(
                series,
                m=m_use,
                tau=tau_use,
                n_micro=args.n_micro,
                n_regimes=args.n_regimes,
                k_nn=args.k_nn,
                theiler=args.theiler,
                alpha=args.alpha,
                method=args.method,
            )

            df = pd.DataFrame({"engine": labels, "confidence": confidence, "quality": quality})
            if args.proxy_mode == "official":
                official_aligned = official.sort_index().reindex(df.index, method="ffill")
                joined = df.join(official_aligned, how="inner")
            else:
                joined = df.copy()
                # market proxies: drawdown, realized vol, VIX
                price = series.reindex(joined.index).astype(float)
                roll_max = price.rolling(args.drawdown_window, min_periods=2).max()
                drawdown = (price / roll_max - 1.0).fillna(0.0)
                ret = price.pct_change().fillna(0.0)
                vol = ret.rolling(args.vol_window, min_periods=2).std().fillna(0.0)
                vix_aligned = None
                if vix_series is not None:
                    vix_aligned = vix_series.reindex(joined.index, method="ffill").ffill()
                joined["proxy_drawdown"] = drawdown
                joined["proxy_vol"] = vol
                if vix_aligned is not None:
                    joined["proxy_vix"] = vix_aligned
            change_rate = joined["engine"].ne(joined["engine"].shift(1)).rolling(args.score_window, min_periods=1).mean()
            joined["change_rate"] = change_rate.fillna(0.0)
            if args.min_confidence > 0:
                joined = joined[joined["confidence"] >= args.min_confidence]
            if args.min_quality > 0:
                joined = joined[joined["quality"] >= args.min_quality]
            if joined.empty:
                continue

            # map regimes to binary proxies
            if args.proxy_mode == "official":
                macro = (joined["macro_regime"] == "RECESSION").astype(int)
                stress = (joined["stress_regime"] == "STRESS").astype(int)
                vol = joined["vol_regime"].isin(["HIGH", "EXTREME"]).astype(int)
            else:
                macro = (joined["proxy_drawdown"] <= args.drawdown_threshold).astype(int)
                vol_thr = float(joined["proxy_vol"].quantile(args.vol_quantile))
                vol = (joined["proxy_vol"] >= vol_thr).astype(int)
                if "proxy_vix" in joined.columns:
                    vix_thr = float(joined["proxy_vix"].quantile(args.vix_quantile))
                    stress = (joined["proxy_vix"] >= vix_thr).astype(int)
                else:
                    stress = vol.copy()

            lag_metrics = []
            for lag in range(-args.max_lag, args.max_lag + 1):
                shifted = joined.copy()
                shifted["engine_shift"] = shifted["engine"].shift(lag)
                shifted["conf_shift"] = shifted["confidence"].shift(lag)
                shifted["qual_shift"] = shifted["quality"].shift(lag)
                shifted["change_shift"] = shifted["change_rate"].shift(lag)
                shifted = shifted.dropna(subset=["engine_shift", "conf_shift", "qual_shift", "change_shift"])
                if args.risk_mode == "score":
                    weights = {"UNSTABLE": 1.0, "TRANSITION": 0.6, "NOISY": 0.7, "STABLE": 0.0}
                    base = shifted["engine_shift"].map(weights).fillna(0.0)
                    score = (
                        base
                        * (1.0 - shifted["conf_shift"])
                        * shifted["qual_shift"].clip(0.0, 1.0)
                        * shifted["change_shift"].clip(0.0, 1.0)
                    )
                    engine_risk = score.astype(float)
                elif args.risk_mode == "mode_unstable":
                    mode_unstable = build_mode_unstable(
                        joined["engine"],
                        joined["confidence"],
                        float(joined["quality"].iloc[0]),
                        window=args.score_window,
                        conf_floor=args.mode_unstable_conf,
                        quality_floor=args.mode_unstable_quality,
                    )
                    engine_risk = mode_unstable.shift(lag).dropna().astype(int)
                    # Align to shifted index for metric computation
                    engine_risk = engine_risk.reindex(shifted.index, fill_value=0)
                elif args.risk_mode == "consensus":
                    consensus = build_consensus_signal(
                        joined["engine"],
                        joined["confidence"],
                        float(joined["quality"].iloc[0]),
                        window=args.score_window,
                        conf_floor=args.mode_unstable_conf,
                        quality_floor=args.mode_unstable_quality,
                        change_rate_threshold=args.consensus_change_rate,
                        entropy_delta_threshold=args.consensus_entropy_delta,
                        min_votes=args.consensus_min_votes,
                    )
                    engine_risk = consensus.shift(lag).dropna().astype(int)
                    engine_risk = engine_risk.reindex(shifted.index, fill_value=0)
                elif args.risk_mode == "balanced_events":
                    consensus = build_consensus_signal(
                        joined["engine"],
                        joined["confidence"],
                        float(joined["quality"].iloc[0]),
                        window=args.score_window,
                        conf_floor=args.balanced_confidence,
                        quality_floor=args.balanced_quality,
                        change_rate_threshold=args.balanced_change_rate,
                        entropy_delta_threshold=args.balanced_entropy_delta,
                        min_votes=args.balanced_min_votes,
                    )
                    engine_risk = consensus.shift(lag).dropna().astype(int)
                    engine_risk = engine_risk.reindex(shifted.index, fill_value=0)
                elif args.risk_mode == "rare_events":
                    # rare events = unstable + high change rate + low confidence/quality, then smoothed
                    base = shifted["engine_shift"].isin(["UNSTABLE"]).astype(int)
                    high_change = (shifted["change_shift"] >= args.rare_change_rate).astype(int)
                    low_conf = (shifted["conf_shift"] <= args.rare_confidence).astype(int)
                    low_qual = (shifted["qual_shift"] <= args.rare_quality).astype(int)
                    engine_risk = ((base + high_change + low_conf + low_qual) >= 3).astype(int)
                elif args.risk_mode == "unstable_only":
                    engine_risk = shifted["engine_shift"].isin(["UNSTABLE"]).astype(int)
                else:
                    engine_risk = shifted["engine_shift"].isin(["UNSTABLE", "TRANSITION"]).astype(int)
                if args.risk_mode not in ("score", "mode_unstable", "consensus", "balanced_events"):
                    engine_risk = smooth_binary(engine_risk, args.min_run)
                    engine_risk = apply_cooldown(engine_risk, args.cooldown)
                macro_s = macro.loc[shifted.index].values
                stress_s = stress.loc[shifted.index].values
                vol_s = vol.loc[shifted.index].values
                if args.risk_mode == "score":
                    lag_metrics.append(
                        {
                            "lag": int(lag),
                            "engine_vs_macro": score_metrics(macro_s, engine_risk.values),
                            "engine_vs_stress": score_metrics(stress_s, engine_risk.values),
                            "engine_vs_vol": score_metrics(vol_s, engine_risk.values),
                        }
                    )
                else:
                    lag_metrics.append(
                        {
                            "lag": int(lag),
                            "engine_vs_macro": classification_metrics(macro_s, engine_risk.values),
                            "engine_vs_stress": classification_metrics(stress_s, engine_risk.values),
                            "engine_vs_vol": classification_metrics(vol_s, engine_risk.values),
                        }
                    )

            # Use smoothed risk signal for turning points (reduces false alarms).
            engine_changes = pd.DatetimeIndex([])
            if args.proxy_mode == "official":
                macro_changes = change_points(joined["macro_regime"])
                stress_changes = change_points(joined["stress_regime"])
                vol_changes = change_points(joined["vol_regime"])
            else:
                macro_changes = change_points(macro)
                stress_changes = change_points(stress)
                vol_changes = change_points(vol)
            if args.risk_mode != "score":
                if args.risk_mode == "mode_unstable":
                    engine_risk_full = build_mode_unstable(
                        joined["engine"],
                        joined["confidence"],
                        float(joined["quality"].iloc[0]),
                        window=args.score_window,
                        conf_floor=args.mode_unstable_conf,
                        quality_floor=args.mode_unstable_quality,
                    )
                elif args.risk_mode == "consensus":
                    engine_risk_full = build_consensus_signal(
                        joined["engine"],
                        joined["confidence"],
                        float(joined["quality"].iloc[0]),
                        window=args.score_window,
                        conf_floor=args.mode_unstable_conf,
                        quality_floor=args.mode_unstable_quality,
                        change_rate_threshold=args.consensus_change_rate,
                        entropy_delta_threshold=args.consensus_entropy_delta,
                        min_votes=args.consensus_min_votes,
                    )
                elif args.risk_mode == "balanced_events":
                    engine_risk_full = build_consensus_signal(
                        joined["engine"],
                        joined["confidence"],
                        float(joined["quality"].iloc[0]),
                        window=args.score_window,
                        conf_floor=args.balanced_confidence,
                        quality_floor=args.balanced_quality,
                        change_rate_threshold=args.balanced_change_rate,
                        entropy_delta_threshold=args.balanced_entropy_delta,
                        min_votes=args.balanced_min_votes,
                    )
                elif args.risk_mode == "rare_events":
                    base = joined["engine"].isin(["UNSTABLE"]).astype(int)
                    high_change = (joined["change_rate"] >= args.rare_change_rate).astype(int)
                    low_conf = (joined["confidence"] <= args.rare_confidence).astype(int)
                    low_qual = (joined["quality"] <= args.rare_quality).astype(int)
                    engine_risk_full = ((base + high_change + low_conf + low_qual) >= 3).astype(int)
                elif args.risk_mode == "unstable_only":
                    engine_risk_full = joined["engine"].isin(["UNSTABLE"]).astype(int)
                else:
                    engine_risk_full = joined["engine"].isin(["UNSTABLE", "TRANSITION"]).astype(int)
                if args.risk_mode == "rare_events":
                    engine_risk_full = smooth_binary(engine_risk_full, args.rare_min_run)
                    engine_risk_full = apply_cooldown(engine_risk_full, args.cooldown)
                elif args.risk_mode not in ("mode_unstable", "consensus", "balanced_events"):
                    engine_risk_full = smooth_binary(engine_risk_full, args.min_run)
                    engine_risk_full = apply_cooldown(engine_risk_full, args.cooldown)
                engine_changes = change_points(engine_risk_full)

            results[f"{ticker}_{tf}"] = {
                "n": int(len(joined)),
                "lag_sweep": lag_metrics,
                "score_thresholds": {},
                "turning_points": {
                    "macro": turn_hit_rate(macro_changes, engine_changes, args.turn_window),
                    "stress": turn_hit_rate(stress_changes, engine_changes, args.turn_window),
                    "vol": turn_hit_rate(vol_changes, engine_changes, args.turn_window),
                },
                "params": {
                    "m": m_use,
                    "tau": tau_use,
                    "n_micro": args.n_micro,
                    "n_regimes": args.n_regimes,
                    "method": args.method,
                    "max_lag": args.max_lag,
                    "turn_window_days": args.turn_window,
                    "risk_mode": args.risk_mode,
                    "min_confidence": args.min_confidence,
                    "min_quality": args.min_quality,
                    "min_run": args.min_run,
                    "cooldown": args.cooldown,
                    "score_window": args.score_window,
                    "score_thresholds": score_thresholds,
                },
            }

            if args.risk_mode == "score" and lag_metrics:
                best_lag = max(lag_metrics, key=lambda x: x["engine_vs_macro"]["roc_auc"])["lag"]
                shifted = joined.copy()
                shifted["engine_shift"] = shifted["engine"].shift(best_lag)
                shifted["conf_shift"] = shifted["confidence"].shift(best_lag)
                shifted["qual_shift"] = shifted["quality"].shift(best_lag)
                shifted["change_shift"] = shifted["change_rate"].shift(best_lag)
                shifted = shifted.dropna(subset=["engine_shift", "conf_shift", "qual_shift", "change_shift"])
                weights = {"UNSTABLE": 1.0, "TRANSITION": 0.6, "NOISY": 0.7, "STABLE": 0.0}
                base = shifted["engine_shift"].map(weights).fillna(0.0)
                score = (
                    base
                    * (1.0 - shifted["conf_shift"])
                    * shifted["qual_shift"].clip(0.0, 1.0)
                    * shifted["change_shift"].clip(0.0, 1.0)
                )
                scores = score.values
                score_pool = scores[scores > 0]
                if len(score_pool) == 0:
                    score_pool = scores
                macro_s = macro.loc[shifted.index].values
                stress_s = stress.loc[shifted.index].values
                vol_s = vol.loc[shifted.index].values
                thresh_results = {}
                for q in score_thresholds:
                    thr = float(np.quantile(score_pool, q))
                    binary = (scores >= thr).astype(int)
                    thresh_results[str(q)] = {
                        "threshold": thr,
                        "macro": classification_metrics(macro_s, binary),
                        "stress": classification_metrics(stress_s, binary),
                        "vol": classification_metrics(vol_s, binary),
                    }
                results[f"{ticker}_{tf}"]["score_thresholds"] = {
                    "best_lag": int(best_lag),
                    "thresholds": thresh_results,
                }

    out_path = outdir / "compare_summary.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # small markdown
    lines = ["# Official Regime Comparison", ""]
    for key, val in results.items():
        lines.append(f"## {key}")
        lines.append(f"- n: {val['n']}")
        if val.get("lag_sweep"):
            if val["params"]["risk_mode"] == "score":
                best_macro = max(val["lag_sweep"], key=lambda x: x["engine_vs_macro"]["roc_auc"])
                best_stress = max(val["lag_sweep"], key=lambda x: x["engine_vs_stress"]["roc_auc"])
                best_vol = max(val["lag_sweep"], key=lambda x: x["engine_vs_vol"]["roc_auc"])
                lines.append(f"- best macro AUC: lag {best_macro['lag']} -> {best_macro['engine_vs_macro']}")
                lines.append(f"- best stress AUC: lag {best_stress['lag']} -> {best_stress['engine_vs_stress']}")
                lines.append(f"- best vol AUC: lag {best_vol['lag']} -> {best_vol['engine_vs_vol']}")
                if val.get("score_thresholds", {}).get("thresholds"):
                    lines.append("- score thresholds:")
                    for q, metrics in val["score_thresholds"]["thresholds"].items():
                        lines.append(f"  - q={q} thr={metrics['threshold']:.6f} macro={metrics['macro']} stress={metrics['stress']} vol={metrics['vol']}")
            else:
                best_macro = max(val["lag_sweep"], key=lambda x: x["engine_vs_macro"]["balanced_accuracy"])
                best_stress = max(val["lag_sweep"], key=lambda x: x["engine_vs_stress"]["balanced_accuracy"])
                best_vol = max(val["lag_sweep"], key=lambda x: x["engine_vs_vol"]["balanced_accuracy"])
                lines.append(f"- best macro BA: lag {best_macro['lag']} -> {best_macro['engine_vs_macro']}")
                lines.append(f"- best stress BA: lag {best_stress['lag']} -> {best_stress['engine_vs_stress']}")
                lines.append(f"- best vol BA: lag {best_vol['lag']} -> {best_vol['engine_vs_vol']}")
        if "turning_points" in val:
            lines.append(f"- turning points macro: {val['turning_points']['macro']}")
            lines.append(f"- turning points stress: {val['turning_points']['stress']}")
            lines.append(f"- turning points vol: {val['turning_points']['vol']}")
        lines.append("")
    (outdir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] wrote {out_path}")


if __name__ == "__main__":
    main()

