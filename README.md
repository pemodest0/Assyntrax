# A-firma Workspace

Toolkit for building and analysing quantum-inspired financial pipelines. This repo bundles source modules, experiment scripts, dashboards and generated artifacts; the notes below highlight where to look for each piece and how to keep the tree tidy.

## Project Layout
- `src/` – core Python packages (`data_pipeline`, `graph_discovery`, `walks`, etc.) used by pipelines, models and experiments.
- `app/` – interactive dashboards and exploratory UIs (Dash/Streamlit) such as `asset_forecast_dashboard.py`, `quantum_explorer.py` and the Ising visualiser.
- `scripts/` – CLI utilities to download data, train models, run forecasts and compare walk strategies (`run_daily_forecast.py`, `run_graph_discovery_*.py`, ...).
- `analysis/` – offline studies and reporting helpers (`stress_pipeline.py`, `metrics_comparison.py`, `make_report.py`).
- `configs/` – JSON configurations for domain-specific pipelines (`data_pipeline_finance.json`, `pipeline_yf*.json`, target definitions).
- `data/` – local datasets (Yahoo Finance dumps under `data/yf`, CSV demos per vertical, synthetic benchmarks, metrics).
- `results/` – generated outputs from scripts/dashboards (forecast metrics, charts, graph discovery dumps).
- `docs/` – Markdown documentation plus reference material now under `docs/references/`.
- `tests/` – pytest suite covering ingestion, quality checks and model sanity tests.

## Common Tasks
- **Run a finance pipeline:** `python scripts/run_pipeline.py --config configs/data_pipeline_finance.json`
- **Daily forecasts:** `python scripts/run_daily_forecast.py --config configs/live_forecast_template.json`
- **Graph discovery:** `python scripts/run_graph_discovery_finance.py`
- **Dashboards:** `python -m app.asset_forecast_dashboard` (or launch other apps from `app/`).
- **Tests:** `pytest` (runs fast unit/regression tests in `tests/`).

## Data & Results Hygiene
- Large CSV exports and forecasts live in `data/` and `results/`. Periodically archive or prune older runs (e.g. move dated folders under `results/archive/`) to keep the repo lean.
- Temporary artefacts (`__pycache__`, `.pyc`, `.pytest_cache`) and platform files (`.DS_Store`) are safe to delete; rerun the cleanup command if they reappear:
  ```powershell
  Get-ChildItem -Recurse -Filter '.DS_Store' -File | Remove-Item -Force
  Get-ChildItem -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
  Get-ChildItem -Recurse -Filter '*.pyc' -File | Remove-Item -Force
  ```
- External references (papers, reports) now live in `docs/references/`; add new material there instead of the repo root.

## Development Notes
- Python caches and generated results are ignored via `.gitignore`; commit only source, configs and curated documentation.
- For new pipelines, base them on the existing templates in `configs/` and document the naming convention to avoid duplicates.
- Keep documentation (`docs/`) and this README up to date when creating new dashboards, scripts or experimental domains.

