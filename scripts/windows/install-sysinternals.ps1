<#
.SYNOPSIS
  Install Microsoft Sysinternals Suite and create desktop shortcuts.

.NOTES
  - Downloads the official SysinternalsSuite.zip from Microsoft.
  - Extracts to C:\Tools\SysinternalsSuite by default.
  - Adds the install directory to the system PATH.
  - Creates a Desktop\Sysinternals folder with shortcuts to all EXE tools.
  - Requires Windows and Administrator privileges for PATH Machine scope and shortcut creation.
#>

Set-StrictMode -Version Latest

# Try to import common module for logging/helpers if available
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-Sysinternals {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\SysinternalsSuite',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing Microsoft Sysinternals Suite...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir = $Destination
    $zipPath = Join-Path $env:TEMP 'SysinternalsSuite.zip'
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'Sysinternals' }

    # Prepare
    if (Get-Command Ensure-Directory -ErrorAction SilentlyContinue) {
        Ensure-Directory -Path $installDir
        Ensure-Directory -Path $desktopShortcutDir
    } else {
        if (-not (Test-Path -LiteralPath $installDir)) { New-Item -ItemType Directory -Path $installDir -Force | Out-Null }
        if (-not (Test-Path -LiteralPath $desktopShortcutDir)) { New-Item -ItemType Directory -Path $desktopShortcutDir -Force | Out-Null }
    }

    # Download official suite
    $primaryUrl = 'https://download.sysinternals.com/files/SysinternalsSuite.zip'
    $fallbackUrl = 'https://live.sysinternals.com/files/SysinternalsSuite.zip'

    try {
        if (Get-Command Set-Tls12IfNeeded -ErrorAction SilentlyContinue) { Set-Tls12IfNeeded }
        if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
            Invoke-SafeDownload -Uri $primaryUrl -OutFile $zipPath -ErrorAction Stop
        } else {
            Invoke-WebRequest -Uri $primaryUrl -OutFile $zipPath -UseBasicParsing -ErrorAction Stop
        }
        Write-Log -Level Success -Message 'Downloaded Sysinternals Suite (primary).'
    } catch {
        Write-Log -Level Warn -Message "Primary download failed: $($_.Exception.Message). Trying fallback..."
        if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
            Invoke-SafeDownload -Uri $fallbackUrl -OutFile $zipPath
        } else {
            Invoke-WebRequest -Uri $fallbackUrl -OutFile $zipPath -UseBasicParsing
        }
    }

    if (-not (Test-Path -LiteralPath $zipPath)) {
        Write-Log -Level Error -Message 'Download failed; SysinternalsSuite.zip not found.'
        return
    }

    # Extract
    try {
        if (Get-Command Expand-Zip -ErrorAction SilentlyContinue) {
            Expand-Zip -ZipPath $zipPath -Destination $installDir
        } else {
            Expand-Archive -Path $zipPath -DestinationPath $installDir -Force
        }
        Write-Log -Level Success -Message "Extracted to $installDir"
    } catch {
        Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
        return
    } finally {
        try { if (Test-Path -LiteralPath $zipPath) { Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue } } catch { }
    }

    # Add to PATH (Machine)
    try {
        if (Get-Command Add-PathIfMissing -ErrorAction SilentlyContinue) {
            Add-PathIfMissing -Path $installDir -Scope Machine
        } else {
            $env:Path = "$env:Path;$installDir"
        }
        Write-Log -Level Success -Message 'Added Sysinternals directory to PATH.'
    } catch {
        Write-Log -Level Warn -Message "Failed to add PATH: $($_.Exception.Message)"
    }

    # Create shortcuts for all EXE tools only if not skipped
    if (-not $SkipShortcuts) {
        try {
            if (Get-Command New-ShortcutsFromFolder -ErrorAction SilentlyContinue) {
                New-ShortcutsFromFolder -Folder $installDir -Filter '*.exe' -ShortcutDir $desktopShortcutDir -WorkingDir $installDir
            } else {
                $shell = New-Object -ComObject WScript.Shell
                Get-ChildItem -Path $installDir -Filter '*.exe' -File | ForEach-Object {
                    $lnk = Join-Path $desktopShortcutDir ("$($_.Name).lnk")
                    $sc = $shell.CreateShortcut($lnk)
                    $sc.TargetPath = $_.FullName
                    $sc.WorkingDirectory = $_.Directory.FullName
                    $sc.WindowStyle = 1
                    $sc.Description = $_.BaseName
                    $sc.Save()
                }
            }
            Write-Log -Level Success -Message "Desktop shortcuts created under $desktopShortcutDir."
        } catch {
            Write-Log -Level Warn -Message "Failed to create some shortcuts: $($_.Exception.Message)"
        }
    }

    Write-Log -Level Success -Message 'Sysinternals Suite installation completed.'
}

# Note: This script is dot-sourced by the orchestrator via tools.json and is not intended to auto-run.
