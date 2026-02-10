param(
  [ValidateSet("daily", "product")]
  [string]$Mode = "daily",
  [int]$Seed = 23,
  [int]$MaxAssets = 80
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo

Write-Host "[unified_pipeline] mode=$Mode repo=$repo"

if ($Mode -eq "daily") {
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ops/run_daily_jobs.ps1 -Seed $Seed -MaxAssets $MaxAssets
  exit $LASTEXITCODE
}

python scripts/bench/validation/run_product_pipeline.py --seed $Seed --max-assets $MaxAssets
exit $LASTEXITCODE
