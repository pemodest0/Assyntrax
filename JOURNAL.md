# Journal

## 2026-01-31
Macro:
- Added a parallel Graph Regime Engine path (`graph_engine/`) without touching the legacy motor.
- Outputs are written to `results/latest_graph/` and designed for website consumption.

Methods used:
- Takens embedding (reused concept) + KMeans microstates.
- Transition matrix P with alpha smoothing.
- Spectral clustering for metastable regimes.
- Graph quality metrics: LCC ratio, low-degree fraction, occupancy entropy, coverage.
- Automatic threshold calibration via quantiles (escape/stretch).
- Gating logic: NOISY only when quality is low.

Current status:
- Example + batch script exist.
- Output schema includes quality, thresholds, recommendation, scores, badges, and optional merges from existing outputs.

Sanity:
- Added sanity checks for degenerate transitions, too many microstates, and low quality forcing NOISY.
- Writes `results/latest_graph/sanity_summary.json`.

Improvements (quality + thresholds):
- Enforced kNN minimum in fast mode to avoid disconnected graphs.
- Adapted n_micro to series length.
- Clipped stretch values by quantiles (q05/q95) before threshold calibration.
- NOISY threshold set to 0.3 (quality-based).

Product polish:
- Added schema_version to graph outputs.
- Reports page renders *_report.md inside the app.
- System Health now reads sanity_summary.json.
- Dashboard shows executive summary (USE/CAUTION/AVOID) from latest_graph universe.

Latest run snapshot (fast, daily+weekly, 41 assets each):
- States: daily 35 TRANSITION / 6 STABLE; weekly 24 TRANSITION / 17 STABLE.
- Recommendations: daily 35 CAUTION / 6 USE; weekly 24 CAUTION / 17 USE.
- Quality scores high (median ~0.95 daily, ~0.93 weekly); NOISY not triggered.
- Alerts concentrated in LOW_CONFIDENCE + REGIME_INSTAVEL; weekly has TOO_MANY_MICROSTATES warnings across assets.
Notes:
- Weekly runs likely benefit from lower n_micro or adjusted microstate sanity threshold.
- Consider tuning escape/stretch quantiles to surface some UNSTABLE labels when regimes are genuinely unstable.

Updates queued (in progress):
- Weekly effective n_micro reduced and microstate sanity threshold relaxed.
- Threshold quantiles adjusted to surface more UNSTABLE labels.
- Confidence/escape smoothed via median filter before labeling.
- Summary JSON per run to compare experiments easily.

Study reference:
- Added `docs/REGIME_METHODS_STUDY.md` with the full theoretical basis
  (Takens, MSM, spectral clustering, regime classification, metrics).

New features (embedded parameters + metrics):
- Auto embedding params (tau via autocorr, m via FNN) with CLI flags in batch script.
- Graph quality now includes Markov entropy rate and graph density.

Auto-embed tuning:
- Constrained tau to <= 3 and m to <= 4.
- Relaxed FNN threshold to 0.15 (less aggressive m selection).

Defaults:
- Manual embedding (m=3, tau=1) is now the default.
- Auto-embed is experimental and requires `--auto-embed`.

Validation:
- Added `scripts/bench/run_graph_regime_validation.py` for synthetic regimes with ground truth.

Auto-embed methods:
- Tau selection supports AMI (default) or ACF via `--tau-method`.
- m selection supports Cao (default) or FNN via `--m-method`.

UI updates:
- Homepage now shows Recent Diagnostics from real graph plots with filters.
- Methods page expanded into sections with leigo/formal blocks.
- About page expanded with story + timeline.
- Dashboard now includes portfolio view, favorites, and direct plot links.
- Graph Engine page includes pipeline diagram and validation summary.

Backtest:
- Added `scripts/bench/run_graph_regime_backtest.py` (walk-forward year-by-year).
- Dashboard includes Backtest by Regime panel with latest series + naive next-day forecast.

Forecast training:
- Added `scripts/bench/run_graph_regime_forecast_train.py` for multi-horizon walk-forward.
- Dashboard backtest panel now supports target + horizon selection.

Microstates tuning:
- Added per-timeframe n_micro overrides in universe runner.
- Weekly microstate sanity threshold relaxed.

Old motor comparison:
- Added `scripts/bench/compare_kmeans_hdbscan.py` to summarize legacy kmeans/hdbscan outputs.

Threshold tuning:
- Lowered escape/stretch quantiles to make UNSTABLE more likely (q65/q70).

Official regimes:
- Added `scripts/data/fetch_official_regimes.py` to download USREC/NFCI/VIX and build `official_regimes.csv`.

Official comparison:
- Added `scripts/bench/compare_official_regimes.py` to compare graph regimes vs USREC/NFCI/VIX.
- 2026-01-31: Extended official regime comparison to include lag sweep, balanced metrics (BA/F1/precision/recall/MCC), and turning-point hit rates with false alarms. Updated `compare_official_regimes.py` and re-ran for SPY/QQQ/GLD daily; outputs in `results/official_regimes/compare/`.
- 2026-01-31: Added risk-mode selector (UNSTABLE-only vs UNSTABLE+TRANSITION) plus quality/confidence filters to `compare_official_regimes.py` for more realistic regime alignment tests.
- 2026-01-31: Added anti-false-alarm smoothing to official comparison: min-run filtering and cooldown between risk signals; updated metrics to use smoothed risk series.
- 2026-01-31: Added daily pipeline runner and cron wrapper (`scripts/ops/run_daily_pipeline.py`, `scripts/ops/cron_daily.sh`) plus `docs/DAILY_PIPELINE.md` for scheduling instructions.
- 2026-01-31: Added global sector endpoint `/api/graph/sector`, new Global Regimes page, and richer RegimeChart legend/gradient. Linked Global Regimes in app nav.
- 2026-01-31: Step 8 UX refinements: sector filters (state/region/recommendation + lead asset), RegimeChart legend, BenchmarkChart labels, forecast gate badges, and tooltips on metrics.
- 2026-01-31: Added ComparePanel (A/B asset) and compare selectors to Global Regimes page.
- 2026-01-31: Replaced A/B compare with multi-asset confidence chart + table (up to 10 assets), reliability flag, and multi-select controls.
- 2026-02-03: Layer 1 governance implemented in graph engine. Auto-calibrated thresholds now include confidence quantiles (conf_lo/conf_hi) and updated escape/stretch quantiles. Low-confidence gating avoids STABLE classification when confidence is below conf_lo. Added forecast reliability gate (quality+confidence+STABLE) and exposed gating metadata in outputs. Added daily audit summary `audit_daily.json` with change counts, low-conf/low-quality tallies, and per-asset status.
- 2026-02-03: Layer 2/3 governance added. Drift metrics (KS + mean deltas), confidence trend, and forecast reliability gating are computed per asset. Outputs now include `gating`, `governance`, `audit_daily.json`, `governance_summary.json`, and `engine_manifest.json` with frozen engine version.
- 2026-02-03: Layer 4–6 added. Stress monitor flags (FAST_REGIME_CHANGES, MICROSTATES_DEGENERATE, ENTROPY_ANOMAL) now emit MODE_UNSTABLE. Run reports generated in `report_run.json` and `report_run.md` with technical/executive summaries. Personality message added in `engine_message.json` for frontend. No forecast blocking; advisory only.
- 2026-02-03: Recalibrated stress monitor thresholds (higher change-rate, higher entropy) and require 2 flags to emit MODE_UNSTABLE. Added auto-smoothing option to official regime comparison and used smoothed risk signal for turning points to reduce false alarms.
- 2026-02-04: Added regime inertia + lag alignment in `run_graph_regime_universe.py`. Regime labels are smoothed (min-run + cooldown with confidence floor), optionally lag-aligned via rolling-mode agreement, and used for plots/outputs. Stability score now penalizes regime flip rate and quality. Stress monitor thresholds hardened (change-rate/entropy/edge fraction) and MODE_UNSTABLE now requires quality<0.45 plus 2 flags. Added lag metadata to governance.
