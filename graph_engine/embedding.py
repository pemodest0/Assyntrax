from __future__ import annotations

import numpy as np
from typing import Tuple


def _autocorr(series: np.ndarray, max_lag: int) -> np.ndarray:
    values = np.asarray(series, dtype=float)
    values = values - np.mean(values)
    denom = np.sum(values * values)
    if denom == 0:
        return np.zeros(max_lag)
    out = np.zeros(max_lag)
    for lag in range(1, max_lag + 1):
        out[lag - 1] = float(np.sum(values[:-lag] * values[lag:]) / denom)
    return out


def _ami(series: np.ndarray, max_lag: int, bins: int = 16) -> np.ndarray:
    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < max_lag + 2:
        return np.zeros(max_lag)
    vmin, vmax = float(values.min()), float(values.max())
    if vmin == vmax:
        return np.zeros(max_lag)
    edges = np.linspace(vmin, vmax, bins + 1)
    ami = np.zeros(max_lag)
    for lag in range(1, max_lag + 1):
        x = values[:-lag]
        y = values[lag:]
        hist2d, _, _ = np.histogram2d(x, y, bins=[edges, edges])
        pxy = hist2d / max(hist2d.sum(), 1.0)
        px = pxy.sum(axis=1, keepdims=True)
        py = pxy.sum(axis=0, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = pxy / (px @ py + 1e-12)
            mi = np.nansum(pxy * np.log(ratio + 1e-12))
        ami[lag - 1] = float(mi)
    return ami


def select_tau(series: np.ndarray, max_lag: int = 20, max_tau: int = 3, method: str = "ami") -> int:
    if method == "ami":
        scores = _ami(series, max_lag=max_lag, bins=16)
    else:
        scores = _autocorr(series, max_lag=max_lag)
    # Prefer first local minimum; fallback to global minimum; else 1.
    for i in range(1, len(scores) - 1):
        if scores[i] < scores[i - 1] and scores[i] < scores[i + 1]:
            return min(i + 1, max_tau)
    if len(scores) > 0:
        return min(int(np.argmin(scores)) + 1, max_tau)
    return min(1, max_tau)


def _fnn_fraction(series: np.ndarray, m: int, tau: int, r_tol: float, a_tol: float) -> float:
    from sklearn.neighbors import NearestNeighbors

    emb_m = takens_embed(series, m=m, tau=tau)
    emb_m1 = takens_embed(series, m=m + 1, tau=tau)
    n = emb_m1.shape[0]
    emb_m = emb_m[:n]

    nn = NearestNeighbors(n_neighbors=2, algorithm="auto")
    nn.fit(emb_m)
    distances, indices = nn.kneighbors(emb_m, return_distance=True)
    d_m = distances[:, 1]
    nbr = indices[:, 1]
    std = float(np.std(series)) if np.std(series) > 0 else 1.0

    delta = np.abs(emb_m1[:, -1] - emb_m1[nbr, -1]) / (d_m + 1e-12)
    d_m1 = np.linalg.norm(emb_m1 - emb_m1[nbr], axis=1)
    false = (delta > r_tol) | ((d_m1 / std) > a_tol)
    return float(np.mean(false))


def _cao_e1(series: np.ndarray, m: int, tau: int) -> float:
    from sklearn.neighbors import NearestNeighbors

    emb_m = takens_embed(series, m=m, tau=tau)
    emb_m1 = takens_embed(series, m=m + 1, tau=tau)
    n = emb_m1.shape[0]
    emb_m = emb_m[:n]
    nn = NearestNeighbors(n_neighbors=2, algorithm="auto")
    nn.fit(emb_m)
    distances, indices = nn.kneighbors(emb_m, return_distance=True)
    nbr = indices[:, 1]
    d_m = distances[:, 1] + 1e-12
    d_m1 = np.linalg.norm(emb_m1 - emb_m1[nbr], axis=1) + 1e-12
    return float(np.mean(d_m1 / d_m))


def select_m(series: np.ndarray, tau: int, max_m: int = 6, threshold: float = 0.15, method: str = "cao") -> int:
    if method == "cao":
        prev = None
        for m in range(2, max_m + 1):
            e1 = _cao_e1(series, m=m, tau=tau)
            if prev is not None and abs(e1 - prev) < 0.01:
                return min(m, max_m)
            prev = e1
        return max_m
    for m in range(2, max_m + 1):
        frac = _fnn_fraction(series, m=m, tau=tau, r_tol=10.0, a_tol=2.0)
        if frac <= threshold:
            return min(m, max_m)
    return max_m


def estimate_embedding_params(
    series: np.ndarray,
    max_tau: int = 20,
    max_m: int = 6,
    tau_method: str = "ami",
    m_method: str = "cao",
) -> Tuple[int, int]:
    tau = select_tau(series, max_lag=max_tau, max_tau=min(3, max_tau), method=tau_method)
    m = select_m(series, tau=tau, max_m=min(4, max_m), method=m_method)
    return m, tau


def takens_embed(series: np.ndarray, m: int, tau: int) -> np.ndarray:
    values = np.asarray(series, dtype=float)
    if values.ndim != 1:
        raise ValueError("series must be 1-D")
    min_len = (m - 1) * tau + 1
    if values.size < min_len:
        raise ValueError("series too short for embedding")
    embed_len = values.size - (m - 1) * tau
    columns = [
        values[(m - 1 - lag) * tau : (m - 1 - lag) * tau + embed_len]
        for lag in range(m)
    ]
    return np.column_stack(columns)
