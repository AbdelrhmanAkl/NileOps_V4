# NileOps — Model Pre-caching & Offline Preparation Script
# Downloads intfloat/multilingual-e5-small and all PaddleOCR models into local project caches for air-gapped execution.

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "          NileOps AI Model Download & Pre-Caching          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$venvPython = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $venvPython = $pyCmd.Source
    } else {
        Write-Error "Python executable not found. Please activate virtual environment."
        exit 1
    }
}

# 1. Pre-cache SentenceTransformers E5 embedding model
Write-Host "`n[1/2] Pre-caching intfloat/multilingual-e5-small in local HuggingFace cache..." -ForegroundColor Yellow
$env:HF_HUB_ENABLE_HF_TRANSFER = "0"
& $venvPython -c @"
import sys, re, os
sys.modules['regex'] = re
from sentence_transformers import SentenceTransformer

model_name = 'intfloat/multilingual-e5-small'
print(f'Downloading / verifying {model_name} in HuggingFace cache...')
model = SentenceTransformer(model_name)
v = model.encode('query: اختبار التنزيل والترميز', normalize_embeddings=True)
print(f'Model cached successfully. Embedding dimension: {len(v)}')
"@
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to download SentenceTransformer embedding model."
    exit $LASTEXITCODE
}

# 2. Pre-cache PaddleOCR models into project data directory
Write-Host "`n[2/2] Pre-caching PaddleOCR models into project data directory (data/paddlex, data/paddle)..." -ForegroundColor Yellow
& $venvPython -c @"
import sys, os
repo_root = os.path.abspath(r'$repoRoot')
sys.path.insert(0, os.path.join(repo_root, 'backend'))
from app.services.image_pipeline import get_ocr_engine

print('Initializing PaddleOCR engine and pre-fetching models...')
engine = get_ocr_engine()
if engine is not None:
    print('PaddleOCR Arabic models successfully verified in local cache.')
else:
    raise RuntimeError('Failed to initialize PaddleOCR engine.')
"@
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to download PaddleOCR models."
    exit $LASTEXITCODE
}

Write-Host "`nOffline model verification complete. Set HF_HUB_OFFLINE=1 for strict air-gapped runtime." -ForegroundColor Green
