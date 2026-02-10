param(
  [string]$TaskName = "Assyntrax_DailyOps",
  [string]$StartTime = "06:10",
  [int]$Seed = 17,
  [int]$MaxAssets = 80
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$scriptPs1 = Join-Path $repo "scripts\ops\run_daily_jobs.ps1"
if (!(Test-Path $scriptPs1)) {
  throw "Script not found: $scriptPs1"
}

$actionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPs1`" -Seed $Seed -MaxAssets $MaxAssets"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs

$time = [DateTime]::ParseExact($StartTime, "HH:mm", $null)
$trigger = New-ScheduledTaskTrigger -Daily -At $time

$userId = "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null

Write-Host "[ops] task registered"
Write-Host "  name: $TaskName"
Write-Host "  time: $StartTime"
Write-Host "  user: $userId"
Write-Host "  exec: powershell.exe"
Write-Host "  args: $actionArgs"
Write-Host ""
Write-Host "Run once now:"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host "Check status:"
Write-Host "  Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
