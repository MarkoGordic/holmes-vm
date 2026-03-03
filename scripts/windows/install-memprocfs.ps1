<#
.SYNOPSIS
  Install MemProcFS from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-MemProcFS {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\MemProcFS',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'MemProcFS.exe')) {
        Write-Log -Level Success -Message "MemProcFS already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading MemProcFS from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/ufrisk/MemProcFS/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query MemProcFS releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'win_x64.*\.zip$' -or ($_.name -match '\.zip$' -and $_.name -match 'win') } | Select-Object -First 1
    if (-not $asset) {
        $asset = $release.assets | Where-Object { $_.name -match '\.zip$' } | Select-Object -First 1
    }
    if (-not $asset) { throw 'No Windows zip found in MemProcFS release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    # Flatten nested folder
    $nested = Get-ChildItem -Path $InstallDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'MemProcFS.exe') } | Select-Object -First 1
    if ($nested) {
        Get-ChildItem -Path $nested.FullName | Move-Item -Destination $InstallDir -Force -ErrorAction SilentlyContinue
        Remove-Item $nested.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

    Add-PathIfMissing -Path $InstallDir
    Write-Log -Level Success -Message "MemProcFS installed to $InstallDir"
}
