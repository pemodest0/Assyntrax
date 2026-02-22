#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]


FEATURE_NAMES = (
    "mean_confidence",
    "mean_quality",
    "pct_transition",
    "hazard_score",
    "hybrid_ews_score",
    "hybrid_var95_hist",
    "hybrid_ewma_sigma",
    "regime_age_days",
    "changepoint_flag",
    "pseudo_bifurcation_flag",
)


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        n = float(value)
        if math.isfinite(n):
            return n
    except Exception:
        pass
    return float(default)


def _norm_stats(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    return mean, std


def _build_adjacency(Xz: np.ndarray, k: int) -> np.ndarray:
    n = Xz.shape[0]
    if n == 0:
        return np.zeros((0, 0), dtype=float)
    if n == 1:
        return np.eye(1, dtype=float)
    k_eff = max(1, min(k, n - 1))
    sim = Xz @ Xz.T
    np.fill_diagonal(sim, -1e9)
    A = np.zeros((n, n), dtype=float)
    for i in range(n):
        idx = np.argpartition(sim[i], -k_eff)[-k_eff:]
        A[i, idx] = 1.0
    A = np.maximum(A, A.T)
    np.fill_diagonal(A, 1.0)
    deg = np.sum(A, axis=1)
    deg_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(deg, 1e-8)))
    return deg_inv_sqrt @ A @ deg_inv_sqrt


def _extract_features(panel: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    entries = panel.get("entries")
    if not isinstance(entries, list):
        return np.zeros((0, len(FEATURE_NAMES)), dtype=float), np.zeros((0,), dtype=float)

    rows = []
    y = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        micro = entry.get("micro")
        gates = entry.get("gates")
        macro = entry.get("macro")
        if not isinstance(micro, dict):
            micro = {}
        if not isinstance(gates, dict):
            gates = {}
        if not isinstance(macro, dict):
            macro = {}

        mean_conf = _to_float(micro.get("mean_confidence"), 0.5)
        mean_quality = _to_float(micro.get("mean_quality"), 0.5)
        pct_transition = _to_float(micro.get("pct_transition"), 0.5)
        hazard = _to_float(gates.get("hazard_score"), 0.5)
        ews = _to_float(gates.get("hybrid_ews_score"), 0.5)
        var95 = _to_float(gates.get("hybrid_var95_hist"), 0.0)
        ewma_sigma = _to_float(gates.get("hybrid_ewma_sigma"), 0.0)
        regime_age = _to_float(gates.get("regime_age_days"), 0.0)
        changepoint = 1.0 if bool(gates.get("changepoint_flag", False)) else 0.0
        pseudo_flag = 1.0 if bool(macro.get("pseudo_bifurcation_flag", False)) else 0.0

        rows.append(
            [
                mean_conf,
                mean_quality,
                pct_transition,
                hazard,
                ews,
                var95,
                ewma_sigma,
                regime_age,
                changepoint,
                pseudo_flag,
            ]
        )

        # pseudo-supervision target in [0,1]
        target = 0.40 * np.clip(pct_transition, 0.0, 1.0) + 0.35 * np.clip(hazard, 0.0, 1.0) + 0.25 * np.clip(
            1.0 - mean_conf, 0.0, 1.0
        )
        y.append(float(np.clip(target, 0.0, 1.0)))

    if not rows:
        return np.zeros((0, len(FEATURE_NAMES)), dtype=float), np.zeros((0,), dtype=float)
    return np.array(rows, dtype=float), np.array(y, dtype=float)


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x_clip = np.clip(x, -20.0, 20.0)
    return 1.0 / (1.0 + np.exp(-x_clip))


def _forward(
    A: np.ndarray,
    X: np.ndarray,
    W1: np.ndarray,
    b1: np.ndarray,
    W2: np.ndarray,
    b2: np.ndarray,
    w_out: np.ndarray,
    b_out: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    Z1 = A @ X @ W1 + b1
    H1 = _relu(Z1)
    Z2 = A @ H1 @ W2 + b2
    H2 = _relu(Z2)
    logits = H2 @ w_out + b_out
    pred = _sigmoid(logits)
    return H1, H2, logits, pred


def _train_gnn(
    X: np.ndarray,
    y: np.ndarray,
    *,
    hidden_dim: int = 16,
    epochs: int = 600,
    lr: float = 0.01,
    l2: float = 1e-4,
    k_neighbors: int = 4,
    seed: int = 42,
) -> dict[str, Any]:
    n, f = X.shape
    if n == 0:
        raise RuntimeError("sem dados para treino do modelo C.")
    mean, std = _norm_stats(X)
    Xz = (X - mean) / std
    A = _build_adjacency(Xz, k=k_neighbors)

    rng = np.random.default_rng(seed)
    W1 = rng.normal(0.0, 0.1, size=(f, hidden_dim))
    b1 = np.zeros((hidden_dim,), dtype=float)
    W2 = rng.normal(0.0, 0.1, size=(hidden_dim, hidden_dim))
    b2 = np.zeros((hidden_dim,), dtype=float)
    w_out = rng.normal(0.0, 0.1, size=(hidden_dim,))
    b_out = 0.0

    losses = []
    for _ in range(epochs):
        H1, H2, logits, pred = _forward(A, Xz, W1, b1, W2, b2, w_out, b_out)
        err = pred - y
        loss = float(np.mean(err**2) + l2 * (np.mean(W1**2) + np.mean(W2**2) + np.mean(w_out**2)))
        losses.append(loss)

        # backprop (mse + sigmoid)
        n_inv = 1.0 / max(1, n)
        d_pred = 2.0 * err * n_inv
        d_logits = d_pred * pred * (1.0 - pred)

        grad_w_out = H2.T @ d_logits + 2.0 * l2 * w_out
        grad_b_out = float(np.sum(d_logits))
        dH2 = np.outer(d_logits, w_out)

        dZ2 = dH2 * (H2 > 0).astype(float)
        grad_W2 = (A @ H1).T @ dZ2 + 2.0 * l2 * W2
        grad_b2 = np.sum(dZ2, axis=0)
        dH1 = A.T @ (dZ2 @ W2.T)

        dZ1 = dH1 * (H1 > 0).astype(float)
        grad_W1 = (A @ Xz).T @ dZ1 + 2.0 * l2 * W1
        grad_b1 = np.sum(dZ1, axis=0)

        W1 -= lr * grad_W1
        b1 -= lr * grad_b1
        W2 -= lr * grad_W2
        b2 -= lr * grad_b2
        w_out -= lr * grad_w_out
        b_out -= lr * grad_b_out

    _, _, _, pred_final = _forward(A, Xz, W1, b1, W2, b2, w_out, b_out)
    rmse = float(np.sqrt(np.mean((pred_final - y) ** 2)))

    return {
        "feature_names": list(FEATURE_NAMES),
        "normalization": {"mean": mean.tolist(), "std": std.tolist()},
        "graph": {"k_neighbors": int(k_neighbors)},
        "architecture": {"input_dim": int(f), "hidden_dim": int(hidden_dim)},
        "weights": {
            "W1": W1.tolist(),
            "b1": b1.tolist(),
            "W2": W2.tolist(),
            "b2": b2.tolist(),
            "w_out": w_out.tolist(),
            "b_out": float(b_out),
        },
        "training": {
            "seed": int(seed),
            "epochs": int(epochs),
            "lr": float(lr),
            "l2": float(l2),
            "loss_last": float(losses[-1] if losses else 0.0),
            "loss_best": float(min(losses) if losses else 0.0),
            "rmse": rmse,
            "n_nodes": int(n),
        },
    }


def _infer_with_checkpoint(checkpoint: dict[str, Any], X: np.ndarray) -> dict[str, Any]:
    feat = checkpoint.get("feature_names")
    if not isinstance(feat, list) or len(feat) != X.shape[1]:
        raise RuntimeError("checkpoint feature_names incompativel.")
    norm = checkpoint.get("normalization")
    graph = checkpoint.get("graph")
    arch = checkpoint.get("architecture")
    w = checkpoint.get("weights")
    if not isinstance(norm, dict) or not isinstance(graph, dict) or not isinstance(arch, dict) or not isinstance(w, dict):
        raise RuntimeError("checkpoint incompleto.")

    mean = np.array(norm.get("mean", []), dtype=float)
    std = np.array(norm.get("std", []), dtype=float)
    if mean.shape[0] != X.shape[1] or std.shape[0] != X.shape[1]:
        raise RuntimeError("checkpoint normalization invalido.")
    Xz = (X - mean) / np.where(std < 1e-8, 1.0, std)

    k = int(graph.get("k_neighbors", 4))
    A = _build_adjacency(Xz, k=k)

    W1 = np.array(w.get("W1"), dtype=float)
    b1 = np.array(w.get("b1"), dtype=float)
    W2 = np.array(w.get("W2"), dtype=float)
    b2 = np.array(w.get("b2"), dtype=float)
    w_out = np.array(w.get("w_out"), dtype=float)
    b_out = float(w.get("b_out", 0.0))

    _, _, _, pred = _forward(A, Xz, W1, b1, W2, b2, w_out, b_out)
    return {
        "node_scores": pred.tolist(),
        "risk_score": float(np.clip(np.mean(pred), 0.0, 1.0)),
        "confidence": float(np.clip(1.0 - np.std(pred), 0.0, 1.0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train model C GNN checkpoint from risk truth panel.")
    parser.add_argument("--panel", type=str, default="results/validation/risk_truth_panel.json")
    parser.add_argument("--out", type=str, default="models/model_c_gnn_checkpoint.json")
    parser.add_argument("--epochs", type=int, default=600)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--l2", type=float, default=1e-4)
    parser.add_argument("--hidden-dim", type=int, default=16)
    parser.add_argument("--k-neighbors", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    panel = _read_json(ROOT / args.panel, {})
    X, y = _extract_features(panel if isinstance(panel, dict) else {})
    if X.shape[0] == 0:
        raise RuntimeError("risk_truth_panel sem entries para treino.")

    ckpt = _train_gnn(
        X,
        y,
        hidden_dim=int(args.hidden_dim),
        epochs=int(args.epochs),
        lr=float(args.lr),
        l2=float(args.l2),
        k_neighbors=int(args.k_neighbors),
        seed=int(args.seed),
    )
    infer = _infer_with_checkpoint(ckpt, X)

    payload = {
        "version": "model_c_gnn_v1",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_panel": str(ROOT / args.panel),
        "checkpoint": ckpt,
        "sanity_inference": infer,
    }

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"[train_model_c_gnn] out={out_path} n_nodes={X.shape[0]} "
        f"risk={infer['risk_score']:.3f} conf={infer['confidence']:.3f}"
    )


if __name__ == "__main__":
    main()

