from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd


@dataclass
class PredictionRecord:
    timestamp: str
    asset: str
    timeframe: str
    horizon: int | None = None
    regime_label: str | None = None
    regime_confidence: float | None = None
    regime_risk: str | None = None
    novelty_score: float | None = None
    transition_rate: float | None = None
    entropy: float | None = None
    y_true: float | None = None
    y_pred: float | None = None
    y_pred_p10: float | None = None
    y_pred_p50: float | None = None
    y_pred_p90: float | None = None
    model_name: str | None = None
    model_family: str | None = None
    forecast_confidence: float | None = None
    warnings: List[str] = field(default_factory=list)
    mase_6m: float | None = None
    smape_6m: float | None = None
    diracc_6m: float | None = None


def _to_dict(rec: PredictionRecord | dict) -> dict:
    if isinstance(rec, PredictionRecord):
        data = asdict(rec)
    else:
        data = dict(rec)
    data["warnings"] = data.get("warnings") or []
    return data


def save_prediction_records(records: Sequence[PredictionRecord | dict], path_jsonl: str | Path, path_csv: str | Path) -> None:
    path_jsonl = Path(path_jsonl)
    path_csv = Path(path_csv)
    rows = [_to_dict(r) for r in records]
    if not rows:
        path_jsonl.write_text("", encoding="utf-8")
        pd.DataFrame(columns=[field for field in PredictionRecord.__dataclass_fields__]).to_csv(path_csv, index=False)
        return
    with path_jsonl.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False))
            f.write("\n")
    df = pd.DataFrame(rows)
    df.to_csv(path_csv, index=False)
