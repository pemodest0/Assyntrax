from __future__ import annotations

from typing import Any, Dict, Optional

# Calibrated score thresholds (weekly) from official proxy comparison.
# Keys are tickers; values are per-proxy thresholds.
_THRESHOLDS_WEEKLY: Dict[str, Dict[str, Optional[float]]] = {
    # Weekly calibrated (score mode, q=0.8/0.9) from compare_official_regimes.
    # SPY: stress q=0.9, vol q=0.8, macro weak (keep None).
    "SPY": {"macro": None, "stress": 0.094958, "vol": 0.055634},
    # QQQ: macro q=0.9, stress q=0.8, vol weak (None).
    "QQQ": {"macro": 0.022336, "stress": 0.018115, "vol": None},
}

# Daily not calibrated yet.
_THRESHOLDS_DAILY: Dict[str, Dict[str, Optional[float]]] = {
    # Daily calibrated from compare_official_regimes (score mode, q=0.8).
    # SPY: best macro BA at q=0.8, moderate stress signal.
    "SPY": {"macro": 0.023313, "stress": 0.023313, "vol": None},
    # QQQ: macro signal weak/moderate, stress weaker.
    "QQQ": {"macro": 0.017214, "stress": 0.017214, "vol": None},
    # GLD not reliable -> keep None.
}

# Sector/base fallbacks (heuristic, v0)
_BASE_DAILY = {"macro": 0.020, "stress": 0.020, "vol": 0.020}
_BASE_WEEKLY = {"macro": 0.020, "stress": 0.090, "vol": 0.055}

_GROUP_MULTIPLIER_DAILY: Dict[str, float] = {
    "equities_us_broad": 0.9,
    "equities_us_sectors": 1.0,
    "equities_international": 1.1,
    "bonds_rates": 1.1,
    "fx": 1.2,
    "crypto": 1.3,
    "volatility": 1.3,
    "energy": 1.2,
    "metals": 1.0,
    "commodities_broad": 1.0,
}

_GROUP_MULTIPLIER_WEEKLY: Dict[str, float] = {
    "equities_us_broad": 0.9,
    "equities_us_sectors": 1.0,
    "equities_international": 1.1,
    "bonds_rates": 1.1,
    "fx": 1.2,
    "crypto": 1.3,
    "volatility": 1.3,
    "energy": 1.2,
    "metals": 1.0,
    "commodities_broad": 1.0,
}


def get_risk_thresholds(ticker: str, timeframe: str, group: Optional[str] = None) -> Dict[str, Any]:
    tf = timeframe.lower()
    if tf == "weekly":
        if ticker in _THRESHOLDS_WEEKLY:
            return _THRESHOLDS_WEEKLY.get(ticker, {}).copy()
        base = _BASE_WEEKLY.copy()
        mult = _GROUP_MULTIPLIER_WEEKLY.get(group or "", 1.0)
        return {k: (None if v is None else float(v) * mult) for k, v in base.items()}
    if tf == "daily":
        if ticker in _THRESHOLDS_DAILY:
            return _THRESHOLDS_DAILY.get(ticker, {}).copy()
        base = _BASE_DAILY.copy()
        mult = _GROUP_MULTIPLIER_DAILY.get(group or "", 1.0)
        return {k: (None if v is None else float(v) * mult) for k, v in base.items()}
    return {}


def set_risk_thresholds(ticker: str, timeframe: str, thresholds: Dict[str, Optional[float]]) -> None:
    tf = timeframe.lower()
    if tf == "weekly":
        _THRESHOLDS_WEEKLY[ticker] = dict(thresholds)
    elif tf == "daily":
        _THRESHOLDS_DAILY[ticker] = dict(thresholds)
