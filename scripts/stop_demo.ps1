# NileOps — Demo Platform Shutdown Script
# إيقاف منصة نايل أوبس
# Gracefully terminates NileOps server, tunnel processes, and Docker database containers.

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $repoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       NileOps Digital Banking — Demo Platform Stop       " -ForegroundColor Cyan
Write-Host "       إيقاف تشغيل منصة نايل أوبس الرقمية                   " -ForegroundColor DarkCyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Stop recorded processes from .run\demo.pid
$pidFile = Join-Path $repoRoot ".run\demo.pid"
if (Test-Path $pidFile) {
    Write-Host "[1/3] Stopping recorded application processes..." -ForegroundColor Yellow
    $lines = Get-Content $pidFile
    foreach ($line in $lines) {
        $targetPid = $null
        $label = "Process"
        if ($line -match "^(?:BACKEND|TUNNEL):(\d+)") {
            $targetPid = [int]$matches[1]
            $label = if ($line -match "^BACKEND") { "Backend Server" } else { "Cloudflare Tunnel" }
        } elseif ($line -match "^\s*(\d+)") {
            $targetPid = [int]$matches[1]
        }

        if ($targetPid) {
            $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "      Stopping $label (PID: $targetPid, Name: $($proc.ProcessName))..." -ForegroundColor Gray
                Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
                Write-Host "      $label (PID: $targetPid) stopped." -ForegroundColor Green
            } else {
                Write-Host "      $label (PID: $targetPid) was already terminated." -ForegroundColor Gray
            }
        }
    }
    Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "      PID tracker file cleared." -ForegroundColor Green
} else {
    Write-Host "[1/3] No .run\demo.pid file found." -ForegroundColor Yellow
    $listener8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($listener8000) {
        $pId = $listener8000[0].OwningProcess
        $p = Get-Process -Id $pId -ErrorAction SilentlyContinue
        $pName = if ($p) { $p.ProcessName } else { "Unknown" }
        Write-Host "      [NOTICE] Port 8000 is occupied by $pName (PID $pId), but it was not recorded in .run\demo.pid." -ForegroundColor Yellow
        Write-Host "      Per project safety rules, unrecorded processes are never killed automatically." -ForegroundColor Yellow
        Write-Host "      If needed, stop it manually: Stop-Process -Id $pId -Force" -ForegroundColor Cyan
    }
}

# 2. Stop Docker database containers (never delete volumes)
Write-Host "`n[2/3] Stopping Docker database containers (postgres, qdrant)..." -ForegroundColor Yellow
docker compose stop postgres qdrant
if ($LASTEXITCODE -ne 0) {
    Write-Warning "docker compose stop reported a non-zero exit code."
} else {
    Write-Host "      Database containers stopped cleanly." -ForegroundColor Green
}

# 3. Confirm ports are free
Write-Host "`n[3/3] Confirming ports (5432, 6333, 8000) are free..." -ForegroundColor Yellow
$portsToCheck = @(5432, 6333, 8000)
$allFree = $false
$swWait = [System.Diagnostics.Stopwatch]::StartNew()

while ($swWait.Elapsed.TotalSeconds -lt 15) {
    $activeConns = Get-NetTCPConnection -LocalPort 5432, 6333, 8000 -State Listen -ErrorAction SilentlyContinue
    if (-not $activeConns) {
        $allFree = $true
        break
    }
    Start-Sleep -Milliseconds 500
}

foreach ($port in $portsToCheck) {
    $active = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($active) {
        $pId = $active[0].OwningProcess
        $p = Get-Process -Id $pId -ErrorAction SilentlyContinue
        $pName = if ($p) { $p.ProcessName } else { "Unknown" }
        Write-Host ("      Port " + $port + ": BUSY (" + $pName + ", PID: " + $pId + ")") -ForegroundColor Red
    } else {
        Write-Host ("      Port " + $port + ": FREE") -ForegroundColor Green
    }
}

if ($allFree) {
    Write-Host "`n==========================================================" -ForegroundColor Green
    Write-Host "  NileOps environment stopped cleanly. Ports are free.    " -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} else {
    Write-Host "`n==========================================================" -ForegroundColor Yellow
    Write-Host "  NileOps stopped, but some ports remain busy.            " -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Yellow
}
