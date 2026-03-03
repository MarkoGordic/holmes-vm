<#
.SYNOPSIS
  Install NirSoft HashMyFiles.
#>
Set-StrictMode -Version Latest

function Install-HashMyFiles {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\HashMyFiles',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'HashMyFiles.exe')) {
        Write-Log -Level Success -Message "HashMyFiles already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading HashMyFiles from NirSoft...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    $url = 'https://www.nirsoft.net/utils/hashmyfiles-x64.zip'
    $tmpZip = Join-Path $env:TEMP 'hashmyfiles-x64.zip'

    try {
        Invoke-SafeDownload -Uri $url -OutFile $tmpZip
    } catch {
        $url = 'https://www.nirsoft.net/utils/hashmyfiles.zip'
        Invoke-SafeDownload -Uri $url -OutFile $tmpZip
    }

    Expand-Zip -ZipPath $tmpZip -Destination $InstallDir
    Remove-Item $tmpZip -Force -ErrorAction SilentlyContinue

    Write-Log -Level Success -Message "HashMyFiles installed to $InstallDir"
}
