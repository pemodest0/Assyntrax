#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np


def _best_by(metric_key: str, lag_sweep: list[dict]) -> dict | None:
    if not lag_sweep:
        return None
    return max(lag_sweep, key=lambda x: x[metric_key]["roc_auc"])


def _plot_auc_by_lag(lag_sweep: list[dict], key: str, title: str, out: Path) -> None:
    if not lag_sweep:
        return
    lags = [x["lag"] for x in lag_sweep]
    aucs = [x[key]["roc_auc"] for x in lag_sweep]
    plt.figure(figsize=(8, 3.5))
    plt.plot(lags, aucs, marker="o", linewidth=1.5)
    plt.axhline(0.5, color="#888888", linestyle="--", linewidth=1)
    plt.title(title)
    plt.xlabel("Lag")
    plt.ylabel("ROC AUC")
    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=160)
    plt.close()


def _plot_thresholds(thresholds: dict, title: str, out: Path) -> None:
    if not thresholds:
        return
    qs = []
    macro = []
    stress = []
    vol = []
    for q, met in thresholds.items():
        qs.append(float(q))
        macro.append(met["macro"]["balanced_accuracy"])
        stress.append(met["stress"]["balanced_accuracy"])
        vol.append(met["vol"]["balanced_accuracy"])
    x = np.arange(len(qs))
    width = 0.25
    plt.figure(figsize=(8, 3.5))
    plt.bar(x - width, macro, width, label="Macro")
    plt.bar(x, stress, width, label="Stress")
    plt.bar(x + width, vol, width, label="Volatilidade")
    plt.xticks(x, [str(q) for q in qs])
    plt.ylim(0.0, 1.0)
    plt.title(title)
    plt.xlabel("Quantil do score")
    plt.ylabel("Balanced Accuracy")
    plt.legend(fontsize=8, ncol=3)
    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=160)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build benchmark visuals for official regime comparison.")
    parser.add_argument("--compare", default="results/official_regimes/compare/compare_summary.json")
    parser.add_argument("--outdir", default="results/official_regimes/compare/plots")
    parser.add_argument("--bench-out", default="results/official_regimes/compare/benchmarks.json")
    args = parser.parse_args()

    compare_path = Path(args.compare)
    outdir = Path(args.outdir)
    bench_out = Path(args.bench_out)

    if not compare_path.exists():
        raise SystemExit(f"Missing {compare_path}")

    data: Dict[str, Any] = json.loads(compare_path.read_text())
    bench_rows = []

    for key, val in data.items():
        lag_sweep = val.get("lag_sweep", [])
        thresholds = (val.get("score_thresholds") or {}).get("thresholds", {})
        best_macro = _best_by("engine_vs_macro", lag_sweep)
        best_stress = _best_by("engine_vs_stress", lag_sweep)
        best_vol = _best_by("engine_vs_vol", lag_sweep)

        _plot_auc_by_lag(
            lag_sweep,
            "engine_vs_macro",
            f"{key} • Macro (ROC AUC por lag)",
            outdir / f"{key}_macro_auc.png",
        )
        _plot_auc_by_lag(
            lag_sweep,
            "engine_vs_stress",
            f"{key} • Stress (ROC AUC por lag)",
            outdir / f"{key}_stress_auc.png",
        )
        _plot_auc_by_lag(
            lag_sweep,
            "engine_vs_vol",
            f"{key} • Volatilidade (ROC AUC por lag)",
            outdir / f"{key}_vol_auc.png",
        )
        _plot_thresholds(
            thresholds,
            f"{key} • Balanced Accuracy por quantil",
            outdir / f"{key}_thresholds.png",
        )

        bench_rows.append(
            {
                "asset_tf": key,
                "best_macro": best_macro,
                "best_stress": best_stress,
                "best_vol": best_vol,
                "thresholds": thresholds,
                "plots": {
                    "macro_auc": f"{outdir.name}/{key}_macro_auc.png",
                    "stress_auc": f"{outdir.name}/{key}_stress_auc.png",
                    "vol_auc": f"{outdir.name}/{key}_vol_auc.png",
                    "thresholds": f"{outdir.name}/{key}_thresholds.png",
                },
            }
        )

    bench_out.parent.mkdir(parents=True, exist_ok=True)
    bench_out.write_text(json.dumps(bench_rows, indent=2), encoding="utf-8")
    print(f"[ok] wrote {bench_out}")


if __name__ == "__main__":
    main()
