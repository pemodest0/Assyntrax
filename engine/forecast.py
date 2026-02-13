from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd


def _infer_step(time_series: pd.Series, dt_seconds: float) -> Optional[pd.Timedelta]:
    if np.isnan(dt_seconds):
        return None
    return pd.to_timedelta(dt_seconds, unit="s")


def _media_recente(values: pd.Series, window: int) -> float:
    window = max(1, min(window, len(values)))
    return float(values.iloc[-window:].mean())


def _tendencia_curta(values: pd.Series, window: int) -> Tuple[float, float]:
    window = max(2, min(window, len(values)))
    y = values.iloc[-window:].to_numpy()
    x = np.arange(window)
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def forecast_series(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    horizon: int,
    method: str,
    dt_seconds: float,
) -> Tuple[pd.DataFrame, str]:
    if horizon <= 0:
        return pd.DataFrame(columns=["time", "value_previsto"]), "Previsao desativada."

    step = _infer_step(df[time_col], dt_seconds)
    if step is None:
        return pd.DataFrame(columns=["time", "value_previsto"]), "Nao foi possivel prever porque o passo de tempo e irregular."

    last_time = df[time_col].iloc[-1]
    values = df[value_col]
    times = [last_time + step * (i + 1) for i in range(horizon)]

    if method == "tendencia_curta":
        slope, intercept = _tendencia_curta(values, window=7)
        preds = [slope * (len(values) + i) + intercept for i in range(1, horizon + 1)]
    else:
        mean_val = _media_recente(values, window=7)
        preds = [mean_val for _ in range(horizon)]

    forecast_df = pd.DataFrame({"time": times, "value_previsto": preds})
    return forecast_df, "Previsao simples baseada nos pontos mais recentes."
