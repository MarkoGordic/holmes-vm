<#
.SYNOPSIS
  Install FLOSS (FireEye Labs Obfuscated String Solver) from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-FLOSS {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\FLOSS',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'floss.exe')) {
        Write-Log -Level Success -Message "FLOSS already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading FLOSS from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/mandiant/flare-floss/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query FLOSS releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'windows.*\.zip$' -or $_.name -match 'win.*\.zip$' } | Select-Object -First 1
    if (-not $asset) {
        # Try standalone exe
        $asset = $release.assets | Where-Object { $_.name -match 'windows' -and $_.name -match '\.exe$' } | Select-Object -First 1
    }
    if (-not $asset) { throw 'No Windows asset found in FLOSS release.' }

    Ensure-Directory -Path $InstallDir

    if ($asset.name -match '\.zip$') {
        $tmpZip = Join-Path $env:TEMP $asset.name
        Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip
        Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
        Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue
    } else {
        $dest = Join-Path $InstallDir 'floss.exe'
        Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $dest
    }

    Add-PathIfMissing -Path $InstallDir
    Write-Log -Level Success -Message "FLOSS installed to $InstallDir"
}
