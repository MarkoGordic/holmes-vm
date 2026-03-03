<#
.SYNOPSIS
  Install x64dbg debugger from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-x64dbg {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\x64dbg',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'release\x96dbg.exe')) {
        Write-Log -Level Success -Message "x64dbg already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading x64dbg from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/x64dbg/x64dbg/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query x64dbg releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'snapshot.*\.zip$' } | Select-Object -First 1
    if (-not $asset) { throw 'No snapshot zip found in x64dbg release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    # x64dbg extracts to release/ subfolder
    $releaseDir = Join-Path $InstallDir 'release'
    if (Test-Path $releaseDir) {
        Add-PathIfMissing -Path $releaseDir
    }

    Write-Log -Level Success -Message "x64dbg installed to $InstallDir"
}
