# Graph Engine Frontend Contract

## Location
The frontend must read from:
- `results/latest_graph/universe_weekly.json`
- `results/latest_graph/universe_daily.json`

## Asset detail
For any asset + timeframe:
```
results/latest_graph/assets/{ASSET}_{TF}.json
results/latest_graph/assets/{ASSET}_{TF}_embedding.csv
results/latest_graph/assets/{ASSET}_{TF}_regimes.csv
results/latest_graph/assets/{ASSET}_{TF}_micrograph.json
results/latest_graph/assets/{ASSET}_{TF}_transitions.json
results/latest_graph/assets/{ASSET}_{TF}_plots/
```

## Asset JSON (minimum)
```
{
  "asset": "SPY",
  "timeframe": "weekly",
  "asof": "YYYY-MM-DD",
  "state": { "label": "STABLE|TRANSITION|UNSTABLE|NOISY", "confidence": 0.0-1.0 },
  "graph": { "n_micro": 500, "k_nn": 15, "theiler": 10, "alpha": 2.0 },
  "metrics": {
    "stay_prob": 0.0-1.0,
    "escape_prob": 0.0-1.0,
    "stretch_mu": -inf..inf,
    "stretch_frac_pos": 0.0-1.0
  },
  "alerts": ["REGIME_INSTAVEL", "LOW_CONFIDENCE"],
  "links": {
    "regimes_csv": "...",
    "embedding_csv": "...",
    "micrograph_json": "...",
    "transitions_json": "..."
  },
  "forecast_diag": { "mase": 0.91, "dir_acc": 0.51, "alerts": ["DIRECAO_FRACA"] },
  "risk": { "label": "HIGH_VOL", "p": 0.73, "model": "RF" }
}
```

## Guarantees
- `asset`, `timeframe`, `state`, `graph`, `metrics`, `alerts`, `links` are always present.
- `forecast_diag` and `risk` are optional (merged from existing outputs if available).
- The universe files always contain an array of asset JSON objects.

## Notes
- Frontend should honor gating: if `state.confidence` below threshold or alerts include
  `LOW_CONFIDENCE`, `REGIME_INSTAVEL`, `NO_STRUCTURE`, show "DO NOT TRUST".
