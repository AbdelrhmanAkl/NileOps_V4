# NileOps — Desktop Shortcut Creator
# إنشاء اختصارات سطح المكتب لمنصة نايل أوبس
# Creates "NileOps.lnk" and "NileOps Stop.lnk" on the current user's Desktop.

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$desktopPath = [Environment]::GetFolderPath('Desktop')

if (-not (Test-Path $desktopPath)) {
    Write-Host "[ERROR] Could not resolve current user's Desktop directory." -ForegroundColor Red
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "     NileOps — Desktop Shortcut Installation Utility      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Target Desktop: $desktopPath" -ForegroundColor Gray

$WshShell = New-Object -ComObject WScript.Shell

# 1. NileOps Launcher Shortcut
$launcherBat = Join-Path $repoRoot "NileOps_Launcher.bat"
$shortcut1Path = Join-Path $desktopPath "NileOps.lnk"

$shortcut1 = $WshShell.CreateShortcut($shortcut1Path)
$shortcut1.TargetPath = $launcherBat
$shortcut1.WorkingDirectory = $repoRoot
$shortcut1.Description = "Launch NileOps Digital Banking Platform"
$shortcut1.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$shortcut1.Save()
Write-Host "  [+] Created: NileOps.lnk (Launch)" -ForegroundColor Green

# 2. NileOps Stop Shortcut
$stopBat = Join-Path $repoRoot "NileOps_Stop.bat"
$shortcut2Path = Join-Path $desktopPath "NileOps Stop.lnk"

$shortcut2 = $WshShell.CreateShortcut($shortcut2Path)
$shortcut2.TargetPath = $stopBat
$shortcut2.WorkingDirectory = $repoRoot
$shortcut2.Description = "Stop NileOps Digital Banking Platform"
$shortcut2.IconLocation = "$env:SystemRoot\System32\shell32.dll,27"
$shortcut2.Save()
Write-Host "  [+] Created: NileOps Stop.lnk (Shutdown)" -ForegroundColor Green

Write-Host "`nShortcuts successfully created on Desktop pointing to this clone:" -ForegroundColor Green
Write-Host "  Launcher: $launcherBat" -ForegroundColor Cyan
Write-Host "  Shutdown: $stopBat" -ForegroundColor Cyan
