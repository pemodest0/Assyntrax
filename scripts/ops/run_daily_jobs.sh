#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEED="${1:-23}"
MAX_ASSETS="${2:-80}"
HEAVY="${3:-}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"

cd "$ROOT"

echo "[ops] repo=$ROOT run_id=$RUN_ID"

if [[ "$HEAVY" == "heavy" ]]; then
  python3 scripts/ops/run_daily_master.py --seed "$SEED" --max-assets "$MAX_ASSETS" --run-id "$RUN_ID" --with-heavy
else
  python3 scripts/ops/run_daily_master.py --seed "$SEED" --max-assets "$MAX_ASSETS" --run-id "$RUN_ID"
fi

echo "[ops] done"
