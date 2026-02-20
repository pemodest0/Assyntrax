#!/usr/bin/env bash
set -euo pipefail

REPO="/Users/PedroHenrique/Desktop/A-firma"
source "$REPO/.venv/bin/activate"
cd "$REPO"

python3 scripts/ops/run_monthly_revalidation.py \
  --profile-file config/sector_alerts_profile.json \
  --hyper-n-sims 20 \
  --hyper-search-n-random 60 \
  --hyper-final-n-random 300 \
  --hyper-min-cal-days 252 \
  --hyper-min-test-days 252 \
  --hyper-two-layer-mode on \
  --hyper-min-alert-gap-days 2 \
  --hyper-gate-mode adaptive \
  --walkforward-start-year 2020 \
  --walkforward-end-year 2025 \
  --walkforward-n-random 120 \
  --walkforward-gate-mode adaptive
