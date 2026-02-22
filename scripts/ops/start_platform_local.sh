#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_PIPELINE=0
WEB_MODE="dev"
PORT=3000
SEED=23
MAX_ASSETS=80
THREADS=1
HEAVY_PIPELINE=0

usage() {
  cat <<USAGE
Usage: scripts/ops/start_platform_local.sh [options]

Options:
  --run-pipeline         Run daily pipeline before web startup
  --heavy-pipeline       Enable heavy diagnostics in daily pipeline
  --web-mode MODE        dev|start (default: dev)
  --port PORT            Web port (default: 3000)
  --seed SEED            Pipeline seed (default: 23)
  --max-assets N         Pipeline max assets (default: 80)
  --threads N            Max computational threads for pipeline (default: 1)
  -h, --help             Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-pipeline)
      RUN_PIPELINE=1
      shift
      ;;
    --heavy-pipeline)
      HEAVY_PIPELINE=1
      shift
      ;;
    --web-mode)
      WEB_MODE="${2:-}"
      shift 2
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --seed)
      SEED="${2:-}"
      shift 2
      ;;
    --max-assets)
      MAX_ASSETS="${2:-}"
      shift 2
      ;;
    --threads)
      THREADS="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[platform] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$WEB_MODE" != "dev" && "$WEB_MODE" != "start" ]]; then
  echo "[platform] invalid --web-mode: $WEB_MODE (expected dev|start)" >&2
  exit 2
fi
if [[ ! "$THREADS" =~ ^[0-9]+$ ]] || [[ "$THREADS" -lt 1 ]]; then
  echo "[platform] invalid --threads: $THREADS (expected integer >= 1)" >&2
  exit 2
fi

echo "[platform] repo=$ROOT mode=$WEB_MODE port=$PORT run_pipeline=$RUN_PIPELINE heavy=$HEAVY_PIPELINE threads=$THREADS"

cd "$ROOT"
if [[ "$RUN_PIPELINE" -eq 1 ]]; then
  if [[ "$HEAVY_PIPELINE" -eq 1 ]]; then
    ASSYNTRAX_THREADS="$THREADS" bash scripts/ops/run_daily_jobs.sh "$SEED" "$MAX_ASSETS" "heavy" "$THREADS"
  else
    ASSYNTRAX_THREADS="$THREADS" bash scripts/ops/run_daily_jobs.sh "$SEED" "$MAX_ASSETS" "" "$THREADS"
  fi
fi

cd "$ROOT/website-ui"
if [[ "$WEB_MODE" == "dev" ]]; then
  npm run dev -- --port "$PORT"
else
  npm run start -- -p "$PORT"
fi
