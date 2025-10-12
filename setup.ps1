#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
    Holmes VM: Python-first orchestrator
    This PowerShell shim ensures Python is present and launches holmes_setup.py (Tkinter GUI).
#>

[CmdletBinding()]
param(
    [switch]$NoGui,
    [switch]$WhatIf,
    [switch]$ForceReinstall,
    [string]$LogDir,
    [switch]$SkipWireshark,
    [switch]$SkipDotNetDesktop,
    [switch]$SkipDnSpyEx,
    [switch]$SkipPeStudio,
    [switch]$SkipEZTools,
    [switch]$SkipRegRipper,
    [switch]$SkipWallpaper,
    [switch]$SkipNetworkCheck,
    [switch]$SkipChainsaw,
    [switch]$SkipVSCode,
    [switch]$SkipSQLiteBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-ChocoPython {
    # Ensure Chocolatey first (if module is available)
    $modulePath = Join-Path $PSScriptRoot 'modules/Holmes.Common.psm1'
    if (Test-Path -LiteralPath $modulePath) {
        try { Import-Module $modulePath -Force -DisableNameChecking } catch { }
        try { if (Get-Command Ensure-Chocolatey -ErrorAction SilentlyContinue) { Ensure-Chocolatey | Out-Null } } catch { }
    }

    # Install or upgrade to latest Python
    if (Get-Command choco.exe -ErrorAction SilentlyContinue) {
        Write-Host 'Ensuring latest Python via Chocolatey (upgrade)...' -ForegroundColor Cyan
        & choco upgrade python -y --no-progress | Out-Null
    }
    elseif (Get-Command Install-ChocoPackage -ErrorAction SilentlyContinue) {
        Write-Host 'Installing Python via Chocolatey helper...' -ForegroundColor Cyan
        Install-ChocoPackage -Name 'python' | Out-Null
    } else {
        Write-Host 'Chocolatey not detected; attempting direct choco call (may fail)...' -ForegroundColor Yellow
        choco install python -y --no-progress | Out-Null
    }

    # Refresh PATH in current session from Machine and User to pick up new entries
    try {
        $machinePath = [Environment]::GetEnvironmentVariable('Path','Machine')
        $userPath = [Environment]::GetEnvironmentVariable('Path','User')
        if ($machinePath -and $userPath) { $env:Path = "$machinePath;$userPath" }
        elseif ($machinePath) { $env:Path = $machinePath }
        elseif ($userPath) { $env:Path = $userPath }
    } catch { }

    # Ensure Chocolatey bin is on PATH (contains python shim)
    try {
        if ($env:ChocolateyInstall) {
            $chocoBin = Join-Path $env:ChocolateyInstall 'bin'
            if (Test-Path -LiteralPath $chocoBin) {
                if (-not ($env:Path -split ';' | Where-Object { $_ -ieq $chocoBin })) { $env:Path = "$env:Path;$chocoBin" }
            }
        }
    } catch { }

    # If still not found, try to locate python.exe in common locations and add to PATH
    if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command py -ErrorAction SilentlyContinue)) {
        $candidate = Get-ChildItem -Path 'C:\' -Directory -Filter 'Python3*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
        if ($candidate) {
            $pyExe = Join-Path $candidate.FullName 'python.exe'
            $pyScripts = Join-Path $candidate.FullName 'Scripts'
            if (Test-Path -LiteralPath $pyExe) {
                if (-not ($env:Path -split ';' | Where-Object { $_ -ieq $candidate.FullName })) { $env:Path = "$env:Path;$($candidate.FullName)" }
            }
            if (Test-Path -LiteralPath $pyScripts) {
                if (-not ($env:Path -split ';' | Where-Object { $_ -ieq $pyScripts })) { $env:Path = "$env:Path;$pyScripts" }
            }
        }
    }
}

function Get-PythonExe {
    if (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
    if (Get-Command py -ErrorAction SilentlyContinue) { return 'py -3' }
    return $null
}

try {
    Ensure-ChocoPython
    $py = Get-PythonExe
    if (-not $py) { throw 'Python not found after installation.' }

    $scriptPath = Join-Path $PSScriptRoot 'holmes_setup.py'
    if (-not (Test-Path -LiteralPath $scriptPath)) { throw "Missing Python setup script at $scriptPath" }

    $args = @()
    if ($NoGui) { $args += '--no-gui' }
    if ($WhatIf) { $args += '--what-if' }
    if ($ForceReinstall) { $args += '--force-reinstall' }
    if ($LogDir) { $args += @('--log-dir', $LogDir) }
    if ($SkipWireshark) { $args += '--skip-wireshark' }
    if ($SkipDotNetDesktop) { $args += '--skip-dotnet-desktop' }
    if ($SkipDnSpyEx) { $args += '--skip-dnspyex' }
    if ($SkipPeStudio) { $args += '--skip-pestudio' }
    if ($SkipEZTools) { $args += '--skip-eztools' }
    if ($SkipRegRipper) { $args += '--skip-regripper' }
    if ($SkipWallpaper) { $args += '--skip-wallpaper' }
    if ($SkipNetworkCheck) { $args += '--skip-network-check' }
    if ($SkipChainsaw) { $args += '--skip-chainsaw' }
    if ($SkipVSCode) { $args += '--skip-vscode' }
    if ($SkipSQLiteBrowser) { $args += '--skip-sqlitebrowser' }

    $cmd = "$py `"$scriptPath`" $($args -join ' ')"
    Write-Host "Launching Python setup UI..." -ForegroundColor Magenta
    # Inherit console; show UI
    & cmd /c $cmd
    exit $LASTEXITCODE
}
catch {
    Write-Host "Setup failed to start: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
