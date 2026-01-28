$ErrorActionPreference = "Stop"

$src = "results/latest"
$dst = "website/public/data/latest"
if (Test-Path "website-ui") {
  $dst = "website-ui/public/data/latest"
}

if (!(Test-Path $src)) {
  Write-Error "Source not found: $src"
}

New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Path "$src\\*" -Destination $dst -Recurse -Force
Write-Host "Synced $src -> $dst"
