<#
.SYNOPSIS
  Install Autopsy from latest GitHub release.

.NOTES
  - Queries https://api.github.com/repos/sleuthkit/autopsy/releases/latest
  - Downloads the Windows zip asset and extracts to C:\Tools\Autopsy
  - Creates a Desktop shortcut to Autopsy64.exe (or Autopsy.exe) in optional category folder
  - Requires Windows & Administrator privileges for full functionality
#>

Set-StrictMode -Version Latest

# Import common module if not already present (for Write-Log, helpers)
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-Autopsy {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\Tools\Autopsy',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing Autopsy...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'Forensics' }

    Ensure-Directory -Path $Destination
    Ensure-Directory -Path $desktopShortcutDir

    $api = 'https://api.github.com/repos/sleuthkit/autopsy/releases/latest'
    Set-Tls12IfNeeded
    $zipUrl = $null
    $zipName = $null

    try {
        $resp = Invoke-RestMethod -Uri $api -UseBasicParsing -ErrorAction Stop -Headers @{ 'User-Agent' = 'Holmes-VM-Installer' }
        # Prefer windows zip assets (Autopsy-<version>.zip). Avoid source code zips.
        $asset = $resp.assets | Where-Object { $_.name -match '(?i)^Autopsy-.*\.zip$' } | Select-Object -First 1
        if (-not $asset) {
            $asset = $resp.assets | Where-Object { $_.name -match '(?i)autopsy.*\.zip$' -and $_.name -notmatch '(?i)source|src' } | Select-Object -First 1
        }
        if ($asset) {
            $zipUrl = $asset.browser_download_url
            $zipName = $asset.name
            Write-Log -Level Info -Message "Selected Autopsy asset: $zipName"
        }
    } catch {
        Write-Log -Level Warn -Message "Failed to query Autopsy release API: $($_.Exception.Message)"
    }

    if (-not $zipUrl) {
        Write-Log -Level Error -Message 'Could not determine Autopsy release asset.'
        return
    }

    $tempZip = Join-Path $env:TEMP 'autopsy-latest.zip'
    Write-Log -Level Info -Message "Downloading Autopsy from: $zipUrl"
    try {
        Invoke-SafeDownload -Uri $zipUrl -OutFile $tempZip | Out-Null
    } catch {
        Write-Log -Level Error -Message "Download failed: $($_.Exception.Message)"
        return
    }

    if (-not (Test-Path -LiteralPath $tempZip)) {
        Write-Log -Level Error -Message 'Download failed; archive not found.'
        return
    }

    $extractTemp = Join-Path $Destination 'extracted-temp'
    Ensure-Directory -Path $extractTemp
    try {
        Expand-Zip -ZipPath $tempZip -Destination $extractTemp
        Write-Log -Level Success -Message 'Archive extracted.'
    } catch {
        Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
        return
    } finally {
        try { Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue } catch { }
    }

    # Move versioned folder contents into destination root
    $rootFolder = Get-ChildItem -Path $extractTemp -Directory | Where-Object { $_.Name -match '^(?i)autopsy-' } | Select-Object -First 1
    if ($rootFolder) {
        try {
            # If destination already contains previous version, keep it by renaming
            $targetDir = Join-Path $Destination $rootFolder.Name
            if (Test-Path -LiteralPath $targetDir) {
                Write-Log -Level Info -Message 'Removing previous extracted folder.'
                Remove-Item -Path $targetDir -Recurse -Force -ErrorAction SilentlyContinue
            }
            Move-Item -Path $rootFolder.FullName -Destination $Destination -Force
            Write-Log -Level Success -Message "Autopsy extracted to $targetDir"
        } catch {
            Write-Log -Level Warn -Message "Failed moving extracted folder: $($_.Exception.Message)"
        }
    } else {
        Write-Log -Level Warn -Message 'Versioned Autopsy folder not found inside zip.'
    }

    try { Remove-Item -Path $extractTemp -Recurse -Force -ErrorAction SilentlyContinue } catch { }

    # Find primary executable (prefer Autopsy64.exe then Autopsy.exe)
    $exe = Get-ChildItem -Path $Destination -Recurse -Filter 'Autopsy64.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $exe) {
        $exe = Get-ChildItem -Path $Destination -Recurse -Filter 'Autopsy.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    }

    if ($exe) {
        Write-Log -Level Success -Message "Located executable: $($exe.FullName)"
        if (-not $SkipShortcuts) {
            try {
                $shell = New-Object -ComObject WScript.Shell
                $lnk = Join-Path $desktopShortcutDir 'Autopsy.lnk'
                $sc = $shell.CreateShortcut($lnk)
                $sc.TargetPath = $exe.FullName
                $sc.WorkingDirectory = $exe.Directory.FullName
                $sc.WindowStyle = 1
                $sc.Description = 'Autopsy'
                $sc.Save()
                Write-Log -Level Success -Message 'Desktop shortcut created for Autopsy.'
            } catch {
                Write-Log -Level Warn -Message "Failed to create shortcut: $($_.Exception.Message)"
            }
        }
    } else {
        Write-Log -Level Warn -Message 'Autopsy executable not found after extraction.'
    }

    Write-Log -Level Success -Message 'Autopsy installation completed.'
}

# Script is dot-sourced by orchestrator; no auto execution.
