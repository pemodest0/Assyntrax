#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class Scenario:
    name: str
    has_shift: bool
    event_idx: int
    signal: np.ndarray  # univariate observable (proxy for returns)


def _robust_z(x: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    out = np.full_like(x, np.nan, dtype=float)
    for i in range(len(x)):
        h = x[: i + 1]
        h = h[np.isfinite(h)]
        if h.size < 10:
            continue
        med = float(np.median(h))
        mad = float(np.median(np.abs(h - med)))
        scale = 1.4826 * mad + eps
        out[i] = (x[i] - med) / scale
    return out


def _rolling_std(x: np.ndarray, w: int) -> np.ndarray:
    out = np.full_like(x, np.nan, dtype=float)
    for i in range(w - 1, len(x)):
        s = x[i - w + 1 : i + 1]
        out[i] = float(np.std(s))
    return out


def _cusum_abs(x: np.ndarray, w: int = 80) -> np.ndarray:
    mu = np.full_like(x, np.nan, dtype=float)
    for i in range(w - 1, len(x)):
        mu[i] = float(np.mean(x[i - w + 1 : i + 1]))
    pos = 0.0
    neg = 0.0
    out = np.zeros_like(x, dtype=float)
    for i, xi in enumerate(x):
        m = mu[i] if np.isfinite(mu[i]) else 0.0
        pos = max(0.0, pos + (xi - m))
        neg = max(0.0, neg - (xi - m))
        out[i] = pos + neg
    return out


def _perm_entropy(series: np.ndarray, order: int = 3) -> float:
    n = len(series)
    if n < order + 1:
        return float("nan")
    counts: dict[tuple[int, ...], int] = {}
    for i in range(n - order + 1):
        pat = tuple(np.argsort(series[i : i + order]))
        counts[pat] = counts.get(pat, 0) + 1
    probs = np.array(list(counts.values()), dtype=float)
    probs /= probs.sum()
    return float(-np.sum(probs * np.log(probs + 1e-12)))


def _rolling_perm_entropy(x: np.ndarray, w: int = 120, order: int = 3) -> np.ndarray:
    out = np.full_like(x, np.nan, dtype=float)
    for i in range(w - 1, len(x)):
        out[i] = _perm_entropy(x[i - w + 1 : i + 1], order=order)
    return out


def _hankel(x: np.ndarray, L: int) -> np.ndarray:
    k = len(x) - L + 1
    if k <= 1:
        return np.empty((0, 0), dtype=float)
    return np.column_stack([x[i : i + k] for i in range(L)])


def _ssa_rank90_signal(x: np.ndarray, w: int = 220, L: int = 48) -> np.ndarray:
    out = np.full_like(x, np.nan, dtype=float)
    prev_rank = None
    for i in range(w - 1, len(x)):
        s = x[i - w + 1 : i + 1]
        X = _hankel(s, min(L, max(8, len(s) // 3)))
        if X.size == 0:
            continue
        _, sv, _ = np.linalg.svd(X, full_matrices=False)
        if sv.size < 2:
            continue
        e = sv**2
        cum = np.cumsum(e) / max(float(e.sum()), 1e-12)
        rank = int(np.searchsorted(cum, 0.90) + 1)
        gap = float(sv[0] / max(sv[1], 1e-9))
        if prev_rank is None:
            prev_rank = rank
        out[i] = abs(rank - prev_rank) + abs(gap - 1.0)
        prev_rank = rank
    return out


def _build_multivariate_obs(x: np.ndarray, n_obs: int, rng: np.random.Generator) -> np.ndarray:
    n = len(x)
    obs = np.zeros((n, n_obs), dtype=float)
    for j in range(n_obs):
        lag = min(j, 12)
        shifted = np.roll(x, lag)
        shifted[:lag] = shifted[lag] if lag > 0 else shifted[0]
        noise = rng.normal(0.0, 0.2 + 0.04 * j, n)
        obs[:, j] = shifted + noise
    return obs


def _eigen_structural_signal(x: np.ndarray, rng: np.random.Generator, n_obs: int = 16, w_corr: int = 200) -> np.ndarray:
    obs = _build_multivariate_obs(x, n_obs=n_obs, rng=rng)
    n = len(x)
    ar = np.full(n, np.nan, dtype=float)
    ent = np.full(n, np.nan, dtype=float)
    gap = np.full(n, np.nan, dtype=float)
    k = max(1, int(round(0.2 * n_obs)))
    for i in range(w_corr - 1, n):
        S = obs[i - w_corr + 1 : i + 1, :]
        C = np.corrcoef(S, rowvar=False)
        vals = np.linalg.eigvalsh(C)
        vals = np.sort(np.maximum(vals, 1e-12))[::-1]
        p = vals / max(vals.sum(), 1e-12)
        ar[i] = float(np.sum(vals[:k]) / max(np.sum(vals), 1e-12))
        ent[i] = float(-np.sum(p * np.log(p + 1e-12)))
        gap[i] = float(vals[0] / max(vals[1], 1e-9)) if vals.size > 1 else 1.0
    z_ar = _robust_z(ar)
    z_ent = _robust_z(-ent)
    z_gap = _robust_z(gap)
    return np.nan_to_num(z_ar) + np.nan_to_num(z_ent) + np.nan_to_num(z_gap)


def _ffill(values: np.ndarray) -> np.ndarray:
    out = np.asarray(values, dtype=float).copy()
    for i in range(1, out.size):
        if not np.isfinite(out[i]) and np.isfinite(out[i - 1]):
            out[i] = out[i - 1]
    return out


def _garch_filter(x: np.ndarray, omega: float, alpha: float, beta: float) -> tuple[np.ndarray, np.ndarray]:
    vals = np.asarray(x, dtype=float)
    n = vals.size
    var = np.zeros(n, dtype=float)
    var[0] = max(float(np.var(vals[: min(30, n)])), 1e-8)
    for t in range(1, n):
        var[t] = omega + alpha * (vals[t - 1] ** 2) + beta * var[t - 1]
        if var[t] <= 1e-12:
            var[t] = 1e-12
    z = vals / np.sqrt(var + 1e-12)
    return z, var


def _fit_garch11_grid(train: np.ndarray) -> tuple[float, float, float]:
    vals = np.asarray(train, dtype=float)
    base_var = max(float(np.var(vals)), 1e-8)
    best = None
    # compact grid to keep PTBP runtime reasonable
    for alpha in (0.02, 0.05, 0.08, 0.12, 0.16):
        for beta in (0.70, 0.78, 0.85, 0.90, 0.94):
            if alpha + beta >= 0.995:
                continue
            omega = max(1e-10, base_var * (1.0 - alpha - beta))
            _, var = _garch_filter(vals, omega=omega, alpha=alpha, beta=beta)
            nll = 0.5 * np.sum(np.log(var + 1e-12) + (vals**2) / (var + 1e-12))
            score = float(nll)
            if best is None or score < best[0]:
                best = (score, omega, alpha, beta)
    if best is None:
        return max(1e-10, 0.05 * base_var), 0.08, 0.90
    return float(best[1]), float(best[2]), float(best[3])


def _garch_lr_signal(x: np.ndarray, train_w: int = 260, test_w: int = 90, step: int = 5) -> np.ndarray:
    n = len(x)
    raw = np.full(n, np.nan, dtype=float)
    start = train_w + test_w - 1
    for i in range(start, n, max(1, step)):
        train = x[i - train_w - test_w + 1 : i - test_w + 1]
        test = x[i - test_w + 1 : i + 1]
        if train.size < 80 or test.size < 30:
            continue
        omega, alpha, beta = _fit_garch11_grid(train)
        combo = np.concatenate([train, test])
        z_all, _ = _garch_filter(combo, omega=omega, alpha=alpha, beta=beta)
        z = z_all[-test_w:]
        n1 = test_w // 2
        n2 = test_w - n1
        s_pool = float(np.var(z, ddof=1) + 1e-12)
        s1 = float(np.var(z[:n1], ddof=1) + 1e-12)
        s2 = float(np.var(z[n1:], ddof=1) + 1e-12)
        # LR for variance break between two halves.
        lr = test_w * np.log(s_pool) - n1 * np.log(s1) - n2 * np.log(s2)
        raw[i] = float(max(0.0, lr))
    raw = _ffill(raw)
    return _robust_z(raw)


def _rmt_gate_signal(x: np.ndarray, rng: np.random.Generator, n_obs: int = 18, w_corr: int = 220, step: int = 3) -> np.ndarray:
    obs = _build_multivariate_obs(x, n_obs=n_obs, rng=rng)
    n = len(x)
    raw = np.full(n, np.nan, dtype=float)
    q = float(n_obs / max(w_corr, 1))
    lambda_max_mp = float((1.0 + np.sqrt(max(q, 1e-12))) ** 2)
    for i in range(w_corr - 1, n, max(1, step)):
        S = obs[i - w_corr + 1 : i + 1, :]
        C = np.corrcoef(S, rowvar=False)
        vals = np.linalg.eigvalsh(C)
        vals = np.sort(np.maximum(vals, 1e-12))[::-1]
        top = float(vals[0]) if vals.size else 1.0
        outband = float(np.mean(vals > lambda_max_mp)) if vals.size else 0.0
        excess = float(np.sum(np.maximum(vals - lambda_max_mp, 0.0)))
        ratio = max(0.0, top / max(lambda_max_mp, 1e-12) - 1.0)
        raw[i] = ratio + outband + excess / max(float(np.sum(np.abs(vals))), 1e-12)
    raw = _ffill(raw)
    return _robust_z(raw)


def _rolling_count_above(sig: np.ndarray, threshold: float, window: int) -> np.ndarray:
    x = np.asarray(sig, dtype=float)
    out = np.zeros_like(x, dtype=float)
    w = max(1, int(window))
    for i in range(x.size):
        j0 = max(0, i - w + 1)
        seg = x[j0 : i + 1]
        seg = seg[np.isfinite(seg)]
        out[i] = float(np.sum(seg > threshold))
    return out


def _harden_structural_signal(
    eigen_sig: np.ndarray,
    baseline_sigs: list[np.ndarray],
    eigen_thr: float = 2.2,
    baseline_thr: float = 2.0,
    persist_window: int = 10,
    persist_min: int = 4,
    consensus_min: int = 1,
) -> np.ndarray:
    e = _ffill(eigen_sig)
    persist = _rolling_count_above(e, threshold=eigen_thr, window=persist_window) >= persist_min
    n = e.size
    consensus = np.zeros(n, dtype=int)
    for b in baseline_sigs:
        bb = _ffill(b)
        consensus += np.where(np.isfinite(bb) & (bb > baseline_thr), 1, 0)
    ok = persist & (consensus >= int(consensus_min))
    out = np.full_like(e, np.nan, dtype=float)
    out[ok] = e[ok]
    return out


def _rmt_secondary_signal(
    rmt_sig: np.ndarray,
    eigen_hardened_sig: np.ndarray,
    rmt_thr: float = 2.6,
    eigen_gate_thr: float = 1.6,
    persist_window: int = 12,
    persist_min: int = 4,
) -> np.ndarray:
    r = _ffill(rmt_sig)
    e = _ffill(eigen_hardened_sig)
    persist = _rolling_count_above(r, threshold=rmt_thr, window=persist_window) >= persist_min
    gate = np.isfinite(e) & (e > eigen_gate_thr)
    ok = persist & gate
    out = np.full_like(r, np.nan, dtype=float)
    out[ok] = 0.75 * r[ok]
    return out


def _snr_add_noise(signal: np.ndarray, snr_db: float, rng: np.random.Generator) -> np.ndarray:
    p_sig = float(np.var(signal))
    p_noise = p_sig / (10 ** (snr_db / 10.0))
    noise = rng.normal(0.0, math.sqrt(max(p_noise, 1e-12)), size=signal.shape[0])
    return signal + noise


def _simulate_lorenz(n: int, seed: int, has_shift: bool) -> Scenario:
    rng = np.random.default_rng(seed)
    dt = 0.01
    sigma = 10.0
    beta = 8.0 / 3.0
    x = np.zeros(n, dtype=float)
    y = np.zeros(n, dtype=float)
    z = np.zeros(n, dtype=float)
    x[0], y[0], z[0] = 1.0, 1.0, 1.0
    t0 = int(0.4 * n)
    t1 = int(0.6 * n)
    ev = (t0 + t1) // 2
    for t in range(1, n):
        if has_shift and t0 <= t <= t1:
            rho = 22.0 + 4.0 * ((t - t0) / max(1, (t1 - t0)))
        else:
            rho = 22.0 if not has_shift else 26.0
        dx = sigma * (y[t - 1] - x[t - 1])
        dy = x[t - 1] * (rho - z[t - 1]) - y[t - 1]
        dz = x[t - 1] * y[t - 1] - beta * z[t - 1]
        x[t] = x[t - 1] + dt * dx
        y[t] = y[t - 1] + dt * dy
        z[t] = z[t - 1] + dt * dz
    obs = np.diff(x, prepend=x[0])
    obs += rng.normal(0.0, 0.01, n)
    return Scenario(name=f"lorenz_{'shift' if has_shift else 'stable'}", has_shift=has_shift, event_idx=ev, signal=obs)


def _simulate_rossler(n: int, seed: int, has_shift: bool) -> Scenario:
    rng = np.random.default_rng(seed)
    dt = 0.02
    a, b = 0.2, 0.2
    x = np.zeros(n, dtype=float)
    y = np.zeros(n, dtype=float)
    z = np.zeros(n, dtype=float)
    x[0], y[0], z[0] = 0.1, 0.0, 0.0
    t0 = int(0.4 * n)
    t1 = int(0.6 * n)
    ev = (t0 + t1) // 2
    for t in range(1, n):
        if has_shift and t0 <= t <= t1:
            c = 2.5 + 2.5 * ((t - t0) / max(1, (t1 - t0)))
        else:
            c = 2.5 if not has_shift else 5.0
        dx = -y[t - 1] - z[t - 1]
        dy = x[t - 1] + a * y[t - 1]
        dz = b + z[t - 1] * (x[t - 1] - c)
        x[t] = x[t - 1] + dt * dx
        y[t] = y[t - 1] + dt * dy
        z[t] = z[t - 1] + dt * dz
    obs = np.diff(x, prepend=x[0])
    obs += rng.normal(0.0, 0.01, n)
    return Scenario(name=f"rossler_{'shift' if has_shift else 'stable'}", has_shift=has_shift, event_idx=ev, signal=obs)


def _simulate_mackey_glass(n: int, seed: int, has_shift: bool) -> Scenario:
    rng = np.random.default_rng(seed)
    beta, gamma, p = 0.2, 0.1, 10
    t0 = int(0.4 * n)
    t1 = int(0.6 * n)
    ev = (t0 + t1) // 2
    x = np.full(n + 300, 1.2, dtype=float)
    for t in range(300, n + 300 - 1):
        idx = t - 300
        if has_shift and t0 <= idx <= t1:
            delta = int(round(15 + 5 * ((idx - t0) / max(1, (t1 - t0)))))
        else:
            delta = 15 if not has_shift else 20
        xd = x[t - delta]
        x[t + 1] = x[t] + (beta * xd / (1 + xd**p) - gamma * x[t])
    raw = x[300 : 300 + n]
    obs = np.diff(raw, prepend=raw[0])
    obs += rng.normal(0.0, 0.01, n)
    return Scenario(name=f"mackey_glass_{'shift' if has_shift else 'stable'}", has_shift=has_shift, event_idx=ev, signal=obs)


def _signal_dict(x: np.ndarray, seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    raw_eigen = _eigen_structural_signal(x, rng=rng)
    raw_garch = _garch_lr_signal(x)
    raw_rmt = _rmt_gate_signal(x, rng=rng)
    raw_vol = _robust_z(_rolling_std(x, w=120))
    raw_cusum = _robust_z(_cusum_abs(x, w=80))
    raw_perm = _robust_z(_rolling_perm_entropy(x, w=120, order=3))
    raw_ssa = _robust_z(_ssa_rank90_signal(x, w=220, L=48))

    # Hardened structural detector:
    # eigen alert requires persistence + partial baseline consensus.
    hardened_eigen = _harden_structural_signal(
        raw_eigen,
        baseline_sigs=[raw_vol, raw_cusum, raw_garch],
        eigen_thr=2.2,
        baseline_thr=2.0,
        persist_window=10,
        persist_min=4,
        consensus_min=1,
    )

    # RMT is demoted to secondary auditor, gated by hardened eigen context.
    rmt_secondary = _rmt_secondary_signal(
        raw_rmt,
        eigen_hardened_sig=hardened_eigen,
        rmt_thr=2.6,
        eigen_gate_thr=1.6,
        persist_window=12,
        persist_min=4,
    )

    return {
        "eigen": hardened_eigen,
        "garch_lr": raw_garch,
        "rmt_gate": rmt_secondary,
        "vol": raw_vol,
        "cusum": raw_cusum,
        "perm_entropy": raw_perm,
        "ssa90": raw_ssa,
    }


def _first_detection(sig: np.ndarray, event_idx: int, train_cut: int = 1000, q: float = 4.5) -> int | None:
    pre = sig[: max(train_cut, int(0.3 * event_idx))]
    pre = pre[np.isfinite(pre)]
    if pre.size < 30:
        return None
    med = float(np.median(pre))
    mad = float(np.median(np.abs(pre - med)))
    thr = med + q * (1.4826 * mad + 1e-9)
    idx = np.where(np.isfinite(sig) & (sig > thr))[0]
    return int(idx[0]) if idx.size else None


def _max_drawdown(returns: np.ndarray) -> float:
    wealth = np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(wealth)
    dd = wealth / np.maximum(peak, 1e-12) - 1.0
    return float(np.min(dd))


def _evaluate(
    scenarios: list[Scenario],
    signals: dict[str, list[np.ndarray]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for i, sc in enumerate(scenarios):
        x = sc.signal
        for model, model_sigs in signals.items():
            sig = model_sigs[i]
            det = _first_detection(sig, sc.event_idx)
            lead = (sc.event_idx - det) if det is not None else None
            post_slice = slice(det, min(len(x), (det or 0) + 350)) if det is not None else slice(0, 0)
            cdar = _max_drawdown(x[post_slice]) if det is not None and (post_slice.stop - post_slice.start) > 10 else np.nan
            rows.append(
                {
                    "scenario": sc.name,
                    "has_shift": sc.has_shift,
                    "model": model,
                    "event_idx": sc.event_idx,
                    "det_idx": det,
                    "lead_time": lead,
                    "alerted": det is not None,
                    "cdar_proxy": cdar,
                }
            )
    detail = pd.DataFrame(rows)
    agg = (
        detail.groupby(["model", "has_shift"], as_index=False)
        .agg(
            n=("scenario", "count"),
            alert_rate=("alerted", "mean"),
            lead_mean=("lead_time", "mean"),
            lead_median=("lead_time", "median"),
            lead_pos_rate=("lead_time", lambda s: float(np.mean(s.dropna() > 0)) if s.notna().any() else np.nan),
            cdar_mean=("cdar_proxy", "mean"),
        )
        .sort_values(["model", "has_shift"])
    )
    return detail, agg


def _clean_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    v = float(value)
    if not np.isfinite(v):
        return None
    return v


def _wilson_ci(p: float | None, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if p is None or n <= 0:
        return None, None
    pp = float(np.clip(p, 0.0, 1.0))
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (pp + z2 / (2.0 * n)) / denom
    half = z * math.sqrt((pp * (1.0 - pp) + z2 / (4.0 * n)) / n) / denom
    return float(max(0.0, center - half)), float(min(1.0, center + half))


def _mean_ci95(values: np.ndarray) -> tuple[float | None, float | None]:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return None, None
    if x.size == 1:
        v = float(x[0])
        return v, v
    mu = float(np.mean(x))
    se = float(np.std(x, ddof=1) / math.sqrt(x.size))
    half = 1.96 * se
    return mu - half, mu + half


def _build_scenarios(n: int, runs: int, snr_db: float, seed: int) -> list[Scenario]:
    out: list[Scenario] = []
    makers: list[Callable[[int, int, bool], Scenario]] = [_simulate_lorenz, _simulate_rossler, _simulate_mackey_glass]
    for r in range(runs):
        for mk in makers:
            for has_shift in (False, True):
                sc = mk(n=n, seed=seed + r * 100 + (11 if has_shift else 3), has_shift=has_shift)
                rng = np.random.default_rng(seed + r * 1000 + (41 if has_shift else 17))
                noisy = _snr_add_noise(sc.signal, snr_db=snr_db, rng=rng)
                out.append(Scenario(name=f"{sc.name}_r{r}", has_shift=has_shift, event_idx=sc.event_idx, signal=noisy))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="PTBP benchmark for Assyntrax Eigen Engine")
    p.add_argument("--outdir", default="results/benchmarks/ptbp")
    p.add_argument("--n", type=int, default=10000)
    p.add_argument("--runs", type=int, default=8)
    p.add_argument("--snr-db", type=float, default=20.0)
    p.add_argument("--seed", type=int, default=23)
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    scenarios = _build_scenarios(n=args.n, runs=args.runs, snr_db=args.snr_db, seed=args.seed)
    signal_bank: dict[str, list[np.ndarray]] = {
        k: []
        for k in ["eigen", "garch_lr", "rmt_gate", "vol", "cusum", "perm_entropy", "ssa90"]
    }

    for i, sc in enumerate(scenarios):
        sd = _signal_dict(sc.signal, seed=args.seed + i * 7)
        for k in signal_bank:
            signal_bank[k].append(sd[k])

    detail, agg = _evaluate(scenarios, signal_bank)
    detail_path = outdir / "ptbp_detail.csv"
    agg_path = outdir / "ptbp_summary.csv"
    detail.to_csv(detail_path, index=False)
    agg.to_csv(agg_path, index=False)

    # Institutional summary
    def _pick(model: str, has_shift: bool, col: str) -> float | None:
        row = agg[(agg["model"] == model) & (agg["has_shift"] == has_shift)]
        if row.empty:
            return None
        return _clean_float(row.iloc[0][col])

    result = {
        "status": "ok",
        "config": {"n": args.n, "runs": args.runs, "snr_db": args.snr_db, "seed": args.seed},
        "models": sorted(agg["model"].unique().tolist()),
        "metrics": {
            "lead_time_mean_shift": {m: _pick(m, True, "lead_mean") for m in sorted(agg["model"].unique())},
            "lead_time_positive_rate_shift": {m: _pick(m, True, "lead_pos_rate") for m in sorted(agg["model"].unique())},
            "false_alert_rate_no_shift": {m: _pick(m, False, "alert_rate") for m in sorted(agg["model"].unique())},
            "cdar_mean_after_alert_shift": {m: _pick(m, True, "cdar_mean") for m in sorted(agg["model"].unique())},
        },
        "metrics_ci95": {
            "alert_rate_shift": {},
            "alert_rate_no_shift": {},
            "lead_time_mean_shift": {},
        },
        "files": {"detail_csv": str(detail_path), "summary_csv": str(agg_path)},
    }

    for model in sorted(agg["model"].unique()):
        row_shift = agg[(agg["model"] == model) & (agg["has_shift"] == True)]
        row_no = agg[(agg["model"] == model) & (agg["has_shift"] == False)]
        p_shift = _clean_float(row_shift.iloc[0]["alert_rate"]) if not row_shift.empty else None
        p_no = _clean_float(row_no.iloc[0]["alert_rate"]) if not row_no.empty else None
        n_shift = int(row_shift.iloc[0]["n"]) if not row_shift.empty else 0
        n_no = int(row_no.iloc[0]["n"]) if not row_no.empty else 0
        ls, us = _wilson_ci(p_shift, n_shift)
        ln, un = _wilson_ci(p_no, n_no)
        result["metrics_ci95"]["alert_rate_shift"][model] = {"lo": ls, "hi": us, "n": n_shift}
        result["metrics_ci95"]["alert_rate_no_shift"][model] = {"lo": ln, "hi": un, "n": n_no}

        lead_vals = detail[(detail["model"] == model) & (detail["has_shift"] == True)]["lead_time"].to_numpy(dtype=float)
        llo, lhi = _mean_ci95(lead_vals)
        result["metrics_ci95"]["lead_time_mean_shift"][model] = {"lo": llo, "hi": lhi, "n": int(np.isfinite(lead_vals).sum())}

    (outdir / "ptbp_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ptbp] done scenarios={len(scenarios)} out={outdir}")


if __name__ == "__main__":
    main()
