<#
.SYNOPSIS
  Install capa (Mandiant capability identifier) from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-Capa {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\capa',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'capa.exe')) {
        Write-Log -Level Success -Message "capa already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading capa from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/mandiant/capa/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query capa releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'windows.*\.zip$' -or $_.name -match 'win.*\.zip$' } | Select-Object -First 1
    if (-not $asset) {
        $asset = $release.assets | Where-Object { $_.name -match 'windows' -and $_.name -match '\.exe$' } | Select-Object -First 1
    }
    if (-not $asset) { throw 'No Windows asset found in capa release.' }

    Ensure-Directory -Path $InstallDir

    if ($asset.name -match '\.zip$') {
        $tmpZip = Join-Path $env:TEMP $asset.name
        Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip
        Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
        Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue
    } else {
        $dest = Join-Path $InstallDir 'capa.exe'
        Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $dest
    }

    # Download capa rules
    $rulesDir = Join-Path $InstallDir 'rules'
    try {
        $rulesZip = Join-Path $env:TEMP 'capa-rules.zip'
        Invoke-SafeDownload -Uri 'https://github.com/mandiant/capa-rules/archive/refs/heads/master.zip' -OutFile $rulesZip
        Ensure-Directory -Path $rulesDir
        Expand-Zip -ZipPath $rulesZip -Destination $rulesDir
        Remove-Item $rulesZip -Force -ErrorAction SilentlyContinue
        Write-Log -Level Success -Message 'capa rules downloaded.'
    } catch {
        Write-Log -Level Warn -Message "Could not download capa rules: $($_.Exception.Message)"
    }

    Add-PathIfMissing -Path $InstallDir
    Write-Log -Level Success -Message "capa installed to $InstallDir"
}
