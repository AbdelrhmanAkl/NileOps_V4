# NileOps — Cloudflare Quick Tunnel Launcher
# Exposes the local unified single-port NileOps instance (http://localhost:8000) securely via Cloudflare.

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         NileOps Digital Banking — Cloudflare Tunnel       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check for cloudflared executable
$cloudflaredCmd = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredCmd) {
    Write-Host "`n[ERROR] 'cloudflared' CLI was not found on this system." -ForegroundColor Red
    Write-Host "`nTo install Cloudflare Tunnel for Windows, run the following command in PowerShell:" -ForegroundColor Yellow
    Write-Host "`n    winget install --id Cloudflare.cloudflared`n" -ForegroundColor Green
    Write-Host "After installation completes, restart your terminal and re-run this script." -ForegroundColor Gray
    exit 1
}

# 2. Check if local NileOps server is running on port 8000
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect("127.0.0.1", 8000)
    $tcp.Close()
} catch {
    Write-Warning "NileOps unified server does not appear to be running on http://127.0.0.1:8000."
    Write-Warning "Make sure to run '.\scripts\start_demo.ps1' in a separate terminal."
}

Write-Host "`nStarting free Cloudflare Quick Tunnel forwarding to http://localhost:8000..." -ForegroundColor Cyan
Write-Host "Capturing public trycloudflare.com URL..." -ForegroundColor Gray

# 3. Launch cloudflared and capture output
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $cloudflaredCmd.Source
$psi.Arguments = "tunnel --url http://localhost:8000"
$psi.RedirectStandardError = $true
$psi.RedirectStandardOutput = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $false

$proc = [System.Diagnostics.Process]::Start($psi)

$urlFound = $false
while (-not $proc.HasExited -and -not $urlFound) {
    $line = $proc.StandardError.ReadLine()
    if ($line) {
        if ($line -match "(https://[a-zA-Z0-9-]+\.trycloudflare\.com)") {
            $tunnelUrl = $matches[1]
            $urlFound = $true
            Write-Host "`n================================================================================" -ForegroundColor Green
            Write-Host "  NileOps Public Demo URL:" -ForegroundColor Green
            Write-Host "  $tunnelUrl" -ForegroundColor White
            Write-Host "================================================================================" -ForegroundColor Green
            Write-Host "`nShare this URL to access the live NileOps Demo Banking application from anywhere." -ForegroundColor Cyan
            Write-Host "Press Ctrl+C to stop the tunnel.`n" -ForegroundColor Gray
        }
    }
}

# Keep forwarding logs until user terminates
try {
    while (-not $proc.HasExited) {
        $line = $proc.StandardError.ReadLine()
        if ($line -and ($line -match "ERR" -or $line -match "Registered tunnel connection")) {
            Write-Host $line -ForegroundColor DarkGray
        }
    }
} finally {
    if (-not $proc.HasExited) {
        $proc.Kill()
    }
}
