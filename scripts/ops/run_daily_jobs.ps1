param(
  [int]$Seed = 23,
  [int]$MaxAssets = 80
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo

$runId = Get-Date -Format "yyyyMMdd"

Write-Host "[ops] repo=$repo run_id=$runId"

python scripts/ops/run_daily_validation.py --seed $Seed --max-assets $MaxAssets --run-id $runId
if ($LASTEXITCODE -ne 0) {
  Write-Host "[ops] validation failed, aborting snapshot/diff"
  exit $LASTEXITCODE
}

python scripts/ops/build_daily_snapshot.py --run-id $runId
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/ops/validate_output_contract.py --snapshot "results/ops/snapshots/$runId/api_snapshot.jsonl"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/ops/daily_diff_report.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/ops/build_run_audit_pack.py --run-id $runId --seed $Seed --max-assets $MaxAssets
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/ops/run_daily_sector_alerts.py --profile-file config/sector_alerts_profile.json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[ops] done"
