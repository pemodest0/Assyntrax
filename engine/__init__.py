"""Unified engine package with stable public API."""

from engine.graph import GraphAsset, GraphConfig, GraphLinks, GraphMetrics, GraphResult, GraphState, run_graph_engine
from engine.temporal import (
    TemporalConfig,
    TemporalSummary,
    YearResult,
    build_temporal_report,
    compare_models,
    evaluate_years,
    load_yearly_csv,
    select_best_horizon,
)

__all__ = [
    "GraphAsset",
    "GraphConfig",
    "GraphLinks",
    "GraphMetrics",
    "GraphResult",
    "GraphState",
    "run_graph_engine",
    "TemporalConfig",
    "TemporalSummary",
    "YearResult",
    "build_temporal_report",
    "compare_models",
    "evaluate_years",
    "load_yearly_csv",
    "select_best_horizon",
]
