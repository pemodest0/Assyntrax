$ErrorActionPreference = "Stop"

$root = "C:\Users\Pedro Henrique\Desktop\A-firma"
Set-Location $root

$latest = "results\latest"
$publicLatest = "website-ui\public\data\latest"
$plotsWfSrc = "results\finance_walkforward_all\plots"
$plotsWfDst = "website-ui\public\data\plots\walkforward"
$riskSrc = "results\finance_risk_all"
$riskDst = "website-ui\public\data\risk"
$labSrcRoot = "results\lab_corr_macro"
$labDstLatest = "website-ui\public\data\lab_corr_macro\latest"

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
    foreach ($file in @("master_plot.png","vol_prob_logreg.png","metrics.json","summary.csv")) {
      $src = Join-Path $_.FullName $file
      if (Test-Path $src) {
        Copy-Item $src -Destination (Join-Path $dest $file) -Force
      }
    }
    $statusSrc = Join-Path $_.FullName "status.json"
    if (Test-Path $statusSrc) {
      Copy-Item $statusSrc -Destination (Join-Path $dest "status.json") -Force
    } else {
      $legacyVerdict = Join-Path $_.FullName "verdict.json"
      if (Test-Path $legacyVerdict) {
        Copy-Item $legacyVerdict -Destination (Join-Path $dest "status.json") -Force
      }
    }
  }
  Write-Host "Synced risk regime assets -> $riskDst"
}

if (Test-Path $labSrcRoot) {
  $run = Get-ChildItem $labSrcRoot -Directory |
    Where-Object { $_.Name -match '^\d{8}T\d{6}Z$' } |
    Sort-Object Name -Descending |
    Select-Object -First 1

  if ($run) {
    New-Item -ItemType Directory -Force -Path $labDstLatest | Out-Null
    $labFiles = @(
      "summary.json",
      "summary_compact.txt",
      "macro_timeseries_T120.csv",
      "case_studies_T120.csv",
      "operational_alerts_T120.json",
      "era_evaluation_T120.json",
      "action_playbook_T120.json",
      "ui_view_model_T120.json",
      "backtest_summary_T120.json"
    )
    foreach ($f in $labFiles) {
      $src = Join-Path $run.FullName $f
      if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $labDstLatest $f) -Force
      }
    }
    Write-Host "Synced lab corr macro -> $labDstLatest (run $($run.Name))"
  }
}
