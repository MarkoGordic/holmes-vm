<#
.SYNOPSIS
  Install NirSoft FullEventLogView.
#>
Set-StrictMode -Version Latest

function Install-FullEventLogView {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\FullEventLogView',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'FullEventLogView.exe')) {
        Write-Log -Level Success -Message "FullEventLogView already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading FullEventLogView from NirSoft...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    $url = 'https://www.nirsoft.net/utils/fulleventlogview-x64.zip'
    $tmpZip = Join-Path $env:TEMP 'fulleventlogview-x64.zip'

    try {
        Invoke-SafeDownload -Uri $url -OutFile $tmpZip
    } catch {
        # Try alternate URL
        $url = 'https://www.nirsoft.net/utils/fulleventlogview.zip'
        Invoke-SafeDownload -Uri $url -OutFile $tmpZip
    }

    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    Write-Log -Level Success -Message "FullEventLogView installed to $InstallDir"
}
