from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


def read_csv(input_path: Path, time_col: str, value_col: str) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"CSV not found: {input_path}")

    try:
        df = pd.read_csv(input_path, sep=None, engine="python")
    except Exception as exc:
        raise ValueError(f"Failed to read CSV: {exc}") from exc

    missing = [col for col in (time_col, value_col) if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. Available columns: {list(df.columns)}"
        )

    return df[[time_col, value_col]].copy()


def coerce_types(df: pd.DataFrame, time_col: str, value_col: str) -> pd.DataFrame:
    out = df.copy()
    out[time_col] = pd.to_datetime(out[time_col], errors="coerce")
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce")
    return out


def load_dataset(
    input_path: Path, time_col: str, value_col: str
) -> Tuple[pd.DataFrame, str, str]:
    df = read_csv(input_path, time_col, value_col)
    df = coerce_types(df, time_col, value_col)
    return df, time_col, value_col
