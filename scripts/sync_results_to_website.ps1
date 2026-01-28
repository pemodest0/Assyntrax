$ErrorActionPreference = "Stop"

$root = "C:\Users\Pedro Henrique\Desktop\A-firma"
Set-Location $root

$latest = "results\latest"
$publicLatest = "website-ui\public\data\latest"
$plotsWfSrc = "results\finance_walkforward_all\plots"
$plotsWfDst = "website-ui\public\data\plots\walkforward"
$riskSrc = "results\finance_risk_all"
$riskDst = "website-ui\public\data\risk"

if (Test-Path $latest) {
  New-Item -ItemType Directory -Force -Path $publicLatest | Out-Null
  Copy-Item -Path "$latest\*" -Destination $publicLatest -Recurse -Force
  Write-Host "Synced latest -> $publicLatest"
}

if (Test-Path $plotsWfSrc) {
  New-Item -ItemType Directory -Force -Path $plotsWfDst | Out-Null
  Copy-Item -Path "$plotsWfSrc\*" -Destination $plotsWfDst -Recurse -Force
  Write-Host "Synced walkforward plots -> $plotsWfDst"
}

if (Test-Path $riskSrc) {
  Get-ChildItem $riskSrc -Directory | ForEach-Object {
    $asset = $_.Name
    $dest = Join-Path $riskDst $asset
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    foreach ($file in @("master_plot.png","vol_prob_logreg.png","verdict.json","metrics.json","summary.csv")) {
      $src = Join-Path $_.FullName $file
      if (Test-Path $src) {
        Copy-Item $src -Destination (Join-Path $dest $file) -Force
      }
    }
  }
  Write-Host "Synced risk regime assets -> $riskDst"
}
