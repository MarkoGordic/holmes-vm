<#
.SYNOPSIS
  Install Detect It Easy (DiE) from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-DetectItEasy {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\DetectItEasy',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'die.exe')) {
        Write-Log -Level Success -Message "Detect It Easy already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading Detect It Easy from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/horsicq/DIE-engine/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query DiE releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match 'die_win64_portable.*\.zip$' } | Select-Object -First 1
    if (-not $asset) {
        $asset = $release.assets | Where-Object { $_.name -match 'win64.*\.zip$' -or $_.name -match 'portable.*\.zip$' } | Select-Object -First 1
    }
    if (-not $asset) { throw 'No Windows portable zip found in DiE release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    # Handle nested folder
    $nested = Get-ChildItem -Path $InstallDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'die.exe') } | Select-Object -First 1
    if ($nested) {
        Get-ChildItem -Path $nested.FullName | Move-Item -Destination $InstallDir -Force -ErrorAction SilentlyContinue
        Remove-Item $nested.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

    Add-PathIfMissing -Path $InstallDir
    Write-Log -Level Success -Message "Detect It Easy installed to $InstallDir"
}
