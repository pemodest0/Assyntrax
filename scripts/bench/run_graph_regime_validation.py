#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from engine.graph.core import run_graph_engine  # noqa: E402


def synth_regimes(n: int = 1500, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 10, n)
    x1 = np.sin(2 * np.pi * 1 * t)  # stable oscillation
    x2 = np.exp(0.01 * np.arange(n))  # transition-like drift
    x3 = rng.normal(0, 1, n)  # noisy
    series = np.concatenate([x1, x2, x3])
    truth = np.array(
        ["STABLE"] * n + ["TRANSITION"] * n + ["NOISY"] * n,
        dtype=object,
    )
    return series, truth


def _confusion(labels: list[str], preds: list[str]) -> dict:
    idx = {k: i for i, k in enumerate(labels)}
    mat = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(labels, preds):
        mat[idx[t], idx[p]] += 1
    return {"labels": labels, "matrix": mat.tolist()}


def _f1(y_true: list[int], y_pred: list[int]) -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-12)
    return {"precision": prec, "recall": rec, "f1": f1}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validation on synthetic regimes (graph_engine).")
    parser.add_argument("--outdir", type=str, default="results/graph_validation")
    parser.add_argument("--n", type=int, default=1500)
    parser.add_argument("--m", type=int, default=3)
    parser.add_argument("--tau", type=int, default=1)
    parser.add_argument("--n-micro", type=int, default=200)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=10)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--method", type=str, default="spectral", choices=["spectral", "pcca"])
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    series, truth = synth_regimes(n=args.n)
    result = run_graph_engine(
        series,
        m=args.m,
        tau=args.tau,
        n_micro=args.n_micro,
        n_regimes=args.n_regimes,
        k_nn=args.k_nn,
        theiler=args.theiler,
        alpha=args.alpha,
        method=args.method,
    )
    pred = result.state_labels.tolist()

    # Align truth length to prediction length (embedding shortens series).
    if len(pred) < len(truth):
        truth = truth[: len(pred)]
    truth_list = truth.tolist()

    # 3-class mapping (UNSTABLE -> TRANSITION)
    mapped = []
    for p in pred:
        if p == "UNSTABLE":
            mapped.append("TRANSITION")
        else:
            mapped.append(p)

    labels = ["STABLE", "TRANSITION", "NOISY"]
    confusion = _confusion(labels, mapped)

    accuracy = float(np.mean([t == p for t, p in zip(truth_list, mapped)]))

    # structure vs noise (binary)
    y_true = [0 if t == "NOISY" else 1 for t in truth_list]
    y_pred = [0 if p == "NOISY" else 1 for p in mapped]
    structure_metrics = _f1(y_true, y_pred)

    summary = {
        "params": {
            "m": args.m,
            "tau": args.tau,
            "n_micro": args.n_micro,
            "n_regimes": args.n_regimes,
            "k_nn": args.k_nn,
            "theiler": args.theiler,
            "alpha": args.alpha,
            "method": args.method,
        },
        "accuracy_3class": accuracy,
        "structure_vs_noise": structure_metrics,
        "quality": result.quality,
        "thresholds": result.thresholds,
        "confusion_3class": confusion,
    }

    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (outdir / "confusion_3class.json").write_text(json.dumps(confusion, indent=2), encoding="utf-8")
    np.savetxt(outdir / "truth_pred.csv", np.column_stack([truth_list, mapped]), fmt="%s", delimiter=",")

    print(f"[ok] wrote {outdir}/summary.json")


if __name__ == "__main__":
    main()

