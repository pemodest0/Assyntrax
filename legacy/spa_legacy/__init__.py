"""Legacy SPA compatibility package.

This module intentionally avoids eager imports to prevent circular
dependencies during transitional migration to ``engine``.
"""

__all__ = [
    "TemporalConfig",
    "TemporalSummary",
    "YearResult",
    "build_temporal_report",
    "compare_models",
    "evaluate_years",
    "load_yearly_csv",
    "select_best_horizon",
]


def __getattr__(name: str):
    if name in __all__:
        from engine.temporal import __dict__ as _temporal_dict

        return _temporal_dict[name]
    raise AttributeError(f"module 'spa' has no attribute {name!r}")

