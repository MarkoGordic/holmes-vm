<#
.SYNOPSIS
  Install Brimdata Zui (GUI for Zeek/Suricata logs) on Windows.

.NOTES
  - Uses GitHub Releases to fetch the latest Windows installer (MSI or EXE).
  - Attempts silent installation with sensible defaults.
  - Requires Windows and Administrator.
#>

Set-StrictMode -Version Latest

# Try to import common module for logging/helpers if available
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

function Install-Zui {
    [CmdletBinding(SupportsShouldProcess)]
    param()

    Write-Log -Level Info -Message 'Installing Brimdata Zui...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $releaseApi = 'https://api.github.com/repos/brimdata/zui/releases/latest'
    $tempDir = $env:TEMP
    $installerPath = Join-Path $tempDir 'zui-installer.tmp'

    # Discover latest Windows asset
    $downloadUrl = $null
    try {
        if (Get-Command Set-Tls12IfNeeded -ErrorAction SilentlyContinue) { Set-Tls12IfNeeded }
        $resp = Invoke-RestMethod -Uri $releaseApi -UseBasicParsing -ErrorAction Stop
        $asset = $resp.assets | Where-Object { ($_.name -match 'windows' -or $_.name -match 'Setup') -and ($_.name -match '\.msi$' -or $_.name -match '\.exe$') } | Select-Object -First 1
        if (-not $asset) {
            # Fallback: try any MSI/EXE if "windows" not present in name
            $asset = $resp.assets | Where-Object { $_.name -match '\.(msi|exe)$' } | Select-Object -First 1
        }
        if ($asset) { $downloadUrl = $asset.browser_download_url }
    } catch {
        Write-Log -Level Warn -Message "Failed to query Zui release API: $($_.Exception.Message)"
    }

    if (-not $downloadUrl) {
        Write-Log -Level Error -Message 'Could not determine Zui Windows installer download URL.'
        return
    }

    # Choose file extension based on URL
    if ($downloadUrl -match '\.msi$') {
        $installerPath = [IO.Path]::ChangeExtension($installerPath, '.msi')
    } elseif ($downloadUrl -match '\.exe$') {
        $installerPath = [IO.Path]::ChangeExtension($installerPath, '.exe')
    } else {
        $installerPath = [IO.Path]::ChangeExtension($installerPath, '.bin')
    }

    Write-Log -Level Info -Message "Downloading: $downloadUrl"
    if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
        Invoke-SafeDownload -Uri $downloadUrl -OutFile $installerPath | Out-Null
    } else {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    }

    if (-not (Test-Path -LiteralPath $installerPath)) {
        Write-Log -Level Error -Message 'Download failed; installer not found.'
        return
    }

    # Run installer silently
    if ($installerPath -like '*.msi') {
        $args = "/i `"$installerPath`" /qn /norestart"
        if ($PSCmdlet.ShouldProcess($installerPath, 'Install Zui (MSI)')) {
            $p = Start-Process -FilePath 'msiexec.exe' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
            if ($p.ExitCode -eq 0) { Write-Log -Level Success -Message 'Zui installed (MSI).' } else { Write-Log -Level Warn -Message "MSI exit code: $($p.ExitCode)" }
        }
    } else {
        # Try common silent flags for EXE installers
        $exeFlags = @('/S', '/silent', '/verysilent', '--silent', '--quiet')
        $installed = $false
        foreach ($flag in $exeFlags) {
            if ($PSCmdlet.ShouldProcess($installerPath, "Install Zui (EXE $flag)")) {
                try {
                    $p = Start-Process -FilePath $installerPath -ArgumentList $flag -Wait -PassThru -WindowStyle Hidden -ErrorAction Stop
                    if ($p.ExitCode -eq 0) { $installed = $true; break }
                    else { Write-Log -Level Warn -Message "Installer exited with code $($p.ExitCode) using flag $flag" }
                } catch {
                    Write-Log -Level Warn -Message "Failed with flag ${flag}: $($_.Exception.Message)"
                }
            }
        }
        if ($installed) { Write-Log -Level Success -Message 'Zui installed.' } else { Write-Log -Level Warn -Message 'Zui installer did not report success; verify manually.' }
    }

    # Best-effort: add Start Menu/Desktop shortcuts are typically created by the installer.
    # Locate Zui.exe to emit a helpful message
    try {
        $candidates = @(
            (Join-Path $env:LOCALAPPDATA 'Programs\Zui\Zui.exe'),
            (Join-Path $env:LOCALAPPDATA 'Programs\zui\Zui.exe'),
            'C:\\Program Files\\Zui\\Zui.exe',
            'C:\\Program Files (x86)\\Zui\\Zui.exe'
        )
        $found = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if ($found) {
            Write-Log -Level Success -Message "Zui executable found at: $found"
        } else {
            Write-Log -Level Warn -Message 'Zui.exe not found in common locations yet. It may appear after first launch or under a user-specific path.'
        }
    } catch { }

    try { if (Test-Path -LiteralPath $installerPath) { Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue } } catch { }
}

# Note: Do not call Export-ModuleMember in a .ps1 script; this file is dot-sourced by the orchestrator.
