# Legacy Candidates (safe-first)

## Active (keep in runtime)
- engine/
- spa/ (compat wrappers during transition)
- graph_engine/ (compat wrappers during transition)
- scripts/ops/
- scripts/bench/validation/
- scripts/realestate/
- website-ui/
- config/
- data/realestate/core/
- data/realestate/normalized/
- data/raw/realestate/manifest.json
- models/auto_regime_model.joblib (+ meta)

## Moved to legacy already
- legacy/root_artifacts/b178833c-66ac-4975-a2c1-29ff93dade38.png
- legacy/root_artifacts/ChatGPT Image 26 de jan. de 2026, 12_34_08.png
- legacy/root_artifacts/Temporal engine.docx

## Removed accidental root garbage
- --mode
- --outdir
- --tickers
- --timeframes

## Candidate to move to legacy (manual approval needed)
- docs/old narrative notes not linked by README (if any)
- scripts/lab/ (if not used in ops/product flow)
- scripts/maintenance/ (after verifying no scheduled task calls)
- legacy wrappers removal stage (spa/graph_engine package-level) only after all imports are stable on engine/

## Not recommended to move now
- VIX (Índice de Volatilidade).pdf (used by scripts/report/extract_vix_pdf_to_md.py default)
- data_sources.json (used by spa/run.py and scripts/data/fetch_datasets.py)
