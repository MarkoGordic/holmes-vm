<#
.SYNOPSIS
  Install FTK Imager (tries Chocolatey, then direct download).
#>
Set-StrictMode -Version Latest

function Install-FTKImager {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\FTK Imager',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    # Check common install locations
    $paths = @(
        'C:\Program Files\AccessData\FTK Imager\FTK Imager.exe',
        'C:\Program Files (x86)\AccessData\FTK Imager\FTK Imager.exe',
        (Join-Path $InstallDir 'FTK Imager.exe')
    )
    foreach ($p in $paths) {
        if (Test-Path $p) {
            Write-Log -Level Success -Message "FTK Imager already installed at $p"
            return
        }
    }

    Write-Log -Level Info -Message 'Installing FTK Imager...'

    # Try Chocolatey first
    if (Get-Command choco.exe -ErrorAction SilentlyContinue) {
        $result = Install-ChocoPackage -Name 'ftkimager' -SuppressDefaultInstallArgs
        if ($result) {
            Write-Log -Level Success -Message 'FTK Imager installed via Chocolatey.'
            return
        }
        Write-Log -Level Warn -Message 'Chocolatey install failed, trying direct download...'
    }

    # Direct download from Exterro (manual URL - may need updating)
    Write-Log -Level Warn -Message 'FTK Imager requires manual download from https://www.exterro.com/ftk-imager'
    Write-Log -Level Info -Message 'Please download and install FTK Imager manually.'
    Ensure-Directory -Path $InstallDir

    Write-Log -Level Warn -Message "FTK Imager: Manual installation required. Download from https://www.exterro.com/ftk-imager"
}
