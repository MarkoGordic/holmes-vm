<#
.SYNOPSIS
  Install ApateDNS and create desktop shortcuts.

.NOTES
  - Attempts to download official ZIP from FireEye/Mandiant.
  - Extracts to C:\Tools\ApateDNS and adds that directory to PATH.
  - Creates Desktop\ApateDNS with a shortcut to ApateDNS.exe.
#>

Set-StrictMode -Version Latest

# Ensure TLS 1.2 for downloads if helper is available
try { if (-not (Get-Command Set-Tls12IfNeeded -ErrorAction SilentlyContinue)) { } else { Set-Tls12IfNeeded } } catch { }

# Try to import common module for logging/helpers if available
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-ApateDNS {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\ApateDNS',
        [string]$ShortcutCategory,
        [switch]$SkipShortcuts
    )

    Write-Log -Level Info -Message 'Installing ApateDNS...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $installDir = $Destination
    $zipPath = Join-Path $env:TEMP 'ApateDNS.zip'
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'ApateDNS' }

    # Ensure directories
    if (Get-Command Ensure-Directory -ErrorAction SilentlyContinue) {
        Ensure-Directory -Path $installDir
        Ensure-Directory -Path $desktopShortcutDir
    } else {
        if (-not (Test-Path -LiteralPath $installDir)) { New-Item -ItemType Directory -Path $installDir -Force | Out-Null }
        if (-not (Test-Path -LiteralPath $desktopShortcutDir)) { New-Item -ItemType Directory -Path $desktopShortcutDir -Force | Out-Null }
    }

    # Candidate download URLs (official first)
    $urls = @(
        'https://www.fireeye.com/content/dam/fireeye-www/global/en/tools/ApateDNS.zip',
        'https://www.fireeye.com/content/dam/fireeye-www/global/en/tools/apatedns.zip',
        'https://download.mandiant.com/flare/ApateDNS.zip'
    )

    $downloaded = $false
    foreach ($u in $urls) {
        try {
            if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
                Invoke-SafeDownload -Uri $u -OutFile $zipPath -ErrorAction Stop | Out-Null
            } else {
                $headers = @{ 'User-Agent' = 'HolmesVM/1.0 (+https://github.com/MarkoGordic/holmes-vm)'; 'Accept' = '*/*' }
                Invoke-WebRequest -Uri $u -OutFile $zipPath -UseBasicParsing -Headers $headers -ErrorAction Stop
            }
            if (Test-Path -LiteralPath $zipPath) { $downloaded = $true; Write-Log -Level Success -Message "Downloaded: $u"; break }
        } catch { Write-Log -Level Warn -Message "Failed to download from $($u): $($_.Exception.Message)" }
    }

    if (-not $downloaded) {
        Write-Log -Level Error -Message 'Could not download ApateDNS from known sources.'
        return
    }

    # Extract
    try {
        if (Get-Command Expand-Zip -ErrorAction SilentlyContinue) {
            Expand-Zip -ZipPath $zipPath -Destination $installDir
        } else {
            Expand-Archive -Path $zipPath -DestinationPath $installDir -Force
        }
        # Unblock files to avoid SmartScreen blocking
        try { Get-ChildItem -Path $installDir -Recurse -File | Unblock-File -ErrorAction SilentlyContinue } catch { }
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
    } catch { }

    # Create desktop shortcut(s) only if not skipped
    $exe = Get-ChildItem -Path $installDir -Recurse -Filter 'ApateDNS.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) {
        if (-not $SkipShortcuts) {
            try {
                $shell = New-Object -ComObject WScript.Shell
                $lnk = Join-Path $desktopShortcutDir 'ApateDNS.lnk'
                $sc = $shell.CreateShortcut($lnk)
                $sc.TargetPath = $exe.FullName
                $sc.WorkingDirectory = $exe.Directory.FullName
                $sc.WindowStyle = 1
                $sc.Description = 'ApateDNS'
                $sc.Save()
                Write-Log -Level Success -Message 'Desktop shortcut created.'
            } catch {
                Write-Log -Level Warn -Message "Failed to create shortcut: $($_.Exception.Message)"
            }
        }
        Write-Log -Level Success -Message 'ApateDNS installation completed.'
    } else {
        Write-Log -Level Warn -Message 'ApateDNS.exe not found after extraction.'
    }
}

# Script is dot-sourced by orchestrator.
