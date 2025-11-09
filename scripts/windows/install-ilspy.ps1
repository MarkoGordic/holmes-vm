<#
.SYNOPSIS
  Install ILSpy (.NET decompiler) from the latest GitHub release and create desktop shortcuts.

.NOTES
  - Downloads latest ILSpy binaries ZIP from GitHub Releases.
  - Extracts to C:\Tools\ILSpy by default.
  - Adds the ILSpy folder to PATH.
  - Creates a Desktop shortcut (optionally in a category folder) to ILSpy.exe.
  - Requires Windows and Administrator for PATH changes and shortcut creation.
#>

Set-StrictMode -Version Latest

# Try to import common module for logging/helpers if available when run standalone
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-ILSpy {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\ILSpy',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing ILSpy (.NET decompiler)...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir = $Destination
    $zipPath = Join-Path $env:TEMP 'ilspy.zip'
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'ILSpy' }

    Ensure-Directory -Path $installDir
    Ensure-Directory -Path $desktopShortcutDir

    $releaseApi = 'https://api.github.com/repos/icsharpcode/ILSpy/releases/latest'
    Set-Tls12IfNeeded

    # Determine asset URL (prefer binaries zip)
    $downloadUrl = $null
    try {
        $resp = Invoke-RestMethod -Uri $releaseApi -UseBasicParsing -ErrorAction Stop -Headers @{ 'User-Agent' = 'Holmes-VM-Installer' }
        $asset = $resp.assets | Where-Object { $_.name -match '(?i)binaries.*\.zip$' } | Select-Object -First 1
        if (-not $asset) {
            # Fallback: any zip that looks like ILSpy portable/binaries
            $asset = $resp.assets | Where-Object { $_.name -match '(?i)ilspy.*\.zip$' -and $_.name -notmatch '(?i)(symbols|sha|checksum|sig)$' } | Select-Object -First 1
        }
        if ($asset) {
            $downloadUrl = $asset.browser_download_url
            Write-Log -Level Info -Message "Selected ILSpy asset: $($asset.name)"
        }
    } catch {
        Write-Log -Level Warn -Message "Failed to query ILSpy release API: $($_.Exception.Message)"
    }

    if (-not $downloadUrl) {
        Write-Log -Level Warn -Message 'Could not identify binaries zip from API; trying generic latest download path.'
        # Known pattern typically works but may change; best-effort fallback
        $downloadUrl = 'https://github.com/icsharpcode/ILSpy/releases/latest/download/ILSpy_binaries.zip'
    }

    Write-Log -Level Info -Message "Downloading ILSpy from: $downloadUrl"
    try {
        Invoke-SafeDownload -Uri $downloadUrl -OutFile $zipPath | Out-Null
    } catch {
        Write-Log -Level Error -Message "Download failed: $($_.Exception.Message)"
        return
    }

    if (-not (Test-Path -LiteralPath $zipPath)) {
        Write-Log -Level Error -Message 'Download failed; archive not found.'
        return
    }

    # Extract to installDir
    try {
        Expand-Zip -ZipPath $zipPath -Destination $installDir
        Write-Log -Level Success -Message "Extracted ILSpy to $installDir"
    } catch {
        Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
        return
    } finally {
        try { if (Test-Path -LiteralPath $zipPath) { Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue } } catch { }
    }

    # Find ILSpy.exe
    $exe = Get-ChildItem -Path $installDir -Recurse -Filter 'ILSpy.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $exe) {
        Write-Log -Level Warn -Message 'ILSpy.exe not found after extraction.'
        return
    }

    $binDir = $exe.Directory.FullName

    # Add to PATH for convenience
    try { Add-PathIfMissing -Path $binDir -Scope Machine } catch { Write-Log -Level Warn -Message "Failed to add PATH: $($_.Exception.Message)" }

    # Create desktop shortcut unless skipped
    if (-not $SkipShortcuts) {
        try {
            New-ShortcutsFromFolder -Folder $binDir -Filter 'ILSpy.exe' -ShortcutDir $desktopShortcutDir -WorkingDir $binDir
            Write-Log -Level Success -Message 'Desktop shortcut created.'
        } catch {
            Write-Log -Level Warn -Message "Failed to create shortcut: $($_.Exception.Message)"
        }
    }

    Write-Log -Level Success -Message 'ILSpy installation completed.'
}

# Note: This script is dot-sourced by the orchestrator and not intended to auto-run.
