<#
.SYNOPSIS
  Install KAPE (Kroll Artifact Parser and Extractor).
  Note: KAPE requires registration at https://www.kroll.com/en/services/cyber-risk/incident-response-litigation-support/kroll-artifact-parser-extractor-kape
#>
Set-StrictMode -Version Latest

function Install-KAPE {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\KAPE',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'kape.exe')) {
        Write-Log -Level Success -Message "KAPE already installed in $InstallDir"
        return
    }

    Write-Log -Level Warn -Message 'KAPE requires free registration to download.'
    Write-Log -Level Info -Message 'Register at: https://www.kroll.com/en/services/cyber-risk/incident-response-litigation-support/kroll-artifact-parser-extractor-kape'
    Write-Log -Level Info -Message "After downloading, extract to $InstallDir"

    Ensure-Directory -Path $InstallDir

    # Create a README with download instructions
    $readme = Join-Path $InstallDir 'DOWNLOAD_INSTRUCTIONS.txt'
    $content = @"
KAPE (Kroll Artifact Parser and Extractor)
==========================================

KAPE requires free registration to download.

1. Register at: https://www.kroll.com/en/services/cyber-risk/incident-response-litigation-support/kroll-artifact-parser-extractor-kape
2. Download the KAPE zip file
3. Extract contents to this folder: $InstallDir
4. Run kape.exe or gkape.exe (GUI version)

For documentation: https://ericzimmerman.github.io/KapeDocs/
"@
    Set-Content -Path $readme -Value $content -Encoding UTF8

    Write-Log -Level Warn -Message "KAPE: Manual download required. Instructions saved to $readme"
}
