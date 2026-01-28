$ErrorActionPreference = "Stop"

$src = "results\finance_walkforward_all\plots"
$dst = "website-ui\public\data\plots"

if (!(Test-Path $src)) {
  Write-Error "Source not found: $src"
}

New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Path "$src\*" -Destination $dst -Recurse -Force
Write-Host "Synced $src -> $dst"
