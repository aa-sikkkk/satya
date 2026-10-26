<#
.SYNOPSIS
    One-command OFFLINE installer for the Satya learning system.

.DESCRIPTION
    Generates a student workspace with a virtual environment and installs
    Satya + all libraries from the wheels/ folder shipped in the offline
    zip. No internet needed at install or run time.
    If wheels/ is absent (small "installer-only" zip), falls back to PyPI.

.USAGE
    Right-click -> Run with PowerShell, or:
    powershell -ExecutionPolicy Bypass -File install_satya.ps1 [-TargetDir <path>]
#>
param(
    [string]$TargetDir = "$HOME\Satya"
)

$ErrorActionPreference = "Stop"
# PS 7.3+: make non-zero native command exits throw; harmless (no-op) on 5.1
$PSNativeCommandUseErrorActionPreference = $true
$Wheel = Get-ChildItem -LiteralPath $PSScriptRoot -Filter "satya_learning_system-*.whl" |
    Select-Object -First 1
if (-not $Wheel) {
    Write-Host "[X] No satya_learning_system wheel found next to install_satya.ps1" -ForegroundColor Red
    exit 1
}
$OfflineWheels = Join-Path $PSScriptRoot "wheels"
$Offline = (Test-Path $OfflineWheels) -and ((Get-ChildItem $OfflineWheels -Filter *.whl | Measure-Object).Count -gt 0)

# 1) Verify Python 3.11-3.12 is available
$Py = Get-Command python -ErrorAction SilentlyContinue
if (-not $Py) {
    Write-Host "[X] Python not found. Install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "    (tick 'Add python.exe to PATH' in the installer) and re-run this script." -ForegroundColor Red
    exit 1
}
$Ver = (& python -c "import sys; print(sys.version_info[:2])" 2>$null)
if ($Ver -notmatch "\(3, (11|12)\)") {
    Write-Host "[X] Python 3.11 or 3.12 required, found: $Ver" -ForegroundColor Red
    exit 1
}

# 2) Create workspace + venv
Write-Host "[1/4] Creating workspace at $TargetDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
Push-Location $TargetDir
if (-not (Test-Path venv)) { python -m venv venv }
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] python -m venv failed (exit $LASTEXITCODE) - see errors above" -ForegroundColor Red
    Pop-Location
    exit 1
}
& "$TargetDir\venv\Scripts\python.exe" -m pip install --upgrade pip -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] pip upgrade failed (exit $LASTEXITCODE)" -ForegroundColor Red
    Pop-Location
    exit 1
}

# 3) Install Satya (+ all deps -> offline wheels bundle if present)
if ($Offline) {
    Write-Host "[2/4] Installing Satya OFFLINE from bundled wheels (no internet needed)..." -ForegroundColor Cyan
    & "$TargetDir\venv\Scripts\pip.exe" install --no-index --find-links "$OfflineWheels" $Wheel.FullName
} else {
    Write-Host "[2/4] No offline bundle detected - installing from PyPI (needs internet, ~2 GB)..." -ForegroundColor Yellow
    & "$TargetDir\venv\Scripts\pip.exe" install -q --no-input $Wheel.FullName
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] pip install failed - see errors above" -ForegroundColor Red
    Pop-Location
    exit 1
}

# 4) Write double-click launchers
Write-Host "[3/4] Writing launcher shortcuts" -ForegroundColor Cyan
Set-Content -LiteralPath "$TargetDir\satya.cmd" -Value @'
@echo off
set "SATYA_BASE_PATH=%~dp0"
"%~dp0venv\Scripts\python.exe" -m student_app.main %*
'@ -Encoding Ascii
Set-Content -LiteralPath "$TargetDir\satya-gui.cmd" -Value @'
@echo off
set "SATYA_BASE_PATH=%~dp0"
"%~dp0venv\Scripts\python.exe" -m student_app.gui_app.main_window
'@ -Encoding Ascii

# 5) Pre-create the model location the app resolves via satya_data/, so the
# student only has to move the downloaded model folder in
Write-Host "[4/4] Done. Next steps:" -ForegroundColor Green
$ModelDir = "$TargetDir\satya_data\models\phi15"
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null
Write-Host "  1. Download the Phi-1.5 model asset from the same release you got this zip from"
Write-Host "     (asset: Student Application + Phi 1.5 Model Download)"
Write-Host "  2. Put the model folder into   $ModelDir"
Write-Host "  3. Launch:  double-click satya-gui.cmd   (or satya.cmd for the CLI)"
Pop-Location
