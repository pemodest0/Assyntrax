#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEED="${SEED:-23}"
MAX_ASSETS="${MAX_ASSETS:-80}"
WITH_HEAVY="${WITH_HEAVY:-0}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"

cd "$ROOT"
echo "[daily_publish] repo=$ROOT run_id=$RUN_ID"

# Coleta de acerto/erro diária para histórico do site (não bloqueia o restante).
python3 scripts/ops/update_prediction_truth_daily.py --run-id "$RUN_ID" || true

MASTER_CODE=0
if [[ "$WITH_HEAVY" == "1" ]]; then
  python3 scripts/ops/run_daily_master.py --seed "$SEED" --max-assets "$MAX_ASSETS" --run-id "$RUN_ID" --with-heavy || MASTER_CODE=$?
else
  python3 scripts/ops/run_daily_master.py --seed "$SEED" --max-assets "$MAX_ASSETS" --run-id "$RUN_ID" || MASTER_CODE=$?
fi

# Atualiza artefatos públicos do motor para o frontend no deploy.
bash scripts/sync_lab_corr_to_website.sh || true

cd "$ROOT/website-ui"
npx vercel --prod --yes

echo "[daily_publish] done run_id=$RUN_ID master_code=$MASTER_CODE"
exit "$MASTER_CODE"
