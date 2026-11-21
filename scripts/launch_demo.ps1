# NileOps — Unified Single-Port Demo Launcher
# تشغيل منصة نايل أوبس للعمليات المصرفية الرقمية
# Orchestrates Docker dependencies, data initialization, local server startup,
# browser launch, and optional Cloudflare tunneling and automated self-checks.

[CmdletBinding()]
param (
    [switch]$Tunnel,
    [switch]$Reset,
    [switch]$Check
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      NileOps Digital Banking — Demo Platform Launcher    " -ForegroundColor Cyan
Write-Host "      منصة نايل أوبس الذكية للعمليات المصرفية الرقمية       " -ForegroundColor DarkCyan
Write-Host "==========================================================" -ForegroundColor Cyan

# a. Verify Python Virtual Environment
$venvPython = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "`n==========================================================" -ForegroundColor Red
    Write-Host " [ERROR] Python virtual environment not found at backend\.venv" -ForegroundColor Red
    Write-Host "==========================================================" -ForegroundColor Red
    Write-Host "Please set up the backend virtual environment by running:" -ForegroundColor Yellow
    Write-Host "    cd backend" -ForegroundColor Cyan
    Write-Host "    python -m venv .venv" -ForegroundColor Cyan
    Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "    pip install -r requirements.txt" -ForegroundColor Cyan
    exit 1
}

# b. Docker Desktop Service Check
Write-Host "`n[1/8] Verifying Docker service & engine status..." -ForegroundColor Yellow
$enginePreCheck = $false
try {
    $infoTest = docker info 2>&1
    if ($LASTEXITCODE -eq 0) { $enginePreCheck = $true }
} catch {}

if (-not $enginePreCheck) {
    $dockerService = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
    if ($dockerService -and $dockerService.Status -ne "Running") {
        Write-Host "      Docker service (com.docker.service) is currently $($dockerService.Status)." -ForegroundColor Yellow
        Write-Host "      Requesting administrative privileges to start com.docker.service..." -ForegroundColor Yellow
        Write-Host "      --> A Windows UAC prompt will appear. Please approve it to continue." -ForegroundColor Cyan
        try {
            Start-Process powershell.exe -ArgumentList "-NoProfile -Command Start-Service com.docker.service" -Verb RunAs -PassThru -Wait -ErrorAction Stop | Out-Null
            Start-Sleep -Seconds 2
        } catch {
            Write-Host "      [!] Windows elevation request was declined or failed." -ForegroundColor Red
            Write-Host "      Please start the service manually in an elevated PowerShell:" -ForegroundColor Yellow
            Write-Host "          Start-Service com.docker.service" -ForegroundColor Cyan
            exit 1
        }
        $dockerService.Refresh()
        if ($dockerService.Status -ne "Running") {
            Write-Host "      [ERROR] com.docker.service is still not running (Status: $($dockerService.Status))." -ForegroundColor Red
            Write-Host "      Please start the service manually as Administrator:" -ForegroundColor Yellow
            Write-Host "          Start-Service com.docker.service" -ForegroundColor Cyan
            exit 1
        }
        Write-Host "      com.docker.service is now Running." -ForegroundColor Green
    }
} else {
    Write-Host "      Docker engine is already active and responsive." -ForegroundColor Green
}

# c. Docker Engine Connectivity Check
Write-Host "`n[2/8] Verifying Docker engine connectivity..." -ForegroundColor Yellow
$engineReady = $false
try {
    $infoOut = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $engineReady = $true
    }
} catch {
    $engineReady = $false
}

if (-not $engineReady) {
    Write-Host "      Docker engine is not responding. Starting Docker Desktop..." -ForegroundColor Yellow
    $desktopExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $desktopExe) {
        Start-Process -FilePath $desktopExe
    } else {
        Write-Host "      Docker Desktop executable not found at default path." -ForegroundColor Yellow
    }

    Write-Host "      Waiting for Docker engine to initialize (timeout 240s)..." -ForegroundColor Gray
    $swEngine = [System.Diagnostics.Stopwatch]::StartNew()
    while ($swEngine.Elapsed.TotalSeconds -lt 240) {
        Start-Sleep -Seconds 5
        try {
            $testInfo = docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                $engineReady = $true
                Write-Host "      Docker engine is ready ($([int]$swEngine.Elapsed.TotalSeconds)s)." -ForegroundColor Green
                break
            }
        } catch {}
        Write-Host "      Waiting for Docker daemon... ($([int]$swEngine.Elapsed.TotalSeconds)s / 240s)" -ForegroundColor Gray
    }

    if (-not $engineReady) {
        Write-Host "`n==========================================================" -ForegroundColor Red
        Write-Host " [ERROR] Docker engine failed to initialize within 4 minutes." -ForegroundColor Red
        Write-Host "==========================================================" -ForegroundColor Red
        Write-Host "Likely remediation steps:" -ForegroundColor Yellow
        Write-Host "  1. Update WSL:                     wsl --update" -ForegroundColor Cyan
        Write-Host "  2. Restart WSL:                    wsl --shutdown" -ForegroundColor Cyan
        Write-Host "  3. Verify hardware virtualization is enabled in BIOS/UEFI." -ForegroundColor Cyan
        Write-Host "  4. Verify Docker Desktop service:  Start-Service com.docker.service" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "      Docker engine is active and reachable." -ForegroundColor Green
}

# d. Port Inspection (5432, 6333, 8000)
Write-Host "`n[3/8] Inspecting ports (5432, 6333, 8000)..." -ForegroundColor Yellow
$runDir = Join-Path $repoRoot ".run"
$pidFile = Join-Path $runDir "demo.pid"
$recordedPids = @()
if (Test-Path $pidFile) {
    Get-Content $pidFile | ForEach-Object {
        if ($_ -match "^(?:BACKEND|TUNNEL):(\d+)") { $recordedPids += [int]$matches[1] }
        elseif ($_ -match "^\s*(\d+)") { $recordedPids += [int]$matches[1] }
    }
}

$connections = Get-NetTCPConnection -LocalPort 5432, 6333, 8000 -State Listen -ErrorAction SilentlyContinue
if ($connections) {
    $uniqueOwners = $connections | Select-Object -Property LocalPort, OwningProcess -Unique
    foreach ($conn in $uniqueOwners) {
        $pPort = $conn.LocalPort
        $pId = $conn.OwningProcess
        $p = Get-Process -Id $pId -ErrorAction SilentlyContinue
        $pName = if ($p) { $p.ProcessName } else { "Unknown" }
        $pPath = if ($p) { $p.Path } else { "Unknown" }

        if ($pPort -in 5432, 6333) {
            $dockerProcNames = @("wslrelay", "com.docker.backend", "com.docker.proxy", "docker-proxy")
            if ($dockerProcNames -notcontains $pName.ToLower()) {
                Write-Host "`n==========================================================" -ForegroundColor Red
                Write-Host " [ERROR] Port $pPort is in use by non-Docker process!" -ForegroundColor Red
                Write-Host "==========================================================" -ForegroundColor Red
                Write-Host "Process Name: $pName" -ForegroundColor Yellow
                Write-Host "Process ID:   $pId" -ForegroundColor Yellow
                Write-Host "Path:         $pPath" -ForegroundColor Yellow
                Write-Host "`nTo stop it manually, run in PowerShell:" -ForegroundColor Cyan
                Write-Host "    Stop-Process -Id $pId -Force" -ForegroundColor Cyan
                exit 1
            }
        } elseif ($pPort -eq 8000) {
            if ($recordedPids -notcontains $pId) {
                Write-Host "`n==========================================================" -ForegroundColor Red
                Write-Host " [ERROR] Port 8000 is occupied by an unrecorded process!" -ForegroundColor Red
                Write-Host "==========================================================" -ForegroundColor Red
                Write-Host "Process Name: $pName" -ForegroundColor Yellow
                Write-Host "Process ID:   $pId" -ForegroundColor Yellow
                Write-Host "Path:         $pPath" -ForegroundColor Yellow
                Write-Host "`nPer project safety guards, unrecorded processes will not be killed automatically." -ForegroundColor Yellow
                Write-Host "To stop it manually, run in PowerShell:" -ForegroundColor Cyan
                Write-Host "    Stop-Process -Id $pId -Force" -ForegroundColor Cyan
                exit 1
            } else {
                Write-Host "      Port 8000 is currently active from existing NileOps instance (PID $pId)." -ForegroundColor Yellow
            }
        }
    }
}
Write-Host "      Ports 5432, 6333, and 8000 are clean." -ForegroundColor Green

# e. Start PostgreSQL and Qdrant Containers
Write-Host "`n[4/8] Starting Docker database containers (postgres, qdrant)..." -ForegroundColor Yellow
docker compose up -d postgres qdrant
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start Docker database containers." -ForegroundColor Red
    exit 1
}

function Wait-TcpPort ([int]$port, [string]$name, [int]$timeoutSec = 90) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Host "      Waiting for $name on port $port (timeout ${timeoutSec}s)..." -ForegroundColor Gray -NoNewline
    while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", $port)
            $tcp.Close()
            Write-Host " Ready ($([int]$sw.Elapsed.TotalSeconds)s)." -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Milliseconds 800
        }
    }
    Write-Host " TIMEOUT!" -ForegroundColor Red
    Write-Host "[ERROR] $name failed to listen on port $port within $timeoutSec seconds." -ForegroundColor Red
    exit 1
}

Wait-TcpPort -port 5432 -name "PostgreSQL" -timeoutSec 90
Wait-TcpPort -port 6333 -name "Qdrant" -timeoutSec 90

# Verify container health
$swHealth = [System.Diagnostics.Stopwatch]::StartNew()
while ($swHealth.Elapsed.TotalSeconds -lt 90) {
    $pgHealth = (docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' nileops_postgres 2>$null)
    $qdHealth = (docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' nileops_qdrant 2>$null)
    if (($pgHealth -in "healthy", "running") -and ($qdHealth -in "healthy", "running")) {
        Write-Host "      Database containers are healthy." -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
}

# f. Optional Ollama Check
Write-Host "`n[5/8] Checking local Ollama service..." -ForegroundColor Yellow
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
        Write-Host "      Ollama installed but not responding. Starting 'ollama serve' in background..." -ForegroundColor Gray
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        try {
            $tcpOllama = New-Object System.Net.Sockets.TcpClient
            $tcpOllama.Connect("127.0.0.1", 11434)
            $tcpOllama.Close()
            $ollamaAvailable = $true
            Write-Host "      Ollama started successfully." -ForegroundColor Green
        } catch {
            Write-Host "      Ollama did not respond. Extractive fallback mode will be used." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "      Ollama CLI not installed. Extractive fallback mode will operate." -ForegroundColor Gray
}

# g. Verify Model Weights and Frontend Distribution
Write-Host "`n[6/8] Verifying AI model files and frontend assets..." -ForegroundColor Yellow
$modelProbeScript = @'
import os, sys, re
sys.modules['regex'] = re
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
from sentence_transformers import SentenceTransformer
try:
    SentenceTransformer('intfloat/multilingual-e5-small', local_files_only=True)
    print('EMBEDDING_OK')
except Exception as e:
    print('EMBEDDING_FAIL:', e)
'@
$probeResult = $modelProbeScript | & $venvPython
$paddlexDir = Join-Path $repoRoot "data\paddlex"
if ($probeResult -notmatch "EMBEDDING_OK" -or -not (Test-Path $paddlexDir)) {
    Write-Host "`n==========================================================" -ForegroundColor Red
    Write-Host " [ERROR] Required offline AI model weights are missing!" -ForegroundColor Red
    Write-Host "==========================================================" -ForegroundColor Red
    Write-Host "Please download the models before running NileOps:" -ForegroundColor Yellow
    Write-Host "    .\scripts\download_models.ps1" -ForegroundColor Cyan
    exit 1
}
Write-Host "      Embedding and OCR models verified in local cache." -ForegroundColor Green

$distIndex = Join-Path $repoRoot "frontend\dist\index.html"
if (-not (Test-Path $distIndex)) {
    Write-Host "      frontend\dist is missing. Installing node packages and building..." -ForegroundColor Yellow
    Push-Location (Join-Path $repoRoot "frontend")
    try {
        if (-not (Test-Path "node_modules")) {
            cmd.exe /c "npm install"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] npm install failed." -ForegroundColor Red
                exit 1
            }
        }
        cmd.exe /c "npm run build"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] npm run build failed." -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
    Write-Host "      Frontend build completed successfully." -ForegroundColor Green
} else {
    Write-Host "      Frontend distribution verified in frontend\dist." -ForegroundColor Green
}

# h & l. First-Run Data Check & Seeding (or -Reset switch)
Write-Host "`n[7/8] Verifying database seed data and Qdrant index..." -ForegroundColor Yellow
$needsReset = $Reset.IsPresent

if (-not $needsReset) {
    $dataCheckScript = @'
import sys
sys.path.insert(0, "backend")
import asyncio
from sqlalchemy import select, func
from app.db.session import async_session_maker
from app.models.policy import PolicyDocument
from app.services.vector_store import qdrant_service
from app.services.embedding import embedding_service

async def check_data():
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(func.count(PolicyDocument.id)))
            policy_count = result.scalar() or 0
        exp_dim = await embedding_service.probe_dimension()
        collections = [c.name for c in qdrant_service.client.get_collections().collections]
        if qdrant_service.collection_name not in collections:
            return True, "Qdrant collection missing"
        col_info = qdrant_service.client.get_collection(qdrant_service.collection_name)
        points_count = getattr(col_info, 'points_count', 0) or 0
        vectors_cfg = getattr(getattr(col_info, 'config', None), 'params', None)
        actual_dim = getattr(getattr(vectors_cfg, 'vectors', None), 'size', None)
        if actual_dim is None and isinstance(getattr(vectors_cfg, 'vectors', None), dict):
            actual_dim = getattr(vectors_cfg, 'vectors', {}).get('size')
        if policy_count == 0:
            return True, "PostgreSQL policy table is empty"
        if points_count == 0:
            return True, "Qdrant collection has 0 points"
        if actual_dim != exp_dim:
            return True, f"Qdrant vector dimension mismatch ({actual_dim} != {exp_dim})"
        return False, "Data is healthy"
    except Exception as e:
        return True, f"Data check exception: {e}"

needs_reset, reason = asyncio.run(check_data())
if needs_reset:
    print("NEEDS_RESET:", reason)
else:
    print("DATA_OK")
'@
    $dataCheckResult = $dataCheckScript | & $venvPython
    if ($dataCheckResult -match "NEEDS_RESET:\s*(.+)") {
        $reason = $matches[1]
        Write-Host "      Data initialization required ($reason)." -ForegroundColor Yellow
        $needsReset = $true
    } else {
        Write-Host "      Database records and Qdrant index verified healthy." -ForegroundColor Green
    }
}

if ($needsReset) {
    Write-Host "      Seeding demo policies and reconciling Qdrant collection..." -ForegroundColor Yellow
    & $venvPython (Join-Path $repoRoot "backend\app\scripts\reset_demo.py")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Data seeding and reconciliation failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "      Data seeded and reconciled successfully." -ForegroundColor Green
}

# i. Start Backend Server in Minimized Window & Record PID
Write-Host "`n[8/8] Starting NileOps server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan

$existingListener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existingListener) {
    Write-Host "      Server is already listening on port 8000." -ForegroundColor Yellow
} else {
    $keyBytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($keyBytes)
    $secretKey = -join ($keyBytes | ForEach-Object { "{0:x2}" -f $_ })
    $keyBytes = $null

    $env:SECRET_KEY = $secretKey
    $env:ENVIRONMENT = "production"
    $env:ENABLE_DOCS = "false"
    $env:HF_HUB_OFFLINE = "1"
    $env:TRANSFORMERS_OFFLINE = "1"
    $env:ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://localhost:8000"]'

    if (-not (Test-Path $runDir)) {
        New-Item -ItemType Directory -Path $runDir -Force | Out-Null
    }

    $backendProc = Start-Process -FilePath $venvPython `
        -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info" `
        -WorkingDirectory (Join-Path $repoRoot "backend") `
        -WindowStyle Minimized `
        -PassThru

    $backendPid = $backendProc.Id
    Write-Host "      Backend process launched (PID: $backendPid)." -ForegroundColor Green

    $pidLines = [System.Collections.Generic.List[string]]::new()
    $pidLines.Add("BACKEND:$backendPid")
    Set-Content -Path $pidFile -Value $pidLines -Encoding ASCII
}

# j. Wait for /health (timeout 120s)
Write-Host "      Waiting for http://127.0.0.1:8000/health (timeout 120s)..." -ForegroundColor Gray
$swHealth = [System.Diagnostics.Stopwatch]::StartNew()
$serverHealthy = $false

while ($swHealth.Elapsed.TotalSeconds -lt 120) {
    try {
        $healthResp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 3 -ErrorAction Stop
        if ($healthResp.status -eq "healthy") {
            $serverHealthy = $true
            Write-Host "      Server is healthy and answering requests! ($([int]$swHealth.Elapsed.TotalSeconds)s)" -ForegroundColor Green
            break
        } elseif ($healthResp.status -eq "degraded") {
            $serverHealthy = $true
            Write-Host "`n==========================================================" -ForegroundColor Yellow
            Write-Host " [WARNING] Backend is running in DEGRADED status:" -ForegroundColor Yellow
            Write-Host " $($healthResp.qdrant_error)" -ForegroundColor Yellow
            Write-Host "==========================================================" -ForegroundColor Yellow
            Write-Host "Tip: Re-run with -Reset to rebuild the vector collection:" -ForegroundColor Cyan
            Write-Host "    .\NileOps_Launcher.bat -Reset" -ForegroundColor Cyan
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $serverHealthy) {
    Write-Host "`n[ERROR] NileOps server failed to respond on http://127.0.0.1:8000/health within 120s." -ForegroundColor Red
    exit 1
}

# Open browser
Write-Host "      Opening http://127.0.0.1:8000 in your default browser..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000"

# k. Cloudflare Tunnel Switch (-Tunnel)
if ($Tunnel.IsPresent) {
    Write-Host "`n==========================================================" -ForegroundColor Cyan
    Write-Host "  Starting Cloudflare Quick Tunnel (-Tunnel switch)..." -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    $cloudflaredCmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if (-not $cloudflaredCmd) {
        Write-Host "  [ERROR] 'cloudflared' CLI was not found on this system." -ForegroundColor Red
        Write-Host "  To install: winget install --id Cloudflare.cloudflared" -ForegroundColor Yellow
    } else {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $cloudflaredCmd.Source
        $psi.Arguments = "tunnel --url http://localhost:8000"
        $psi.RedirectStandardError = $true
        $psi.RedirectStandardOutput = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true

        $tunnelProc = [System.Diagnostics.Process]::Start($psi)
        $tunnelPid = $tunnelProc.Id

        $existingPids = @()
        if (Test-Path $pidFile) { $existingPids = Get-Content $pidFile }
        $existingPids += "TUNNEL:$tunnelPid"
        Set-Content -Path $pidFile -Value $existingPids -Encoding ASCII

        Write-Host "  Waiting for public tunnel URL from Cloudflare..." -ForegroundColor Gray
        $tunnelUrl = $null
        $swTunnel = [System.Diagnostics.Stopwatch]::StartNew()
        while (-not $tunnelProc.HasExited -and -not $tunnelUrl -and ($swTunnel.Elapsed.TotalSeconds -lt 30)) {
            $line = $tunnelProc.StandardError.ReadLine()
            if ($line -and $line -match "(https://[a-zA-Z0-9-]+\.trycloudflare\.com)") {
                $tunnelUrl = $matches[1]
            }
        }

        if ($tunnelUrl) {
            try { Set-Clipboard -Value $tunnelUrl } catch {}
            Write-Host "`n  ================================================================" -ForegroundColor Green
            Write-Host "  NileOps Public Demo URL: $tunnelUrl" -ForegroundColor Green
            Write-Host "  (Copied to clipboard!)" -ForegroundColor Green
            Write-Host "  ================================================================" -ForegroundColor Green
            Write-Host "  [NOTICE] A public tunnel link requires coordinator approval." -ForegroundColor Yellow
            Write-Host "  Ensure this tunnel is stopped after the demo by running NileOps_Stop.bat." -ForegroundColor Yellow
        } else {
            Write-Host "  [WARNING] Could not capture Cloudflare tunnel URL within 30 seconds." -ForegroundColor Yellow
        }
    }
}

# l. Automated Self-Check Switch (-Check)
if ($Check.IsPresent) {
    Write-Host "`n==========================================================" -ForegroundColor Cyan
    Write-Host "  Running Automated Self-Check (-Check switch)..." -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    & "$PSScriptRoot\demo_selfcheck.ps1"
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  NileOps Digital Banking Platform is running!           " -ForegroundColor Green
Write-Host "  URL:  http://127.0.0.1:8000                            " -ForegroundColor White
Write-Host "  To stop: Run NileOps_Stop.bat or scripts\stop_demo.ps1 " -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Green
