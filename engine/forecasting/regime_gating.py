from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class GatingDecision:
    selected_model: str
    forecast_confidence: float
    use_forecast_bool: bool
    warnings: list[str]


def select_model_for_regime(
    registry: pd.DataFrame,
    asset: str,
    timeframe: str,
    regime_label: str,
    regime_confidence: float,
    novelty_score: float,
    mase_col: str = "mase",
) -> GatingDecision:
    warnings: list[str] = []
    if regime_confidence < 0.6 or novelty_score > 0.95:
        warnings.append("REGIME_INSTAVEL")
        return GatingDecision(
            selected_model="naive_persistence",
            forecast_confidence=0.2,
            use_forecast_bool=False,
            warnings=warnings,
        )

    subset = registry[
        (registry["asset"] == asset)
        & (registry["timeframe"] == timeframe)
        & (registry["regime_label"] == regime_label)
    ]
    if subset.empty:
        warnings.append("REGISTRY_EMPTY")
        return GatingDecision(
            selected_model="naive_persistence",
            forecast_confidence=0.4,
            use_forecast_bool=True,
            warnings=warnings,
        )

    grouped = subset.groupby("model_name")[mase_col].mean()
    best_model = grouped.sort_values().index[0]
    best_mase = float(grouped.loc[best_model])
    conf = float(np.clip(1.2 - best_mase, 0.1, 0.9))
    return GatingDecision(
        selected_model=best_model,
        forecast_confidence=conf,
        use_forecast_bool=True,
        warnings=warnings,
    )
