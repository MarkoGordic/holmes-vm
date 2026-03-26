<#
.SYNOPSIS
  Disable Windows Defender on a forensics VM.

.DESCRIPTION
  Disables real-time protection, cloud-delivered protection, automatic sample
  submission, behavior monitoring, scheduled scans, and Defender notifications.
  Adds a scan exclusion for C:\Tools so forensics utilities are not quarantined.

  WARNING: This script is intended for DIGITAL FORENSICS VMs ONLY.
  Do NOT run this on production systems, personal workstations, or any machine
  exposed to untrusted networks without compensating controls. Disabling
  Defender on a forensics VM prevents it from interfering with malware samples,
  evidence files, and analysis tooling.

  All changes are registry-based and non-destructive -- no Defender files are
  deleted. Some settings may fail silently when Tamper Protection is active or
  when Group Policy overrides are in effect.
#>

Set-StrictMode -Version Latest

try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path $PSScriptRoot 'Holmes.Common.psm1'
        if (-not (Test-Path -LiteralPath $commonPath)) {
            $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'windows/Holmes.Common.psm1'
        }
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -Force -DisableNameChecking }
    }
} catch { }

function Set-DefenderRegistryValue {
    <#
    .SYNOPSIS
      Helper to set a Defender-related registry DWORD, swallowing errors that
      occur when Tamper Protection or Group Policy blocks the write.
    #>
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][int]$Value,
        [string]$Description
    )

    try {
        New-Item -Path $Path -Force -ErrorAction SilentlyContinue | Out-Null
        if ($PSCmdlet.ShouldProcess("$Path\$Name", "Set DWORD=$Value ($Description)")) {
            New-ItemProperty -Path $Path -Name $Name -Value $Value -PropertyType DWord -Force -ErrorAction Stop | Out-Null
        }
        return $true
    } catch {
        Write-Log -Level Warn -Message "Could not set $Name ($Description): $($_.Exception.Message)"
        return $false
    }
}

function Disable-WindowsDefender {
    <#
    .SYNOPSIS
      Disables Windows Defender components for forensics VM use.

    .DESCRIPTION
      Applies registry-based configuration to disable Defender real-time
      scanning, cloud protection, sample submission, behavior monitoring,
      scheduled scans, and tray notifications. Also adds C:\Tools as a scan
      exclusion path. Requires elevation (Run as Administrator).

      This is for FORENSICS VMs ONLY -- not for production systems.
    #>
    [CmdletBinding(SupportsShouldProcess)]
    param()

    Write-Log -Level Info -Message 'Disabling Windows Defender for forensics VM setup...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $defenderPolicy = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender'
    $realtimePolicy = "$defenderPolicy\Real-Time Protection"
    $spynetPolicy   = "$defenderPolicy\Spynet"
    $reportingPolicy = "$defenderPolicy\Reporting"
    $scanPolicy     = "$defenderPolicy\Scan"

    # ---------------------------------------------------------------
    # 1. Disable real-time protection
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Disabling real-time protection...'
    Set-DefenderRegistryValue -Path $realtimePolicy -Name 'DisableRealtimeMonitoring' -Value 1 `
        -Description 'Real-time monitoring'
    Set-DefenderRegistryValue -Path $realtimePolicy -Name 'DisableOnAccessProtection' -Value 1 `
        -Description 'On-access protection'
    Set-DefenderRegistryValue -Path $realtimePolicy -Name 'DisableScanOnRealtimeEnable' -Value 1 `
        -Description 'Scan on real-time enable'
    Set-DefenderRegistryValue -Path $realtimePolicy -Name 'DisableIOAVProtection' -Value 1 `
        -Description 'Downloaded file scanning'

    # ---------------------------------------------------------------
    # 2. Disable cloud-delivered protection
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Disabling cloud-delivered protection...'
    Set-DefenderRegistryValue -Path $spynetPolicy -Name 'SpynetReporting' -Value 0 `
        -Description 'Cloud protection reporting'
    Set-DefenderRegistryValue -Path $spynetPolicy -Name 'SubmitSamplesConsent' -Value 2 `
        -Description 'Sample submission (2=Never send)'

    # ---------------------------------------------------------------
    # 3. Disable automatic sample submission
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Disabling automatic sample submission...'
    Set-DefenderRegistryValue -Path $defenderPolicy -Name 'SubmitSamplesConsent' -Value 2 `
        -Description 'Global sample submission'

    # ---------------------------------------------------------------
    # 4. Disable behavior monitoring
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Disabling behavior monitoring...'
    Set-DefenderRegistryValue -Path $realtimePolicy -Name 'DisableBehaviorMonitoring' -Value 1 `
        -Description 'Behavior monitoring'

    # ---------------------------------------------------------------
    # 5. Add exclusion for C:\Tools (forensics tool directory)
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Adding scan exclusion for C:\Tools...'
    try {
        if ($PSCmdlet.ShouldProcess('C:\Tools', 'Add Defender exclusion path')) {
            Add-MpPreference -ExclusionPath 'C:\Tools' -ErrorAction Stop
            Write-Log -Level Success -Message 'Exclusion path C:\Tools added via Add-MpPreference.'
        }
    } catch {
        Write-Log -Level Warn -Message "Add-MpPreference failed (expected if Defender service is stopped): $($_.Exception.Message)"
        # Fallback: set exclusion via registry
        $exclusionPath = "$defenderPolicy\Exclusions\Paths"
        Set-DefenderRegistryValue -Path $exclusionPath -Name 'C:\Tools' -Value 0 `
            -Description 'Exclusion path C:\Tools'
    }

    # ---------------------------------------------------------------
    # 6. Disable Windows Defender scheduled scans
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Disabling scheduled scans...'
    Set-DefenderRegistryValue -Path $scanPolicy -Name 'DisableScanningMappedNetworkDrivesForFullScan' -Value 1 `
        -Description 'Network drive scan'
    Set-DefenderRegistryValue -Path $scanPolicy -Name 'DisableEmailScanning' -Value 1 `
        -Description 'Email scanning'
    # ScheduleDay 8 = never (valid range: 0=daily, 1-7=day of week, 8=never)
    Set-DefenderRegistryValue -Path $scanPolicy -Name 'ScheduleDay' -Value 8 `
        -Description 'Scheduled scan day (8=never)'

    # Also disable via Set-MpPreference if cmdlet is available
    try {
        if ($PSCmdlet.ShouldProcess('Defender scheduled scan', 'Disable via Set-MpPreference')) {
            Set-MpPreference -DisableScanningMappedNetworkDrivesForFullScan $true -ErrorAction SilentlyContinue
            Set-MpPreference -ScanScheduleDay 8 -ErrorAction SilentlyContinue
        }
    } catch { }

    # ---------------------------------------------------------------
    # 7. Disable Defender notifications / tray icon
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Disabling Defender notifications and tray icon...'
    Set-DefenderRegistryValue -Path $defenderPolicy -Name 'DisableRoutinelyTakingAction' -Value 1 `
        -Description 'Routine action notifications'
    $notifyPolicy = "$defenderPolicy\Notifications"
    Set-DefenderRegistryValue -Path $notifyPolicy -Name 'DisableNotifications' -Value 1 `
        -Description 'Defender notifications'

    # Hide the Security Center systray icon
    $systrayPath = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Systray'
    Set-DefenderRegistryValue -Path $systrayPath -Name 'HideSystray' -Value 1 `
        -Description 'Security Center tray icon'

    # Disable the SecurityHealthSystray startup entry
    try {
        $runKey = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
        if (Get-ItemProperty -Path $runKey -Name 'SecurityHealth' -ErrorAction SilentlyContinue) {
            if ($PSCmdlet.ShouldProcess('SecurityHealth run entry', 'Remove')) {
                Remove-ItemProperty -Path $runKey -Name 'SecurityHealth' -Force -ErrorAction SilentlyContinue
                Write-Log -Level Info -Message 'Removed SecurityHealth startup entry.'
            }
        }
    } catch { }

    # ---------------------------------------------------------------
    # 8. Attempt to disable Tamper Protection (registry-based)
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Attempting to disable Tamper Protection (may fail if currently active)...'
    $tamperPath = 'HKLM:\SOFTWARE\Microsoft\Windows Defender\Features'
    $tamperResult = Set-DefenderRegistryValue -Path $tamperPath -Name 'TamperProtection' -Value 0 `
        -Description 'Tamper Protection'
    if (-not $tamperResult) {
        Write-Log -Level Warn -Message 'Tamper Protection could not be disabled via registry. Disable it manually: Windows Security > Virus & threat protection > Manage settings > Tamper Protection = Off, then re-run this script.'
    }

    # ---------------------------------------------------------------
    # 9. Disable Defender AntiSpyware (master kill switch)
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Setting DisableAntiSpyware policy...'
    Set-DefenderRegistryValue -Path $defenderPolicy -Name 'DisableAntiSpyware' -Value 1 `
        -Description 'AntiSpyware (master switch)'
    Set-DefenderRegistryValue -Path $defenderPolicy -Name 'DisableAntiVirus' -Value 1 `
        -Description 'AntiVirus'

    # ---------------------------------------------------------------
    # 10. Try to stop and disable the Defender service
    # ---------------------------------------------------------------
    Write-Log -Level Info -Message 'Attempting to stop Defender services...'
    foreach ($svc in @('WinDefend', 'WdNisSvc', 'SecurityHealthService')) {
        try {
            if ($PSCmdlet.ShouldProcess($svc, 'Stop and disable service')) {
                sc.exe stop $svc 2>$null | Out-Null
                sc.exe config $svc start= disabled 2>$null | Out-Null
            }
        } catch { }
    }

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    Write-Log -Level Success -Message 'Windows Defender disable configuration applied.'
    Write-Log -Level Info -Message 'NOTE: A reboot may be required for all changes to take effect.'
    Write-Log -Level Info -Message 'NOTE: If Tamper Protection was active, disable it manually first, then re-run this script.'
}

# Dot-sourced by orchestrator; not auto-executed.
