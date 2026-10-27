<#
.SYNOPSIS
    Package the local Phi 1.5 GGUF model as a release asset.

.DESCRIPTION
    Verifies the maintainer's local model bundle (an offline-run
    artifact, gitignored), zips it as Satya_Phi_1_5_Model_Win.zip so
    students can unzip it into
    %USERPROFILE%\Satya\satya_data\models\phi15.
    Optionally attaches the asset to a GitHub release with gh.

.USAGE
    powershell -ExecutionPolicy Bypass -File package_model.ps1 `
        [-ModelDir <path>] [-OutDir <path>] [-Tag v2.4.1]
    Download the model once (any machine with internet):
      huggingface: phi-1.5 GGUF Q4_K_M, e.g. from ggml/phi-1.5-gguf
    and place the .gguf file into satya_data/models/phi15/.
#>
param(
    [string]$ModelDir = (Join-Path (Get-Item $PSScriptRoot).Parent.Parent.FullName "satya_data\models\phi15"),
    [string]$OutDir = (Get-Location).Path,
    [string]$Tag = "",
    [string]$Repo = "aa-sikkkk/satya"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

if (-not (Test-Path -LiteralPath $ModelDir)) {
    Write-Host "[X] Model dir not found: $ModelDir" -ForegroundColor Red
    Write-Host "    Download the .gguf file once and place it there (see header comment)." -ForegroundColor Red
    exit 1
}

$Models = Get-ChildItem -LiteralPath $ModelDir -Filter "*.gguf"
if (-not $Models) {
    Write-Host "[X] No .gguf file found in $ModelDir" -ForegroundColor Red
    Write-Host "    The runtime (ai_model/model_utils/model_handler.py) globs *.gguf here." -ForegroundColor Red
    exit 1
}
if ($Models.Count -gt 1) {
    Write-Host "[!] Multiple .gguf files found; using the largest:" -ForegroundColor Yellow
    $Models | ForEach-Object { Write-Host ("    {0}  ({1:N0} MB)" -f $_.Name, ($_.Length / 1MB)) }
    $Models = $Models | Sort-Object Length -Descending | Select-Object -First 1
}
$Model = $Models
if ($Model.Length -lt 300MB) {
    Write-Host "[X] File looks too small for a Phi-1.5 GGUF Q4_K_M (expected ~500-1100 MB)." -ForegroundColor Red
    Write-Host "    Aborting - a partial download would break student installs silently." -ForegroundColor Red
    exit 1
}
if ($Model.Length -gt 1GB) {
    Write-Host "[X] File exceeds the ~1 GB inference memory budget (staying CPU-only);" -ForegroundColor Red
    Write-Host "    refusing to ship. Ship a lighter quant instead." -ForegroundColor Red
    exit 1
}
$SizeMB = [math]::Round($Model.Length / 1MB, 0)
Write-Host ("[1/3] Model: {0}  ({1} MB)" -f $Model.Name, $SizeMB)

$OutZip = Join-Path $OutDir "Satya_Phi_1_5_Model_Win.zip"
Write-Host "[2/3] Zipping to $OutZip ..."
if (Test-Path $OutZip) { Remove-Item -Force $OutZip }
# Zip ONLY the selected .gguf at the archive root: students unzip it straight
# into %USERPROFILE%\Satya\satya_data\models\phi15 (QUICKSTART documents this).
Compress-Archive -Path $Model.FullName -DestinationPath $OutZip -CompressionLevel Fastest
Write-Host ("      asset: {0}  ({1:N0} MB)" -f (Split-Path $OutZip -Leaf), ((Get-Item $OutZip).Length / 1MB))

if ($Tag) {
    Write-Host "[3/3] Attaching to release $Tag (repo $Repo) ..."
    gh release upload $Tag $OutZip --clobber --repo $Repo
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "      uploaded."
} else {
    Write-Host "[3/3] No -Tag given: attach manually with" -ForegroundColor Cyan
    Write-Host "      gh release upload <tag> `"$OutZip`" --clobber"
}

Write-Host "[done] QUICKSTART documents this asset as Satya_Phi_1_5_Model_Win.zip -" -ForegroundColor Green
Write-Host "       keep release, docs and installer text in sync when renaming."
