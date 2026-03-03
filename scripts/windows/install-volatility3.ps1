<#
.SYNOPSIS
  Install Volatility 3 via pip into a dedicated virtualenv.
#>
Set-StrictMode -Version Latest

function Install-Volatility3 {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\Volatility3',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    $venvDir = Join-Path $InstallDir '.venv'
    $volExe = Join-Path $venvDir 'Scripts\vol.exe'

    if (Test-Path $volExe) {
        Write-Log -Level Success -Message "Volatility 3 already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Installing Volatility 3...'
    Ensure-Directory -Path $InstallDir

    # Create virtualenv
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $python) { throw 'Python not found. Install Python first.' }

    & $python.Source -m venv $venvDir
    $pip = Join-Path $venvDir 'Scripts\pip.exe'

    & $pip install --upgrade pip setuptools wheel 2>&1 | Out-Null
    & $pip install volatility3 2>&1 | Out-Null

    if (-not (Test-Path $volExe)) {
        # Try alternative: vol3 or vol
        $volExe = Get-ChildItem (Join-Path $venvDir 'Scripts') -Filter 'vol*' -File | Select-Object -First 1
    }

    # Download symbol tables
    $symbolsDir = Join-Path $InstallDir 'symbols'
    Ensure-Directory -Path $symbolsDir
    try {
        Write-Log -Level Info -Message 'Downloading Windows symbol tables...'
        $symbolUrl = 'https://downloads.volatilityfoundation.org/volatility3/symbols/windows.zip'
        $symbolZip = Join-Path $env:TEMP 'vol3-windows-symbols.zip'
        Invoke-SafeDownload -Uri $symbolUrl -OutFile $symbolZip
        Expand-Zip -ZipPath $symbolZip -Destination $symbolsDir
        Remove-Item $symbolZip -Force -ErrorAction SilentlyContinue
        Write-Log -Level Success -Message 'Volatility 3 Windows symbols downloaded.'
    } catch {
        Write-Log -Level Warn -Message "Could not download symbols: $($_.Exception.Message)"
    }

    # Create a convenience batch wrapper
    $wrapper = Join-Path $InstallDir 'vol3.bat'
    $content = "@echo off`r`n`"$venvDir\Scripts\python.exe`" -m volatility3 %*"
    Set-Content -Path $wrapper -Value $content -Encoding ASCII

    Add-PathIfMissing -Path $InstallDir
    Write-Log -Level Success -Message "Volatility 3 installed to $InstallDir"
}
