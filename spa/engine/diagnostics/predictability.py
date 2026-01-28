"""Diagnósticos quantitativos de previsibilidade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np


@dataclass
class ACFSummary:
    max_lag: int
    acf_values: np.ndarray
    significant_lags: List[int]
    acf1: float
    threshold: float


@dataclass
class HurstSummary:
    hurst: float
    method: str


@dataclass
class LyapunovProxy:
    lambda_hat: float
    horizon_scale: float
    growth_mode: str


def compute_acf(series: np.ndarray, max_lag: int = 60) -> ACFSummary:
    """Calcula a ACF até max_lag e identifica lags significativos.

    Args:
        series: Série 1-D.
        max_lag: Número máximo de lags.

    Returns:
        ACFSummary com lags significativos e acf(1).
    """
    x = np.asarray(series, dtype=float)
    x = x[np.isfinite(x)]
    if x.size < 5:
        return ACFSummary(max_lag, np.array([]), [], float("nan"), float("nan"))
    x = x - np.mean(x)
    denom = np.dot(x, x)
    if denom == 0:
        return ACFSummary(max_lag, np.zeros(max_lag), [], 0.0, 0.0)
    max_lag = min(max_lag, x.size - 1)
    acf_vals = np.array([np.dot(x[:-lag], x[lag:]) / denom for lag in range(1, max_lag + 1)])
    threshold = 2.0 / np.sqrt(x.size)
    significant = [i + 1 for i, v in enumerate(acf_vals) if abs(v) >= threshold]
    acf1 = float(acf_vals[0]) if acf_vals.size else float("nan")
    return ACFSummary(max_lag, acf_vals, significant, acf1, threshold)


def hurst_exponent_rs(series: np.ndarray, min_window: int = 10, max_window: int = 200) -> HurstSummary:
    """Calcula o expoente de Hurst via R/S (rescaled range).

    Args:
        series: Série 1-D.
        min_window: Tamanho mínimo de janela.
        max_window: Tamanho máximo de janela.

    Returns:
        HurstSummary com H estimado.
    """
    x = np.asarray(series, dtype=float)
    x = x[np.isfinite(x)]
    n = x.size
    if n < min_window * 2:
        return HurstSummary(float("nan"), "rs")
    max_window = min(max_window, n // 2)
    window_sizes = np.unique(np.logspace(np.log10(min_window), np.log10(max_window), num=10).astype(int))
    rs_vals = []
    sizes = []
    for w in window_sizes:
        if w < 5:
            continue
        n_blocks = n // w
        if n_blocks < 2:
            continue
        rs_block = []
        for i in range(n_blocks):
            block = x[i * w : (i + 1) * w]
            mean = np.mean(block)
            dev = block - mean
            cum = np.cumsum(dev)
            r = np.max(cum) - np.min(cum)
            s = np.std(block)
            if s > 0:
                rs_block.append(r / s)
        if rs_block:
            rs_vals.append(np.mean(rs_block))
            sizes.append(w)
    if len(rs_vals) < 2:
        return HurstSummary(float("nan"), "rs")
    slope = np.polyfit(np.log(sizes), np.log(rs_vals), 1)[0]
    return HurstSummary(float(slope), "rs")


def lyapunov_proxy(errors_by_horizon: Iterable[float], horizons: Iterable[int]) -> LyapunovProxy:
    """Estima crescimento local de erro e um lambda efetivo.

    Args:
        errors_by_horizon: Erros médios por horizonte (mesmo tamanho de horizons).
        horizons: Lista de horizontes (inteiros).

    Returns:
        LyapunovProxy com lambda estimado e escala característica.
    """
    h = np.array(list(horizons), dtype=float)
    e = np.array(list(errors_by_horizon), dtype=float)
    mask = np.isfinite(e) & (e > 0) & np.isfinite(h) & (h > 0)
    if mask.sum() < 2:
        return LyapunovProxy(float("nan"), float("nan"), "insufficient")
    h = h[mask]
    e = e[mask]
    slope = np.polyfit(h, np.log(e), 1)[0]
    lambda_hat = float(slope)
    horizon_scale = float(1.0 / slope) if slope > 0 else float("inf")
    growth_mode = "exponencial" if slope > 0 else "lento"
    return LyapunovProxy(lambda_hat, horizon_scale, growth_mode)


def classify_predictability(
    acf: ACFSummary,
    hurst: HurstSummary,
    lyap: LyapunovProxy,
    win_rate: float,
    avg_improvement: float,
) -> str:
    """Classifica previsibilidade com base em ACF, Hurst e crescimento do erro."""
    if not np.isfinite(hurst.hurst) and not acf.significant_lags:
        return "ESSENCIALMENTE_RUIDOSO"
    if win_rate >= 0.6 and avg_improvement > 0:
        return "PREVISIVEL_CURTO_PRAZO"
    if lyap.lambda_hat > 0.2 and abs(acf.acf1) < acf.threshold:
        return "INSTAVEL_OU_CAOTICO"
    if abs(hurst.hurst - 0.5) <= 0.05 and abs(acf.acf1) < acf.threshold:
        return "ESSENCIALMENTE_RUIDOSO"
    return "REGIME_DEPENDENTE"
