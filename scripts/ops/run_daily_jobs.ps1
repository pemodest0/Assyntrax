param(
  [int]$Seed = 23,
  [int]$MaxAssets = 80,
  [switch]$WithHeavy
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo

$runId = Get-Date -Format "yyyyMMddTHHmmssZ"

Write-Host "[ops] repo=$repo run_id=$runId"

if ($WithHeavy) {
  python scripts/ops/run_daily_master.py --seed $Seed --max-assets $MaxAssets --run-id $runId --with-heavy
} else {
  python scripts/ops/run_daily_master.py --seed $Seed --max-assets $MaxAssets --run-id $runId
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[ops] done"
