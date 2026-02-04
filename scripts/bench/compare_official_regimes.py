#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, matthews_corrcoef, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph_engine.core import run_graph_engine  # noqa: E402
from graph_engine.embedding import estimate_embedding_params  # noqa: E402


def load_series(path: Path, timeframe: str) -> pd.Series:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    col = "close" if "close" in df.columns else df.columns[-1]
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
    parser.add_argument("--risk-mode", default="unstable_transition", choices=["unstable_transition", "unstable_only"])
    parser.add_argument("--min-confidence", type=float, default=0.0)
    parser.add_argument("--min-quality", type=float, default=0.0)
    parser.add_argument("--min-run", type=int, default=1, help="Require consecutive risk run length")
    parser.add_argument("--cooldown", type=int, default=0, help="Cooldown periods between risk signals")
    parser.add_argument("--auto-smoothing", action="store_true", help="Auto-tune min_run/cooldown to reduce false alarms")
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

    official_path = Path(args.official)
    if not official_path.exists():
        raise SystemExit("official_regimes.csv not found. Run fetch_official_regimes.py first.")
    official = load_official(official_path)
    official = official.set_index("date")

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
            joined = df.join(official, how="inner")
            if args.min_confidence > 0:
                joined = joined[joined["confidence"] >= args.min_confidence]
            if args.min_quality > 0:
                joined = joined[joined["quality"] >= args.min_quality]
            if joined.empty:
                continue

            # map regimes to binary proxies
            macro = (joined["macro_regime"] == "RECESSION").astype(int)
            stress = (joined["stress_regime"] == "STRESS").astype(int)
            vol = joined["vol_regime"].isin(["HIGH", "EXTREME"]).astype(int)

            lag_metrics = []
            for lag in range(-args.max_lag, args.max_lag + 1):
                shifted = joined.copy()
                shifted["engine_shift"] = shifted["engine"].shift(lag)
                shifted = shifted.dropna(subset=["engine_shift"])
                if args.risk_mode == "unstable_only":
                    engine_risk = shifted["engine_shift"].isin(["UNSTABLE"]).astype(int)
                else:
                    engine_risk = shifted["engine_shift"].isin(["UNSTABLE", "TRANSITION"]).astype(int)
                engine_risk = smooth_binary(engine_risk, args.min_run)
                engine_risk = apply_cooldown(engine_risk, args.cooldown)
                macro_s = macro.loc[shifted.index].values
                stress_s = stress.loc[shifted.index].values
                vol_s = vol.loc[shifted.index].values
                lag_metrics.append(
                    {
                        "lag": int(lag),
                        "engine_vs_macro": classification_metrics(macro_s, engine_risk.values),
                        "engine_vs_stress": classification_metrics(stress_s, engine_risk.values),
                        "engine_vs_vol": classification_metrics(vol_s, engine_risk.values),
                    }
                )

            # Use smoothed risk signal for turning points (reduces false alarms).
            if args.risk_mode == "unstable_only":
                engine_risk_full = joined["engine"].isin(["UNSTABLE"]).astype(int)
            else:
                engine_risk_full = joined["engine"].isin(["UNSTABLE", "TRANSITION"]).astype(int)
            engine_risk_full = smooth_binary(engine_risk_full, args.min_run)
            engine_risk_full = apply_cooldown(engine_risk_full, args.cooldown)
            engine_changes = change_points(engine_risk_full)
            macro_changes = change_points(joined["macro_regime"])
            stress_changes = change_points(joined["stress_regime"])
            vol_changes = change_points(joined["vol_regime"])

            results[f"{ticker}_{tf}"] = {
                "n": int(len(joined)),
                "lag_sweep": lag_metrics,
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
                },
            }

    out_path = outdir / "compare_summary.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # small markdown
    lines = ["# Official Regime Comparison", ""]
    for key, val in results.items():
        lines.append(f"## {key}")
        lines.append(f"- n: {val['n']}")
        if val.get("lag_sweep"):
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
