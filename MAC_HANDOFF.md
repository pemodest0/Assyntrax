# Mac Handoff Guide

This file summarizes the current state and how to continue on the Mac.

## Repo state
- Project root: `C:\Users\Pedro Henrique\Desktop\A-firma`
- Engine name: **spa.engine**
- Key modules:
  - `spa/engine/diagnostics/regime_labels.py` (Takens embedding, clustering, labeling, local features)
  - `spa/engine/diagnostics/auto_regime_model.py` (auto-regime model + feature vector)
- New scripts:
  - `scripts/run_phase1_curriculum.py` (local+real data ingest; supports `--no-plots`)
  - `scripts/run_phase1_heavy_synthetic.py` (heavy synthetic generator w/ progress)
  - `scripts/run_auto_benchmark.py` (benchmark pipeline)
  - `scripts/run_global_multivariate.py` (global multivariate map)
  - `scripts/generate_universe_report.py` (final report)
  - `scripts/train_auto_regime_model.py`, `scripts/evaluate_auto_regime_model.py`
  - `scripts/compare_auto_eval.py`, `scripts/run_with_progress.py`

## Latest results (Windows)
- Auto model (after heavy synthetic):
  - Holdout accuracy ~0.93
  - Weighted F1 ~0.93
  - See `results/auto_regime_eval/report.md`
- Heavy synthetic generated in `results/phase1_heavy_synthetic/`

## What NOT to copy to the Mac
- `results/` (large, can be regenerated)
- `data/` (unless you need specific local datasets)

## What to copy to the Mac (USB)
- `scripts/`
- `spa/engine/`
- `models/` (if you want the trained auto-regime model)
- `MAC_HANDOFF.md` (this file)

## Recommended setup on Mac
1) Create a fresh clone or copy the repo.
2) Install deps:
   - Python 3.10+
   - `pip install numpy pandas scikit-learn hdbscan matplotlib tqdm yfinance scipy`
3) (Optional) restore model:
   - copy `models/auto_regime_model.joblib`
   - copy `models/auto_regime_model_meta.json`

## Main commands (Mac)
### 1) Build the global multivariate map (universe)
```bash
python scripts/run_global_multivariate.py \
  --outdir results/global_multivariate \
  --allow-downloads \
  --start 2000-01-01 --end 2024-12-31 \
  --m 2 --tau 1 --pca 10 --method auto
```

### 2) Generate final universe report
```bash
python scripts/generate_universe_report.py \
  --global-dir results/global_multivariate \
  --eval-report results/auto_regime_eval/report.md \
  --out results/universe_report.md
```

### 3) If you want to rebuild the auto-regime model
```bash
python scripts/train_auto_regime_model.py --results results --model-dir models
python scripts/evaluate_auto_regime_model.py \
  --results results --model-dir models \
  --outdir results/auto_regime_eval \
  --min-count 2 --kfold 5 --group-holdout --group-kfold
```

## Notes
- If downloads get blocked by yfinance, run in smaller ticker batches.
- For lighter runs, use `--no-plots` in `run_phase1_curriculum.py`.
- The global multivariate pipeline is intentionally **no-plots** to keep it light.
