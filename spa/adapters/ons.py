from __future__ import annotations

from typing import Dict, Optional

import pandas as pd


_FILTER_ALIASES = {
    "subsistema": ["nom_subsistema", "id_subsistema"],
    "subsystem": ["nom_subsistema", "id_subsistema"],
}


def _resolve_filter_key(df: pd.DataFrame, key: str) -> Optional[str]:
    if key in df.columns:
        return key
    for alias in _FILTER_ALIASES.get(key, []):
        if alias in df.columns:
            return alias
    return None


def normalize_ons(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    group_cols: Optional[list[str]] = None,
    mode: str = "sum",
    select_filters: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    work = df.copy()
    work[time_col] = pd.to_datetime(work[time_col], errors="coerce")
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[time_col, value_col])

    if mode not in {"sum", "select"}:
        raise ValueError(f"Unsupported ons mode: {mode}")

    if mode == "select":
        if not select_filters:
            raise ValueError("select mode requires --ons-filter KEY=VALUE")
        for key, value in select_filters.items():
            resolved = _resolve_filter_key(work, key)
            if not resolved:
                raise ValueError(f"Filter column not found: {key}")
            work = work[work[resolved] == value]

    if group_cols:
        group_keys = [time_col] + group_cols
        grouped = work.groupby(group_keys, as_index=False)[value_col].sum()
        work = grouped

    aggregated = work.groupby(time_col, as_index=False)[value_col].sum()
    aggregated = aggregated.sort_values(time_col).drop_duplicates(subset=[time_col])
    aggregated = aggregated.rename(columns={time_col: "time", value_col: "value"})
    return aggregated[["time", "value"]]

