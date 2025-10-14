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
    $assetName = $null
    try {
        if (Get-Command Set-Tls12IfNeeded -ErrorAction SilentlyContinue) { Set-Tls12IfNeeded }
        Write-Log -Level Info -Message "Querying Zui releases from GitHub API..."
        $resp = Invoke-RestMethod -Uri $releaseApi -UseBasicParsing -ErrorAction Stop -Headers @{ 'User-Agent' = 'Holmes-VM-Installer' }
        Write-Log -Level Info -Message "Found release: $($resp.tag_name) - $($resp.name)"
        
        # Look for Windows installer - prefer setup.exe, then .msi, then .exe
        $asset = $resp.assets | Where-Object { 
            $_.name -match '(?i)windows.*setup.*\.exe$' -or 
            $_.name -match '(?i)setup.*windows.*\.exe$' -or
            $_.name -match '(?i)setup.*\.exe$'
        } | Select-Object -First 1
        
        if (-not $asset) {
            Write-Log -Level Info -Message "No setup.exe found, looking for MSI..."
            $asset = $resp.assets | Where-Object { $_.name -match '(?i)\.msi$' } | Select-Object -First 1
        }
        
        if (-not $asset) {
            Write-Log -Level Info -Message "No MSI found, looking for any Windows executable..."
            $asset = $resp.assets | Where-Object { 
                ($_.name -match '(?i)windows' -or $_.name -match '(?i)win') -and 
                ($_.name -match '\.exe$' -or $_.name -match '\.msi$')
            } | Select-Object -First 1
        }
        
        if (-not $asset) {
            # Fallback: try any installer-looking file
            Write-Log -Level Info -Message "Looking for any installer file..."
            $asset = $resp.assets | Where-Object { 
                $_.name -match '\.(msi|exe)$' -and 
                $_.name -notmatch '(?i)(mac|linux|dmg|appimage|deb|rpm)' 
            } | Select-Object -First 1
        }
        
        if ($asset) { 
            $downloadUrl = $asset.browser_download_url 
            $assetName = $asset.name
            Write-Log -Level Success -Message "Found installer: $assetName"
        } else {
            Write-Log -Level Warn -Message "Available assets:"
            $resp.assets | ForEach-Object { Write-Log -Level Info -Message "  - $($_.name)" }
        }
    } catch {
        Write-Log -Level Warn -Message "Failed to query Zui release API: $($_.Exception.Message)"
    }

    if (-not $downloadUrl) {
        Write-Log -Level Error -Message 'Could not determine Zui Windows installer download URL.'
        Write-Log -Level Info -Message 'Please visit https://github.com/brimdata/zui/releases to download manually.'
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

    Write-Log -Level Info -Message "Downloading from: $downloadUrl"
    Write-Log -Level Info -Message "Saving to: $installerPath"
    
    try {
        if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
            Invoke-SafeDownload -Uri $downloadUrl -OutFile $installerPath | Out-Null
        } else {
            Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing -Headers @{ 'User-Agent' = 'Holmes-VM-Installer' }
        }
    } catch {
        Write-Log -Level Error -Message "Download failed: $($_.Exception.Message)"
        return
    }

    if (-not (Test-Path -LiteralPath $installerPath)) {
        Write-Log -Level Error -Message 'Download failed; installer not found.'
        return
    }
    
    $fileSize = (Get-Item $installerPath).Length
    Write-Log -Level Success -Message "Downloaded successfully ($([math]::Round($fileSize/1MB, 2)) MB)"

    # Run installer silently
    $installed = $false
    if ($installerPath -like '*.msi') {
        $args = "/i `"$installerPath`" /qn /norestart /L*v `"$env:TEMP\zui-install.log`""
        Write-Log -Level Info -Message "Running MSI installer with arguments: $args"
        if ($PSCmdlet.ShouldProcess($installerPath, 'Install Zui (MSI)')) {
            try {
                $p = Start-Process -FilePath 'msiexec.exe' -ArgumentList $args -Wait -PassThru -NoNewWindow
                Write-Log -Level Info -Message "MSI installer exited with code: $($p.ExitCode)"
                if ($p.ExitCode -eq 0 -or $p.ExitCode -eq 3010) { 
                    $installed = $true
                    Write-Log -Level Success -Message 'Zui installed (MSI).' 
                    if ($p.ExitCode -eq 3010) {
                        Write-Log -Level Warn -Message "Reboot required (exit code 3010)"
                    }
                } else { 
                    Write-Log -Level Warn -Message "MSI exit code: $($p.ExitCode)"
                    Write-Log -Level Info -Message "Check log file at: $env:TEMP\zui-install.log"
                }
            } catch {
                Write-Log -Level Error -Message "MSI installation failed: $($_.Exception.Message)"
            }
        }
    } else {
        # Try common silent flags for EXE installers
        $exeFlags = @(
            @('/S', 'NSIS-style silent'),
            @('/VERYSILENT /NORESTART', 'Inno Setup style'),
            @('/silent', 'Generic silent'),
            @('--silent', 'Unix-style silent'),
            @('/quiet', 'MSI-style quiet'),
            @('/q', 'Short quiet')
        )
        
        foreach ($flagInfo in $exeFlags) {
            $flag = $flagInfo[0]
            $desc = $flagInfo[1]
            
            Write-Log -Level Info -Message "Trying installation with flag: $flag ($desc)"
            
            if ($PSCmdlet.ShouldProcess($installerPath, "Install Zui (EXE $flag)")) {
                try {
                    $p = Start-Process -FilePath $installerPath -ArgumentList $flag -Wait -PassThru -NoNewWindow -ErrorAction Stop
                    Write-Log -Level Info -Message "Installer exited with code: $($p.ExitCode)"
                    
                    if ($p.ExitCode -eq 0) { 
                        $installed = $true
                        Write-Log -Level Success -Message "Zui installed successfully using flag: $flag"
                        break 
                    } elseif ($p.ExitCode -eq 3010) {
                        $installed = $true
                        Write-Log -Level Success -Message "Zui installed successfully (reboot required)"
                        break
                    } else { 
                        Write-Log -Level Warn -Message "Installer exited with code $($p.ExitCode) using flag $flag" 
                    }
                } catch {
                    Write-Log -Level Warn -Message "Failed with flag ${flag}: $($_.Exception.Message)"
                }
            }
        }
        
        if ($installed) { 
            Write-Log -Level Success -Message 'Zui installed.' 
        } else { 
            Write-Log -Level Warn -Message 'Zui installer did not report success with any known silent flags.'
            Write-Log -Level Info -Message 'You may need to run the installer manually from:'
            Write-Log -Level Info -Message "  $installerPath"
        }
    }

    # Verify installation and locate Zui.exe
    if ($installed) {
        Start-Sleep -Seconds 2
        try {
            $candidates = @(
                (Join-Path $env:LOCALAPPDATA 'Programs\Zui\Zui.exe'),
                (Join-Path $env:LOCALAPPDATA 'Programs\zui\Zui.exe'),
                (Join-Path $env:LOCALAPPDATA 'Zui\Zui.exe'),
                'C:\\Program Files\\Zui\\Zui.exe',
                'C:\\Program Files (x86)\\Zui\\Zui.exe',
                'C:\\Program Files\\Brimdata\\Zui\\Zui.exe',
                'C:\\Program Files (x86)\\Brimdata\\Zui\\Zui.exe'
            )
            
            $found = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
            
            if ($found) {
                Write-Log -Level Success -Message "Zui executable found at: $found"
                Write-Log -Level Info -Message "You can launch Zui from the Start Menu or directly from: $found"
            } else {
                Write-Log -Level Warn -Message 'Zui.exe not found in common locations.'
                Write-Log -Level Info -Message 'Searching file system...'
                
                # Try to find it in common installation directories
                $searchPaths = @(
                    $env:LOCALAPPDATA,
                    'C:\\Program Files',
                    'C:\\Program Files (x86)'
                )
                
                foreach ($searchPath in $searchPaths) {
                    if (Test-Path $searchPath) {
                        $found = Get-ChildItem -Path $searchPath -Recurse -Filter 'Zui.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
                        if ($found) {
                            Write-Log -Level Success -Message "Found Zui at: $($found.FullName)"
                            break
                        }
                    }
                }
                
                if (-not $found) {
                    Write-Log -Level Info -Message 'Zui may appear in Start Menu after first launch or system restart.'
                }
            }
        } catch {
            Write-Log -Level Warn -Message "Could not verify Zui installation: $($_.Exception.Message)"
        }
    }

    # Cleanup installer file
    try { 
        if (Test-Path -LiteralPath $installerPath) { 
            Remove-Item -Path $installerPath -Force -ErrorAction SilentlyContinue 
            Write-Log -Level Info -Message "Cleaned up installer file"
        } 
    } catch { }
}

# Note: Do not call Export-ModuleMember in a .ps1 script; this file is dot-sourced by the orchestrator.
