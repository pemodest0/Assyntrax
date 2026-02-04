# Daily Pipeline (Fetch + Engine)

This pipeline updates data sources and regenerates graph engine outputs.

## Run manually

```bash
python3 scripts/ops/run_daily_pipeline.py --mode fast --outdir results/latest_graph
```

With auto-embedding:

```bash
python3 scripts/ops/run_daily_pipeline.py \
  --mode fast \
  --auto-embed \
  --tau-method ami \
  --m-method cao \
  --outdir results/latest_graph
```

## Cron (macOS)

Edit crontab:

```bash
crontab -e
```

Example: run every day at 6:00

```bash
0 6 * * * /Users/PedroHenrique/Desktop/A-firma/scripts/ops/cron_daily.sh >> /Users/PedroHenrique/Desktop/A-firma/logs/cron_daily.log 2>&1
```

## Notes
- Requires `FRED_API_KEY` for finance macro data.
- The scripts do not overwrite legacy outputs; they update `results/latest_graph`.
