from __future__ import annotations

import numpy as np
from sklearn.cluster import SpectralClustering, KMeans


def _pcca_like(p_matrix: np.ndarray, n_regimes: int, seed: int) -> np.ndarray:
    # Simple PCCA-like approach: cluster dominant eigenvectors of P.
    vals, vecs = np.linalg.eig(p_matrix.T)
    order = np.argsort(-np.real(vals))
    vecs = np.real(vecs[:, order[:n_regimes]])
    km = KMeans(n_clusters=n_regimes, random_state=seed, n_init=10)
    return km.fit_predict(vecs)


def metastable_regimes(
    p_matrix: np.ndarray,
    n_regimes: int,
    seed: int = 7,
    method: str = "spectral",
) -> np.ndarray:
    affinity = (p_matrix + p_matrix.T) / 2.0
    if method == "pcca":
        return _pcca_like(p_matrix, n_regimes=n_regimes, seed=seed)
    clustering = SpectralClustering(
        n_clusters=n_regimes,
        affinity="precomputed",
        random_state=seed,
        assign_labels="kmeans",
    )
    return clustering.fit_predict(affinity)
