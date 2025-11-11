<#
.SYNOPSIS
  Install ShadowExplorer (portable preferred) and create a desktop shortcut.

.NOTES
  - Prefers the official portable ZIP to avoid installer UI and EULA prompts.
  - Falls back to the setup EXE with common silent flags if ZIP is unavailable.
  - Extracts to C:\Tools\ShadowExplorer by default.
  - Creates a Desktop shortcut (optionally inside a category folder).
  - Requires Windows and Administrator for PATH/shortcut operations.
#>

Set-StrictMode -Version Latest

# Try to import common module for logging/helpers if available
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-ShadowExplorer {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\ShadowExplorer',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing ShadowExplorer...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir = $Destination
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'Forensics' }

    Ensure-Directory -Path $installDir
    Ensure-Directory -Path $desktopShortcutDir

    # Prefer portable zip to avoid installer UI
    $portableUrl = 'https://www.shadowexplorer.com/uploads/ShadowExplorer-0.9-portable.zip'
    $setupUrl    = 'https://www.shadowexplorer.com/uploads/ShadowExplorer-0.9-setup.exe'
    $tempBase = Join-Path $env:TEMP ('shadowexplorer_' + [Guid]::NewGuid().ToString('N'))
    $zipPath = "$tempBase.zip"
    $exePath = "$tempBase.exe"

    $downloaded = $false
    $mode = 'zip'

    try {
        if (Get-Command Test-UrlReachable -ErrorAction SilentlyContinue) {
            if (Test-UrlReachable -Url $portableUrl -TimeoutSec 6) {
                Write-Log -Level Info -Message "Downloading portable archive: $portableUrl"
                Invoke-SafeDownload -Uri $portableUrl -OutFile $zipPath | Out-Null
                $downloaded = Test-Path -LiteralPath $zipPath
                $mode = 'zip'
            }
        }
    } catch { }

    if (-not $downloaded) {
        Write-Log -Level Warn -Message 'Portable ZIP not reachable; trying setup EXE.'
        try {
            Invoke-SafeDownload -Uri $setupUrl -OutFile $exePath | Out-Null
            $downloaded = Test-Path -LiteralPath $exePath
            $mode = 'exe'
        } catch {
            Write-Log -Level Error -Message "Failed to download ShadowExplorer: $($_.Exception.Message)"
            return
        }
    }

    if (-not $downloaded) {
        Write-Log -Level Error -Message 'Could not download ShadowExplorer from known URLs.'
        return
    }

    if ($mode -eq 'zip') {
        try {
            Expand-Zip -ZipPath $zipPath -Destination $installDir
            Write-Log -Level Success -Message "Extracted ShadowExplorer to $installDir"
        } catch {
            Write-Log -Level Error -Message "Extraction failed: $($_.Exception.Message)"
            return
        } finally {
            try { if (Test-Path -LiteralPath $zipPath) { Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue } } catch { }
        }
    } else {
        # Attempt silent install for EXE
        $installed = $false
        $flags = @(
            @('/VERYSILENT /NORESTART', 'Inno Setup style'),
            @('/S', 'NSIS style'),
            @('/quiet', 'MSI style'),
            @('/silent', 'Generic silent')
        )
        foreach ($pair in $flags) {
            $f = $pair[0]; $desc = $pair[1]
            Write-Log -Level Info -Message "Running setup with: $f ($desc)"
            try {
                if ($PSCmdlet.ShouldProcess($exePath, "Install ShadowExplorer ($f)")) {
                    $p = Start-Process -FilePath $exePath -ArgumentList $f -Wait -PassThru -NoNewWindow -ErrorAction Stop
                    if ($p.ExitCode -eq 0 -or $p.ExitCode -eq 3010) { $installed = $true; break }
                }
            } catch {
                Write-Log -Level Warn -Message "Silent flag failed: $($_.Exception.Message)"
            }
        }
        try { if (Test-Path -LiteralPath $exePath) { Remove-Item -Path $exePath -Force -ErrorAction SilentlyContinue } } catch { }

        if (-not $installed) {
            Write-Log -Level Warn -Message 'Setup did not report success with known silent flags.'
            Write-Log -Level Info -Message 'You may need to install manually.'
        }
    }

    # Locate ShadowExplorer.exe (portable or installed)
    $exe = $null
    try {
        $candidates = @(
            (Join-Path $installDir 'ShadowExplorer.exe'),
            (Get-ChildItem -Path $installDir -Recurse -Filter 'ShadowExplorer.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 | ForEach-Object { $_.FullName }),
            'C:\\Program Files\\ShadowExplorer\\ShadowExplorer.exe',
            'C:\\Program Files (x86)\\ShadowExplorer\\ShadowExplorer.exe'
        ) | Where-Object { $_ }
        foreach ($c in $candidates) { if ($c -and (Test-Path -LiteralPath $c)) { $exe = $c; break } }
    } catch { }

    if (-not $exe) {
        Write-Log -Level Warn -Message 'ShadowExplorer.exe not found; skipping shortcut creation.'
        return
    }

    # Optional: add to PATH for convenience (portable)
    try { Add-PathIfMissing -Path (Split-Path -Parent $exe) -Scope Machine } catch { }

    if (-not $SkipShortcuts) {
        try {
            New-ShortcutsFromFolder -Folder (Split-Path -Parent $exe) -Filter 'ShadowExplorer.exe' -ShortcutDir $desktopShortcutDir -WorkingDir (Split-Path -Parent $exe)
            Write-Log -Level Success -Message 'Desktop shortcut created.'
        } catch {
            Write-Log -Level Warn -Message "Failed to create desktop shortcut: $($_.Exception.Message)"
        }
    }

    Write-Log -Level Success -Message 'ShadowExplorer installation step completed.'
}

# Note: This script is dot-sourced by the orchestrator and not intended to auto-run.
