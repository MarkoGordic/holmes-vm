<#
.SYNOPSIS
  Install NTCore CFF Explorer (Explorer Suite) and create desktop shortcuts.

.NOTES
  - Tries Chocolatey package 'explorersuite' first for reliability.
  - Falls back to direct download from NTCore if Chocolatey is unavailable.
  - Creates Desktop\CFF Explorer with a shortcut to CFF Explorer.
#>

Set-StrictMode -Version Latest

# Try to import common module for logging/helpers if available
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-CFFExplorer {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\CFFExplorer',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing CFF Explorer (Explorer Suite)...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir = $Destination
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'CFF Explorer' }

    # Ensure directories
    if (Get-Command Ensure-Directory -ErrorAction SilentlyContinue) {
        Ensure-Directory -Path $installDir
        Ensure-Directory -Path $desktopShortcutDir
    } else {
        if (-not (Test-Path -LiteralPath $installDir)) { New-Item -ItemType Directory -Path $installDir -Force | Out-Null }
        if (-not (Test-Path -LiteralPath $desktopShortcutDir)) { New-Item -ItemType Directory -Path $desktopShortcutDir -Force | Out-Null }
    }

    $exePath = $null

    # Prefer Chocolatey installation if available
    $chocoInstalled = $false
    try { $chocoInstalled = [bool](Get-Command choco.exe -ErrorAction SilentlyContinue) } catch { $chocoInstalled = $false }

    if ($chocoInstalled) {
        try {
            if (Get-Command Install-ChocoPackage -ErrorAction SilentlyContinue) {
                Install-ChocoPackage -Name 'explorersuite' | Out-Null
            } else {
                & choco install explorersuite -y --no-progress | Out-Null
            }
        } catch { Write-Log -Level Warn -Message "Chocolatey install failed: $($_.Exception.Message)" }
    }

    # Try to locate CFF Explorer executable
    $searchDirs = @(
        'C:\\Program Files (x86)\\Explorer Suite',
        'C:\\Program Files\\Explorer Suite',
        'C:\\ProgramData\\chocolatey\\lib\\explorersuite',
        $installDir
    )

    foreach ($dir in $searchDirs) {
        if (Test-Path -LiteralPath $dir) {
            $found = Get-ChildItem -Path $dir -Recurse -Filter 'CFF Explorer.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $exePath = $found.FullName; break }
        }
    }

    # If not found, fallback to direct download from NTCore
    if (-not $exePath) {
        Write-Log -Level Info -Message 'Falling back to direct download from NTCore...'
        $primaryUrl = 'https://ntcore.com/files/ExplorerSuite.zip'
        $altUrl1    = 'https://ntcore.com/files/CFF_Explorer.zip'
        $altUrl2    = 'https://ntcore.com/files/ExplorerSuite.exe'
        $tmpZip = Join-Path $env:TEMP 'ExplorerSuite.zip'
        $tmpExe = Join-Path $env:TEMP 'ExplorerSuiteSetup.exe'
        try {
            if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
                Invoke-SafeDownload -Uri $primaryUrl -OutFile $tmpZip
            } else {
                Invoke-WebRequest -Uri $primaryUrl -OutFile $tmpZip -UseBasicParsing
            }
        } catch {
            Write-Log -Level Warn -Message "Zip download failed: $($_.Exception.Message). Trying alternate URLs..."
        }
        if (-not (Test-Path -LiteralPath $tmpZip)) {
            try {
                if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
                    Invoke-SafeDownload -Uri $altUrl1 -OutFile $tmpZip
                } else {
                    Invoke-WebRequest -Uri $altUrl1 -OutFile $tmpZip -UseBasicParsing
                }
            } catch { }
        }

        if (Test-Path -LiteralPath $tmpZip) {
            try {
                if (Get-Command Expand-Zip -ErrorAction SilentlyContinue) {
                    Expand-Zip -ZipPath $tmpZip -Destination $installDir
                } else {
                    Expand-Archive -Path $tmpZip -DestinationPath $installDir -Force
                }
                $found = Get-ChildItem -Path $installDir -Recurse -Filter 'CFF Explorer.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($found) { $exePath = $found.FullName }
            } catch {
                Write-Log -Level Warn -Message "Extraction failed: $($_.Exception.Message)"
            } finally {
                try { Remove-Item -Path $tmpZip -Force -ErrorAction SilentlyContinue } catch { }
            }
        }

        if (-not $exePath) {
            # Try setup EXE silently
            try {
                if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
                    Invoke-SafeDownload -Uri $altUrl2 -OutFile $tmpExe
                } else {
                    Invoke-WebRequest -Uri $altUrl2 -OutFile $tmpExe -UseBasicParsing
                }
                $flags = @('/S','/silent','/VERYSILENT /NORESTART','/quiet')
                foreach ($f in $flags) {
                    try {
                        $p = Start-Process -FilePath $tmpExe -ArgumentList $f -Wait -PassThru -NoNewWindow -ErrorAction Stop
                        if ($p.ExitCode -eq 0 -or $p.ExitCode -eq 3010) { break }
                    } catch { }
                }
            } catch {
                Write-Log -Level Warn -Message "Setup download failed: $($_.Exception.Message)"
            }
            # Search again post-setup
            foreach ($dir in $searchDirs) {
                if (Test-Path -LiteralPath $dir) {
                    $found = Get-ChildItem -Path $dir -Recurse -Filter 'CFF Explorer.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($found) { $exePath = $found.FullName; break }
                }
            }
            try { if (Test-Path -LiteralPath $tmpExe) { Remove-Item -Path $tmpExe -Force -ErrorAction SilentlyContinue } } catch { }
        }
    }

    if ($exePath) {
        Write-Log -Level Success -Message "CFF Explorer located at: $exePath"
        
        # Create desktop shortcut only if not skipped
        if (-not $SkipShortcuts) {
            try {
                $shell = New-Object -ComObject WScript.Shell
                $lnk = Join-Path $desktopShortcutDir 'CFF Explorer.lnk'
                $sc = $shell.CreateShortcut($lnk)
                $sc.TargetPath = $exePath
                $sc.WorkingDirectory = Split-Path -Parent $exePath
                $sc.WindowStyle = 1
                $sc.Description = 'CFF Explorer'
                $sc.Save()
                Write-Log -Level Success -Message "Shortcut created: $lnk"
            } catch {
                Write-Log -Level Warn -Message "Failed to create shortcut: $($_.Exception.Message)"
            }
        }
        
        Write-Log -Level Success -Message 'CFF Explorer installation completed.'
    } else {
        Write-Log -Level Error -Message 'Could not install or locate CFF Explorer.'
    }
}

# Script is dot-sourced by orchestrator.
