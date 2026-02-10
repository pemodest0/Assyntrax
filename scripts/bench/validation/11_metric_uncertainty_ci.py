#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "uncertainty"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _bootstrap_ci(values: np.ndarray, n_boot: int, seed: int) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    vals = values[np.isfinite(values)]
    if vals.size == 0:
        return (np.nan, np.nan, np.nan)
    means = np.empty(n_boot, dtype=float)
    n = vals.size
    for i in range(n_boot):
        sample = vals[rng.integers(0, n, n)]
        means[i] = float(np.mean(sample))
    lo, med, hi = np.quantile(means, [0.05, 0.5, 0.95])
    return float(lo), float(med), float(hi)


def main() -> None:
    parser = argparse.ArgumentParser(description="CI 5-95 por bootstrap para metricas da validacao.")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--n-boot", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    src_master = ROOT / "results" / "validation" / "universe_mini" / "master_summary.csv"
    src_stress = ROOT / "results" / "validation" / "synthetic_false_alarm_stress" / "stress_detail.csv"
    src_robust = ROOT / "results" / "validation" / "robustness" / "aggregate.json"

    if not src_master.exists():
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": "missing_universe_master_summary"})
        print("[uncertainty] fail missing_universe_master_summary")
        return

    master = pd.read_csv(src_master)
    master["domain"] = master["asset_id"].astype(str).str.startswith("RE_").map({True: "realestate", False: "finance"})

    rows: list[dict[str, Any]] = []
    for domain, dg in master.groupby("domain"):
        for metric in ["mean_confidence", "mean_quality", "pct_transition"]:
            vals = pd.to_numeric(dg[metric], errors="coerce").to_numpy()
            lo, med, hi = _bootstrap_ci(vals, args.n_boot, args.seed + hash((domain, metric)) % 10000)
            rows.append(
                {
                    "scope": f"domain:{domain}",
                    "metric": metric,
                    "ci05": lo,
                    "median": med,
                    "ci95": hi,
                    "n": int(np.isfinite(vals).sum()),
                }
            )

    for metric in ["mean_confidence", "mean_quality", "pct_transition"]:
        vals = pd.to_numeric(master[metric], errors="coerce").to_numpy()
        lo, med, hi = _bootstrap_ci(vals, args.n_boot, args.seed + hash(("all", metric)) % 10000)
        rows.append(
            {
                "scope": "all_assets",
                "metric": metric,
                "ci05": lo,
                "median": med,
                "ci95": hi,
                "n": int(np.isfinite(vals).sum()),
            }
        )

    if src_stress.exists():
        stress = pd.read_csv(src_stress)
        for kind in ["no_shift", "has_shift"]:
            sg = stress[stress["kind"] == kind]
            vals = pd.to_numeric(sg["pct_transition"], errors="coerce").to_numpy()
            lo, med, hi = _bootstrap_ci(vals, args.n_boot, args.seed + hash((kind, "pct_transition")) % 10000)
            rows.append(
                {
                    "scope": f"synthetic:{kind}",
                    "metric": "pct_transition",
                    "ci05": lo,
                    "median": med,
                    "ci95": hi,
                    "n": int(np.isfinite(vals).sum()),
                }
            )

    ci_df = pd.DataFrame(rows)
    ci_df.to_csv(outdir / "metrics_ci.csv", index=False)

    stability = np.nan
    if src_robust.exists():
        try:
            rob = json.loads(src_robust.read_text(encoding="utf-8"))
            stability = float(rob.get("stability_score", np.nan))
        except Exception:
            stability = np.nan

    conservative = {}
    for metric in ["mean_confidence", "mean_quality", "pct_transition"]:
        subset = ci_df[(ci_df["scope"] == "all_assets") & (ci_df["metric"] == metric)]
        if not subset.empty:
            conservative[metric] = {
                "conservative_value": float(subset.iloc[0]["ci05"]),
                "median": float(subset.iloc[0]["median"]),
                "ci95": float(subset.iloc[0]["ci95"]),
            }

    summary = {
        "status": "ok",
        "n_boot": args.n_boot,
        "seed": args.seed,
        "stability_score_point": None if not np.isfinite(stability) else float(stability),
        "conservative_overall_metrics": conservative,
        "outputs": {
            "metrics_ci": str(outdir / "metrics_ci.csv"),
        },
    }
    _json_dump(outdir / "summary.json", summary)
    print(f"[uncertainty] ok rows={len(ci_df)} n_boot={args.n_boot}")


if __name__ == "__main__":
    main()

