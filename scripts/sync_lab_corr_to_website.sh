#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAB_ROOT="$ROOT/results/lab_corr_macro"
POINTER="$LAB_ROOT/latest_release.json"
DST="$ROOT/website-ui/public/data/lab_corr_macro/latest"

if [[ ! -f "$POINTER" ]]; then
  echo "[sync_lab_corr] pointer not found: $POINTER" >&2
  exit 1
fi

RUN_ID="$(python3 - << 'PY'
import json
from pathlib import Path
obj=json.loads(Path('results/lab_corr_macro/latest_release.json').read_text())
print(obj.get('run_id','').strip())
PY
)"

if [[ -z "$RUN_ID" ]]; then
  echo "[sync_lab_corr] run_id vazio no latest_release.json" >&2
  exit 1
fi

SRC="$LAB_ROOT/$RUN_ID"
if [[ ! -d "$SRC" ]]; then
  echo "[sync_lab_corr] run dir not found: $SRC" >&2
  exit 1
fi

mkdir -p "$DST"

copy_if_exists() {
  local file="$1"
  if [[ -f "$SRC/$file" ]]; then
    cp "$SRC/$file" "$DST/$file"
  fi
}

# Core files used by /api/lab/corr/latest and dashboard
copy_if_exists "summary.json"
copy_if_exists "summary_compact.txt"
copy_if_exists "qa_checks.json"
copy_if_exists "asset_regime_diagnostics.csv"
copy_if_exists "sector_regime_diagnostics.csv"
copy_if_exists "asset_sector_summary.json"
copy_if_exists "significance_summary_by_window.csv"

for w in 60 120 252; do
  copy_if_exists "macro_timeseries_T${w}.csv"
  copy_if_exists "case_studies_T${w}.csv"
  copy_if_exists "operational_alerts_T${w}.json"
  copy_if_exists "era_evaluation_T${w}.json"
  copy_if_exists "action_playbook_T${w}.json"
  copy_if_exists "ui_view_model_T${w}.json"
  copy_if_exists "regime_series_T${w}.csv"
  copy_if_exists "alert_levels_T${w}.csv"
done

# Keep a small pointer inside website-ui/public for traceability
cat > "$DST/latest_release.json" << JSON
{
  "run_id": "$RUN_ID",
  "run_dir": "$SRC",
  "synced_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source": "results/lab_corr_macro/latest_release.json"
}
JSON

echo "[sync_lab_corr] synced run $RUN_ID -> $DST"
