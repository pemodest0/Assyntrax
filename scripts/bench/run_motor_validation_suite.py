#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bench import run_eigen_ptbp as ptbp  # noqa: E402


DETECTORS = ("eigen", "vol", "cusum", "garch_lr", "rmt_gate")
DEFAULT_ASSETS = "^VIX,SPY,QQQ,TLT,HYG,LQD,GLD,BTC-USD,EWZ,DBC"


@dataclass
class EventEval:
    event_detected: bool
    lead_time: float | None
    false_alarm_rate: float


@dataclass
class HardeningConfig:
    eigen_thr: float = 1.2
    baseline_thr: float = 1.0
    persist_window: int = 8
    persist_min: int = 2
    consensus_min: int = 0
    rmt_thr: float = 2.4
    rmt_eigen_gate_thr: float = 1.2
    rmt_persist_window: int = 10
    rmt_persist_min: int = 3
    eigen_alert_q: float = 3.0


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _parse_float_list(raw: str) -> list[float]:
    out: list[float] = []
    for token in str(raw).split(","):
        token = token.strip()
        if not token:
            continue
        out.append(float(token))
    return out


def _parse_str_list(raw: str) -> list[str]:
    return [t.strip() for t in str(raw).split(",") if t.strip()]


def _robust_threshold(sig: np.ndarray, train_cut: int = 900, q: float = 4.5) -> float | None:
    s = np.asarray(sig, dtype=float)
    base = s[: min(train_cut, s.size)]
    base = base[np.isfinite(base)]
    if base.size < 30:
        return None
    med = float(np.median(base))
    mad = float(np.median(np.abs(base - med)))
    return med + q * (1.4826 * mad + 1e-9)


def _alert_mask(sig: np.ndarray, train_cut: int = 900, q: float = 4.5) -> tuple[np.ndarray, float | None]:
    thr = _robust_threshold(sig, train_cut=train_cut, q=q)
    s = np.asarray(sig, dtype=float)
    if thr is None:
        return np.zeros(s.size, dtype=bool), None
    return np.isfinite(s) & (s > thr), float(thr)


def _model_alert_q(model: str, cfg: HardeningConfig) -> float:
    if model == "eigen":
        return float(cfg.eigen_alert_q)
    if model == "rmt_gate":
        return 3.8
    if model == "garch_lr":
        return 3.5
    return 4.0


def _rolling_mean(x: np.ndarray, w: int) -> np.ndarray:
    s = pd.Series(np.asarray(x, dtype=float))
    return s.rolling(int(w), min_periods=max(5, int(w // 4))).mean().to_numpy(dtype=float)


def _rolling_std(x: np.ndarray, w: int) -> np.ndarray:
    s = pd.Series(np.asarray(x, dtype=float))
    return s.rolling(int(w), min_periods=max(5, int(w // 4))).std().to_numpy(dtype=float)


def _robust_z_fast(x: np.ndarray, clip: float = 12.0) -> np.ndarray:
    v = np.asarray(x, dtype=float)
    mask = np.isfinite(v)
    if not np.any(mask):
        return np.zeros_like(v, dtype=float)
    m = float(np.median(v[mask]))
    mad = float(np.median(np.abs(v[mask] - m)))
    sc = 1.4826 * mad + 1e-9
    out = np.zeros_like(v, dtype=float)
    out[mask] = (v[mask] - m) / sc
    return np.clip(out, -clip, clip)


def _ffill_nan(x: np.ndarray) -> np.ndarray:
    out = np.asarray(x, dtype=float).copy()
    for i in range(1, out.size):
        if not np.isfinite(out[i]) and np.isfinite(out[i - 1]):
            out[i] = out[i - 1]
    if out.size and not np.isfinite(out[0]):
        out[0] = 0.0
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def _build_obs_fast(x: np.ndarray, n_obs: int = 8) -> np.ndarray:
    n = x.size
    obs = np.zeros((n, n_obs), dtype=float)
    for j in range(n_obs):
        lag = min(j, 8)
        col = np.roll(x, lag)
        if lag > 0:
            col[:lag] = col[lag]
        obs[:, j] = col
    return obs


def _spectral_signals_fast(x: np.ndarray, w_corr: int = 96, n_obs: int = 6, step: int = 16) -> tuple[np.ndarray, np.ndarray]:
    obs = _build_obs_fast(x, n_obs=n_obs)
    n = x.size
    ar = np.full(n, np.nan, dtype=float)
    ent = np.full(n, np.nan, dtype=float)
    gap = np.full(n, np.nan, dtype=float)
    rot = np.full(n, np.nan, dtype=float)
    rmt = np.full(n, np.nan, dtype=float)
    q = float(n_obs / max(w_corr, 1))
    lambda_max_mp = float((1.0 + np.sqrt(max(q, 1e-12))) ** 2)
    prev_u: np.ndarray | None = None

    for i in range(w_corr - 1, n, max(1, step)):
        s = obs[i - w_corr + 1 : i + 1, :]
        c = np.corrcoef(s, rowvar=False)
        vals, vecs = np.linalg.eigh(c)
        idx = np.argsort(vals)[::-1]
        vals = np.maximum(vals[idx], 1e-12)
        vecs = vecs[:, idx]
        if vals.size < 2:
            continue
        p = vals / max(float(np.sum(vals)), 1e-12)
        ar[i] = float(np.sum(vals[:2]) / max(float(np.sum(vals)), 1e-12))
        ent[i] = float(-np.sum(p * np.log(p + 1e-12)))
        gap[i] = float(vals[0] / max(vals[1], 1e-9))
        u = vecs[:, 0]
        if prev_u is not None:
            rot[i] = float(1.0 - abs(float(np.dot(prev_u, u))))
        prev_u = u.copy()

        ratio = max(0.0, vals[0] / max(lambda_max_mp, 1e-12) - 1.0)
        outband = float(np.mean(vals > lambda_max_mp))
        rmt[i] = ratio + outband

    eigen = (
        _robust_z_fast(_ffill_nan(ar))
        + _robust_z_fast(-_ffill_nan(ent))
        + _robust_z_fast(_ffill_nan(gap))
        + _robust_z_fast(_ffill_nan(rot))
    )
    rmt_z = _robust_z_fast(_ffill_nan(rmt))
    return eigen, rmt_z


def _rolling_count_above(sig: np.ndarray, threshold: float, window: int) -> np.ndarray:
    s = np.asarray(sig, dtype=float)
    out = np.zeros(s.size, dtype=float)
    for i in range(s.size):
        j0 = max(0, i - int(window) + 1)
        seg = s[j0 : i + 1]
        out[i] = float(np.sum(np.isfinite(seg) & (seg > threshold)))
    return out


def _harden_structural_signal(
    eigen_sig: np.ndarray,
    baseline_sigs: list[np.ndarray],
    cfg: HardeningConfig,
) -> np.ndarray:
    e = _ffill_nan(eigen_sig)
    persist = _rolling_count_above(e, threshold=cfg.eigen_thr, window=cfg.persist_window) >= cfg.persist_min
    consensus = np.zeros(e.size, dtype=int)
    for b in baseline_sigs:
        bb = _ffill_nan(b)
        consensus += np.where(bb > cfg.baseline_thr, 1, 0)
    ok = persist & (consensus >= int(cfg.consensus_min))
    out = np.full_like(e, np.nan, dtype=float)
    out[ok] = e[ok]
    return out


def _rmt_secondary_signal(
    rmt_sig: np.ndarray,
    eigen_hardened_sig: np.ndarray,
    cfg: HardeningConfig,
) -> np.ndarray:
    r = _ffill_nan(rmt_sig)
    e = _ffill_nan(eigen_hardened_sig)
    persist = _rolling_count_above(r, threshold=cfg.rmt_thr, window=cfg.rmt_persist_window) >= cfg.rmt_persist_min
    gate = e > cfg.rmt_eigen_gate_thr
    out = np.full_like(r, np.nan, dtype=float)
    out[persist & gate] = r[persist & gate]
    return out


def _compute_base_signals_fast(x: np.ndarray) -> dict[str, np.ndarray]:
    x = np.asarray(x, dtype=float)
    vol = _robust_z_fast(_rolling_std(x, 120))
    mu = _rolling_mean(x, 80)
    cusum_raw = np.nancumsum(np.nan_to_num(np.abs(x - np.nan_to_num(mu))))
    cusum = _robust_z_fast(cusum_raw)
    var_s = pd.Series(x).rolling(20, min_periods=10).var().to_numpy(dtype=float)
    var_l = pd.Series(x).rolling(120, min_periods=30).var().to_numpy(dtype=float)
    garch_proxy = _robust_z_fast(np.log((var_s + 1e-12) / (var_l + 1e-12)))
    eigen_raw, rmt_raw = _spectral_signals_fast(x, w_corr=96, n_obs=6, step=16)
    return {
        "vol": vol,
        "cusum": cusum,
        "garch_lr": garch_proxy,
        "eigen_raw": eigen_raw,
        "rmt_raw": rmt_raw,
    }


def _compose_signals(base: dict[str, np.ndarray], cfg: HardeningConfig) -> dict[str, np.ndarray]:
    eigen = _harden_structural_signal(
        base["eigen_raw"],
        baseline_sigs=[base["vol"], base["cusum"], base["garch_lr"]],
        cfg=cfg,
    )
    rmt = _rmt_secondary_signal(
        base["rmt_raw"],
        eigen_hardened_sig=eigen,
        cfg=cfg,
    )
    return {
        "eigen": eigen,
        "vol": base["vol"],
        "cusum": base["cusum"],
        "garch_lr": base["garch_lr"],
        "rmt_gate": rmt,
    }


def _signal_dict_fast(x: np.ndarray, seed: int, cfg: HardeningConfig) -> dict[str, np.ndarray]:
    _ = seed
    base = _compute_base_signals_fast(x)
    return _compose_signals(base, cfg=cfg)


def _evaluate_single_event_alerts(
    alerts: np.ndarray,
    event_idx: int | None,
    pre_window: int = 30,
    post_window: int = 10,
    warmup: int = 250,
) -> EventEval:
    a = np.asarray(alerts, dtype=bool).copy()
    n = a.size
    w0 = min(max(0, int(warmup)), n)
    if w0 > 0:
        a[:w0] = False
    if event_idx is None:
        fa_rate = float(np.mean(a[w0:])) if n else 0.0
        return EventEval(event_detected=False, lead_time=None, false_alarm_rate=fa_rate)

    e = int(event_idx)
    i0 = max(w0, e - pre_window)
    i1 = min(n, e + post_window + 1)
    idx = np.where(a[i0:i1])[0]
    if idx.size == 0:
        zone = np.zeros(n, dtype=bool)
        zone[i0:i1] = True
        fa_rate = float(np.mean(a[w0:] & (~zone[w0:]))) if n else 0.0
        return EventEval(event_detected=False, lead_time=None, false_alarm_rate=fa_rate)

    abs_idx = i0 + idx
    before = abs_idx[abs_idx <= e]
    det = int(before[-1]) if before.size else int(abs_idx[0])
    lead = float(e - det)

    zone = np.zeros(n, dtype=bool)
    zone[i0:i1] = True
    fa_rate = float(np.mean(a[w0:] & (~zone[w0:]))) if n else 0.0
    return EventEval(event_detected=True, lead_time=lead, false_alarm_rate=fa_rate)


def _lead_pxx(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.nanpercentile(np.asarray(values, dtype=float), q))


def _alerts_per_month(alerts: np.ndarray, periods_per_month: float = 21.0) -> float:
    a = np.asarray(alerts, dtype=bool)
    if a.size == 0:
        return float("nan")
    months = max(a.size / periods_per_month, 1e-9)
    return float(np.sum(a) / months)


def _switches_per_1000(alerts: np.ndarray) -> float:
    a = np.asarray(alerts, dtype=int)
    if a.size <= 1:
        return 0.0
    switches = float(np.sum(np.abs(np.diff(a))))
    return float(switches / max(a.size / 1000.0, 1e-9))


def _balanced_score(tpr: float | None, fpr: float | None, lead_p50: float | None) -> float | None:
    if tpr is None or fpr is None:
        return None
    lead_component = 0.5
    if lead_p50 is not None and np.isfinite(lead_p50):
        lead_component = float(np.clip((lead_p50 + 20.0) / 40.0, 0.0, 1.0))
    return float((tpr + (1.0 - fpr) + lead_component) / 3.0)


def _summarize_from_event_rows(rows: pd.DataFrame, model_col: str = "model") -> pd.DataFrame:
    out: list[dict[str, Any]] = []
    if rows.empty:
        return pd.DataFrame(out)
    for model, g in rows.groupby(model_col):
        gs = g[g["has_shift"] == True]
        gn = g[g["has_shift"] == False]
        tpr = float(gs["event_detected"].mean()) if not gs.empty else np.nan
        fpr = float(gn["false_alarm_rate"].mean()) if not gn.empty else np.nan
        leads = gs["lead_time"].dropna().to_numpy(dtype=float) if "lead_time" in gs.columns else np.array([], dtype=float)
        lead_p50 = float(np.nanpercentile(leads, 50)) if leads.size else np.nan
        lead_p90 = float(np.nanpercentile(leads, 90)) if leads.size else np.nan
        alerts_m = float(g["alerts_per_month"].mean()) if "alerts_per_month" in g.columns else np.nan
        switches = float(g["switches_per_1000"].mean()) if "switches_per_1000" in g.columns else np.nan
        tpr_v = None if not np.isfinite(tpr) else float(tpr)
        fpr_v = None if not np.isfinite(fpr) else float(fpr)
        l50_v = None if not np.isfinite(lead_p50) else float(lead_p50)
        l90_v = None if not np.isfinite(lead_p90) else float(lead_p90)
        am_v = None if not np.isfinite(alerts_m) else float(alerts_m)
        sw_v = None if not np.isfinite(switches) else float(switches)
        out.append(
            {
                "model": str(model),
                "tpr": tpr_v,
                "fpr": fpr_v,
                "lead_p50": l50_v,
                "lead_p90": l90_v,
                "alerts_per_month": am_v,
                "switches_per_1000": sw_v,
                "balanced_score": _balanced_score(tpr_v, fpr_v, l50_v),
            }
        )
    return pd.DataFrame(out).sort_values("model").reset_index(drop=True)


def _phase_randomized(x: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = x.shape[0]
    xf = np.fft.rfft(x)
    amp = np.abs(xf)
    phase = np.angle(xf)
    rand_phase = rng.uniform(-np.pi, np.pi, size=phase.shape[0])
    rand_phase[0] = phase[0]
    if n % 2 == 0:
        rand_phase[-1] = phase[-1]
    xf_new = amp * np.exp(1j * rand_phase)
    return np.fft.irfft(xf_new, n=n).astype(float)


def _zscore(x: np.ndarray) -> np.ndarray:
    s = np.asarray(x, dtype=float)
    mu = float(np.nanmean(s))
    sd = float(np.nanstd(s))
    if not np.isfinite(sd) or sd <= 1e-12:
        return np.zeros_like(s)
    return (s - mu) / sd


def _family_from_scenario_name(name: str) -> str:
    n = str(name).lower()
    if n.startswith("lorenz"):
        return "lorenz"
    if n.startswith("rossler"):
        return "rossler"
    if n.startswith("mackey_glass"):
        return "mackey_glass"
    return "unknown"


def _load_close_series(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    cols = {str(c).lower(): str(c) for c in df.columns}
    dcol = cols.get("date") or cols.get("data") or cols.get("datetime") or cols.get("timestamp")
    ccol = cols.get("close") or cols.get("adj_close") or cols.get("price") or cols.get("value")
    if dcol is None or ccol is None:
        raise ValueError(f"missing date/close columns in {path}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[dcol], errors="coerce"),
            "close": pd.to_numeric(df[ccol], errors="coerce"),
        }
    ).dropna()
    out = out.sort_values("date").drop_duplicates("date")
    if out.shape[0] < 350:
        raise ValueError(f"insufficient rows ({out.shape[0]}) in {path.name}")
    return out.reset_index(drop=True)


def _download_asset_once(asset: str, path: Path) -> bool:
    try:
        import yfinance as yf  # type: ignore
    except Exception:
        return False
    try:
        t = yf.Ticker(asset)
        hist = t.history(period="max", auto_adjust=False)
        if hist is None or hist.empty:
            return False
        hist = hist.reset_index()
        date_col = "Date" if "Date" in hist.columns else ("Datetime" if "Datetime" in hist.columns else None)
        if date_col is None or "Close" not in hist.columns:
            return False
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(hist[date_col], errors="coerce"),
                "close": pd.to_numeric(hist["Close"], errors="coerce"),
            }
        ).dropna()
        if out.empty:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(path, index=False)
        return True
    except Exception:
        return False


def _event_indices_from_truth(truth: np.ndarray, min_gap: int = 21) -> np.ndarray:
    t = np.asarray(truth, dtype=int)
    if t.size == 0:
        return np.array([], dtype=int)
    edges = np.where((t == 1) & (np.r_[0, t[:-1]] == 0))[0]
    if edges.size == 0:
        return edges
    kept: list[int] = []
    last = -10**9
    for e in edges:
        if (e - last) >= min_gap:
            kept.append(int(e))
            last = int(e)
    return np.asarray(kept, dtype=int)


def _evaluate_alerts_vs_events(
    alerts: np.ndarray,
    event_idx: np.ndarray,
    pre_window: int = 30,
    post_window: int = 10,
    warmup: int = 260,
) -> tuple[float | None, float | None, list[float]]:
    a = np.asarray(alerts, dtype=bool).copy()
    n = a.size
    w0 = min(max(0, int(warmup)), n)
    if w0 > 0:
        a[:w0] = False
    if event_idx.size == 0:
        return None, float(np.mean(a)) if n else None, []

    leads: list[float] = []
    hits = 0
    zone = np.zeros(n, dtype=bool)
    for e in event_idx:
        i0 = max(w0, int(e) - pre_window)
        i1 = min(n, int(e) + post_window + 1)
        zone[i0:i1] = True
        idx = np.where(a[i0:i1])[0]
        if idx.size == 0:
            continue
        abs_idx = i0 + idx
        before = abs_idx[abs_idx <= int(e)]
        det = int(before[-1]) if before.size else int(abs_idx[0])
        hits += 1
        leads.append(float(int(e) - det))

    safe = ~zone
    fpr = float(np.mean(a[safe])) if np.any(safe) else None
    tpr = float(hits / event_idx.size)
    return tpr, fpr, leads


def _primary_scorecard(det: pd.DataFrame, primary_model: str) -> dict[str, Any]:
    row = det[det["model"] == primary_model]
    if row.empty:
        return {
            "primary_model": primary_model,
            "tpr": None,
            "fpr": None,
            "lead_p50": None,
            "lead_p90": None,
            "alerts_per_month": None,
            "switches_per_1000": None,
        }
    r = row.iloc[0].to_dict()
    return {
        "primary_model": primary_model,
        "tpr": r.get("tpr"),
        "fpr": r.get("fpr"),
        "lead_p50": r.get("lead_p50"),
        "lead_p90": r.get("lead_p90"),
        "alerts_per_month": r.get("alerts_per_month"),
        "switches_per_1000": r.get("switches_per_1000"),
    }


def _calibrate_hardening(seed: int, n_synth: int, snr_levels: list[float]) -> tuple[HardeningConfig, pd.DataFrame]:
    snr = float(min(snr_levels)) if snr_levels else 10.0
    scenarios = ptbp._build_scenarios(n=max(900, min(1200, n_synth)), runs=4, snr_db=snr, seed=seed + 9001)
    cache: list[tuple[bool, int, dict[str, np.ndarray]]] = []
    for sc in scenarios:
        cache.append((bool(sc.has_shift), int(sc.event_idx), _compute_base_signals_fast(sc.signal)))

    grid_rows: list[dict[str, Any]] = []
    best_cfg = HardeningConfig()
    best_score = -1e9
    best_cfg_ctrl = None
    best_score_ctrl = -1e9
    for eigen_thr in (1.0, 1.2, 1.4, 1.6):
        for baseline_thr in (0.8, 1.2, 1.4):
            for persist_min in (1, 2, 3):
                for consensus_min in (0, 1):
                    for alert_q in (2.0, 2.5, 3.0, 3.5):
                        cfg = HardeningConfig(
                            eigen_thr=float(eigen_thr),
                            baseline_thr=float(baseline_thr),
                            persist_window=8,
                            persist_min=int(persist_min),
                            consensus_min=int(consensus_min),
                            eigen_alert_q=float(alert_q),
                        )
                        hits: list[bool] = []
                        falses: list[bool] = []
                        leads: list[float] = []
                        for has_shift, ev_idx, base in cache:
                            sigs = _compose_signals(base, cfg=cfg)
                            warmup = max(250, int(0.3 * len(sigs["eigen"])))
                            alerts, _ = _alert_mask(sigs["eigen"], train_cut=warmup, q=cfg.eigen_alert_q)
                            ev = _evaluate_single_event_alerts(
                                alerts,
                                event_idx=ev_idx if has_shift else None,
                                pre_window=max(120, int(0.15 * len(sigs["eigen"]))),
                                post_window=20,
                                warmup=warmup,
                            )
                            if has_shift:
                                hits.append(bool(ev.event_detected))
                                if ev.lead_time is not None:
                                    leads.append(float(ev.lead_time))
                            else:
                                falses.append(float(ev.false_alarm_rate))
                        tpr = float(np.mean(hits)) if hits else 0.0
                        fpr = float(np.mean(falses)) if falses else 1.0
                        lead_p50 = float(np.nanpercentile(np.asarray(leads, dtype=float), 50)) if leads else np.nan
                        ctrl = _run_hand_controls(cfg=cfg, seed=777)
                        ctrl_ok = bool(ctrl.get("shift_strong_detected")) and (not bool(ctrl.get("stable_false_alarm")))
                        feasible = (tpr >= 0.60) and (fpr <= 0.25)
                        score = (
                            (10.0 if feasible else 0.0)
                            + (2.0 if ctrl_ok else -2.0)
                            + (2.0 * tpr)
                            - (1.4 * fpr)
                            + (0.03 * (lead_p50 if np.isfinite(lead_p50) else 0.0))
                        )
                        if score > best_score:
                            best_score = score
                            best_cfg = cfg
                        if ctrl_ok and score > best_score_ctrl:
                            best_score_ctrl = score
                            best_cfg_ctrl = cfg
                        grid_rows.append(
                            {
                                "eigen_thr": eigen_thr,
                                "baseline_thr": baseline_thr,
                                "persist_min": persist_min,
                                "consensus_min": consensus_min,
                                "alert_q": alert_q,
                                "tpr": tpr,
                                "fpr": fpr,
                                "lead_p50": (None if not np.isfinite(lead_p50) else lead_p50),
                                "control_shift_detected": bool(ctrl.get("shift_strong_detected")),
                                "control_stable_false_alarm": bool(ctrl.get("stable_false_alarm")),
                                "feasible": feasible,
                                "score": score,
                            }
                        )
    selected = best_cfg_ctrl if best_cfg_ctrl is not None else best_cfg
    return selected, pd.DataFrame(grid_rows).sort_values("score", ascending=False).reset_index(drop=True)


def _run_hand_controls(cfg: HardeningConfig, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed + 123456)
    n = 3000
    e = n // 2
    x_shift = rng.normal(0.0, 1.0, n)
    x_shift[e:] = rng.normal(0.0, 4.0, n - e)
    a_shift, _ = _alert_mask(_signal_dict_fast(x_shift, seed=seed + 1, cfg=cfg)["eigen"], train_cut=800, q=cfg.eigen_alert_q)
    ev_shift = _evaluate_single_event_alerts(a_shift, event_idx=e, pre_window=300, post_window=40, warmup=800)

    x_stable = rng.normal(0.0, 1.0, n)
    a_stable, _ = _alert_mask(_signal_dict_fast(x_stable, seed=seed + 2, cfg=cfg)["eigen"], train_cut=800, q=cfg.eigen_alert_q)
    ev_stable = _evaluate_single_event_alerts(a_stable, event_idx=None, warmup=800)
    return {
        "shift_strong_detected": bool(ev_shift.event_detected),
        "shift_strong_lead": ev_shift.lead_time,
        "stable_false_alarm": bool(ev_stable.false_alarm_rate > 0.02),
        "stable_false_alarm_rate": float(ev_stable.false_alarm_rate),
    }


def run_synthetic_truth(
    run_id: str,
    outdir: Path,
    runs_synth: int,
    snr_levels: list[float],
    seed: int,
    n_synth: int,
    cfg: HardeningConfig,
) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for snr in snr_levels:
        scenarios = ptbp._build_scenarios(n=n_synth, runs=runs_synth, snr_db=float(snr), seed=seed + int(100 * snr))
        for i, sc in enumerate(scenarios):
            sigs = _signal_dict_fast(sc.signal, seed=seed + i * 17 + int(snr * 11), cfg=cfg)
            fam = _family_from_scenario_name(sc.name)
            for model in DETECTORS:
                sig = np.asarray(sigs[model], dtype=float)
                warmup = max(250, int(0.3 * sig.size))
                alerts, _ = _alert_mask(sig, train_cut=warmup, q=_model_alert_q(model, cfg))
                ev = _evaluate_single_event_alerts(
                    alerts,
                    event_idx=(int(sc.event_idx) if bool(sc.has_shift) else None),
                    pre_window=max(120, int(0.15 * sig.size)),
                    post_window=10,
                    warmup=warmup,
                )
                rows.append(
                    {
                        "snr_db": float(snr),
                        "scenario": sc.name,
                        "asset": fam,
                        "has_shift": bool(sc.has_shift),
                        "model": model,
                        "event_detected": bool(ev.event_detected),
                        "lead_time": ev.lead_time,
                        "false_alarm_rate": float(ev.false_alarm_rate),
                        "alerts_per_month": _alerts_per_month(alerts),
                        "switches_per_1000": _switches_per_1000(alerts),
                    }
                )

    detail = pd.DataFrame(rows)
    det = _summarize_from_event_rows(detail)
    pa_rows: list[dict[str, Any]] = []
    for (asset, model), g in detail.groupby(["asset", "model"]):
        gs = g[g["has_shift"] == True]
        gn = g[g["has_shift"] == False]
        leads = gs["lead_time"].dropna().to_numpy(dtype=float)
        pa_rows.append(
            {
                "asset": asset,
                "model": model,
                "tpr": (None if gs.empty else float(gs["event_detected"].mean())),
                "fpr": (None if gn.empty else float(gn["false_alarm_rate"].mean())),
                "lead_p50": (None if leads.size == 0 else float(np.nanpercentile(leads, 50))),
                "alerts_per_month": float(g["alerts_per_month"].mean()),
                "switches_per_1000": float(g["switches_per_1000"].mean()),
            }
        )
    per_asset = pd.DataFrame(pa_rows).sort_values(["asset", "model"])
    controls = _run_hand_controls(cfg=cfg, seed=777)

    detail.to_csv(outdir / "detail.csv", index=False)
    det.to_csv(outdir / "detector_metrics.csv", index=False)
    per_asset.to_csv(outdir / "per_asset.csv", index=False)

    summary = {
        "status": "ok",
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "runs_synth": runs_synth,
            "snr_levels": snr_levels,
            "seed": seed,
            "n_synth": n_synth,
            "hardening": cfg.__dict__,
        },
        "controls": controls,
        "scorecard": _primary_scorecard(det, primary_model="eigen"),
        "detectors": det.to_dict(orient="records"),
        "files": {
            "summary_json": str(outdir / "summary.json"),
            "detail_csv": str(outdir / "detail.csv"),
            "detector_csv": str(outdir / "detector_metrics.csv"),
            "per_asset_csv": str(outdir / "per_asset.csv"),
        },
    }
    _json_dump(outdir / "summary.json", summary)
    return summary


def run_real_proxy(run_id: str, outdir: Path, assets: list[str], seed: int, cfg: HardeningConfig) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = ROOT / "data" / "raw" / "finance" / "yfinance_daily"
    data_dir.mkdir(parents=True, exist_ok=True)
    vix_path = data_dir / "^VIX.csv"
    if not vix_path.exists() and not _download_asset_once("^VIX", vix_path):
        vix_path = data_dir / "VIX.csv"
    vix_df = _load_close_series(vix_path).rename(columns={"close": "vix"})

    rows: list[dict[str, Any]] = []
    per_asset_rows: list[dict[str, Any]] = []
    skipped_assets: list[dict[str, str]] = []
    for ai, asset in enumerate(assets):
        p = data_dir / f"{asset}.csv"
        if not p.exists() and (not _download_asset_once(asset, p)):
            skipped_assets.append({"asset": asset, "reason": "missing_file_and_download_failed"})
            continue
        try:
            df = _load_close_series(p).rename(columns={"close": "price"})
        except Exception as exc:
            skipped_assets.append({"asset": asset, "reason": f"load_failed: {exc}"})
            continue
        merged = df.merge(vix_df, on="date", how="inner").sort_values("date").reset_index(drop=True)
        if merged.shape[0] < 350:
            skipped_assets.append({"asset": asset, "reason": "insufficient_intersection"})
            continue
        ret = np.log(merged["price"]).diff().fillna(0.0).to_numpy(dtype=float)
        vix = merged["vix"].to_numpy(dtype=float)
        drawdown60 = merged["price"] / merged["price"].rolling(60, min_periods=10).max() - 1.0
        rv20 = pd.Series(ret).rolling(20, min_periods=10).std()
        vix_thr = float(np.nanquantile(vix, 0.90))
        rv_thr = float(np.nanquantile(rv20.to_numpy(dtype=float), 0.90))
        truth = ((vix >= vix_thr) | (drawdown60.to_numpy(dtype=float) <= -0.08) | (rv20.to_numpy(dtype=float) >= rv_thr)).astype(int)
        event_idx = _event_indices_from_truth(truth, min_gap=21)
        sigs = _signal_dict_fast(ret, seed=seed + ai * 37, cfg=cfg)
        last_vals: dict[str, float] = {}
        model_cache: dict[str, dict[str, Any]] = {}
        for model in DETECTORS:
            sig = np.asarray(sigs[model], dtype=float)
            warmup = max(260, int(0.35 * sig.size))
            alerts, thr = _alert_mask(sig, train_cut=warmup, q=_model_alert_q(model, cfg))
            tpr, fpr, leads = _evaluate_alerts_vs_events(alerts, event_idx=event_idx, pre_window=30, post_window=10, warmup=warmup)
            lead_p50 = _lead_pxx(leads, 50)
            lead_p90 = _lead_pxx(leads, 90)
            last_finite = sig[np.isfinite(sig)]
            last_vals[model] = float(last_finite[-1]) if last_finite.size else float("nan")
            rows.append(
                {
                    "asset": asset,
                    "has_shift": True,
                    "model": model,
                    "tpr": tpr,
                    "fpr": fpr,
                    "lead_p50": lead_p50,
                    "lead_p90": lead_p90,
                    "alerts_per_month": _alerts_per_month(alerts),
                    "switches_per_1000": _switches_per_1000(alerts),
                    "event_hits": int(len(leads)),
                    "n_events": int(event_idx.size),
                    "alert_rate": float(np.mean(alerts)),
                    "threshold": thr,
                }
            )
            model_cache[model] = {
                "alerts": alerts,
                "lead_p50": lead_p50,
                "tpr": tpr,
                "fpr": fpr,
                "switches_per_1000": _switches_per_1000(alerts),
                "alert_rate": float(np.mean(alerts)),
            }

        ev_eigen = model_cache.get("eigen", {})
        eigen_last = last_vals.get("eigen", float("nan"))
        regime_final = "UNKNOWN"
        if np.isfinite(eigen_last) and eigen_last >= 2.0:
            regime_final = "UNSTABLE"
        elif np.isfinite(eigen_last) and eigen_last >= 1.0:
            regime_final = "TRANSITION"
        elif np.isfinite(eigen_last):
            regime_final = "STABLE"
        tpr_e = ev_eigen.get("tpr")
        fpr_e = ev_eigen.get("fpr")
        if regime_final == "UNSTABLE" and (tpr_e is None or tpr_e >= 0.5):
            status_final = "watch"
        elif regime_final == "STABLE" and (fpr_e is None or fpr_e <= 0.25):
            status_final = "validated"
        else:
            status_final = "inconclusive"
        ordered = sorted([(k, v) for k, v in last_vals.items() if np.isfinite(v)], key=lambda kv: kv[1], reverse=True)
        top3_str = ",".join([f"{k}:{v:.2f}" for k, v in ordered[:3]]) if ordered else ""
        per_asset_rows.append(
            {
                "asset": asset,
                "regime_final": regime_final,
                "status_final": status_final,
                "alert_rate": ev_eigen.get("alert_rate"),
                "switches": ev_eigen.get("switches_per_1000"),
                "top_3_reasons": top3_str,
                "n_events_proxy": int(event_idx.size),
                "event_thresholds": f"vix_q90={vix_thr:.2f};dd60=-0.08;rv20_q90={rv_thr:.4f}",
            }
        )

    det_rows = pd.DataFrame(rows)
    if det_rows.empty:
        det = pd.DataFrame(columns=["model", "tpr", "fpr", "lead_p50", "lead_p90", "alerts_per_month", "switches_per_1000", "balanced_score"])
    else:
        det = det_rows.groupby("model", as_index=False).agg(
            tpr=("tpr", "mean"),
            fpr=("fpr", "mean"),
            lead_p50=("lead_p50", "median"),
            lead_p90=("lead_p90", "median"),
            alerts_per_month=("alerts_per_month", "mean"),
            switches_per_1000=("switches_per_1000", "mean"),
        ).sort_values("model").reset_index(drop=True)
        det["balanced_score"] = det.apply(
            lambda r: _balanced_score(None if pd.isna(r["tpr"]) else float(r["tpr"]), None if pd.isna(r["fpr"]) else float(r["fpr"]), None if pd.isna(r["lead_p50"]) else float(r["lead_p50"])),
            axis=1,
        )

    per_asset = pd.DataFrame(per_asset_rows).sort_values("asset").reset_index(drop=True) if per_asset_rows else pd.DataFrame(columns=["asset"])
    det_rows.to_csv(outdir / "detail.csv", index=False)
    det.to_csv(outdir / "detector_metrics.csv", index=False)
    per_asset.to_csv(outdir / "per_asset.csv", index=False)
    status = "ok"
    if skipped_assets and not per_asset_rows:
        status = "fail"
    elif skipped_assets:
        status = "partial"
    summary = {
        "status": status,
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {"assets": assets, "seed": seed, "hardening": cfg.__dict__},
        "scorecard": _primary_scorecard(det, primary_model="eigen"),
        "detectors": det.to_dict(orient="records"),
        "n_assets_ok": int(len(per_asset_rows)),
        "n_assets_skipped": int(len(skipped_assets)),
        "skipped_assets": skipped_assets,
        "files": {
            "summary_json": str(outdir / "summary.json"),
            "detail_csv": str(outdir / "detail.csv"),
            "detector_csv": str(outdir / "detector_metrics.csv"),
            "per_asset_csv": str(outdir / "per_asset.csv"),
        },
    }
    _json_dump(outdir / "summary.json", summary)
    return summary


def run_sanity_ablation(run_id: str, outdir: Path, runs_synth: int, seed: int, n_synth: int, cfg: HardeningConfig) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    runs = max(4, min(8, (runs_synth // 10) + 3))
    scenarios = ptbp._build_scenarios(n=n_synth, runs=runs, snr_db=20.0, seed=seed + 7001)
    variant_rows: list[dict[str, Any]] = []
    variants = ("baseline", "shuffle", "phase_randomized")
    rng = np.random.default_rng(seed + 999)
    scale_mismatch: dict[str, list[float]] = {m: [] for m in DETECTORS}

    for i, sc in enumerate(scenarios):
        base_x = np.asarray(sc.signal, dtype=float)
        x_map = {"baseline": base_x, "shuffle": rng.permutation(base_x), "phase_randomized": _phase_randomized(base_x, seed + 3000 + i)}
        for variant in variants:
            sigs = _signal_dict_fast(x_map[variant], seed=seed + i * 41 + (0 if variant == "baseline" else 9), cfg=cfg)
            for model in DETECTORS:
                sig = np.asarray(sigs[model], dtype=float)
                warmup = max(250, int(0.3 * sig.size))
                alerts, _ = _alert_mask(sig, train_cut=warmup, q=_model_alert_q(model, cfg))
                ev = _evaluate_single_event_alerts(
                    alerts,
                    event_idx=(int(sc.event_idx) if bool(sc.has_shift) else None),
                    pre_window=max(120, int(0.15 * sig.size)),
                    post_window=10,
                    warmup=warmup,
                )
                variant_rows.append(
                    {
                        "variant": variant,
                        "model": model,
                        "has_shift": bool(sc.has_shift),
                        "event_detected": bool(ev.event_detected),
                        "lead_time": ev.lead_time,
                        "false_alarm_rate": float(ev.false_alarm_rate),
                        "alerts_per_month": _alerts_per_month(alerts),
                        "switches_per_1000": _switches_per_1000(alerts),
                    }
                )
        z1 = _zscore(base_x)
        z2 = _zscore(base_x * 7.0)
        s1 = _signal_dict_fast(z1, seed=seed + 5100 + i, cfg=cfg)
        s2 = _signal_dict_fast(z2, seed=seed + 5100 + i, cfg=cfg)
        for model in DETECTORS:
            w1 = max(250, int(0.3 * len(z1)))
            w2 = max(250, int(0.3 * len(z2)))
            a1, _ = _alert_mask(np.asarray(s1[model], dtype=float), train_cut=w1, q=_model_alert_q(model, cfg))
            a2, _ = _alert_mask(np.asarray(s2[model], dtype=float), train_cut=w2, q=_model_alert_q(model, cfg))
            scale_mismatch[model].append(float(np.mean(a1 != a2)) if a1.size else 0.0)

    detail = pd.DataFrame(variant_rows)
    per_variant: dict[str, pd.DataFrame] = {v: _summarize_from_event_rows(detail[detail["variant"] == v]) for v in variants}

    flat_rows: list[dict[str, Any]] = []
    for v, dfv in per_variant.items():
        for _, r in dfv.iterrows():
            flat_rows.append(
                {
                    "asset": v,
                    "model": r["model"],
                    "tpr": r["tpr"],
                    "fpr": r["fpr"],
                    "lead_p50": r["lead_p50"],
                    "lead_p90": r["lead_p90"],
                    "alerts_per_month": r["alerts_per_month"],
                    "switches_per_1000": r["switches_per_1000"],
                    "balanced_score": r["balanced_score"],
                }
            )
    per_asset = pd.DataFrame(flat_rows).sort_values(["asset", "model"])
    per_asset.to_csv(outdir / "per_asset.csv", index=False)
    detail.to_csv(outdir / "detail.csv", index=False)

    scale_mismatch_mean = {m: float(np.mean(v)) if v else np.nan for m, v in scale_mismatch.items()}
    scale_ok = bool(all(np.isfinite(v) and v <= 0.02 for v in scale_mismatch_mean.values()))
    base_e = per_variant["baseline"]
    shuf_e = per_variant["shuffle"]
    phase_e = per_variant["phase_randomized"]

    def _metric(df: pd.DataFrame, model: str, col: str) -> float | None:
        hit = df[df["model"] == model]
        if hit.empty:
            return None
        x = hit.iloc[0][col]
        return None if pd.isna(x) else float(x)

    base_tpr = _metric(base_e, "eigen", "tpr")
    shuf_tpr = _metric(shuf_e, "eigen", "tpr")
    phase_tpr = _metric(phase_e, "eigen", "tpr")
    shuffle_drop = bool(base_tpr is not None and shuf_tpr is not None and shuf_tpr <= base_tpr * 0.70)
    phase_drop = bool(base_tpr is not None and phase_tpr is not None and phase_tpr <= base_tpr * 0.75)

    flags: list[str] = []
    if not shuffle_drop:
        flags.append("FLAG: shuffle did not reduce performance enough")
    if not phase_drop:
        flags.append("FLAG: phase_randomized did not reduce performance enough")
    if not scale_ok:
        flags.append("FLAG: scale invariance failed")

    summary = {
        "status": ("ok" if not flags else "warn"),
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {"runs_synth_for_sanity": runs, "seed": seed, "n_synth": n_synth, "hardening": cfg.__dict__},
        "scorecard": _primary_scorecard(base_e, primary_model="eigen"),
        "variants": {v: per_variant[v].to_dict(orient="records") for v in variants},
        "scale_invariance": {"mismatch_rate_mean": scale_mismatch_mean},
        "checks": {"shuffle_performance_drop": shuffle_drop, "phase_performance_drop": phase_drop, "scale_invariance_ok": scale_ok, "flags": flags},
        "files": {
            "summary_json": str(outdir / "summary.json"),
            "detail_csv": str(outdir / "detail.csv"),
            "per_asset_csv": str(outdir / "per_asset.csv"),
        },
    }
    _json_dump(outdir / "summary.json", summary)
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description="Motor validation suite: synthetic truth, real proxy, sanity/ablation.")
    p.add_argument("--runs_synth", type=int, default=50)
    p.add_argument("--snr_levels", type=str, default="20,10")
    p.add_argument("--assets", type=str, default=DEFAULT_ASSETS)
    p.add_argument("--outdir", type=str, default=str(ROOT / "results" / "benchmarks"))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n_synth", type=int, default=1200)
    args = p.parse_args()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_base = Path(args.outdir)
    synth_dir = out_base / "synthetic_truth" / run_id
    real_dir = out_base / "real_proxy" / run_id
    sanity_dir = out_base / "sanity_ablation" / run_id
    snr_levels = _parse_float_list(args.snr_levels)
    assets = _parse_str_list(args.assets)

    print(f"[suite] run_id={run_id}")
    print("[suite] calibrating eigen hardening thresholds...")
    cfg, grid = _calibrate_hardening(seed=args.seed, n_synth=args.n_synth, snr_levels=snr_levels)
    (out_base / "calibration" / run_id).mkdir(parents=True, exist_ok=True)
    grid.to_csv(out_base / "calibration" / run_id / "hardening_grid.csv", index=False)
    _json_dump(out_base / "calibration" / run_id / "selected_hardening.json", cfg.__dict__)
    print(f"[suite] selected cfg={cfg}")

    print(f"[suite] synthetic_truth -> {synth_dir}")
    synth = run_synthetic_truth(run_id, synth_dir, runs_synth=args.runs_synth, snr_levels=snr_levels, seed=args.seed, n_synth=args.n_synth, cfg=cfg)
    print(f"[suite] synthetic done status={synth.get('status')} controls={synth.get('controls')}")

    print(f"[suite] real_proxy -> {real_dir}")
    real = run_real_proxy(run_id, real_dir, assets=assets, seed=args.seed + 111, cfg=cfg)
    print(f"[suite] real_proxy done status={real.get('status')} skipped={real.get('n_assets_skipped')}")

    print(f"[suite] sanity_ablation -> {sanity_dir}")
    sanity = run_sanity_ablation(run_id, sanity_dir, runs_synth=args.runs_synth, seed=args.seed + 222, n_synth=args.n_synth, cfg=cfg)
    print(f"[suite] sanity done status={sanity.get('status')}")

    suite_summary = {
        "status": "ok",
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "hardening": cfg.__dict__,
        "paths": {
            "synthetic_truth": str(synth_dir),
            "real_proxy": str(real_dir),
            "sanity_ablation": str(sanity_dir),
            "calibration": str(out_base / "calibration" / run_id),
        },
        "sections": {
            "synthetic_truth_status": synth.get("status"),
            "real_proxy_status": real.get("status"),
            "sanity_ablation_status": sanity.get("status"),
        },
    }
    _json_dump(out_base / "motor_validation_suite_last_run.json", suite_summary)
    print(f"[suite] done run_id={run_id}")


if __name__ == "__main__":
    main()
