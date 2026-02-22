param(
  [switch]$RunPipeline = $false,
  [ValidateSet("dev", "start")]
  [string]$WebMode = "dev",
  [int]$Port = 3000,
  [int]$Seed = 23,
  [int]$MaxAssets = 80
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo

Write-Host "[platform] repo=$repo mode=$WebMode port=$Port run_pipeline=$RunPipeline"

if ($RunPipeline) {
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ops/run_daily_jobs.ps1 -Seed $Seed -MaxAssets $MaxAssets
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Set-Location (Join-Path $repo "website-ui")
if ($WebMode -eq "dev") {
  npm run dev -- --port $Port
} else {
  npm run start -- -p $Port
}

