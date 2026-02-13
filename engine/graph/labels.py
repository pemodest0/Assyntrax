from __future__ import annotations

from collections import defaultdict, deque

import numpy as np


def compute_confidence(p_matrix: np.ndarray, micro_regime: np.ndarray, micro_labels: np.ndarray) -> np.ndarray:
    conf = np.zeros_like(micro_labels, dtype=float)
    for i, state in enumerate(micro_labels):
        same = micro_regime == micro_regime[state]
        conf[i] = p_matrix[state, same].sum()
    return conf


def _largest_component_ratio(n_nodes: int, edges: list[tuple[int, int]]) -> float:
    if n_nodes == 0:
        return 0.0
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    visited = set()
    best = 0
    for i in range(n_nodes):
        if i in visited:
            continue
        q = deque([i])
        visited.add(i)
        size = 0
        while q:
            cur = q.popleft()
            size += 1
            for nxt in graph.get(cur, []):
                if nxt not in visited:
                    visited.add(nxt)
                    q.append(nxt)
        best = max(best, size)
    return best / max(n_nodes, 1)


def _stationary_distribution(p_matrix: np.ndarray, max_iter: int = 500, tol: float = 1e-8) -> np.ndarray:
    n = p_matrix.shape[0]
    if n == 0:
        return np.array([])
    pi = np.ones(n, dtype=float) / n
    for _ in range(max_iter):
        nxt = pi @ p_matrix
        if np.linalg.norm(nxt - pi, ord=1) < tol:
            pi = nxt
            break
        pi = nxt
    return pi / max(pi.sum(), 1e-12)


def _entropy_rate(p_matrix: np.ndarray, pi: np.ndarray) -> float:
    if p_matrix.size == 0 or pi.size == 0:
        return 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        logp = np.log(p_matrix + 1e-12)
    return float(-np.sum(pi[:, None] * p_matrix * logp))


def compute_graph_quality(
    n_nodes: int,
    edges: list[tuple[int, int]],
    occupancy: np.ndarray,
    p_matrix: np.ndarray,
    embedding_stats: dict[str, float],
) -> dict[str, float]:
    degrees = np.zeros(n_nodes, dtype=float)
    for a, b in edges:
        degrees[a] += 1
        degrees[b] += 1
    deg_low_frac = float(np.mean(degrees <= 1)) if n_nodes > 0 else 1.0

    lcc_ratio = _largest_component_ratio(n_nodes, edges)

    occ = occupancy / max(occupancy.sum(), 1.0)
    entropy = -np.sum(occ * np.log2(occ + 1e-12))
    entropy_norm = float(entropy / np.log2(len(occ) + 1e-12)) if len(occ) > 1 else 0.0

    coverage = float(np.mean(occupancy >= 3)) if len(occupancy) else 0.0

    edge_set = set()
    for a, b in edges:
        edge_set.add((a, b) if a <= b else (b, a))
    max_edges = n_nodes * (n_nodes - 1) / 2 if n_nodes > 1 else 1
    graph_density = float(len(edge_set) / max_edges)

    if p_matrix.size:
        active = np.count_nonzero(p_matrix > 0) - p_matrix.shape[0]
        active_edges = max(active, 0)
        active_edge_frac = float(active_edges / max(1, p_matrix.shape[0] * (p_matrix.shape[0] - 1)))
    else:
        active_edge_frac = 0.0

    pi = _stationary_distribution(p_matrix)
    entropy_rate = _entropy_rate(p_matrix, pi)

    quality = 0.35 * lcc_ratio + 0.2 * (1.0 - deg_low_frac) + 0.2 * entropy_norm + 0.15 * coverage + 0.1 * graph_density
    quality = float(np.clip(quality, 0.0, 1.0))

    return {
        "score": quality,
        "lcc_ratio": float(lcc_ratio),
        "deg_low_frac": float(deg_low_frac),
        "occupancy_entropy_norm": float(entropy_norm),
        "coverage": float(coverage),
        "graph_density": float(graph_density),
        "active_edge_frac": float(active_edge_frac),
        "entropy_rate": float(entropy_rate),
    }


def _median_filter(values: np.ndarray, window: int) -> np.ndarray:
    if window <= 1 or len(values) == 0:
        return values
    half = window // 2
    out = np.empty_like(values, dtype=float)
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        out[i] = float(np.median(values[lo:hi]))
    return out


def _hmm_smooth_labels(labels: list[str], noise: float = 0.05) -> list[str]:
    obs = np.asarray(labels, dtype=object)
    states = list(dict.fromkeys(obs.tolist()))
    if len(states) <= 1:
        return labels
    state_map = {s: i for i, s in enumerate(states)}
    inv_map = {i: s for s, i in state_map.items()}
    obs_idx = np.array([state_map[s] for s in obs], dtype=int)
    k = len(states)
    counts = np.ones((k, k), dtype=float) * 1e-3
    for a, b in zip(obs_idx[:-1], obs_idx[1:]):
        counts[a, b] += 1.0
    trans = counts / counts.sum(axis=1, keepdims=True)
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
    return [inv_map[int(s)] for s in path]


def compute_thresholds(
    escape: np.ndarray,
    stretch_mu: np.ndarray,
    stretch_frac_pos: np.ndarray,
    conf: np.ndarray,
    timeframe: str = "daily",
) -> dict[str, float]:
    # Auto-calibrated thresholds (quantiles) to avoid manual tuning.
    if timeframe == "daily":
        escape_lo_q = 0.50
        stretch_lo_q = 0.40
        conf_hi_q = 0.60
    else:
        escape_lo_q = 0.45
        stretch_lo_q = 0.35
        conf_hi_q = 0.70

    escape_lo = float(np.quantile(escape, escape_lo_q))
    escape_hi = float(np.quantile(escape, 0.80))
    stretch_lo = float(np.quantile(stretch_mu, stretch_lo_q))
    stretch_hi = float(np.quantile(stretch_mu, 0.75))
    frac_hi = float(np.quantile(stretch_frac_pos, 0.75))
    conf_lo = float(np.quantile(conf, 0.35))
    conf_hi = float(np.quantile(conf, conf_hi_q))
    return {
        "escape_lo": escape_lo,
        "escape_hi": escape_hi,
        "stretch_lo": stretch_lo,
        "stretch_hi": stretch_hi,
        "frac_hi": frac_hi,
        "conf_lo": conf_lo,
        "conf_hi": conf_hi,
    }


def label_state(conf: float, stretch_mu: float, escape: float, frac_pos: float, thresholds: dict[str, float]) -> str:
    if escape >= thresholds["escape_hi"] and (frac_pos >= thresholds["frac_hi"] or stretch_mu >= thresholds["stretch_hi"]):
        return "UNSTABLE"
    if escape <= thresholds["escape_lo"] and stretch_mu <= thresholds["stretch_lo"]:
        return "STABLE"
    return "TRANSITION"


def labels_for_series(
    conf: np.ndarray,
    stretch_mu: np.ndarray,
    stretch_frac_pos: np.ndarray,
    quality_score: float,
    noisy_threshold: float = 0.3,
    timeframe: str = "daily",
    smooth_method: str | None = None,
    smooth_noise: float = 0.05,
) -> tuple[np.ndarray, dict[str, float]]:
    conf_smoothed = _median_filter(conf, window=5)
    escape = 1.0 - conf_smoothed
    thresholds = compute_thresholds(escape, stretch_mu, stretch_frac_pos, conf_smoothed, timeframe=timeframe)
    labels = []
    for c, s, f in zip(conf_smoothed, stretch_mu, stretch_frac_pos):
        if quality_score < noisy_threshold:
            labels.append("NOISY")
        else:
            c_val = float(c)
            if c_val < thresholds["conf_lo"]:
                # Low confidence -> avoid STABLE classification.
                if (1.0 - c_val) >= thresholds["escape_hi"]:
                    labels.append("UNSTABLE")
                else:
                    labels.append("TRANSITION")
            else:
                labels.append(label_state(c_val, float(s), float(1.0 - c_val), float(f), thresholds))
    if smooth_method == "hmm":
        labels = _hmm_smooth_labels(labels, noise=smooth_noise)
    return np.asarray(labels), thresholds
