# Dashboard Spec

## Assets Table (core)
Columns:
- Asset, Sector
- Price_t0 (last close), Price_t-1, Price_t-2, Return_t0
- Regime_now (label), Regime_prev, Regime_stability (0-1)
- Confidence_now (0-100), Warning_flags (list)
- SimilarEra_start, SimilarEra_end, SimilarEra_score (0-1)
- Forecast_next_close_arima, Forecast_next_close_xgb, Forecast_next_close_qr
- Forecast_next_close_motor
- Verdict (YES/NO/DEPENDS) + Reason_short

## Gating rules (main point)
- If Confidence_now < threshold OR warnings include NO_STRUCTURE/DIRECAO_FRACA/REGIME_INSTAVEL:
  - highlight in red
  - show forecasts with "not reliable"
  - block any action/recommendation

## Drill-down (asset detail)
- Time series (close/returns)
- Regime over time
- Phase-space plots (2D/3D) colored by regime
- "Why no trust" panel
- "Similar historical era" panel with side-by-side comparison

## Data artifacts
Generate:
- results/dashboard/asset_table.csv
- results/dashboard/asset_detail/{TICKER}.json
Rebuild by CLI:
python scripts/build_dashboard_data.py --tickers ... --frequency daily|weekly
