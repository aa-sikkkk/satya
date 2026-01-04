# Nuitka Build Script for Satya GUI Application
# This script builds a standalone Windows executable using Nuitka

param(
    [switch]$Clean,
    [string]$OutputName = "SatyaGUI.exe"
)


$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Satya Nuitka Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow
Write-Host ""

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    $BuildDir = Join-Path $ProjectRoot "build"
    $DistDir = Join-Path $ProjectRoot "dist"
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    Write-Host "Clean complete." -ForegroundColor Green
    Write-Host ""
}

# Verify bootstrap exists
$BootstrapPath = Join-Path $ScriptDir "bootstrap.py"
if (-not (Test-Path $BootstrapPath)) {
    Write-Host "ERROR: bootstrap.py not found at $BootstrapPath" -ForegroundColor Red
    exit 1
}

# Verify required directories exist
$RequiredDirs = @(
    "satya_data",
    "scripts\data_collection\data\content",
    "student_app\gui_app\images"
)

Write-Host "Verifying required directories..." -ForegroundColor Yellow
foreach ($Dir in $RequiredDirs) {
    $FullPath = Join-Path $ProjectRoot $Dir
    if (-not (Test-Path $FullPath)) {
        Write-Host "WARNING: Directory not found: $FullPath" -ForegroundColor Yellow
    }
    else {
        Write-Host "  [OK] Found: $Dir" -ForegroundColor Green
    }
}
Write-Host ""

# Check if Nuitka is installed
Write-Host "Checking Nuitka installation..." -ForegroundColor Yellow
try {
    $NuitkaVersion = python -m nuitka --version 2>&1
    Write-Host "  [OK] Nuitka found: $NuitkaVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [X] Nuitka not found. Installing..." -ForegroundColor Yellow
    pip install nuitka
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Nuitka" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Build the executable
Write-Host "Building executable with Nuitka..." -ForegroundColor Cyan
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Change to project root for build
Push-Location $ProjectRoot

try {
    # Build command with all necessary flags
    $BuildCommand = @(
        "python", "-m", "nuitka",
        "--onefile",
        "--windows-console-mode=disable", 
        "--standalone",
        "--assume-yes-for-downloads",
        "--enable-plugin=tk-inter",  
        "--include-package-data=customtkinter", 
        "--include-package-data=PIL",  
        "--include-package-data=chromadb",  
        "--include-package-data=llama_cpp",  
        "--include-data-dir=$ProjectRoot\satya_data=satya_data",
        "--include-data-dir=$ProjectRoot\scripts\data_collection\data\content=scripts\data_collection\data\content",
        "--include-data-dir=$ProjectRoot\student_app\gui_app\images=student_app\gui_app\images",
        "--nofollow-import-to=torch",  
        "--nofollow-import-to=torchvision",  
        "--nofollow-import-to=torchaudio",  
        "--nofollow-import-to=transformers",  
        "--nofollow-import-to=clip",  
        "--nofollow-import-to=matplotlib", 
        "--output-filename=$OutputName",
        "--output-dir=dist",
        "--main=$BootstrapPath"  # Use bootstrap as entry point
    )

    # Remove empty icon parameter if no icon specified
    $BuildCommand = $BuildCommand | Where-Object { $_ -ne "--windows-icon-from-ico=" }

    Write-Host "Executing build command..." -ForegroundColor Cyan
    Write-Host "Command: $($BuildCommand -join ' ')" -ForegroundColor Gray
    Write-Host ""

    & $BuildCommand[0] $BuildCommand[1..($BuildCommand.Length-1)]

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Build Successful!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        $OutputPath = Join-Path $ProjectRoot "dist\$OutputName"
        if (Test-Path $OutputPath) {
            $FileSize = (Get-Item $OutputPath).Length / 1MB
            Write-Host "Output: $OutputPath" -ForegroundColor Green
            Write-Host "Size: $([math]::Round($FileSize, 2)) MB" -ForegroundColor Green
        }
        Write-Host ""
        Write-Host "The executable is ready for distribution!" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Build Failed!" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Check the error messages above for details." -ForegroundColor Yellow
        exit 1
    }
} finally {
    Pop-Location
}

