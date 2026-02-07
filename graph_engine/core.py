from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .embedding import takens_embed
from .microstates import build_microstates
from .graph_builder import transition_counts, normalize_counts, knn_edges, build_micrograph
from .metastable import metastable_regimes
from .labels import compute_confidence, labels_for_series, compute_graph_quality


@dataclass
class GraphResult:
    embedding: np.ndarray
    micro_labels: np.ndarray
    centroids: np.ndarray
    p_matrix: np.ndarray
    micro_regime: np.ndarray
    confidence: np.ndarray
    stretch_mu: np.ndarray
    stretch_frac_pos: np.ndarray
    state_labels: np.ndarray
    micrograph: dict[str, Any]
    quality: dict[str, float]
    thresholds: dict[str, float]


def local_divergence(embedded: np.ndarray, theiler: int = 10) -> tuple[np.ndarray, np.ndarray]:
    n = embedded.shape[0]
    stretch = np.zeros(n - 1)
    frac_pos = np.zeros(n - 1)
    for i in range(n - 1):
        j = max(0, i - theiler)
        k = min(n - 1, i + theiler)
        a = embedded[i]
        b = embedded[k]
        c = embedded[i + 1]
        d = embedded[min(n - 1, k + 1)]
        d0 = np.linalg.norm(a - b) + 1e-8
        d1 = np.linalg.norm(c - d) + 1e-8
        ell = np.log(d1 / d0)
        stretch[i] = ell
        frac_pos[i] = 1.0 if ell > 0 else 0.0
    return stretch, frac_pos


def run_graph_engine(
    series: np.ndarray,
    m: int = 3,
    tau: int = 1,
    n_micro: int = 200,
    micro_method: str = "kmeans",
    micro_params: dict | None = None,
    micro_smooth: str | None = None,
    micro_smooth_noise: float = 0.05,
    n_regimes: int = 4,
    k_nn: int = 5,
    theiler: int = 10,
    alpha: float = 2.0,
    seed: int = 7,
    method: str = "spectral",
    timeframe: str = "daily",
    state_smooth: str | None = None,
    state_smooth_noise: float = 0.05,
) -> GraphResult:
    embedding = takens_embed(series, m=m, tau=tau)
    micro_labels, centroids = build_microstates(
        embedding,
        n_micro=n_micro,
        seed=seed,
        method=micro_method,
        cluster_params=micro_params,
        smooth_method=micro_smooth,
        smooth_noise=micro_smooth_noise,
    )
    counts = transition_counts(micro_labels)
    p_matrix = normalize_counts(counts, alpha=alpha)
    micro_regime = metastable_regimes(p_matrix, n_regimes=n_regimes, seed=seed, method=method)
    conf = compute_confidence(p_matrix, micro_regime, micro_labels)
    stretch, frac_pos = local_divergence(embedding, theiler=theiler)
    if stretch.size > 0:
        lo = float(np.quantile(stretch, 0.05))
        hi = float(np.quantile(stretch, 0.95))
        stretch = np.clip(stretch, lo, hi)
    stretch_mu = np.pad(stretch, (0, 1), mode="edge")
    stretch_frac_pos = np.pad(frac_pos, (0, 1), mode="edge")
    edges = knn_edges(centroids, k=k_nn)
    micrograph = build_micrograph(centroids, edges)
    occupancy = np.bincount(micro_labels, minlength=n_micro).astype(float)
    quality = compute_graph_quality(n_micro, edges, occupancy, p_matrix, {"n_points": float(len(micro_labels))})
    state_labels, thresholds = labels_for_series(
        conf,
        stretch_mu,
        stretch_frac_pos,
        quality_score=quality["score"],
        timeframe=timeframe,
        smooth_method=state_smooth,
        smooth_noise=state_smooth_noise,
    )
    return GraphResult(
        embedding=embedding,
        micro_labels=micro_labels,
        centroids=centroids,
        p_matrix=p_matrix,
        micro_regime=micro_regime,
        confidence=conf,
        stretch_mu=stretch_mu,
        stretch_frac_pos=stretch_frac_pos,
        state_labels=state_labels,
        micrograph=micrograph,
        quality=quality,
        thresholds=thresholds,
    )
