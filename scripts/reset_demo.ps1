# NileOps Demo Reset Script
# Resets the synthetic demo database ('nileops'), purges temporary demo requests,
# cleans temporary uploads, and reconciles the Qdrant knowledge base.
#
# HARD-FAIL SAFETY GUARD: Strictly refuses execution if connected to any test database.

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      NileOps Digital Banking — Demo Environment Reset     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Virtual Environment
$venvPython = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Python virtual environment not found at backend\.venv\Scripts\python.exe"
    exit 1
}

# 2. Check Database URL Safety Guard
$envFile = Join-Path $repoRoot "backend\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*DATABASE_URL\s*=\s*(.+)$") {
            $dbUrl = $matches[1].Trim()
            if ($dbUrl -match "test") {
                Write-Error "HARD-STOP SAFETY GUARD: DATABASE_URL ($dbUrl) points to a test database! Refusing reset."
                exit 1
            }
        }
    }
}

# 3. Execute Reset Logic
Write-Host "Resetting synthetic transactions, requests, audit trails, and vector index..." -ForegroundColor Yellow

& $venvPython (Join-Path $repoRoot "backend\app\scripts\reset_demo.py")
if ($LASTEXITCODE -ne 0) {
    Write-Error "Demo environment reset failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "`nDemo environment successfully reset to canonical baseline state." -ForegroundColor Green
Write-Host "Ready for demo presentations." -ForegroundColor Green
