<#
.SYNOPSIS
  Install oletools (Python-based OLE/MS Office analysis toolkit).
#>
Set-StrictMode -Version Latest

function Install-OleTools {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\oletools',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    Write-Log -Level Info -Message 'Installing oletools via pip...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    # Try system Python first, then fall back to py launcher
    $python = $null
    foreach ($cmd in @('python', 'python3', 'py')) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) { $python = $found.Source; break }
    }

    if (-not $python) {
        Write-Log -Level Warning -Message 'Python not found. Please install Python first, then run: pip install oletools'
        return
    }

    # Create a virtual environment for oletools
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

    Write-Log -Level Info -Message 'Installing oletools package...'
    & $pipExe install --upgrade oletools 2>&1 | ForEach-Object { Write-Log -Level Info -Message $_ }

    # Create a launcher batch file
    $launcherContent = @"
@echo off
"%~dp0venv\Scripts\python.exe" -m oletools %*
"@
    Set-Content -Path (Join-Path $InstallDir 'oletools.bat') -Value $launcherContent

    # Create individual launchers for common tools
    foreach ($tool in @('olevba', 'oleid', 'rtfobj', 'oleobj', 'mraptor')) {
        $toolLauncher = @"
@echo off
"%~dp0venv\Scripts\$tool.exe" %*
"@
        Set-Content -Path (Join-Path $InstallDir "$tool.bat") -Value $toolLauncher
    }

    Write-Log -Level Success -Message "oletools installed to $InstallDir"
}
