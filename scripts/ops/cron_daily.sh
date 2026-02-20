#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -f "$REPO/.venv/bin/activate" ]; then
  # Prefer local venv when available.
  source "$REPO/.venv/bin/activate"
fi

export FRED_API_KEY="${FRED_API_KEY:-}"
cd "$REPO"

python3 scripts/ops/run_daily_pipeline.py --mode fast --outdir results/latest_graph
python3 scripts/ops/run_daily_sector_alerts.py --profile-file config/sector_alerts_profile.json
