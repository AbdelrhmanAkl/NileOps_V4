# NileOps — Production Demo Launcher
# Orchestrates dependencies, environment variables, security guards, and starts the unified single-port server.

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      NileOps Digital Banking — Production Demo Startup    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Virtual Environment
$venvPython = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Python virtual environment not found at backend\.venv\Scripts\python.exe"
    exit 1
}

# 2. Check and Build Frontend Distribution if Missing
$distIndex = Join-Path $repoRoot "frontend\dist\index.html"
if (-not (Test-Path $distIndex)) {
    Write-Host "[Frontend] Missing frontend\dist\index.html. Running npm install and npm run build..." -ForegroundColor Yellow
    Push-Location (Join-Path $repoRoot "frontend")
    try {
        if (-not (Test-Path "node_modules")) {
            & npm.cmd install
            if ($LASTEXITCODE -ne 0) {
                Write-Error "npm install failed in frontend."
                exit $LASTEXITCODE
            }
        }
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) {
            Write-Error "npm run build failed in frontend."
            exit $LASTEXITCODE
        }
    } finally {
        Pop-Location
    }
}

# 3. Check Docker Daemon
Write-Host "[1/6] Checking Docker infrastructure..." -ForegroundColor Yellow
try {
    $dockerCheck = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker Desktop is not running. Please start Docker and re-run this script."
        exit 1
    }
} catch {
    Write-Error "Docker is not available in PATH or daemon is stopped. Please start Docker."
    exit 1
}

# Start PostgreSQL and Qdrant containers
Write-Host "      Starting PostgreSQL and Qdrant containers..." -ForegroundColor Gray
docker compose up -d postgres qdrant
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start database containers via docker compose."
    exit 1
}

# 3. Wait for database ports 5432 and 6333
function Wait-ForPort ([int]$port, [string]$serviceName, [int]$timeoutSec = 30) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Host "      Waiting for $serviceName on port $port..." -ForegroundColor Gray -NoNewline
    while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", $port)
            $tcp.Close()
            Write-Host " Ready." -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Milliseconds 600
        }
    }
    Write-Host " Timeout!" -ForegroundColor Red
    Write-Error "$serviceName failed to become available on port $port within $timeoutSec seconds."
    exit 1
}

Wait-ForPort -port 5432 -serviceName "PostgreSQL"
Wait-ForPort -port 6333 -serviceName "Qdrant Vector DB"

# 4. Check Ollama (Local LLM)
Write-Host "[2/6] Checking local Ollama service..." -ForegroundColor Yellow
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
$ollamaAvailable = $false
if ($ollamaCmd) {
    try {
        $tcpOllama = New-Object System.Net.Sockets.TcpClient
        $tcpOllama.Connect("127.0.0.1", 11434)
        $tcpOllama.Close()
        $ollamaAvailable = $true
        Write-Host "      Ollama is running on port 11434." -ForegroundColor Green
    } catch {
        Write-Host "      Ollama installed but not running. Attempting to start 'ollama serve'..." -ForegroundColor Gray
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        try {
            $tcpOllama = New-Object System.Net.Sockets.TcpClient
            $tcpOllama.Connect("127.0.0.1", 11434)
            $tcpOllama.Close()
            $ollamaAvailable = $true
            Write-Host "      Ollama started successfully." -ForegroundColor Green
        } catch {
            Write-Host "      Could not connect to Ollama daemon. Fallback mode enabled." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "      Ollama CLI not found in PATH. Fallback mode enabled." -ForegroundColor Yellow
}

if (-not $ollamaAvailable) {
    Write-Host "      [Notice] Operating in deterministic fallback mode (100% functional, rule-based)." -ForegroundColor Cyan
}

# 5. Pre-flight Model Cache Check
Write-Host "[3/6] Running pre-flight AI model verification..." -ForegroundColor Yellow
$modelCheckResult = & $venvPython -c @"
import os, sys, re
sys.modules['regex'] = re
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
from sentence_transformers import SentenceTransformer
try:
    SentenceTransformer('intfloat/multilingual-e5-small', local_files_only=True)
    print('PREFLIGHT_OK')
except Exception as e:
    print('PREFLIGHT_FAIL:', e)
"@

if ($modelCheckResult -notmatch "PREFLIGHT_OK") {
    Write-Error "Offline embedding model is missing from HuggingFace cache!`nPlease run 'scripts\download_models.ps1' to pre-cache required weights."
    exit 1
}
Write-Host "      Offline embedding model (multilingual-e5-small) verified in cache." -ForegroundColor Green

# Verify OCR weights
$paddlexDir = Join-Path $repoRoot "data\paddlex"
if (-not (Test-Path $paddlexDir)) {
    Write-Warning "data\paddlex directory not found. OCR will use local models or fallback."
} else {
    Write-Host "      Local OCR weights verified in data\paddlex." -ForegroundColor Green
}

# 6. Database Migrations and Seed
Write-Host "[4/6] Initializing and seeding demo database..." -ForegroundColor Yellow
& $venvPython (Join-Path $repoRoot "backend\app\scripts\reset_demo.py")
if ($LASTEXITCODE -ne 0) {
    Write-Error "Database initialization/reset failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

# 7. Configure Production Environment and Ephemeral Secret Key
Write-Host "[5/6] Securing production environment configuration..." -ForegroundColor Yellow

# Generate cryptographically secure ephemeral 256-bit secret key in memory (never written to disk or printed)
$keyBytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($keyBytes)
$env:SECRET_KEY = -join ($keyBytes | ForEach-Object { "{0:x2}" -f $_ })
$keyBytes = $null

$env:ENVIRONMENT = "production"
$env:ENABLE_DOCS = "false"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://localhost:8000"]'

Write-Host "      Ephemeral 256-bit SECRET_KEY configured in memory." -ForegroundColor Green
Write-Host "      ENVIRONMENT=production (Interactive Swagger /docs and /openapi.json disabled)." -ForegroundColor Green
Write-Host "      Strict air-gapped offline flags activated (HF_HUB_OFFLINE=1)." -ForegroundColor Green

# 8. Start Uvicorn Server
Write-Host "[6/6] Launching NileOps Unified Single-Port Server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Write-Host "      Frontend SPA & Backend API are served unified at http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "      Press Ctrl+C to stop the server.`n" -ForegroundColor Gray

Push-Location (Join-Path $repoRoot "backend")
try {
    & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
} finally {
    Pop-Location
}
