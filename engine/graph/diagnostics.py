from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import pairwise_distances

from .embedding import takens_embed

try:  # optional dependency
    import ruptures as rpt
except Exception:  # pragma: no cover
    rpt = None

def _subsample(values: np.ndarray, max_points: int = 800) -> np.ndarray:
    if values.size <= max_points:
        return values
    idx = np.linspace(0, values.size - 1, max_points).astype(int)
    return values[idx]


def _ami_adaptive(series: np.ndarray, max_lag: int, bins: int = 16) -> np.ndarray:
    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < max_lag + 2:
        return np.zeros(max_lag)
    qs = np.linspace(0.0, 1.0, bins + 1)
    edges = np.quantile(values, qs)
    if np.unique(edges).size < bins + 1:
        edges = np.linspace(float(values.min()), float(values.max()), bins + 1)
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


def estimate_tau_adaptive(series: np.ndarray, max_lag: int = 20) -> Tuple[int, Dict[str, Any]]:
    scores = _ami_adaptive(series, max_lag=max_lag, bins=16)
    tau = 1
    for i in range(1, len(scores) - 1):
        if scores[i] < scores[i - 1] and scores[i] < scores[i + 1]:
            tau = i + 1
            break
    else:
        if len(scores) > 0:
            tau = int(np.argmin(scores)) + 1
    return tau, {"ami": scores.tolist(), "tau": int(tau)}


def _cao_metrics(series: np.ndarray, tau: int, max_dim: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    values = np.asarray(series, dtype=float)
    e1 = []
    e2 = []
    for m in range(1, max_dim):
        emb_m = takens_embed(values, m=m, tau=tau)
        emb_m1 = takens_embed(values, m=m + 1, tau=tau)
        n = min(emb_m.shape[0], emb_m1.shape[0])
        emb_m = emb_m[:n]
        emb_m1 = emb_m1[:n]
        nn = NearestNeighbors(n_neighbors=2, algorithm="auto")
        nn.fit(emb_m)
        distances, indices = nn.kneighbors(emb_m, return_distance=True)
        nbr = indices[:, 1]
        d_m = distances[:, 1] + 1e-12
        d_m1 = np.linalg.norm(emb_m1 - emb_m1[nbr], axis=1) + 1e-12
        e1.append(float(np.mean(d_m1 / d_m)))
        # Cao E2 approximation: mean difference of added component
        added = np.abs(emb_m1[:, -1] - emb_m1[nbr, -1]) + 1e-12
        prev = np.abs(emb_m[:, -1] - emb_m[nbr, -1]) + 1e-12
        e2.append(float(np.mean(added / prev)))
    return np.asarray(e1), np.asarray(e2)


def estimate_embedding_dim(series: np.ndarray, tau: int, max_dim: int = 10) -> Dict[str, Any]:
    e1, e2 = _cao_metrics(series, tau=tau, max_dim=max_dim)
    m_opt = 3
    if e1.size > 2:
        for i in range(1, len(e1)):
            if abs(e1[i] - e1[i - 1]) < 0.01:
                m_opt = i + 1
                break
    e2_std = float(np.std(e2)) if e2.size else 0.0
    is_random = bool(e2.size > 0 and e2_std < 0.01)
    return {
        "m_opt": int(m_opt),
        "e1": e1.tolist(),
        "e2": e2.tolist(),
        "is_random": is_random,
        "e2_std": e2_std,
    }


def estimate_lle_rosenstein(embedded: np.ndarray, theiler: int = 10, max_t: int = 20) -> Dict[str, Any]:
    n = embedded.shape[0]
    if n < max_t + 5:
        return {"lle": float("nan"), "ftle_recent": float("nan")}
    nn = NearestNeighbors(n_neighbors=10, algorithm="auto")
    nn.fit(embedded)
    distances, indices = nn.kneighbors(embedded, return_distance=True)
    neighbors = []
    for i in range(n):
        cand = indices[i, 1:]
        j = None
        for c in cand:
            if abs(int(c) - i) > theiler:
                j = int(c)
                break
        if j is None:
            continue
        neighbors.append((i, j))
    if len(neighbors) < 10:
        return {"lle": float("nan"), "ftle_recent": float("nan")}

    max_t = min(max_t, n - 1)
    div = np.zeros(max_t)
    counts = np.zeros(max_t)
    for i, j in neighbors:
        max_k = min(max_t, n - max(i, j) - 1)
        if max_k <= 1:
            continue
        for k in range(1, max_k):
            d0 = np.linalg.norm(embedded[i] - embedded[j]) + 1e-12
            d1 = np.linalg.norm(embedded[i + k] - embedded[j + k]) + 1e-12
            div[k] += np.log(d1 / d0)
            counts[k] += 1
    valid = counts > 0
    if not np.any(valid):
        return {"lle": float("nan"), "ftle_recent": float("nan")}
    y = div[valid] / counts[valid]
    x = np.arange(len(y))
    fit_len = min(10, len(y))
    if fit_len < 2:
        lle = float("nan")
    else:
        coeff = np.polyfit(x[:fit_len], y[:fit_len], 1)[0]
        lle = float(coeff)

    # FTLE recent (short horizon)
    h = min(5, max_t - 1)
    ftle_vals = []
    for i, j in neighbors:
        if i + h >= n or j + h >= n:
            continue
        d0 = np.linalg.norm(embedded[i] - embedded[j]) + 1e-12
        d1 = np.linalg.norm(embedded[i + h] - embedded[j + h]) + 1e-12
        ftle_vals.append(float(np.log(d1 / d0) / max(h, 1)))
    ftle_recent = float(np.mean(ftle_vals)) if ftle_vals else float("nan")
    return {"lle": lle, "ftle_recent": ftle_recent}


def _rqa_metrics(embedded: np.ndarray, max_points: int = 600) -> Dict[str, float]:
    if embedded.shape[0] > max_points:
        idx = np.linspace(0, embedded.shape[0] - 1, max_points).astype(int)
        data = embedded[idx]
    else:
        data = embedded
    if data.shape[0] < 10:
        return {"det": float("nan"), "lam": float("nan"), "tt": float("nan")}
    dist = pairwise_distances(data)
    eps = np.quantile(dist, 0.1)
    R = (dist <= eps).astype(int)
    np.fill_diagonal(R, 0)
    total_rec = float(R.sum())
    if total_rec == 0:
        return {"det": 0.0, "lam": 0.0, "tt": 0.0}

    # Diagonal lines
    det_count = 0
    for k in range(-R.shape[0] + 1, R.shape[0]):
        diag = np.diag(R, k=k)
        run = 0
        for v in diag:
            if v:
                run += 1
            else:
                if run >= 2:
                    det_count += run
                run = 0
        if run >= 2:
            det_count += run
    det = det_count / total_rec

    # Vertical lines
    lam_count = 0
    vert_lengths = []
    for col in range(R.shape[1]):
        run = 0
        for v in R[:, col]:
            if v:
                run += 1
            else:
                if run >= 2:
                    lam_count += run
                    vert_lengths.append(run)
                run = 0
        if run >= 2:
            lam_count += run
            vert_lengths.append(run)
    lam = lam_count / total_rec
    tt = float(np.mean(vert_lengths)) if vert_lengths else 0.0
    return {"det": float(det), "lam": float(lam), "tt": float(tt)}


def _intrinsic_dim_twonn(embedded: np.ndarray) -> float:
    if embedded.shape[0] < 10:
        return float("nan")
    nn = NearestNeighbors(n_neighbors=3, algorithm="auto")
    nn.fit(embedded)
    distances, _ = nn.kneighbors(embedded, return_distance=True)
    r1 = distances[:, 1] + 1e-12
    r2 = distances[:, 2] + 1e-12
    ratios = np.log(r2 / r1)
    if not np.isfinite(ratios).any():
        return float("nan")
    mean_ratio = float(np.nanmean(ratios))
    if mean_ratio <= 1e-12:
        return float("nan")
    return float(1.0 / mean_ratio)


def _anisotropy_score(embedded: np.ndarray) -> float:
    if embedded.shape[0] < 5:
        return float("nan")
    cov = np.cov(embedded.T)
    if cov.ndim != 2:
        return float("nan")
    vals = np.linalg.eigvalsh(cov)
    vals = np.sort(vals)[::-1]
    if vals.size < 2:
        return float("nan")
    return float(vals[0] / max(vals[1], 1e-12))


def _zero_one_test(series: np.ndarray, n_c: int = 5) -> float:
    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 100:
        return float("nan")
    max_len = 2000
    if values.size > max_len:
        idx = np.linspace(0, values.size - 1, max_len).astype(int)
        values = values[idx]
    n = values.size
    t = np.arange(n)
    ks = []
    rng = np.random.default_rng(7)
    for _ in range(n_c):
        c = rng.uniform(0.1, 2.9)
        p = np.cumsum(values * np.cos(c * t))
        q = np.cumsum(values * np.sin(c * t))
        m = (p - p[0]) ** 2 + (q - q[0]) ** 2
        if np.std(m) < 1e-12:
            continue
        corr = np.corrcoef(t, m)[0, 1]
        ks.append(float(corr))
    if not ks:
        return float("nan")
    return float(np.clip(np.mean(ks), 0.0, 1.0))


def _safe_returns(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 3:
        return np.array([])
    if np.nanmin(values) <= 0:
        diffs = np.diff(values)
        return diffs[np.isfinite(diffs)]
    log_vals = np.log(values + 1e-12)
    diffs = np.diff(log_vals)
    return diffs[np.isfinite(diffs)]


def _rolling_ews(returns: np.ndarray, window: int = 60) -> dict[str, float]:
    if returns.size < max(20, window + 5):
        return {"ar1": float("nan"), "var": float("nan"), "skew": float("nan"), "kurt": float("nan"), "ar1_slope": float("nan"), "var_slope": float("nan")}
    w = min(window, max(20, returns.size // 3))
    metrics = []
    for i in range(w, returns.size + 1):
        seg = returns[i - w : i]
        if seg.size < 5:
            continue
        seg = seg - np.mean(seg)
        ar1 = np.corrcoef(seg[:-1], seg[1:])[0, 1] if seg.size > 2 else 0.0
        var = float(np.var(seg))
        skew = float(np.mean((seg / (np.std(seg) + 1e-12)) ** 3))
        kurt = float(np.mean((seg / (np.std(seg) + 1e-12)) ** 4))
        metrics.append((ar1, var, skew, kurt))
    if not metrics:
        return {"ar1": float("nan"), "var": float("nan"), "skew": float("nan"), "kurt": float("nan"), "ar1_slope": float("nan"), "var_slope": float("nan")}
    arr = np.asarray(metrics)
    latest = arr[-1]
    trend_len = min(10, arr.shape[0])
    x = np.arange(trend_len)
    ar1_slope = float(np.polyfit(x, arr[-trend_len:, 0], 1)[0]) if trend_len > 1 else float("nan")
    var_slope = float(np.polyfit(x, arr[-trend_len:, 1], 1)[0]) if trend_len > 1 else float("nan")
    return {
        "ar1": float(latest[0]),
        "var": float(latest[1]),
        "skew": float(latest[2]),
        "kurt": float(latest[3]),
        "ar1_slope": ar1_slope,
        "var_slope": var_slope,
    }


def _detect_change_points(values: np.ndarray, min_size: int = 30, model: str = "rbf") -> dict[str, Any]:
    data = np.asarray(values, dtype=float)
    data = data[np.isfinite(data)]
    if data.size < min_size * 2:
        return {"cpd_indices": [], "cpd_last_offset": None, "cpd_score": float("nan")}
    if rpt is not None:
        algo = rpt.Pelt(model=model, min_size=min_size, jump=1)
        bkpts = algo.fit(data).predict(pen=2.0 * np.log(len(data)))
        bkpts = [int(b) for b in bkpts if b < len(data)]
    else:
        scores = []
        for i in range(min_size, len(data) - min_size):
            pre = data[i - min_size : i]
            post = data[i : i + min_size]
            if pre.size < 5 or post.size < 5:
                continue
            score = abs(np.mean(post) - np.mean(pre)) + abs(np.var(post) - np.var(pre))
            scores.append((i, float(score)))
        scores.sort(key=lambda x: x[1], reverse=True)
        bkpts = []
        for idx, _ in scores[:5]:
            if all(abs(idx - b) > min_size for b in bkpts):
                bkpts.append(idx)
        bkpts.sort()
    last_offset = int(len(data) - bkpts[-1]) if bkpts else None
    score = float("nan")
    if bkpts:
        score = float(len(bkpts))
    return {"cpd_indices": bkpts, "cpd_last_offset": last_offset, "cpd_score": score}


def compute_diagnostics(
    series: np.ndarray,
    m: int,
    tau: int,
    theiler: int,
    max_points: int = 800,
) -> Dict[str, Any]:
    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < (m - 1) * tau + 10:
        return {"status": "insufficient"}
    sub = _subsample(values, max_points=max_points)
    tau_adapt, ami_info = estimate_tau_adaptive(sub, max_lag=min(20, sub.size // 4))
    cao_info = estimate_embedding_dim(sub, tau=tau, max_dim=min(10, max(3, m + 3)))
    emb = takens_embed(sub, m=m, tau=tau)
    lle_info = estimate_lle_rosenstein(emb, theiler=theiler, max_t=min(20, emb.shape[0] - 1))
    rqa = _rqa_metrics(emb)
    id_est = _intrinsic_dim_twonn(emb)
    anis = _anisotropy_score(emb)
    k_val = _zero_one_test(sub)
    returns = _safe_returns(values)
    ews = _rolling_ews(returns, window=min(80, max(20, returns.size // 4))) if returns.size else {}
    cpd_ret = _detect_change_points(returns, min_size=max(15, min(50, returns.size // 6))) if returns.size else {}
    cpd_price = _detect_change_points(values, min_size=max(20, min(80, values.size // 8))) if values.size else {}
    recent_window = min(252, values.size)
    cpd_recent = {}
    if recent_window >= 120:
        recent_slice = values[-recent_window:]
        cpd_recent = _detect_change_points(recent_slice, min_size=max(20, recent_window // 6))
    cpd = {
        "returns": cpd_ret,
        "price": cpd_price,
        "recent": cpd_recent,
        "cpd_last_offset": None,
    }
    offsets = []
    for source in (cpd_ret, cpd_price):
        if isinstance(source, dict):
            off = source.get("cpd_last_offset")
            if isinstance(off, (int, float)):
                offsets.append(int(off))
    if offsets:
        cpd["cpd_last_offset"] = int(min(offsets))

    structure_score = float(
        np.nanmean(
            [
                rqa.get("det", np.nan),
                rqa.get("lam", np.nan),
                1.0 - min(1.0, (id_est if np.isfinite(id_est) else 1.0) / max(2.0, m)),
                min(1.0, (anis if np.isfinite(anis) else 1.0) / 10.0),
                1.0 - abs(0.5 - (k_val if np.isfinite(k_val) else 0.5)),
            ]
        )
    )

    return {
        "status": "ok",
        "tau_adaptive": int(tau_adapt),
        "ami": ami_info.get("ami", []),
        "cao": cao_info,
        "lle": lle_info.get("lle", float("nan")),
        "ftle_recent": lle_info.get("ftle_recent", float("nan")),
        "rqa_det": rqa.get("det", float("nan")),
        "rqa_lam": rqa.get("lam", float("nan")),
        "rqa_tt": rqa.get("tt", float("nan")),
        "intrinsic_dim": id_est,
        "anisotropy": anis,
        "chaos_k": k_val,
        "structure_score": structure_score,
        "ews": ews,
        "cpd": cpd,
    }
