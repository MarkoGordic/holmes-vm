<#
.SYNOPSIS
  Install Hayabusa (Windows event log fast forensics) from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-Hayabusa {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\Hayabusa',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'hayabusa.exe')) {
        Write-Log -Level Success -Message "Hayabusa already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading Hayabusa from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/Yamato-Security/hayabusa/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query Hayabusa releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'win-x64.*\.zip$' -or $_.name -match 'windows.*x64.*\.zip$' } | Select-Object -First 1
    if (-not $asset) {
        $asset = $release.assets | Where-Object { $_.name -match 'win.*\.zip$' } | Select-Object -First 1
    }
    if (-not $asset) { throw 'No Windows zip found in Hayabusa release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    # Flatten nested folder
    $nested = Get-ChildItem -Path $InstallDir -Directory | Select-Object -First 1
    if ($nested -and (Get-ChildItem -Path $nested.FullName -Filter '*.exe' -Recurse)) {
        Get-ChildItem -Path $nested.FullName | Move-Item -Destination $InstallDir -Force -ErrorAction SilentlyContinue
        Remove-Item $nested.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Rename exe if needed (hayabusa releases often have version in name)
    $exes = Get-ChildItem -Path $InstallDir -Filter 'hayabusa*.exe' -File
    $target = Join-Path $InstallDir 'hayabusa.exe'
    if ($exes -and -not (Test-Path $target)) {
        Copy-Item $exes[0].FullName $target -Force
    }

    Add-PathIfMissing -Path $InstallDir
    Write-Log -Level Success -Message "Hayabusa installed to $InstallDir"
}
