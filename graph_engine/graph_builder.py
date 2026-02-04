from __future__ import annotations

import numpy as np
from sklearn.neighbors import NearestNeighbors


def transition_counts(labels: np.ndarray) -> np.ndarray:
    n = int(labels.max()) + 1
    counts = np.zeros((n, n), dtype=float)
    for a, b in zip(labels[:-1], labels[1:]):
        counts[int(a), int(b)] += 1.0
    return counts


def normalize_counts(counts: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    smoothed = counts + alpha
    row_sums = smoothed.sum(axis=1, keepdims=True)
    return smoothed / np.maximum(row_sums, 1e-12)


def knn_edges(centroids: np.ndarray, k: int) -> list[tuple[int, int]]:
    if k <= 0:
        return []
    nn = NearestNeighbors(n_neighbors=min(k + 1, len(centroids)))
    nn.fit(centroids)
    _, indices = nn.kneighbors(centroids)
    edges = []
    for i, row in enumerate(indices):
        for j in row[1:]:
            edges.append((i, int(j)))
    return edges


def build_micrograph(centroids: np.ndarray, edges: list[tuple[int, int]]) -> dict:
    return {
        "nodes": [{"id": i, "x": float(c[0]), "y": float(c[1])} for i, c in enumerate(centroids)],
        "edges": [{"source": int(a), "target": int(b)} for a, b in edges],
    }
