<#
.SYNOPSIS
  Install OfficeMalScanner (Frank Boldewin's Office malware scanner).
  Scans Office documents for shellcode, encrypted macros, and PE anomalies.
#>
Set-StrictMode -Version Latest

function Install-OfficeMalScanner {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\OfficeMalScanner',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'OfficeMalScanner.exe')) {
        Write-Log -Level Success -Message "OfficeMalScanner already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Installing OfficeMalScanner...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    $zipPath = Join-Path $env:TEMP 'OfficeMalScanner.zip'

    # Primary: download from known mirror / archive
    $urls = @(
        'https://www.yourdownloadsite.com/OfficeMalScanner.zip',  # placeholder
        'http://www.reconstructer.org/code/OfficeMalScanner.zip'
    )

    # OfficeMalScanner is hard to find online — try GitHub mirrors first
    $ghMirrors = @(
        'https://github.com/clubjacker/OfficeMalScanner/archive/refs/heads/master.zip',
        'https://github.com/bromiley/OfficeMalScanner/archive/refs/heads/master.zip'
    )

    $downloaded = $false
    foreach ($url in $ghMirrors) {
        Write-Log -Level Info -Message "Trying: $url"
        try {
            Invoke-SafeDownload -Uri $url -OutFile $zipPath -ErrorAction Stop | Out-Null
            if ((Test-Path $zipPath) -and (Get-Item $zipPath).Length -gt 1000) {
                $downloaded = $true
                break
            }
        } catch {
            Write-Log -Level Info -Message "Mirror failed: $($_.Exception.Message)"
        }
    }

    if (-not $downloaded) {
        # Fallback: try the original reconstructer.org URL
        try {
            Invoke-SafeDownload -Uri 'http://www.reconstructer.org/code/OfficeMalScanner.zip' -OutFile $zipPath -ErrorAction Stop | Out-Null
            if ((Test-Path $zipPath) -and (Get-Item $zipPath).Length -gt 1000) { $downloaded = $true }
        } catch {
            Write-Log -Level Warn -Message "Original source also failed: $($_.Exception.Message)"
        }
    }

    if (-not $downloaded) {
        Write-Log -Level Error -Message 'OfficeMalScanner could not be downloaded from any source.'
        return
    }

    try {
        Expand-Zip -ZipPath $zipPath -Destination $InstallDir
        # GitHub archives extract into a subfolder — flatten if needed
        $sub = Get-ChildItem $InstallDir -Directory | Where-Object { $_.Name -match 'OfficeMalScanner' } | Select-Object -First 1
        if ($sub) {
            Get-ChildItem $sub.FullName -Recurse | Move-Item -Destination $InstallDir -Force -ErrorAction SilentlyContinue
            Remove-Item $sub.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
        Get-ChildItem $InstallDir -Recurse -File | Unblock-File -ErrorAction SilentlyContinue
        Write-Log -Level Success -Message "OfficeMalScanner installed to $InstallDir"
    } catch {
        Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
    } finally {
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    }

    Add-PathIfMissing -Path $InstallDir -Scope Machine
    Write-Log -Level Success -Message 'OfficeMalScanner installation completed.'
}
