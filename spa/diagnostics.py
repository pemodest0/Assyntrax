from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def classify_volatility(rolling_std: pd.Series) -> str:
    clean = rolling_std.dropna()
    if clean.empty:
        return "unknown"
    p33, p66 = np.percentile(clean, [33, 66])
    recent = float(clean.iloc[-1])
    if recent <= p33:
        return "low"
    if recent <= p66:
        return "medium"
    return "high"


def detect_regime_change(series: pd.Series, window: int = 48) -> Dict[str, object]:
    if len(series) < window * 2:
        return {"change_detected": False, "relative_variance_change": 0.0}
    recent = series.iloc[-window:]
    prior = series.iloc[-2 * window : -window]
    var_recent = float(np.var(recent, ddof=1))
    var_prior = float(np.var(prior, ddof=1))
    if var_prior == 0:
        return {"change_detected": False, "relative_variance_change": 0.0}
    relative_change = (var_recent - var_prior) / var_prior
    return {
        "change_detected": relative_change >= 0.5,
        "relative_variance_change": float(relative_change),
    }


def risk_score(vol_class: str, regime_change: Dict[str, object]) -> int:
    base = {"low": 20, "medium": 50, "high": 80}.get(vol_class, 40)
    if regime_change.get("change_detected"):
        base += 10
    return int(max(0, min(100, base)))


def run_diagnostics(df: pd.DataFrame, value_col: str, rolling_std: pd.Series) -> Dict[str, object]:
    vol_class = classify_volatility(rolling_std)
    regime = detect_regime_change(df[value_col])
    score = risk_score(vol_class, regime)

    return {
        "volatility_class": vol_class,
        "regime_change": regime,
        "risk_score": score,
    }

