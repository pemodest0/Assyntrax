#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _summarize_audit(audit: dict) -> dict:
    rows = audit.get("rows", []) if isinstance(audit, dict) else []
    total = len(rows)
    flags: Dict[str, int] = {}
    for row in rows:
        for f in row.get("stress_flags", []) or []:
            flags[f] = flags.get(f, 0) + 1
    rate = {k: (v / max(total, 1)) for k, v in flags.items()}
    return {"total": total, "flags": flags, "rates": rate}


def _best_models(forecast_root: Path) -> dict:
    if not forecast_root.exists():
        return {}
    results: dict = {}
    for ticker_dir in forecast_root.iterdir():
        if not ticker_dir.is_dir():
            continue
        for tf_dir in ticker_dir.iterdir():
            if not tf_dir.is_dir():
                continue
            best = {}
            for fp in tf_dir.glob("*_h*.json"):
                data = _load_json(fp)
                by_year = data.get("by_year", {})
                if not by_year:
                    continue
                # aggregate across years: mean MASE for each model
                model_scores: Dict[str, List[float]] = {}
                for yr in by_year.values():
                    overall = yr.get("overall", {})
                    for model, metrics in overall.items():
                        mase = metrics.get("mase")
                        if isinstance(mase, (int, float)):
                            model_scores.setdefault(model, []).append(float(mase))
                if not model_scores:
                    continue
                avg = {m: sum(v) / max(len(v), 1) for m, v in model_scores.items()}
                best_model = min(avg.items(), key=lambda kv: kv[1])
                key = fp.stem  # ticker_tf_target_hX
                best[key] = {"model": best_model[0], "mase": best_model[1], "avg": avg}
            if best:
                results[f"{ticker_dir.name}/{tf_dir.name}"] = best
    return results


def _recommendations(governance: dict, audit_sum: dict) -> Tuple[List[str], List[str]]:
    recs = []
    cmds = []
    counts = _safe_get(governance, "counts", default={}) or {}
    total = counts.get("total", 0) or 0
    stress_rate = (audit_sum.get("flags", {}).get("MODE_UNSTABLE", 0) / max(total, 1))
    low_conf = counts.get("low_conf", 0) or 0
    low_quality = counts.get("low_quality", 0) or 0

    if low_quality / max(total, 1) > 0.3:
        recs.append("Qualidade baixa elevada: reduza n_micro (ex: 400) e aumente k_nn (ex: 12).")
    if low_conf / max(total, 1) > 0.3:
        recs.append("Confiança baixa: avalie reduzir tau (acf) ou ajustar conf_hi (q60).")
    if stress_rate > 0.2:
        recs.append("Stress alto: aumentar min_run e cooldown na suavização dos regimes.")

    # Suggested command template (manual)
    cmds.append(
        "python3 scripts/bench/run_graph_regime_universe.py --tickers \"SPY,QQQ,GLD\" "
        "--timeframes daily,weekly --mode heavy --n-micro 400 --n-regimes 6 "
        "--k-nn 12 --theiler 10 --alpha 2.0 --outdir results/latest_graph"
    )
    return recs, cmds


def main() -> None:
    parser = argparse.ArgumentParser(description="Safira (advisor) for Assyntrax engine.")
    parser.add_argument("--results", default="results/latest_graph")
    parser.add_argument("--forecast", default="results/forecast_suite")
    parser.add_argument("--out", default="results/safira_recommendations.json")
    args = parser.parse_args()

    results_dir = Path(args.results)
    governance = _load_json(results_dir / "governance_summary.json")
    audit = _load_json(results_dir / "audit_daily.json")
    audit_sum = _summarize_audit(audit)
    best_models = _best_models(Path(args.forecast))

    recs, cmds = _recommendations(governance, audit_sum)

    payload = {
        "asof": _safe_get(governance, "asof"),
        "run": _safe_get(governance, "run", default={}),
        "counts": _safe_get(governance, "counts", default={}),
        "audit": audit_sum,
        "best_models": best_models,
        "recommendations": recs,
        "suggested_commands": cmds,
    }

    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("[safira] recomendações salvas em", args.out)
    if recs:
        print("Recomendações:")
        for r in recs:
            print("-", r)
    if cmds:
        print("Comandos sugeridos:")
        for c in cmds:
            print("-", c)


if __name__ == "__main__":
    main()
