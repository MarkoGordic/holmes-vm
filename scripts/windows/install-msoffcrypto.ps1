<#
.SYNOPSIS
  Install msoffcrypto-tool (decrypt password-protected Office documents).
  Python-based tool that supports MS Office 97-2019 encryption formats.
#>
Set-StrictMode -Version Latest

function Install-MsOffCrypto {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\msoffcrypto',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    Write-Log -Level Info -Message 'Installing msoffcrypto-tool via pip...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    # Refresh PATH from registry — Chocolatey may have installed Python in this session
    $machPath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machPath;$userPath"

    # Find Python
    $python = $null
    foreach ($cmd in @('python', 'python3', 'py')) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) { $python = $found.Source; break }
    }
    if (-not $python) {
        foreach ($p in @('C:\Python313\python.exe', 'C:\Python312\python.exe',
                         'C:\Python311\python.exe', 'C:\ProgramData\chocolatey\bin\python.exe')) {
            if (Test-Path $p) { $python = $p; break }
        }
    }

    if (-not $python) {
        Write-Log -Level Warn -Message 'Python not found. Skipping msoffcrypto-tool install.'
        return
    }

    # Create a virtual environment
    $venvDir = Join-Path $InstallDir 'venv'
    if (-not (Test-Path $venvDir)) {
        Write-Log -Level Info -Message 'Creating virtual environment...'
        & $python -m venv $venvDir
    }

    $pipExe = Join-Path $venvDir 'Scripts\pip.exe'
    if (-not (Test-Path $pipExe)) {
        Write-Log -Level Error -Message 'Failed to create virtual environment.'
        return
    }

    Write-Log -Level Info -Message 'Installing msoffcrypto-tool package...'
    & $pipExe install --upgrade msoffcrypto-tool 2>&1 | ForEach-Object { Write-Log -Level Info -Message $_ }

    # Check if installed successfully
    $msoffcryptoExe = Join-Path $venvDir 'Scripts\msoffcrypto-tool.exe'
    if (-not (Test-Path $msoffcryptoExe)) {
        Write-Log -Level Error -Message 'msoffcrypto-tool installation failed.'
        return
    }

    # Create a launcher batch file
    $launcherContent = @"
@echo off
"%~dp0venv\Scripts\msoffcrypto-tool.exe" %*
"@
    Set-Content -Path (Join-Path $InstallDir 'msoffcrypto-tool.bat') -Value $launcherContent

    Add-PathIfMissing -Path $InstallDir -Scope Machine
    Write-Log -Level Success -Message "msoffcrypto-tool installed to $InstallDir"
}
