"""Legacy graph_engine compatibility package.

This module intentionally avoids eager imports to prevent circular
dependencies during transitional migration to ``engine.graph``.
"""

__all__ = [
    "GraphAsset",
    "GraphConfig",
    "GraphLinks",
    "GraphMetrics",
    "GraphState",
    "GraphResult",
    "run_graph_engine",
]


def __getattr__(name: str):
    if name in __all__:
        from engine.graph import __dict__ as _graph_dict

        return _graph_dict[name]
    raise AttributeError(f"module 'graph_engine' has no attribute {name!r}")
