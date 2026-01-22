param(
  [switch]$Yes
)

$targets = @(
  "api",
  "dados",
  "legado",
  "results",
  "website",
  "venv",
  "n sei c pode exluir",
  "data\\external",
  "data\\yfinance_cache",
  "data\\processed",
  "author.png"
)

if (-not $Yes) {
  Write-Host "Dry-run. Pass -Yes to delete the following paths:" -ForegroundColor Yellow
  $targets | ForEach-Object { Write-Host "  $_" }
  exit 1
}

foreach ($t in $targets) {
  if (Test-Path $t) {
    Remove-Item -Recurse -Force $t
    Write-Host "Removed: $t"
  }
}

# Remove per-year ONS CSVs, keep aggregated files
$onsDir = "data\\raw\\ONS\\ons_carga_diaria"
if (Test-Path $onsDir) {
  Get-ChildItem -Path $onsDir -Filter "CARGA_ENERGIA_*.csv" | ForEach-Object {
    Remove-Item -Force $_.FullName
    Write-Host "Removed: $($_.FullName)"
  }
  if (Test-Path "$onsDir\\ons_carga_diaria_2016_2025.csv") {
    Remove-Item -Force "$onsDir\\ons_carga_diaria_2016_2025.csv"
    Write-Host "Removed: $onsDir\\ons_carga_diaria_2016_2025.csv"
  }
}
