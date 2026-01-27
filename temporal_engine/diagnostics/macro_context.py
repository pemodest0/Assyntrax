"""Utilidades para anexar contexto macro a transições de regimes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from pathlib import Path

import numpy as np

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

MONTHS = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}


@dataclass(frozen=True)
class MacroEvent:
    asset: str
    date_start: datetime
    date_end: datetime
    variation: str
    description: str
    date_text: str


def _parse_date_piece(day: str, month: str, year: str) -> datetime:
    return datetime(int(year), MONTHS[month.lower()], int(day))


def parse_date_range(text: str) -> tuple[datetime, datetime] | None:
    text = text.strip()
    # 29 dez 2012 – 4 jan 2013
    match = re.match(r"(\d{1,2})\s+(\w{3})\s+(\d{4})\s*[–-]\s*(\d{1,2})\s+(\w{3})\s+(\d{4})", text)
    if match:
        d1, m1, y1, d2, m2, y2 = match.groups()
        return _parse_date_piece(d1, m1, y1), _parse_date_piece(d2, m2, y2)
    # 22–28 fev 2020
    match = re.match(r"(\d{1,2})\s*[–-]\s*(\d{1,2})\s+(\w{3})\s+(\d{4})", text)
    if match:
        d1, d2, m, y = match.groups()
        start = _parse_date_piece(d1, m, y)
        end = _parse_date_piece(d2, m, y)
        return start, end
    # 2 mar 2007
    match = re.match(r"(\d{1,2})\s+(\w{3})\s+(\d{4})", text)
    if match:
        d, m, y = match.groups()
        dt = _parse_date_piece(d, m, y)
        return dt, dt
    return None


def load_macro_events(md_path: Path) -> list[MacroEvent]:
    if not md_path.exists():
        return []
    events: list[MacroEvent] = []
    current_asset = ""
    for raw in md_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            current_asset = line.replace("## ", "").strip()
            continue
        if not line.startswith("|"):
            continue
        if "---" in line or "Data" in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        date_text, variation, description = parts[0], parts[1], "|".join(parts[2:]).strip()
        parsed = parse_date_range(date_text)
        if parsed is None:
            continue
        start, end = parsed
        events.append(
            MacroEvent(
                asset=current_asset,
                date_start=start,
                date_end=end,
                variation=variation,
                description=description,
                date_text=date_text,
            )
        )
    return events


def _to_datetime_array(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values)
    if pd is not None:
        return pd.to_datetime(arr).to_numpy()
    return arr.astype("datetime64[ns]")


def annotate_transitions(
    dates: np.ndarray,
    labels: np.ndarray,
    events: list[MacroEvent],
    asset: str | None = None,
    window_days: int = 3,
) -> list[dict[str, str]]:
    if dates.size == 0 or labels.size == 0:
        return []
    dates_dt = _to_datetime_array(dates)
    window = np.timedelta64(int(window_days), "D")
    notes: list[dict[str, str]] = []
    for idx in range(1, len(labels)):
        if labels[idx] == labels[idx - 1]:
            continue
        t = dates_dt[idx]
        for ev in events:
            if asset and asset.lower() not in ev.asset.lower():
                continue
            ev_start = np.datetime64(ev.date_start)
            ev_end = np.datetime64(ev.date_end)
            if t + window < ev_start or t - window > ev_end:
                continue
            notes.append(
                {
                    "date": str(t)[:10],
                    "from": str(labels[idx - 1]),
                    "to": str(labels[idx]),
                    "asset": ev.asset,
                    "range": ev.date_text,
                    "variation": ev.variation,
                    "description": ev.description,
                }
            )
    return notes
