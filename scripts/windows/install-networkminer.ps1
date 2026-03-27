<#
.SYNOPSIS
  Install NetworkMiner (network forensics tool) from netresec.com and create desktop shortcuts.

.NOTES
  - Downloads directly from netresec.com (redirect URL → latest versioned ZIP).
  - Falls back to Chocolatey if direct download fails.
  - Extracts to C:\Tools\NetworkMiner and unblocks all files.
  - Creates a desktop shortcut (optionally in a category subfolder).
#>

Set-StrictMode -Version Latest

# Try to import common module for logging/helpers if available when run standalone
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-NetworkMiner {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\Tools\NetworkMiner',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing NetworkMiner...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir    = $Destination
    $zipPath       = Join-Path $env:TEMP 'NetworkMiner-latest.zip'
    $desktopRoot   = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) {
        Join-Path $desktopRoot $ShortcutCategory
    } else {
        Join-Path $desktopRoot 'NetworkMiner'
    }

    Ensure-Directory -Path $installDir
    Ensure-Directory -Path $desktopShortcutDir

    # Already-installed check
    $existingExe = Get-ChildItem -Path $installDir -Recurse -Filter 'NetworkMiner.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($existingExe) {
        Write-Log -Level Success -Message 'NetworkMiner already installed; skipping download.'
        return
    }

    Set-Tls12IfNeeded

    # --- Primary: direct download from netresec.com ---
    # The redirect URL always points to the latest release ZIP.
    $downloadUrl = 'https://www.netresec.com/?download=NetworkMiner'

    # Try to resolve a versioned link from the download page (more reliable for redirects)
    try {
        $headers = @{ 'User-Agent' = 'HolmesVM/1.0 (+https://github.com/MarkoGordic/holmes-vm)' }
        $resp = Invoke-WebRequest -Uri 'https://www.netresec.com/?page=NetworkMiner' -UseBasicParsing -Headers $headers -TimeoutSec 30 -ErrorAction Stop
        $link = ($resp.Links | Where-Object { $_.href -match 'NetworkMiner_\d[\d.]+\.zip$' } | Select-Object -First 1).href
        if ($link -match '^https?://') {
            $downloadUrl = $link
            Write-Log -Level Info -Message "Resolved versioned URL: $downloadUrl"
        }
    } catch {
        Write-Log -Level Info -Message "Could not scrape versioned URL; using redirect URL."
    }

    $downloaded = $false
    Write-Log -Level Info -Message "Downloading NetworkMiner from: $downloadUrl"
    try {
        Invoke-SafeDownload -Uri $downloadUrl -OutFile $zipPath -ErrorAction Stop | Out-Null
        if (Test-Path -LiteralPath $zipPath) { $downloaded = $true }
    } catch {
        Write-Log -Level Warn -Message "Direct download failed: $($_.Exception.Message)"
    }

    # --- Fallback: Chocolatey ---
    if (-not $downloaded) {
        Write-Log -Level Info -Message 'Trying Chocolatey fallback...'
        try {
            choco install networkminer -y --no-progress 2>&1 | ForEach-Object { Write-Log -Level Info -Message $_ }
            # Chocolatey installs to C:\tools\NetworkMiner or ProgramData\chocolatey\lib\networkminer
            foreach ($candidate in @('C:\tools\NetworkMiner', 'C:\ProgramData\chocolatey\lib\networkminer\tools')) {
                if (Test-Path $candidate) {
                    $chocoExe = Get-ChildItem $candidate -Recurse -Filter 'NetworkMiner.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($chocoExe) {
                        Write-Log -Level Success -Message "NetworkMiner installed via Chocolatey at $($chocoExe.FullName)"
                        $installDir = $chocoExe.Directory.FullName
                    }
                }
            }
        } catch {
            Write-Log -Level Error -Message "Chocolatey install failed: $($_.Exception.Message)"
        }

        # Verify something installed
        $finalExe = Get-ChildItem -Path $installDir -Recurse -Filter 'NetworkMiner.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $finalExe) {
            Write-Log -Level Error -Message 'NetworkMiner could not be installed (both direct download and Chocolatey failed).'
            return
        }
    } else {
        # Extract the downloaded ZIP
        try {
            Expand-Zip -ZipPath $zipPath -Destination $installDir
            Write-Log -Level Success -Message "Extracted to $installDir"
        } catch {
            Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
            return
        } finally {
            try { if (Test-Path -LiteralPath $zipPath) { Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue } } catch { }
        }

        # Unblock all extracted files (SmartScreen / zone identifier)
        try { Get-ChildItem -Path $installDir -Recurse -File | Unblock-File -ErrorAction SilentlyContinue } catch { }
    }

    # Add to PATH
    try { Add-PathIfMissing -Path $installDir -Scope Machine } catch { }

    # Locate executable (may be in a versioned subfolder, e.g. NetworkMiner_2-9\NetworkMiner.exe)
    $exe = Get-ChildItem -Path $installDir -Recurse -Filter 'NetworkMiner.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $exe) {
        Write-Log -Level Warn -Message 'NetworkMiner.exe not found after installation.'
        return
    }

    # Create desktop shortcut
    if (-not $SkipShortcuts) {
        try {
            $wsh = New-Object -ComObject WScript.Shell
            $lnkPath = Join-Path $desktopShortcutDir 'NetworkMiner.lnk'
            $sc = $wsh.CreateShortcut($lnkPath)
            $sc.TargetPath      = $exe.FullName
            $sc.WorkingDirectory = $exe.Directory.FullName
            $sc.WindowStyle     = 1
            $sc.Description     = 'NetworkMiner – Network Forensics Analyser'
            $sc.Save()
            Write-Log -Level Success -Message "Desktop shortcut created: $lnkPath"
        } catch {
            Write-Log -Level Warn -Message "Failed to create shortcut: $($_.Exception.Message)"
        }
    }

    Write-Log -Level Success -Message 'NetworkMiner installation completed.'
}

# Note: This script is dot-sourced by the orchestrator and not intended to auto-run.
