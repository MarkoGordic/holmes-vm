<#
.SYNOPSIS
  Install PE-bear from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-PEBear {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\PE-bear',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'PE-bear.exe')) {
        Write-Log -Level Success -Message "PE-bear already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading PE-bear from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/hasherezade/pe-bear/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query PE-bear releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'x64.*\.zip$' -and $_.name -notmatch 'linux|macos' } | Select-Object -First 1
    if (-not $asset) {
        $asset = $release.assets | Where-Object { $_.name -match '\.zip$' -and $_.name -notmatch 'linux|macos' } | Select-Object -First 1
    }
    if (-not $asset) { throw 'No Windows zip found in PE-bear release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    # Flatten nested folder if present
    $nested = Get-ChildItem -Path $InstallDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'PE-bear.exe') } | Select-Object -First 1
    if ($nested) {
        Get-ChildItem -Path $nested.FullName | Move-Item -Destination $InstallDir -Force -ErrorAction SilentlyContinue
        Remove-Item $nested.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Log -Level Success -Message "PE-bear installed to $InstallDir"
}
