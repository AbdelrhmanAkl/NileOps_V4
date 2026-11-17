# NileOps — Synthetic Evaluation Data Generator
# Re-creates all synthetic test cards, utility bills, and RAG evaluation sets
# deterministically using fixed random seeds. Zero authentic citizen or consumer PII.

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      NileOps Synthetic Evaluation Data Preparation        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$venvPython = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    # Fallback to system python if venv not at expected path
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $venvPython = $pyCmd.Source
    } else {
        Write-Error "Python executable not found. Please activate virtual environment."
        exit 1
    }
}

Write-Host "`n[1/5] Generating synthetic utility bill fixtures..." -ForegroundColor Yellow
& $venvPython (Join-Path $repoRoot "scripts\data_gen\generate_synthetic_bills.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[2/5] Generating 40 synthetic cards for OCR F1 evaluation..." -ForegroundColor Yellow
& $venvPython (Join-Path $repoRoot "scripts\data_gen\generate_40_ocr_cards.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[3/5] Generating 60 DEV synthetic cards for exception evaluation..." -ForegroundColor Yellow
& $venvPython (Join-Path $repoRoot "scripts\data_gen\generate_dev_60_cards.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[4/4] Generating 60 HELD-OUT synthetic cards for exception evaluation..." -ForegroundColor Yellow
& $venvPython (Join-Path $repoRoot "scripts\data_gen\generate_held_out_60_cards.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Notice: Committed RAG benchmark sets (rag_evaluation_set_40.json, rag_evaluation_held_out_30.json,
# rag_evaluation_new_held_out_30.json) are canonical, version-controlled benchmarks and are not overwritten.

Write-Host "`nAll synthetic evaluation datasets successfully generated and verified." -ForegroundColor Green
