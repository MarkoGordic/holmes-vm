<#
.SYNOPSIS
  Install Didier Stevens PDF analysis tools (pdf-parser, pdfid).
#>
Set-StrictMode -Version Latest

function Install-PdfTools {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\pdf-tools',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if ((Test-Path (Join-Path $InstallDir 'pdf-parser.py')) -and (Test-Path (Join-Path $InstallDir 'pdfid.py'))) {
        Write-Log -Level Success -Message "PDF tools already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Downloading Didier Stevens PDF tools...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    # Download pdf-parser
    $pdfParserZip = Join-Path $env:TEMP 'pdf-parser.zip'
    try {
        $apiUrl = 'https://api.github.com/repos/DidierStevens/DidierStevensSuite/contents'
        $headers = @{ 'User-Agent' = 'Holmes-VM' }
        # Direct download from the suite repository
        $pdfParserUrl = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/pdf-parser.py'
        $pdfIdUrl = 'https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/pdfid.py'

        Invoke-SafeDownload -Uri $pdfParserUrl -OutFile (Join-Path $InstallDir 'pdf-parser.py')
        Write-Log -Level Info -Message 'Downloaded pdf-parser.py'

        Invoke-SafeDownload -Uri $pdfIdUrl -OutFile (Join-Path $InstallDir 'pdfid.py')
        Write-Log -Level Info -Message 'Downloaded pdfid.py'

        # Also grab some other useful scripts
        $extraTools = @('oledump.py', 'emldump.py', 'zipdump.py', 'base64dump.py')
        foreach ($tool in $extraTools) {
            try {
                $toolUrl = "https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/$tool"
                Invoke-SafeDownload -Uri $toolUrl -OutFile (Join-Path $InstallDir $tool)
                Write-Log -Level Info -Message "Downloaded $tool"
            } catch {
                Write-Log -Level Warning -Message "Could not download $tool (non-critical)"
            }
        }
    } catch {
        Write-Log -Level Error -Message "Failed to download PDF tools: $_"
        return
    }

    # Create batch launchers
    foreach ($script in (Get-ChildItem $InstallDir -Filter '*.py')) {
        $name = $script.BaseName
        $launcher = @"
@echo off
python "%~dp0$($script.Name)" %*
"@
        Set-Content -Path (Join-Path $InstallDir "$name.bat") -Value $launcher
    }

    Write-Log -Level Success -Message "PDF tools installed to $InstallDir"
}
