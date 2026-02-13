from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.neighbors import NearestNeighbors

try:  # optional dependency
    from hdbscan import HDBSCAN
except Exception:  # pragma: no cover
    HDBSCAN = None


def _remap_labels(labels: np.ndarray) -> tuple[np.ndarray, dict[int, int]]:
    unique = [int(v) for v in np.unique(labels) if v >= 0]
    mapping = {old: new for new, old in enumerate(unique)}
    remapped = np.array([mapping.get(int(v), -1) for v in labels], dtype=int)
    return remapped, mapping


def _centroids_from_labels(embedded: np.ndarray, labels: np.ndarray, n_clusters: int) -> np.ndarray:
    centroids = np.zeros((n_clusters, embedded.shape[1]), dtype=float)
    for k in range(n_clusters):
        mask = labels == k
        if not np.any(mask):
            continue
        centroids[k] = np.mean(embedded[mask], axis=0)
    return centroids


def _assign_noise_to_nearest(embedded: np.ndarray, labels: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    if centroids.size == 0:
        return labels
    noise_idx = np.where(labels < 0)[0]
    if noise_idx.size == 0:
        return labels
    nn = NearestNeighbors(n_neighbors=1)
    nn.fit(centroids)
    nearest = nn.kneighbors(embedded[noise_idx], return_distance=False).ravel()
    labels = labels.copy()
    labels[noise_idx] = nearest
    return labels


def _hmm_smooth(labels: np.ndarray, noise: float = 0.05) -> np.ndarray:
    obs = np.asarray(labels, dtype=int)
    states = np.unique(obs)
    if states.size <= 1:
        return obs
    state_map = {int(s): i for i, s in enumerate(states)}
    inv_map = {i: int(s) for s, i in state_map.items()}
    obs_idx = np.array([state_map[int(s)] for s in obs], dtype=int)
    k = states.size
    counts = np.ones((k, k), dtype=float) * 1e-3
    for a, b in zip(obs_idx[:-1], obs_idx[1:]):
        counts[a, b] += 1.0
    trans = counts / counts.sum(axis=1, keepdims=True)
    if k == 1:
        return obs
    emit = np.full((k, k), noise / max(k - 1, 1), dtype=float)
    np.fill_diagonal(emit, 1.0 - noise)
    log_trans = np.log(trans + 1e-12)
    log_emit = np.log(emit + 1e-12)
    log_pi = np.full(k, -np.log(k), dtype=float)
    dp = np.zeros((obs_idx.size, k), dtype=float)
    back = np.zeros((obs_idx.size, k), dtype=int)
    dp[0] = log_pi + log_emit[:, obs_idx[0]]
    for t in range(1, obs_idx.size):
        scores = dp[t - 1][:, None] + log_trans
        back[t] = np.argmax(scores, axis=0)
        dp[t] = scores[back[t], np.arange(k)] + log_emit[:, obs_idx[t]]
    path = np.zeros(obs_idx.size, dtype=int)
    path[-1] = int(np.argmax(dp[-1]))
    for t in range(obs_idx.size - 2, -1, -1):
        path[t] = back[t + 1, path[t + 1]]
    return np.array([inv_map[int(s)] for s in path], dtype=int)


def build_microstates(
    embedded: np.ndarray,
    n_micro: int,
    seed: int = 7,
    method: str = "kmeans",
    cluster_params: dict | None = None,
    smooth_method: str | None = None,
    smooth_noise: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    params = cluster_params or {}
    method = (method or "kmeans").lower()
    if method in ("hdbscan", "hdbscan_hmm"):
        if HDBSCAN is None:
            method = "kmeans"
        else:
            min_cluster_size = int(params.get("min_cluster_size", max(5, n_micro // 10)))
            min_samples = params.get("min_samples", None)
            clusterer = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples)
            labels = clusterer.fit_predict(embedded)
            if np.all(labels < 0):
                method = "kmeans"
            else:
                labels, mapping = _remap_labels(labels)
                n_clusters = len(mapping)
                centroids = _centroids_from_labels(embedded, labels, n_clusters)
                labels = _assign_noise_to_nearest(embedded, labels, centroids)
                if smooth_method == "hmm" or method == "hdbscan_hmm":
                    labels = _hmm_smooth(labels, noise=smooth_noise)
                return labels, centroids

    if method == "dbscan":
        eps = float(params.get("eps", 0.5))
        min_samples = int(params.get("min_samples", 5))
        clusterer = DBSCAN(eps=eps, min_samples=min_samples)
        labels = clusterer.fit_predict(embedded)
        labels, mapping = _remap_labels(labels)
        n_clusters = len(mapping)
        if n_clusters == 0:
            method = "kmeans"
        else:
            centroids = _centroids_from_labels(embedded, labels, n_clusters)
            labels = _assign_noise_to_nearest(embedded, labels, centroids)
            if smooth_method == "hmm":
                labels = _hmm_smooth(labels, noise=smooth_noise)
            return labels, centroids

    km = KMeans(n_clusters=n_micro, random_state=seed, n_init=10)
    labels = km.fit_predict(embedded)
    if smooth_method == "hmm":
        labels = _hmm_smooth(labels, noise=smooth_noise)
    return labels, km.cluster_centers_
