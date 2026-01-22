from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def compute_features(df: pd.DataFrame, time_col: str, value_col: str) -> Dict[str, object]:
    series = df[value_col]
    increments = series.diff().dropna()
    rolling_std = series.rolling(window=24, min_periods=2).std()

    autocorr = {}
    for lag in range(1, 25):
        autocorr[str(lag)] = float(series.autocorr(lag=lag))

    return {
        "mean": float(series.mean()),
        "std": float(series.std()),
        "increments": increments,
        "rolling_std": rolling_std,
        "autocorr": autocorr,
    }

