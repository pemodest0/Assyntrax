from __future__ import annotations

import hashlib
from typing import Iterable, Tuple

import numpy as np
import pandas as pd


def ensure_sorted_dates(dates: Iterable) -> None:
    series = pd.Series(pd.to_datetime(dates, errors="coerce")).dropna()
    if not series.is_monotonic_increasing:
        raise ValueError("Datas fora de ordem; ordene antes de treinar/testar.")


def validate_time_split(
    dates: Iterable,
    train_mask: np.ndarray,
    test_mask: np.ndarray,
    train_end: pd.Timestamp | None = None,
    test_start: pd.Timestamp | None = None,
    test_end: pd.Timestamp | None = None,
) -> None:
    dates = pd.Series(pd.to_datetime(dates, errors="coerce"))
    ensure_sorted_dates(dates)
    train_mask = np.asarray(train_mask, dtype=bool)
    test_mask = np.asarray(test_mask, dtype=bool)
    if not train_mask.any() or not test_mask.any():
        raise ValueError("Split invalido: treino ou teste vazio.")
    if np.any(train_mask & test_mask):
        raise ValueError("Split invalido: sobreposicao entre treino e teste.")
    if train_end is not None:
        if dates[train_mask].max() > train_end:
            raise ValueError("Dados de treino passam do limite temporal.")
        if dates[test_mask].min() <= train_end:
            raise ValueError("Dados de teste incluem datas de treino.")
    if test_start is not None and dates[test_mask].min() < test_start:
        raise ValueError("Dados de teste incluem datas antes do inicio definido.")
    if test_end is not None and dates[test_mask].max() > test_end:
        raise ValueError("Dados de teste incluem datas apos o fim definido.")


def split_hash(train_idx: np.ndarray, test_idx: np.ndarray) -> str:
    payload = np.concatenate([train_idx.astype(np.int64), test_idx.astype(np.int64)])
    return hashlib.sha256(payload.tobytes()).hexdigest()


def safe_test_indices(test_mask: np.ndarray, min_valid_index: int) -> Tuple[np.ndarray, int]:
    test_mask = np.asarray(test_mask, dtype=bool)
    test_indices = np.where(test_mask)[0]
    if test_indices.size == 0:
        return np.array([], dtype=int), 0
    safe_indices = test_indices[test_indices >= min_valid_index]
    dropped = int(test_indices.size - safe_indices.size)
    return safe_indices, dropped
