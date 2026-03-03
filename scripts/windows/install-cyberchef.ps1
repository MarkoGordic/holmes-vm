<#
.SYNOPSIS
  Install CyberChef offline from GitHub releases.
#>
Set-StrictMode -Version Latest

function Install-CyberChef {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\CyberChef',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'CyberChef*.html')) {
        Write-Log -Level Success -Message "CyberChef already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading CyberChef from GitHub...'
    Set-Tls12IfNeeded
    $apiUrl = 'https://api.github.com/repos/gchq/CyberChef/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -UseBasicParsing -ErrorAction Stop
    } catch {
        throw "Failed to query CyberChef releases: $($_.Exception.Message)"
    }

    $asset = $release.assets | Where-Object { $_.name -match '\.zip$' } | Select-Object -First 1
    if (-not $asset) { throw 'No zip asset found in latest CyberChef release.' }

    $tmpZip = Join-Path $env:TEMP $asset.name
    Invoke-SafeDownload -Uri $asset.browser_download_url -OutFile $tmpZip

    Ensure-Directory -Path $InstallDir
    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    # Rename the HTML file to CyberChef.html for easy access
    $html = Get-ChildItem -Path $InstallDir -Filter 'CyberChef*.html' -Recurse | Select-Object -First 1
    if ($html) {
        $dest = Join-Path $InstallDir 'CyberChef.html'
        if ($html.FullName -ne $dest) {
            Copy-Item $html.FullName $dest -Force
        }
    }

    Write-Log -Level Success -Message "CyberChef installed to $InstallDir"
}
