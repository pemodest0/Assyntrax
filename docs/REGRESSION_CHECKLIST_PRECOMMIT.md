# Pre-Commit Regression Checklist

## Scope
- Unified public package: `engine/`
- Legacy compatibility wrappers: `spa`, `graph_engine`
- Script imports migrated from legacy modules to `engine.*`

## Automated checks run
- `python -m py_compile engine/__init__.py engine/graph/__init__.py engine/temporal/__init__.py spa/__init__.py graph_engine/__init__.py`
- `python scripts/bench/run_finance_walkforward.py --help`
- `python scripts/bench/run_graph_regime_universe.py --help`
- `python -m compileall -q engine spa graph_engine scripts`
- `python -c "from spa import TemporalConfig; from graph_engine import run_graph_engine; print('compat_ok')"`

## Results
- All checks passed after fixing `from __future__` ordering in 5 scripts.
- No direct imports from `spa.*` or `graph_engine.*` remain under `scripts/`.
- Legacy wrappers still resolve old imports.

## Notes
- This change does not remove old modules; it introduces a stable API and keeps compatibility.
- Full functional benchmark suite should still be executed before release commit.
