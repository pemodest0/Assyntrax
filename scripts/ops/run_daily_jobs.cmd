@echo off
setlocal
set SCRIPT_DIR=%~dp0
set SEED=%1
set MAXASSETS=%2
set HEAVY=%3
if "%SEED%"=="" set SEED=23
if "%MAXASSETS%"=="" set MAXASSETS=80

if /I "%HEAVY%"=="heavy" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_daily_jobs.ps1" -Seed %SEED% -MaxAssets %MAXASSETS% -WithHeavy
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_daily_jobs.ps1" -Seed %SEED% -MaxAssets %MAXASSETS%
)
exit /b %ERRORLEVEL%
