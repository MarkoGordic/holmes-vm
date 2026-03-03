<#
.SYNOPSIS
  Install Arsenal Image Mounter from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-ArsenalImageMounter {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\ArsenalImageMounter',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'ArsenalImageMounter.exe')) {
        Write-Log -Level Success -Message "Arsenal Image Mounter already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading Arsenal Image Mounter from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/ArsenalRecon/Arsenal-Image-Mounter/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query Arsenal Image Mounter releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match '\.zip$' -or $_.name -match '\.exe$' } | Select-Object -First 1
    if (-not $asset) { throw 'No zip/exe found in Arsenal Image Mounter release.' }

    Ensure-Directory -Path $InstallDir

    if ($asset.name -match '\.zip$') {
        $tmpZip = Join-Path $env:TEMP $asset.name
        Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip
        Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
        Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue
    } else {
        $dest = Join-Path $InstallDir $asset.name
        Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $dest
    }

    Write-Log -Level Success -Message "Arsenal Image Mounter installed to $InstallDir"
}
