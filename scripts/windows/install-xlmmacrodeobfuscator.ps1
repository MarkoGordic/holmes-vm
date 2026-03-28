<#
.SYNOPSIS
  Install XLMMacroDeobfuscator (Excel 4.0 XLM macro deobfuscation tool).
  Decodes and deobfuscates XLM macros commonly used in malicious Office documents.
#>
Set-StrictMode -Version Latest

function Install-XLMMacroDeobfuscator {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\XLMMacroDeobfuscator',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    Write-Log -Level Info -Message 'Installing XLMMacroDeobfuscator via pip...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    # Refresh PATH from registry
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
        Write-Log -Level Warn -Message 'Python not found. Skipping XLMMacroDeobfuscator install.'
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

    Write-Log -Level Info -Message 'Installing XLMMacroDeobfuscator package...'
    & $pipExe install --upgrade XLMMacroDeobfuscator 2>&1 | ForEach-Object { Write-Log -Level Info -Message $_ }

    # Check if installed successfully
    $xlmExe = Join-Path $venvDir 'Scripts\xlmdeobfuscator.exe'
    if (-not (Test-Path $xlmExe)) {
        Write-Log -Level Error -Message 'XLMMacroDeobfuscator installation failed.'
        return
    }

    # Create launcher batch files
    $launcherContent = @"
@echo off
"%~dp0venv\Scripts\xlmdeobfuscator.exe" %*
"@
    Set-Content -Path (Join-Path $InstallDir 'xlmdeobfuscator.bat') -Value $launcherContent

    Add-PathIfMissing -Path $InstallDir -Scope Machine
    Write-Log -Level Success -Message "XLMMacroDeobfuscator installed to $InstallDir"
}
