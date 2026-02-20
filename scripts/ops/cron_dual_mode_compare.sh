#!/usr/bin/env bash
set -euo pipefail

REPO="/Users/PedroHenrique/Desktop/A-firma"
source "$REPO/.venv/bin/activate"
cd "$REPO"

python3 scripts/ops/run_dual_mode_compare.py \
  --profile-useful config/sector_alerts_profile_useful.json \
  --profile-aggressive config/sector_alerts_profile_aggressive97.json \
  --n-random 20 \
  --lookbacks 10,20,30
