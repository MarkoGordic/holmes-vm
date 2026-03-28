<#
.SYNOPSIS
  Install OffVis (Microsoft Office binary format visualizer).
  Helps visualize and analyze the internal structure of Office documents.
#>
Set-StrictMode -Version Latest

function Install-OffVis {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$InstallDir = 'C:\Tools\OffVis',
        [string]$ShortcutCategory = ''
    )

    Import-Module (Join-Path $PSScriptRoot 'Holmes.Common.psm1') -Force -DisableNameChecking
    Assert-WindowsAndAdmin

    if (Test-Path (Join-Path $InstallDir 'OffVis.exe')) {
        Write-Log -Level Success -Message "OffVis already installed in $InstallDir"
        return
    }

    Write-Log -Level Info -Message 'Installing OffVis...'
    Set-Tls12IfNeeded
    Ensure-Directory -Path $InstallDir

    $zipPath = Join-Path $env:TEMP 'OffVis.zip'

    # OffVis was originally from Microsoft — try known mirrors
    $urls = @(
        'https://github.com/wikipedia2008/OffVis/archive/refs/heads/master.zip',
        'https://github.com/OffVis/OffVis/archive/refs/heads/master.zip'
    )

    $downloaded = $false
    foreach ($url in $urls) {
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
        Write-Log -Level Error -Message 'OffVis could not be downloaded from any source.'
        return
    }

    try {
        Expand-Zip -ZipPath $zipPath -Destination $InstallDir
        # GitHub archives extract into a subfolder — flatten if needed
        $sub = Get-ChildItem $InstallDir -Directory | Where-Object { $_.Name -match 'OffVis' } | Select-Object -First 1
        if ($sub) {
            Get-ChildItem $sub.FullName -Recurse | Move-Item -Destination $InstallDir -Force -ErrorAction SilentlyContinue
            Remove-Item $sub.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
        Get-ChildItem $InstallDir -Recurse -File | Unblock-File -ErrorAction SilentlyContinue
        Write-Log -Level Success -Message "OffVis installed to $InstallDir"
    } catch {
        Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
    } finally {
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    }

    Write-Log -Level Success -Message 'OffVis installation completed.'
}
