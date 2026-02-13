from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from engine.adapters.ons import normalize_ons


_ONS_HINT_COLUMNS = {
    "din_instante",
    "nom_subsistema",
    "id_subsistema",
    "val_cargaenergiamwmed",
}


def _should_normalize_ons(source: Optional[str], df: pd.DataFrame) -> bool:
    if source == "ONS":
        return True
    if source:
        return False
    return any(col in df.columns for col in _ONS_HINT_COLUMNS)


def preprocess(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    source: Optional[str] = None,
    ons_mode: str = "sum",
    ons_filters: Optional[Dict[str, str]] = None,
    limpar: bool = False,
    limite_pico: float = 6.0,
    preencher: bool = True,
    remover_repetidos: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, float], str, str]:
    work = df.copy()
    if _should_normalize_ons(source, work):
        work = normalize_ons(
            work,
            time_col=time_col,
            value_col=value_col,
            mode=ons_mode,
            select_filters=ons_filters,
        )
        time_col = "time"
        value_col = "value"

    rows_in = int(len(work))
    invalid_time = int(work[time_col].isna().sum())
    work = work.dropna(subset=[time_col])

    removed_duplicates = 0
    if remover_repetidos:
        before = len(work)
        work = work.groupby(time_col, as_index=False)[value_col].mean()
        removed_duplicates = int(before - len(work))

    work = work.sort_values(time_col).reset_index(drop=True)

    clamped_points = 0
    filled_points = 0

    if limpar:
        median = float(work[value_col].median())
        mad = float(np.median(np.abs(work[value_col] - median)))
        if mad > 0:
            lower = median - limite_pico * mad
            upper = median + limite_pico * mad
            before_vals = work[value_col].copy()
            work[value_col] = work[value_col].clip(lower=lower, upper=upper)
            clamped_points = int((before_vals != work[value_col]).sum())

    if preencher:
        before_na = int(work[value_col].isna().sum())
        work[value_col] = work[value_col].ffill(limit=3)
        after_na = int(work[value_col].isna().sum())
        filled_points = max(0, before_na - after_na)

    work = work.dropna(subset=[value_col])

    if len(work) < 2:
        raise ValueError("Not enough data points after preprocessing.")

    deltas = work[time_col].diff().dt.total_seconds().dropna()
    deltas = deltas[deltas > 0]
    dt_seconds = float(np.median(deltas)) if not deltas.empty else float("nan")

    rows_out = int(len(work))
    altered = invalid_time + removed_duplicates + clamped_points + filled_points
    ratio = altered / max(rows_in, 1)
    if rows_out < 10 or np.isnan(dt_seconds):
        confianca = "baixa"
    elif ratio >= 0.2:
        confianca = "baixa"
    elif ratio >= 0.05:
        confianca = "media"
    else:
        confianca = "alta"

    meta = {
        "dt_seconds": dt_seconds,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "invalid_time": invalid_time,
        "removed_duplicates": removed_duplicates,
        "clamped_points": clamped_points,
        "filled_points": filled_points,
        "confianca": confianca,
    }
    return work, meta, time_col, value_col
