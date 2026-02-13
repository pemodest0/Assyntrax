from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np

from engine.graph.embedding import estimate_embedding_params, takens_embed

try:
    from sklearn.mixture import GaussianMixture
except Exception:  # pragma: no cover
    GaussianMixture = None


@dataclass
class MultilayerConfig:
    warmup_min: int = 260
    window_ref: int = 180
    window_cur: int = 120
    step: int = 5
    lambda_gap: float = 0.45
    ts_alert_z: float = 2.2
    ts_consensus_z: float = 1.8
    persist_window: int = 10
    persist_min: int = 4
    consensus_min: int = 1
    vol_window: int = 60
    cusum_window: int = 40
    hmm_window: int = 120
    vol_alert_z: float = 2.2
    cusum_alert_z: float = 2.2
    hmm_alert_z: float = 1.8


def _robust_z_online(values: np.ndarray, min_points: int = 25, eps: float = 1e-9) -> np.ndarray:
    out = np.full(values.shape, np.nan, dtype=float)
    for i in range(values.size):
        x = values[: i + 1]
        x = x[np.isfinite(x)]
        if x.size < min_points:
            continue
        med = float(np.median(x))
        mad = float(np.median(np.abs(x - med)))
        scale = 1.4826 * mad + eps
        out[i] = (values[i] - med) / scale
    return out


def _safe_returns(series: np.ndarray) -> np.ndarray:
    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 4:
        return np.array([], dtype=float)
    if float(np.nanmin(values)) <= 0.0:
        out = np.diff(values)
    else:
        out = np.diff(np.log(values + 1e-12))
    return out[np.isfinite(out)]


def _hankel(values: np.ndarray, L: int) -> np.ndarray:
    n = values.size
    k = n - L + 1
    if n < L + 2 or k <= 1:
        return np.empty((0, 0), dtype=float)
    return np.vstack([values[i : i + k] for i in range(L)])


def _omega_gd(beta: float) -> float:
    # Gavish-Donoho polynomial approximation for unknown sigma threshold:
    # tau* = omega(beta) * median(singular_values)
    b = float(np.clip(beta, 0.0, 1.0))
    return 0.56 * (b**3) - 0.95 * (b**2) + 1.82 * b + 1.43


def _gd_rank(svals: np.ndarray, beta: float) -> Tuple[int, float]:
    s = np.asarray(svals, dtype=float)
    s = s[np.isfinite(s)]
    if s.size == 0:
        return 1, 0.0
    tau = _omega_gd(beta) * float(np.median(s))
    rank = int(np.sum(s >= tau))
    rank = max(1, min(rank, s.size))
    return rank, float(tau)


def _subspace_metrics(
    ref_values: np.ndarray,
    cur_values: np.ndarray,
    l_ref: int,
    l_cur: int,
) -> Dict[str, float]:
    Xr = _hankel(ref_values, L=l_ref)
    Xc = _hankel(cur_values, L=l_cur)
    if Xr.size == 0 or Xc.size == 0:
        return {
            "d_proj": np.nan,
            "d_geo": np.nan,
            "gap_cur": np.nan,
            "rank_ref": np.nan,
            "rank_cur": np.nan,
            "tau_ref": np.nan,
            "tau_cur": np.nan,
        }

    ur, sr, _ = np.linalg.svd(Xr, full_matrices=False)
    uc, sc, _ = np.linalg.svd(Xc, full_matrices=False)
    beta_r = min(float(Xr.shape[0] / max(Xr.shape[1], 1)), 1.0)
    beta_c = min(float(Xc.shape[0] / max(Xc.shape[1], 1)), 1.0)
    rr, tau_r = _gd_rank(sr, beta=beta_r)
    rc, tau_c = _gd_rank(sc, beta=beta_c)

    rr = max(1, min(rr, ur.shape[1]))
    rc = max(1, min(rc, uc.shape[1]))
    r = min(rr, rc)
    Ur = ur[:, :r]
    Uc = uc[:, :r]

    S = Ur.T @ Uc
    g = np.linalg.svd(S, compute_uv=False)
    g = np.clip(g, -1.0, 1.0)
    theta = np.arccos(g)

    d_proj = float(np.sqrt(max(0.0, r - float(np.sum(g**2)))))
    d_geo = float(np.sqrt(float(np.sum(theta**2))))
    gap_cur = float(sc[0] / max(sc[1], 1e-9)) if sc.size > 1 else 1.0
    return {
        "d_proj": d_proj,
        "d_geo": d_geo,
        "gap_cur": gap_cur,
        "rank_ref": float(rr),
        "rank_cur": float(rc),
        "tau_ref": float(tau_r),
        "tau_cur": float(tau_c),
    }


def _rolling_std(values: np.ndarray, window: int) -> np.ndarray:
    out = np.full(values.shape, np.nan, dtype=float)
    if values.size < window:
        return out
    for i in range(window - 1, values.size):
        seg = values[i - window + 1 : i + 1]
        out[i] = float(np.std(seg))
    return out


def _cusum_abs(values: np.ndarray, window: int) -> np.ndarray:
    out = np.full(values.shape, np.nan, dtype=float)
    if values.size < window:
        return out
    mu = np.full(values.shape, np.nan, dtype=float)
    for i in range(window - 1, values.size):
        mu[i] = float(np.mean(values[i - window + 1 : i + 1]))
    pos = 0.0
    neg = 0.0
    for i, v in enumerate(values):
        m = mu[i] if np.isfinite(mu[i]) else 0.0
        pos = max(0.0, pos + (v - m))
        neg = max(0.0, neg - (v - m))
        out[i] = pos + neg
    return out


def _hmm_auditor(values: np.ndarray, window: int, step: int) -> np.ndarray:
    out = np.full(values.shape, np.nan, dtype=float)
    if values.size < window or GaussianMixture is None:
        return out
    for i in range(window - 1, values.size, max(1, step)):
        seg = values[i - window + 1 : i + 1]
        X = seg.reshape(-1, 1)
        try:
            gmm = GaussianMixture(n_components=2, covariance_type="full", random_state=7)
            gmm.fit(X)
            probs = gmm.predict_proba(X)
            states = np.argmax(probs, axis=1)
            switch_rate = float(np.mean(states[1:] != states[:-1])) if states.size > 1 else 0.0
            entropy = float(-np.mean(np.sum(probs * np.log(probs + 1e-12), axis=1)))
            out[i] = switch_rate + entropy
        except Exception:
            out[i] = np.nan
    return out


def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0))))


def _trailing_hits(values: np.ndarray, threshold: float, window: int) -> tuple[int, int]:
    x = np.asarray(values, dtype=float)
    finite_idx = np.where(np.isfinite(x))[0]
    if finite_idx.size == 0:
        return 0, 0
    take = finite_idx[-max(1, window) :]
    vals = x[take]
    flags = vals > threshold
    hits = int(np.sum(flags))
    max_run = 0
    run = 0
    for ok in flags:
        run = run + 1 if ok else 0
        if run > max_run:
            max_run = run
    return hits, max_run


def _layer0_observability(values: np.ndarray, cfg: MultilayerConfig) -> Dict[str, Any]:
    n = int(values.size)
    nan_ratio = float(np.mean(~np.isfinite(values))) if n else 1.0
    finite = values[np.isfinite(values)]
    var = float(np.var(finite)) if finite.size else 0.0
    ok = bool(n >= cfg.warmup_min and finite.size >= cfg.warmup_min and var > 1e-12)
    return {
        "ok": ok,
        "n_points": n,
        "nan_ratio": nan_ratio,
        "variance": var,
    }


def run_multilayer_engine(
    series: np.ndarray,
    timeframe: str = "daily",
    m_hint: int | None = None,
    tau_hint: int | None = None,
    cfg: MultilayerConfig | None = None,
) -> Dict[str, Any]:
    cfg = cfg or MultilayerConfig()
    returns = _safe_returns(np.asarray(series, dtype=float))
    layer0 = _layer0_observability(returns, cfg=cfg)
    if not layer0["ok"]:
        return {
            "status": "insufficient",
            "decision": {
                "label": "INCONCLUSIVE",
                "confidence": 0.0,
                "auditor_support": 0.0,
            },
            "layers": {"layer0": layer0},
        }

    # Layer 1: PSR (Takens-based) + stochastic robustness proxy (Stark context).
    if m_hint is None or tau_hint is None:
        m_auto, tau_auto = estimate_embedding_params(
            returns,
            max_tau=20,
            max_m=6,
            tau_method="ami",
            m_method="cao",
        )
    else:
        m_auto, tau_auto = int(m_hint), int(tau_hint)
    m_use = max(2, int(m_auto))
    tau_use = max(1, int(tau_auto))
    emb = takens_embed(returns, m=m_use, tau=tau_use)
    noise_to_signal = float(np.var(np.diff(returns)) / max(np.var(returns), 1e-12))
    layer1 = {
        "m": m_use,
        "tau": tau_use,
        "embedding_points": int(emb.shape[0]),
        "noise_to_signal": noise_to_signal,
        "stark_context": "forced/noisy dynamics handled via robustness gates",
    }

    # Layer 2/3: adaptive spectral windows + Grassmann distances.
    n = returns.size
    d_proj = np.full(n, np.nan, dtype=float)
    d_geo = np.full(n, np.nan, dtype=float)
    gap = np.full(n, np.nan, dtype=float)
    rank_ref = np.full(n, np.nan, dtype=float)
    rank_cur = np.full(n, np.nan, dtype=float)

    # Weekly can use shorter windows due lower sample density.
    w_ref = cfg.window_ref if timeframe == "daily" else max(90, cfg.window_ref // 2)
    w_cur = cfg.window_cur if timeframe == "daily" else max(60, cfg.window_cur // 2)
    # Trajectory matrix size tied to embedding dimension.
    l_ref = int(np.clip(3 * m_use, 8, max(12, w_ref // 3)))
    l_cur = int(np.clip(3 * m_use, 8, max(12, w_cur // 3)))

    for t in range(w_ref + w_cur - 1, n, max(1, cfg.step)):
        ref_seg = returns[t - w_ref - w_cur + 1 : t - w_cur + 1]
        cur_seg = returns[t - w_cur + 1 : t + 1]
        met = _subspace_metrics(ref_seg, cur_seg, l_ref=l_ref, l_cur=l_cur)
        d_proj[t] = met["d_proj"]
        d_geo[t] = met["d_geo"]
        gap[t] = met["gap_cur"]
        rank_ref[t] = met["rank_ref"]
        rank_cur[t] = met["rank_cur"]

    z_geo = _robust_z_online(d_proj)
    z_gap = _robust_z_online(gap)
    ts = z_geo + cfg.lambda_gap * z_gap

    # Layer 4: auditors.
    vol_sig = _robust_z_online(_rolling_std(returns, window=cfg.vol_window))
    cusum_sig = _robust_z_online(_cusum_abs(returns, window=cfg.cusum_window))
    hmm_sig = _robust_z_online(_hmm_auditor(returns, window=cfg.hmm_window, step=max(1, cfg.step)))

    # Layer 5: fusion/decision.
    idx = int(n - 1)
    ts_last = float(ts[idx]) if np.isfinite(ts[idx]) else 0.0
    v_last = float(vol_sig[idx]) if np.isfinite(vol_sig[idx]) else 0.0
    c_last = float(cusum_sig[idx]) if np.isfinite(cusum_sig[idx]) else 0.0
    h_last = float(hmm_sig[idx]) if np.isfinite(hmm_sig[idx]) else 0.0

    struct_prob = _sigmoid((ts_last - cfg.ts_alert_z) / 1.1)

    ts_hits, ts_max_run = _trailing_hits(ts, threshold=cfg.ts_alert_z, window=cfg.persist_window)
    eigen_persist_ok = bool(ts_hits >= cfg.persist_min or ts_max_run >= cfg.persist_min)

    flag_vol = bool(v_last > cfg.vol_alert_z)
    flag_cusum = bool(c_last > cfg.cusum_alert_z)
    flag_hmm = bool(h_last > cfg.hmm_alert_z)
    flags = int(flag_vol) + int(flag_cusum) + int(flag_hmm)
    auditor_support = flags / 3.0
    consensus_ok = bool(flags >= cfg.consensus_min)

    # Hardened decision gate:
    # alert only if structural score persists AND at least partial baseline consensus exists.
    alert_triggered = bool(eigen_persist_ok and consensus_ok and ts_last >= cfg.ts_consensus_z)
    confidence = float(np.clip(0.60 * struct_prob + 0.25 * auditor_support + (0.15 if alert_triggered else 0.0), 0.0, 1.0))

    if noise_to_signal > 2.2 and not alert_triggered and struct_prob < 0.55 and auditor_support < 0.34:
        label = "NOISY"
    elif alert_triggered and struct_prob >= 0.55:
        label = "UNSTABLE"
    elif struct_prob < 0.35 and flags == 0:
        label = "STABLE"
    else:
        label = "TRANSITION"

    reasons = []
    if ts_last > cfg.ts_alert_z:
        reasons.append("grassmann_rotation_high")
    if v_last > cfg.vol_alert_z:
        reasons.append("vol_auditor_high")
    if c_last > cfg.cusum_alert_z:
        reasons.append("cusum_auditor_high")
    if h_last > cfg.hmm_alert_z:
        reasons.append("hmm_auditor_high")
    if noise_to_signal > 2.2:
        reasons.append("high_noise_to_signal")
    if not eigen_persist_ok:
        reasons.append("eigen_not_persistent")
    if not consensus_ok:
        reasons.append("baseline_consensus_low")

    layer2 = {
        "trajectory_matrix": {
            "window_ref": int(w_ref),
            "window_cur": int(w_cur),
            "L_ref": int(l_ref),
            "L_cur": int(l_cur),
        },
        "rank_ref_last": float(rank_ref[idx]) if np.isfinite(rank_ref[idx]) else None,
        "rank_cur_last": float(rank_cur[idx]) if np.isfinite(rank_cur[idx]) else None,
    }
    layer3 = {
        "ts_last": ts_last,
        "d_proj_last": float(d_proj[idx]) if np.isfinite(d_proj[idx]) else None,
        "d_geo_last": float(d_geo[idx]) if np.isfinite(d_geo[idx]) else None,
        "gap_last": float(gap[idx]) if np.isfinite(gap[idx]) else None,
        "alert_z": float(cfg.ts_alert_z),
    }
    layer4 = {
        "vol_z_last": v_last,
        "cusum_z_last": c_last,
        "hmm_z_last": h_last,
        "vol_flag": flag_vol,
        "cusum_flag": flag_cusum,
        "hmm_flag": flag_hmm,
        "consensus_count": flags,
        "consensus_required": int(cfg.consensus_min),
        "support": auditor_support,
        "eigen_hits_window": int(ts_hits),
        "eigen_max_run_window": int(ts_max_run),
        "eigen_persist_ok": eigen_persist_ok,
        "alert_triggered": alert_triggered,
    }

    return {
        "status": "ok",
        "decision": {
            "label": label,
            "confidence": confidence,
            "auditor_support": auditor_support,
            "structural_probability": struct_prob,
            "alert_triggered": alert_triggered,
            "reasons": reasons,
        },
        "layers": {
            "layer0": layer0,
            "layer1": layer1,
            "layer2": layer2,
            "layer3": layer3,
            "layer4": layer4,
        },
    }
