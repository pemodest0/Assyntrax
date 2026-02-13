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
    c = np.asarray(centroids, dtype=float)
    if c.ndim == 1:
        c = c.reshape(-1, 1)

    nodes = []
    for i, row in enumerate(c):
        x = float(row[0]) if row.size >= 1 else 0.0
        y = float(row[1]) if row.size >= 2 else 0.0
        nodes.append({"id": i, "x": x, "y": y})

    return {
        "nodes": nodes,
        "edges": [{"source": int(a), "target": int(b)} for a, b in edges],
    }
