<#
.SYNOPSIS
  Install YARA from GitHub releases and download community rules.
#>
Set-StrictMode -Version Latest

function Install-YARA {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\YARA',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'yara64.exe')) {
        Write-Log -Level Success -Message "YARA already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading YARA from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/VirusTotal/yara/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query YARA releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'yara.*win64.*\.zip$' } | Select-Object -First 1
    if (-not $asset) {
        $asset = $release.assets | Where-Object { $_.name -match 'win64.*\.zip$' } | Select-Object -First 1
    }
    if (-not $asset) { throw 'No Windows x64 zip found in YARA release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    Add-PathIfMissing -Path $InstallDir

    # Download YARA rules collection
    $rulesDir = Join-Path $InstallDir 'rules'
    Ensure-Directory -Path $rulesDir
    try {
        $rulesZip = Join-Path $env:TEMP 'yara-rules.zip'
        Invoke-SafeDownload -Uri 'https://github.com/Yara-Rules/rules/archive/refs/heads/master.zip' -OutFile $rulesZip
        Expand-Zip -ZipPath $rulesZip -Destination $rulesDir
        Remove-Item $rulesZip -Force -ErrorAction SilentlyContinue
        Write-Log -Level Success -Message 'YARA community rules downloaded.'
    } catch {
        Write-Log -Level Warn -Message "Could not download YARA rules: $($_.Exception.Message)"
    }

    Write-Log -Level Success -Message "YARA installed to $InstallDir"
}
