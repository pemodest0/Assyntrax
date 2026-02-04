#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

import numpy as np
try:
    from tqdm import tqdm
except Exception:  # pragma: no cover
    tqdm = None
import json

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from graph_engine.core import run_graph_engine  # noqa: E402
from graph_engine.embedding import estimate_embedding_params  # noqa: E402
from graph_engine.plots import (  # noqa: E402
    plot_embedding_2d,
    plot_stretch_hist,
    plot_timeline_regime,
    plot_transition_matrix,
)
from graph_engine.schema import GraphAsset, GraphConfig, GraphLinks, GraphMetrics, GraphState, iso_now  # noqa: E402
from graph_engine.version import ENGINE_VERSION  # noqa: E402
from graph_engine.export import write_asset_bundle, write_universe  # noqa: E402
from graph_engine.merge_existing import merge_forecast_risk  # noqa: E402
from graph_engine.sanity import sanity_alerts  # noqa: E402
from graph_engine.report import write_asset_report  # noqa: E402


def load_series_from_csv(path: Path, timeframe: str) -> np.ndarray:
    import pandas as pd

    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    col = "close" if "close" in df.columns else df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, col]).sort_values(date_col)
    if timeframe == "weekly":
        weekly = (
            df.set_index(date_col)[col]
            .astype(float)
            .resample("W")
            .last()
            .dropna()
        )
        return weekly.values
    series = df[col].astype(float)
    return series.values


def _ks_statistic(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) == 0 or len(b) == 0:
        return 0.0
    a = np.sort(a)
    b = np.sort(b)
    i = j = 0
    cdf_a = cdf_b = 0.0
    n = len(a)
    m = len(b)
    d = 0.0
    while i < n and j < m:
        if a[i] <= b[j]:
            i += 1
            cdf_a = i / n
        else:
            j += 1
            cdf_b = j / m
        d = max(d, abs(cdf_a - cdf_b))
    return float(d)


def _smooth_labels(
    labels: list[str],
    confidence: np.ndarray,
    min_run: int = 3,
    cooldown: int = 2,
    conf_floor: float = 0.45,
) -> list[str]:
    if not labels:
        return []
    conf = np.asarray(confidence, dtype=float)
    current = labels[0]
    smoothed = [current]
    cooldown_left = 0
    for i in range(1, len(labels)):
        lbl = labels[i]
        if lbl == current:
            smoothed.append(current)
            continue
        if cooldown_left > 0:
            cooldown_left -= 1
            smoothed.append(current)
            continue
        end = min(len(labels), i + max(1, min_run))
        if all(labels[j] == lbl for j in range(i, end)):
            conf_avg = float(np.mean(conf[i:end])) if end > i else float(conf[i])
            if conf_avg >= conf_floor:
                current = lbl
                cooldown_left = max(0, cooldown)
                smoothed.append(current)
                continue
        smoothed.append(current)
    return smoothed


def _rolling_mode(labels: list[str], window: int = 3) -> list[str]:
    if not labels:
        return []
    out: list[str] = []
    for i in range(len(labels)):
        start = max(0, i - window + 1)
        segment = labels[start : i + 1]
        counts: dict[str, int] = {}
        for lbl in segment:
            counts[lbl] = counts.get(lbl, 0) + 1
        out.append(max(counts.items(), key=lambda kv: kv[1])[0])
    return out


def _align_lag(labels: list[str], ref: list[str], max_lag: int = 6) -> tuple[list[str], int, float]:
    if not labels or not ref:
        return labels, 0, 0.0

    def _shift(vals: list[str], lag: int) -> list[str | None]:
        if lag == 0:
            return list(vals)
        if lag > 0:
            return [None] * lag + vals[:-lag]
        return vals[-lag:] + [None] * (-lag)

    best_lag = 0
    best_score = -1.0
    for lag in range(-max_lag, max_lag + 1):
        shifted = _shift(labels, lag)
        matches = 0
        total = 0
        for s, r in zip(shifted, ref):
            if s is None:
                continue
            total += 1
            if s == r:
                matches += 1
        score = matches / total if total else 0.0
        if score > best_score:
            best_score = score
            best_lag = lag
    if best_lag == 0:
        return labels, 0, best_score
    aligned = _shift(labels, best_lag)
    return [lbl if lbl is not None else labels[0] for lbl in aligned], best_lag, best_score


def build_asset_output(
    ticker: str,
    timeframe: str,
    series: np.ndarray,
    outdir: Path,
    n_micro: int,
    n_regimes: int,
    k_nn: int,
    theiler: int,
    alpha: float,
    mode: str,
    m: int | None,
    tau: int | None,
    auto_embed: bool,
    tau_method: str,
    m_method: str,
    method: str,
) -> tuple[GraphAsset, dict]:
    if auto_embed or m is None or tau is None:
        m_auto, tau_auto = estimate_embedding_params(series, tau_method=tau_method, m_method=m_method)
        m_use = m_auto
        tau_use = tau_auto
    else:
        m_use = m
        tau_use = tau

    if timeframe == "weekly":
        effective_micro = min(n_micro, max(40, len(series) // 12))
    else:
        effective_micro = min(n_micro, max(50, len(series) // 8))
    effective_knn = k_nn if mode == "heavy" else max(5, min(10, effective_micro // 10))
    result = run_graph_engine(
        series,
        m=m_use,
        tau=tau_use,
        n_micro=effective_micro,
        n_regimes=n_regimes,
        k_nn=effective_knn,
        theiler=theiler,
        alpha=alpha,
        seed=7,
        method=method,
    )

    raw_labels = [str(lbl) for lbl in result.state_labels]
    smooth_labels = _smooth_labels(
        raw_labels,
        result.confidence,
        min_run=3,
        cooldown=2,
        conf_floor=float(result.thresholds.get("conf_lo", 0.3)),
    )
    ref_labels = _rolling_mode(smooth_labels, window=3)
    aligned_labels, lag_opt, lag_score = _align_lag(smooth_labels, ref_labels, max_lag=6)

    conf_now = float(result.confidence[-1])
    escape_now = 1.0 - conf_now
    stretch_mu = float(result.stretch_mu[-1])
    state_label = aligned_labels[-1]
    quality_score = result.quality["score"]

    alerts: List[str] = []
    quality_floor = 0.35
    if quality_score < quality_floor:
        alerts.append("LOW_QUALITY")
    conf_floor = float(result.thresholds.get("conf_lo", 0.3))
    if conf_now < conf_floor:
        alerts.append("LOW_CONFIDENCE")
    if escape_now > 0.6:
        alerts.append("REGIME_INSTAVEL")

    base = f"{ticker}_{timeframe}"
    links = GraphLinks(
        regimes_csv=f"assets/{base}_regimes.csv",
        embedding_csv=f"assets/{base}_embedding.csv",
        micrograph_json=f"assets/{base}_micrograph.json",
        transitions_json=f"assets/{base}_transitions.json",
    )

    merged = merge_forecast_risk(ticker, timeframe, outdir)

    # thresholds + quality already computed in result
    asset = GraphAsset(
        asset=ticker,
        timeframe=timeframe,
        asof=iso_now(),
        group="unknown",
        state=GraphState(label=str(state_label), confidence=conf_now),
        graph=GraphConfig(n_micro=effective_micro, k_nn=effective_knn, theiler=theiler, alpha=alpha, method=method),
        metrics=GraphMetrics(
            stay_prob=conf_now,
            escape_prob=escape_now,
            stretch_mu=stretch_mu,
            stretch_frac_pos=float(result.stretch_frac_pos[-1]),
        ),
        quality=result.quality,
        alerts=alerts,
        links=links,
        engine_version=ENGINE_VERSION,
        forecast_diag=merged.get("forecast_diag"),
        risk=merged.get("risk"),
        thresholds=result.thresholds,
    )

    recommendation = "USE"
    if asset.state.label in ("UNSTABLE", "NOISY"):
        recommendation = "AVOID"
    elif asset.state.label == "TRANSITION":
        recommendation = "CAUTION"
    asset.recommendation = recommendation
    # Stability penalizes excessive regime flipping.
    badges: List[str] = []
    if asset.metrics.escape_prob > 0.7:
        badges.append("HIGH_ESCAPE")
    if asset.quality and asset.quality.get("score", 1.0) < 0.4:
        badges.append("LOW_QUALITY")
    if conf_now < 0.3:
        badges.append("LOW_CONFIDENCE")
    asset.badges = badges

    conf_hi = float(result.thresholds.get("conf_hi", 0.6))
    reliable = bool(
        (quality_score >= max(quality_floor, 0.5))
        and (conf_now >= conf_hi)
        and (asset.state.label == "STABLE")
    )
    gate_reasons = []
    if quality_score < max(quality_floor, 0.5):
        gate_reasons.append("QUALIDADE_BAIXA")
    if conf_now < conf_hi:
        gate_reasons.append("CONFIANCA_BAIXA")
    if asset.state.label != "STABLE":
        gate_reasons.append("REGIME_NAO_ESTAVEL")
    asset.gating = {
        "forecast_reliable": reliable,
        "reasons": gate_reasons,
        "quality_floor": max(quality_floor, 0.5),
        "conf_floor": conf_hi,
    }

    conf_series = result.confidence
    escape_series = 1.0 - conf_series
    window = max(30, min(120, max(1, len(conf_series) // 3)))
    recent_conf = conf_series[-window:]
    prior_conf = conf_series[:-window] if len(conf_series) > window else conf_series
    recent_escape = escape_series[-window:]
    prior_escape = escape_series[:-window] if len(escape_series) > window else escape_series
    ks_conf = _ks_statistic(recent_conf, prior_conf)
    ks_escape = _ks_statistic(recent_escape, prior_escape)
    mean_conf_delta = float(np.mean(recent_conf) - np.mean(conf_series))
    mean_escape_delta = float(np.mean(recent_escape) - np.mean(escape_series))
    drift_score = float(max(ks_conf, ks_escape, abs(mean_conf_delta), abs(mean_escape_delta)))
    trend = 0.0
    if len(recent_conf) >= 5:
        x = np.arange(len(recent_conf))
        trend = float(np.polyfit(x, recent_conf, 1)[0])

    # Stress monitor (camada 4)
    changes = 0
    for i in range(1, len(aligned_labels)):
        if aligned_labels[i] != aligned_labels[i - 1]:
            changes += 1
    change_rate = changes / max(1, len(aligned_labels) - 1)
    recent_changes = 0
    for i in range(max(1, len(aligned_labels) - window), len(aligned_labels)):
        if aligned_labels[i] != aligned_labels[i - 1]:
            recent_changes += 1
    recent_change_rate = recent_changes / max(1, window)

    entropy_rate = float(result.quality.get("entropy_rate", 0.0)) if result.quality else 0.0
    entropy_norm = float(entropy_rate / max(1e-12, np.log(effective_micro + 1)))
    lcc_ratio = float(result.quality.get("lcc_ratio", 0.0)) if result.quality else 0.0
    deg_low_frac = float(result.quality.get("deg_low_frac", 1.0)) if result.quality else 1.0
    active_edge_frac = float(result.quality.get("active_edge_frac", 0.0)) if result.quality else 0.0

    stress_flags: List[str] = []
    if recent_change_rate > 0.55 or change_rate > 0.45:
        stress_flags.append("FAST_REGIME_CHANGES")
    if lcc_ratio < 0.7 or deg_low_frac > 0.6 or active_edge_frac < 0.05:
        stress_flags.append("MICROSTATES_DEGENERATE")
    if entropy_norm > 0.95:
        stress_flags.append("ENTROPY_ANOMAL")

    if len(stress_flags) >= 2 and quality_score < 0.45:
        alerts.append("MODE_UNSTABLE")

    asset.governance = {
        "drift_score": drift_score,
        "ks_conf": ks_conf,
        "ks_escape": ks_escape,
        "mean_conf_delta": mean_conf_delta,
        "mean_escape_delta": mean_escape_delta,
        "confidence_trend": trend,
        "window": int(window),
        "lag_opt": lag_opt,
        "lag_agreement": lag_score,
        "stress": {
            "flags": stress_flags,
            "change_rate": change_rate,
            "recent_change_rate": recent_change_rate,
            "entropy_rate": entropy_rate,
            "entropy_norm": entropy_norm,
            "lcc_ratio": lcc_ratio,
            "deg_low_frac": deg_low_frac,
            "active_edge_frac": active_edge_frac,
        },
    }

    base_stability = float(1.0 - asset.metrics.escape_prob)
    stability_score = float(max(0.0, base_stability * quality_score * (1.0 - change_rate)))
    instability_score = float(1.0 - stability_score)
    predictability_score = float(max(0.0, stability_score * (1.0 - max(0.0, asset.metrics.stretch_frac_pos))))
    asset.scores = {
        "stability_score": stability_score,
        "instability_score": instability_score,
        "predictability_score": predictability_score,
    }

    metrics_payload = {
        "stay_prob": asset.metrics.stay_prob,
        "escape_prob": asset.metrics.escape_prob,
        "stretch_mu": asset.metrics.stretch_mu,
        "stretch_frac_pos": asset.metrics.stretch_frac_pos,
    }
    graph_params = {
        "m": m_use,
        "tau": tau_use,
        "n_micro": effective_micro,
        "n_regimes": n_regimes,
        "k_nn": effective_knn,
        "theiler": theiler,
        "alpha": alpha,
        "method": method,
        "tau_method": tau_method if auto_embed else "manual",
        "m_method": m_method if auto_embed else "manual",
    }

    regimes_rows = [
        {"t": int(i), "regime": str(r), "confidence": float(c)}
        for i, (r, c) in enumerate(zip(aligned_labels, result.confidence))
    ]
    transitions = {"matrix": result.p_matrix.tolist()}

    write_asset_bundle(
        asset,
        outdir,
        embedding=result.embedding[:, :2],
        regimes=regimes_rows,
        micrograph=result.micrograph,
        transitions=transitions,
    )

    write_asset_report(
        outdir,
        asset=asset.asset,
        timeframe=asset.timeframe,
        state_label=asset.state.label,
        confidence=asset.state.confidence,
        quality=asset.quality or {},
        metrics=metrics_payload,
        thresholds=asset.thresholds or {},
        graph_params=graph_params,
        recommendation=asset.recommendation or "USE",
        gating=asset.gating,
    )

    plots_dir = (outdir / "assets" / f"{ticker}_{timeframe}_plots")
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_timeline_regime(plots_dir, aligned_labels, result.confidence)
    plot_transition_matrix(plots_dir, result.p_matrix)
    plot_embedding_2d(plots_dir, result.embedding[:, :2], result.micro_regime[result.micro_labels])
    plot_stretch_hist(plots_dir, result.stretch_mu, aligned_labels)

    last_idx = len(aligned_labels) - 1
    prev_label = aligned_labels[last_idx - 1] if last_idx > 0 else aligned_labels[last_idx]
    change_steps = 0
    for i in range(last_idx - 1, -1, -1):
        if aligned_labels[i] != aligned_labels[last_idx]:
            change_steps = last_idx - i
            break
    audit = {
        "asset": ticker,
        "timeframe": timeframe,
        "state_now": str(aligned_labels[last_idx]),
        "state_prev": str(prev_label),
        "changed": bool(aligned_labels[last_idx] != prev_label),
        "steps_since_change": int(change_steps),
        "confidence": conf_now,
        "quality": quality_score,
        "forecast_reliable": reliable,
        "drift_score": drift_score,
        "confidence_trend": trend,
        "stress_flags": list(stress_flags),
        "alerts": list(alerts),
    }

    return asset, audit


def summarize_universe(records: list[GraphAsset], run_meta: dict) -> dict:
    recs = [r.to_dict() for r in records]
    def _count(key):
        counts = {}
        for r in recs:
            val = r.get(key)
            counts[val] = counts.get(val, 0) + 1
        return counts
    def _count_nested(path):
        counts = {}
        for r in recs:
            cur = r
            for p in path:
                cur = (cur or {}).get(p)
            counts[cur] = counts.get(cur, 0) + 1
        return counts
    alerts = {}
    badges = {}
    qualities = []
    for r in recs:
        for a in r.get("alerts") or []:
            alerts[a] = alerts.get(a, 0) + 1
        for b in r.get("badges") or []:
            badges[b] = badges.get(b, 0) + 1
        q = (r.get("quality") or {}).get("score")
        if isinstance(q, (int, float)):
            qualities.append(float(q))
    qualities.sort()
    def _median(vals):
        if not vals:
            return None
        mid = len(vals) // 2
        return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    return {
        "run": run_meta,
        "counts": {
            "total": len(recs),
            "recommendation": _count("recommendation"),
            "state": _count_nested(["state", "label"]),
        },
        "alerts": alerts,
        "badges": badges,
        "quality": {
            "min": qualities[0] if qualities else None,
            "median": _median(qualities),
            "max": qualities[-1] if qualities else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Graph Regime Engine (B1) for multiple assets.")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers")
    parser.add_argument("--timeframes", default="weekly", help="daily,weekly")
    parser.add_argument("--outdir", default="results/latest_graph", help="Output directory")
    parser.add_argument("--run-id", default="", help="Optional run id suffix for outdir")
    parser.add_argument("--mode", default="fast", choices=["fast", "heavy"])
    parser.add_argument("--n-micro", type=int, default=200)
    parser.add_argument("--n-micro-daily", type=int, default=0, help="Override n_micro for daily")
    parser.add_argument("--n-micro-weekly", type=int, default=0, help="Override n_micro for weekly")
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=10)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--metastable-method", default="spectral", choices=["spectral", "pcca"])
    parser.add_argument("--m", type=int, default=3, help="Embedding dimension (manual default)")
    parser.add_argument("--tau", type=int, default=1, help="Embedding lag (manual default)")
    parser.add_argument("--auto-embed", action="store_true", help="Enable experimental auto embedding (FNN/ACF)")
    parser.add_argument("--tau-method", default="ami", choices=["ami", "acf"], help="Auto tau method")
    parser.add_argument("--m-method", default="cao", choices=["cao", "fnn"], help="Auto m method")
    args = parser.parse_args()

    if args.run_id:
        outdir = Path(f"{args.outdir}_{args.run_id}")
    else:
        outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    tickers = []
    for t in args.tickers.split(","):
        t = t.strip()
        if not t:
            continue
        if t.lower().endswith(".csv"):
            t = t[:-4]
        tickers.append(t)
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    universe_daily: List[GraphAsset] = []
    universe_weekly: List[GraphAsset] = []

    sanity_summary = {}
    total = len(timeframes) * len(tickers)
    iterator = (
        tqdm(((tf, ticker) for tf in timeframes for ticker in tickers), total=total, desc="graph-benchmark")
        if tqdm
        else ((tf, ticker) for tf in timeframes for ticker in tickers)
    )
    missing = []
    audit_rows = []
    for tf, ticker in iterator:
        # Placeholder loader: expects CSV in data/raw/finance/yfinance_daily/{ticker}.csv
        # Replace with existing loaders if needed.
        csv_path = Path("data/raw/finance/yfinance_daily") / f"{ticker}.csv"
        if not csv_path.exists():
            missing.append(ticker)
            print(f"[skip] missing {csv_path}")
            continue
        series = load_series_from_csv(csv_path, tf)
        n_micro_tf = args.n_micro
        if tf == "daily" and args.n_micro_daily > 0:
            n_micro_tf = args.n_micro_daily
        if tf == "weekly" and args.n_micro_weekly > 0:
            n_micro_tf = args.n_micro_weekly
        asset, audit = build_asset_output(
            ticker,
            tf,
            series,
            outdir,
            n_micro=n_micro_tf,
            n_regimes=args.n_regimes,
            k_nn=args.k_nn,
            theiler=args.theiler,
            alpha=args.alpha,
            mode=args.mode,
            m=args.m,
            tau=args.tau,
            auto_embed=args.auto_embed,
            tau_method=args.tau_method,
            m_method=args.m_method,
            method=args.metastable_method,
        )
        audit_rows.append(audit)
        extra_alerts = sanity_alerts(
            ticker,
            n_micro=args.n_micro,
            n_points=len(series),
            escape_prob=asset.metrics.escape_prob,
            quality_score=asset.quality.get("score", 1.0) if asset.quality else 1.0,
            timeframe=tf,
        )
        if extra_alerts:
            asset.alerts.extend(extra_alerts)
            if "LOW_QUALITY_FORCE_NOISY" in extra_alerts:
                asset.state.label = "NOISY"
                asset.recommendation = "AVOID"
            sanity_summary.setdefault(ticker, {}).setdefault(tf, []).extend(extra_alerts)
        if tf == "daily":
            universe_daily.append(asset)
        else:
            universe_weekly.append(asset)

    if universe_weekly:
        write_universe(universe_weekly, outdir / "universe_weekly.json")
    if universe_daily:
        write_universe(universe_daily, outdir / "universe_daily.json")

    run_meta = {
        "run_id": args.run_id or "latest_graph",
        "engine_version": ENGINE_VERSION,
        "mode": args.mode,
        "n_micro": args.n_micro,
        "n_regimes": args.n_regimes,
        "k_nn": args.k_nn,
        "theiler": args.theiler,
        "alpha": args.alpha,
        "metastable_method": args.metastable_method,
        "tau_method": args.tau_method,
        "m_method": args.m_method,
        "timeframes": timeframes,
        "tickers": tickers,
    }
    if universe_weekly:
        summary = summarize_universe(universe_weekly, run_meta | {"timeframe": "weekly"})
        (outdir / "summary_weekly.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if universe_daily:
        summary = summarize_universe(universe_daily, run_meta | {"timeframe": "daily"})
        (outdir / "summary_daily.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if sanity_summary:
        (outdir / "sanity_summary.json").write_text(
            json.dumps(sanity_summary, indent=2),
            encoding="utf-8",
        )

    if audit_rows:
        # Daily audit summary for governance layer 1.
        counts = {
            "total": len(audit_rows),
            "changed": sum(1 for r in audit_rows if r.get("changed")),
            "low_conf": sum(1 for r in audit_rows if "LOW_CONFIDENCE" in (r.get("alerts") or [])),
            "low_quality": sum(1 for r in audit_rows if "LOW_QUALITY" in (r.get("alerts") or [])),
            "unstable": sum(1 for r in audit_rows if r.get("state_now") == "UNSTABLE"),
            "noisy": sum(1 for r in audit_rows if r.get("state_now") == "NOISY"),
            "reliable": sum(1 for r in audit_rows if r.get("forecast_reliable")),
        }
        stress_count = sum(1 for r in audit_rows if r.get("stress_flags"))
        audit_payload = {
            "asof": iso_now(),
            "run": run_meta,
            "counts": counts,
            "rows": audit_rows,
        }
        (outdir / "audit_daily.json").write_text(
            json.dumps(audit_payload, indent=2),
            encoding="utf-8",
        )

        drift_high = sum(1 for r in audit_rows if r.get("drift_score", 0.0) >= 0.25)
        trend_down = sum(1 for r in audit_rows if r.get("confidence_trend", 0.0) < 0.0)
        governance = {
            "asof": iso_now(),
            "run": run_meta,
            "counts": counts,
            "drift_high": drift_high,
            "trend_down": trend_down,
            "stress_high": stress_count,
            "status": "WATCH" if drift_high / max(1, len(audit_rows)) > 0.25 else "OK",
            "notes": "Governança camada 2/3: drift + tendência. Sem bloqueio de forecast.",
        }
        (outdir / "governance_summary.json").write_text(
            json.dumps(governance, indent=2),
            encoding="utf-8",
        )
        # Camada 5: relatório automático do run (técnico + executivo)
        reliable_rate = counts["reliable"] / max(1, counts["total"])
        stress_rate = stress_count / max(1, counts["total"])
        exec_verdict = "Confiável hoje: SIM" if reliable_rate >= 0.4 and stress_rate < 0.2 else "Confiável hoje: NÃO"
        exec_reasons = []
        if reliable_rate < 0.4:
            exec_reasons.append("poucos ativos com confiança alta")
        if stress_rate >= 0.2:
            exec_reasons.append("muitos ativos em modo instável")
        if drift_high / max(1, counts["total"]) > 0.25:
            exec_reasons.append("drift elevado em parte do universo")
        report = {
            "asof": iso_now(),
            "run": run_meta,
            "technical": {
                "counts": counts,
                "drift_high": drift_high,
                "trend_down": trend_down,
                "stress_high": stress_count,
            },
            "executive": {
                "verdict": exec_verdict,
                "reasons": exec_reasons,
                "reliable_rate": reliable_rate,
                "stress_rate": stress_rate,
            },
        }
        (outdir / "report_run.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        report_md = f"""# Relatório do Run — {run_meta.get('run_id')}

## Resumo executivo
- {exec_verdict}
- Razões: {", ".join(exec_reasons) if exec_reasons else "sem alertas críticos"}
- Taxa de confiança alta: {reliable_rate:.2f}
- Taxa de stress: {stress_rate:.2f}

## Resumo técnico
- Total de ativos: {counts["total"]}
- Mudanças recentes: {counts["changed"]}
- Low confidence: {counts["low_conf"]}
- Low quality: {counts["low_quality"]}
- Unstable: {counts["unstable"]}
- Noisy: {counts["noisy"]}
- Drift alto: {drift_high}
- Tendência de confiança em queda: {trend_down}
- Stress alto (MODE_UNSTABLE): {stress_count}
"""
        (outdir / "report_run.md").write_text(report_md, encoding="utf-8")

        # Camada 6: mensagem com "personalidade" para o front-end
        if reliable_rate >= 0.4 and stress_rate < 0.2:
            message = "Motor diz: Estrutura confiável detectada. Forecast liberado."
        else:
            message = "Motor diz: NÃO operar hoje. Estrutura fraca ou instável."
        (outdir / "engine_message.json").write_text(
            json.dumps(
                {
                    "asof": iso_now(),
                    "message": message,
                    "reliable_rate": reliable_rate,
                    "stress_rate": stress_rate,
                    "reasons": exec_reasons,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (outdir / "engine_manifest.json").write_text(
            json.dumps(
                {
                    "asof": iso_now(),
                    "engine_version": ENGINE_VERSION,
                    "schema_version": "1.0",
                    "run": run_meta,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    if missing:
        (outdir / "missing_assets.json").write_text(
            json.dumps(sorted(set(missing)), indent=2),
            encoding="utf-8",
        )

    # Example command:
    # python scripts/bench/run_graph_regime_universe.py --tickers "SPY,QQQ" --timeframes weekly --mode fast


if __name__ == "__main__":
    main()
