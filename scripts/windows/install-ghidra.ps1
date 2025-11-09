<#
.SYNOPSIS
  Install Ghidra from the latest GitHub release and create desktop shortcuts.

.NOTES
  - Downloads latest ghidra_*.zip from GitHub Releases (NationalSecurityAgency/ghidra).
  - Extracts to C:\Tools\Ghidra by default.
  - Adds the ghidra installation directory (bin) to PATH for ghidraRun.bat convenience.
  - Creates a Desktop shortcut (optionally in a category folder) to ghidraRun.bat.
  - Requires Windows and Administrator for PATH changes and shortcut creation.

  Java requirement:
  - Ghidra bundles a runtime in recent releases. If not present, user must install a compatible JDK.
#>

Set-StrictMode -Version Latest

# Try to import common module for logging/helpers if available when run standalone
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-Ghidra {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\Ghidra',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing Ghidra...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir = $Destination
    $zipPath = Join-Path $env:TEMP 'ghidra.zip'
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'Ghidra' }

    Ensure-Directory -Path $installDir
    Ensure-Directory -Path $desktopShortcutDir

    $releaseApi = 'https://api.github.com/repos/NationalSecurityAgency/ghidra/releases/latest'
    Set-Tls12IfNeeded

    # Determine Windows asset zip
    $downloadUrl = $null
    try {
        $resp = Invoke-RestMethod -Uri $releaseApi -UseBasicParsing -ErrorAction Stop -Headers @{ 'User-Agent' = 'Holmes-VM-Installer' }
        # Prefer ghidra_*_PUBLIC_*.zip
        $asset = $resp.assets | Where-Object { $_.name -match '(?i)^ghidra_.*_PUBLIC.*\.zip$' } | Select-Object -First 1
        if (-not $asset) {
            $asset = $resp.assets | Where-Object { $_.name -match '(?i)ghidra.*\.zip$' -and $_.name -notmatch '(?i)(src|source|patch|checksum|sig)$' } | Select-Object -First 1
        }
        if ($asset) {
            $downloadUrl = $asset.browser_download_url
            Write-Log -Level Info -Message "Selected Ghidra asset: $($asset.name)"
        }
    } catch {
        Write-Log -Level Warn -Message "Failed to query Ghidra release API: $($_.Exception.Message)"
    }

    if (-not $downloadUrl) {
        Write-Log -Level Warn -Message 'Could not determine Ghidra download URL from API; trying generic latest download path.'
        $downloadUrl = 'https://github.com/NationalSecurityAgency/ghidra/releases/latest/download/ghidra.zip'
    }

    Write-Log -Level Info -Message "Downloading Ghidra from: $downloadUrl"
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

    # Extract under installDir; Ghidra zip contains a versioned folder, flatten it
    $extractedRoot = Join-Path $installDir 'extracted-temp'
    Ensure-Directory -Path $extractedRoot

    try {
        Expand-Zip -ZipPath $zipPath -Destination $extractedRoot
        Write-Log -Level Success -Message "Extracted Ghidra into $extractedRoot"
    } catch {
        Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
        return
    } finally {
        try { if (Test-Path -LiteralPath $zipPath) { Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue } } catch { }
    }

    # Locate top-level ghidra_* folder and move to installDir root
    $ghidraFolder = Get-ChildItem -Path $extractedRoot -Directory | Where-Object { $_.Name -match '^(?i)ghidra_' } | Select-Object -First 1
    if ($ghidraFolder) {
        $targetDir = Join-Path $installDir $ghidraFolder.Name
        try {
            if (Test-Path -LiteralPath $targetDir) {
                # Remove existing (upgrade scenario)
                Remove-Item -Path $targetDir -Recurse -Force -ErrorAction SilentlyContinue
            }
            Move-Item -Path $ghidraFolder.FullName -Destination $installDir -Force
            Write-Log -Level Success -Message "Ghidra installed to $targetDir"
        } catch {
            Write-Log -Level Warn -Message "Failed to move extracted folder: $($_.Exception.Message)"
        }
        # Clean temp
        try { Remove-Item -Path $extractedRoot -Recurse -Force -ErrorAction SilentlyContinue } catch { }
    } else {
        Write-Log -Level Warn -Message 'Could not find ghidra_* folder in extracted contents.'
    }

    # Try to locate ghidraRun.bat for shortcut
    $bat = Get-ChildItem -Path $installDir -Recurse -Filter 'ghidraRun.bat' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($bat) {
        $binDir = $bat.Directory.FullName
        try { Add-PathIfMissing -Path $binDir -Scope Machine } catch { Write-Log -Level Warn -Message "Failed to add PATH: $($_.Exception.Message)" }
        if (-not $SkipShortcuts) {
            try {
                # Create shortcut pointing to the .bat with working dir at binDir
                $shell = New-Object -ComObject WScript.Shell
                $lnkPath = Join-Path $desktopShortcutDir 'Ghidra.lnk'
                $sc = $shell.CreateShortcut($lnkPath)
                $sc.TargetPath = $bat.FullName
                $sc.WorkingDirectory = $binDir
                $sc.WindowStyle = 1
                $sc.Description = 'Ghidra'
                $sc.Save()
                Write-Log -Level Success -Message 'Desktop shortcut created for Ghidra.'
            } catch {
                Write-Log -Level Warn -Message "Failed to create shortcut: $($_.Exception.Message)"
            }
        }
    } else {
        Write-Log -Level Warn -Message 'ghidraRun.bat not found; skipping shortcut creation.'
    }

    Write-Log -Level Success -Message 'Ghidra installation completed.'
}

# Note: This script is dot-sourced by the orchestrator and not intended to auto-run.
