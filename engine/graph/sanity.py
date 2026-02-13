from __future__ import annotations

from typing import Dict, List


def sanity_alerts(
    asset: str,
    n_micro: int,
    n_points: int,
    escape_prob: float,
    quality_score: float,
    timeframe: str,
) -> List[str]:
    alerts: List[str] = []
    if quality_score < 0.2:
        alerts.append("LOW_QUALITY_FORCE_NOISY")
    if escape_prob >= 0.99 or escape_prob <= 0.01:
        alerts.append("DEGENERATE_TRANSITIONS")
    # Weekly series are shorter; allow a larger microstate ratio before warning.
    limit = n_points // (2 if timeframe == "weekly" else 6)
    if n_micro > max(1, limit):
        alerts.append("TOO_MANY_MICROSTATES")
    return alerts
