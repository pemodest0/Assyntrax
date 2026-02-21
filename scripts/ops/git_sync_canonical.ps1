param(
  [string]$Remote = "origin",
  [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

Write-Host "[sync] canonical remote: $Remote/$Branch"
git fetch $Remote --prune
git reset --hard "$Remote/$Branch"
git clean -fd

Write-Host "[sync] local now matches $Remote/$Branch"
git status -sb
git rev-parse --short HEAD
