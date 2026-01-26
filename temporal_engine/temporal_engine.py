from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import csv
import math

import numpy as np


@dataclass
class TemporalConfig:
    min_improvement_pct: float = 0.02
    required_win_rate: float = 0.6
    required_years_min: int = 5
    max_std_improvement: float = 0.15


@dataclass
class YearResult:
    year: int
    model_error: float
    baseline_error: float


@dataclass
class TemporalSummary:
    verdict: str
    horizon: str
    years: int
    win_rate: float
    avg_improvement: float
    std_improvement: float
    wins: int
    losses: int
    gap_to_target: float
    notes: List[str]


def _improvement(model_error: float, baseline_error: float) -> float | None:
    if baseline_error is None or baseline_error <= 0:
        return None
    return (baseline_error - model_error) / baseline_error


def evaluate_years(years: Iterable[YearResult], cfg: TemporalConfig) -> TemporalSummary:
    improvements: List[float] = []
    for item in years:
        value = _improvement(item.model_error, item.baseline_error)
        if value is None or not math.isfinite(value):
            continue
        improvements.append(value)

    if not improvements:
        return TemporalSummary(
            verdict="NAO",
            horizon="",
            years=0,
            win_rate=0.0,
            avg_improvement=0.0,
            std_improvement=0.0,
            wins=0,
            losses=0,
            gap_to_target=1.0,
            notes=["Sem dados suficientes para avaliar previsibilidade."],
        )

    wins = sum(1 for v in improvements if v >= cfg.min_improvement_pct)
    losses = len(improvements) - wins
    win_rate = wins / len(improvements)
    avg_improvement = float(np.mean(improvements))
    std_improvement = float(np.std(improvements)) if len(improvements) > 1 else 0.0

    notes: List[str] = []
    if len(improvements) < cfg.required_years_min:
        verdict = "DEPENDE"
        notes.append("Amostra de anos insuficiente para veredito definitivo.")
    elif win_rate >= cfg.required_win_rate and avg_improvement >= cfg.min_improvement_pct:
        verdict = "SIM"
    elif win_rate >= 0.4 and avg_improvement > 0:
        verdict = "DEPENDE"
        notes.append("Ganho positivo, mas inconsistência entre anos.")
    else:
        verdict = "NAO"

    if std_improvement > cfg.max_std_improvement:
        notes.append("Variabilidade alta; resultados instáveis ano a ano.")

    gap_win = max(0.0, cfg.required_win_rate - win_rate)
    gap_gain = max(0.0, cfg.min_improvement_pct - avg_improvement)
    gap_to_target = max(gap_win, gap_gain)

    return TemporalSummary(
        verdict=verdict,
        horizon="",
        years=len(improvements),
        win_rate=win_rate,
        avg_improvement=avg_improvement,
        std_improvement=std_improvement,
        wins=wins,
        losses=losses,
        gap_to_target=gap_to_target,
        notes=notes,
    )


def select_best_horizon(
    horizon_results: Dict[str, List[YearResult]],
    cfg: TemporalConfig,
) -> Tuple[str, TemporalSummary]:
    summaries: Dict[str, TemporalSummary] = {}
    for horizon, results in horizon_results.items():
        summary = evaluate_years(results, cfg)
        summary.horizon = horizon
        summaries[horizon] = summary

    best = None
    for horizon, summary in summaries.items():
        if best is None:
            best = summary
            continue
        if summary.verdict == "SIM" and best.verdict != "SIM":
            best = summary
            continue
        if summary.verdict == best.verdict:
            if summary.win_rate > best.win_rate:
                best = summary
            elif summary.win_rate == best.win_rate and summary.avg_improvement > best.avg_improvement:
                best = summary

    if best is None:
        best = TemporalSummary(
            verdict="NAO",
            horizon="",
            years=0,
            win_rate=0.0,
            avg_improvement=0.0,
            std_improvement=0.0,
            wins=0,
            losses=0,
            gap_to_target=1.0,
            notes=["Nenhum horizonte disponível para avaliação."],
        )
    return best.horizon, best


def compare_models(
    models: Dict[str, Dict[str, List[YearResult]]],
    cfg: TemporalConfig,
) -> Dict[str, TemporalSummary]:
    summaries: Dict[str, TemporalSummary] = {}
    for model_name, horizon_data in models.items():
        horizon, summary = select_best_horizon(horizon_data, cfg)
        summary.horizon = horizon
        summaries[model_name] = summary
    return summaries


def build_temporal_report(
    summaries: Dict[str, TemporalSummary],
    cfg: TemporalConfig,
) -> Dict[str, object]:
    if not summaries:
        return {
            "verdict": "NAO",
            "notes": ["Sem modelos avaliados."],
        }

    best_model = None
    for name, summary in summaries.items():
        if best_model is None:
            best_model = name
            continue
        current = summaries[best_model]
        if summary.verdict == "SIM" and current.verdict != "SIM":
            best_model = name
            continue
        if summary.verdict == current.verdict:
            if summary.win_rate > current.win_rate:
                best_model = name
            elif summary.win_rate == current.win_rate and summary.avg_improvement > current.avg_improvement:
                best_model = name

    best_summary = summaries[best_model]
    verdict = best_summary.verdict
    horizon = best_summary.horizon or "indefinido"

    notes = list(best_summary.notes)
    if verdict == "SIM":
        notes.append(
            f"Modelo {best_model} superou baseline em {best_summary.wins} de {best_summary.years} anos."
        )
    elif verdict == "DEPENDE":
        notes.append("Previsibilidade parcial: usar apenas em horizontes curtos ou condições estáveis.")
    else:
        notes.append("Não há evidência consistente de previsibilidade útil.")

    return {
        "verdict": verdict,
        "best_model": best_model,
        "horizon": horizon,
        "win_rate": best_summary.win_rate,
        "avg_improvement": best_summary.avg_improvement,
        "std_improvement": best_summary.std_improvement,
        "gap_to_target": best_summary.gap_to_target,
        "config": {
            "min_improvement_pct": cfg.min_improvement_pct,
            "required_win_rate": cfg.required_win_rate,
            "required_years_min": cfg.required_years_min,
        },
        "model_summaries": {
            name: {
                "verdict": summary.verdict,
                "horizon": summary.horizon,
                "years": summary.years,
                "win_rate": summary.win_rate,
                "avg_improvement": summary.avg_improvement,
                "std_improvement": summary.std_improvement,
                "gap_to_target": summary.gap_to_target,
                "notes": summary.notes,
            }
            for name, summary in summaries.items()
        },
        "notes": notes,
    }


def load_yearly_csv(
    path: Path,
    year_col: str,
    model_col: str,
    baseline_col: str,
) -> List[YearResult]:
    rows: List[YearResult] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if year_col not in row or model_col not in row or baseline_col not in row:
                continue
            try:
                year = int(float(row[year_col]))
                model_error = float(row[model_col])
                baseline_error = float(row[baseline_col])
            except ValueError:
                continue
            rows.append(YearResult(year=year, model_error=model_error, baseline_error=baseline_error))
    return rows
