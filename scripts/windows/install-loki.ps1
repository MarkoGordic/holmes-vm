<#
.SYNOPSIS
  Install Loki IOC Scanner from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-Loki {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\Loki',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'loki.exe')) {
        Write-Log -Level Success -Message "Loki already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading Loki IOC Scanner from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/Neo23x0/Loki/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query Loki releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match '\.zip$' } | Select-Object -First 1
    if (-not $asset) { throw 'No zip asset found in Loki release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    # Flatten nested folder
    $nested = Get-ChildItem -Path $InstallDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'loki.exe') } | Select-Object -First 1
    if ($nested) {
        Get-ChildItem -Path $nested.FullName | Move-Item -Destination $InstallDir -Force -ErrorAction SilentlyContinue
        Remove-Item $nested.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

    Add-PathIfMissing -Path $InstallDir
    Write-Log -Level Success -Message "Loki installed to $InstallDir"
}
