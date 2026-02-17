<#
.SYNOPSIS
  Best-effort uninstall of Microsoft Edge and disable Edge update services.

.DESCRIPTION
  Attempts to remove system-level and user-level Edge installations using
  setup.exe when available. Also disables edgeupdate services and removes
  common desktop/start menu shortcuts to keep browser folders clean.
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

function Get-EdgeSetupCandidates {
    [CmdletBinding()]
    param()

    $roots = @(
        "$env:ProgramFiles(x86)\\Microsoft\\Edge\\Application",
        "$env:ProgramFiles\\Microsoft\\Edge\\Application"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    $candidates = @()
    foreach ($root in $roots) {
        try {
            $items = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending
            foreach ($item in $items) {
                $setup = Join-Path $item.FullName 'Installer\\setup.exe'
                if (Test-Path -LiteralPath $setup) {
                    $candidates += $setup
                }
            }
        } catch { }
    }

    return $candidates | Select-Object -Unique
}

function Invoke-EdgeSetupUninstall {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$SetupPath,
        [switch]$SystemLevel
    )

    $baseArgs = @('--uninstall', '--msedge', '--force-uninstall', '--verbose-logging')
    if ($SystemLevel) {
        $baseArgs += '--system-level'
    }

    if ($PSCmdlet.ShouldProcess($SetupPath, "Run Edge uninstall ($($baseArgs -join ' '))")) {
        $p = Start-Process -FilePath $SetupPath -ArgumentList $baseArgs -PassThru -Wait -NoNewWindow -ErrorAction SilentlyContinue
        if (-not $p) { return $false }
        # 0 = success. On some builds 20/21 can indicate "already removed" semantics.
        return ($p.ExitCode -eq 0 -or $p.ExitCode -eq 20 -or $p.ExitCode -eq 21)
    }
    return $true
}

function Disable-EdgeUpdateServices {
    [CmdletBinding()]
    param()
    foreach ($svc in @('edgeupdate', 'edgeupdatem')) {
        try {
            sc.exe stop $svc | Out-Null
        } catch { }
        try {
            sc.exe config $svc start= disabled | Out-Null
        } catch { }
    }
}

function Remove-EdgeShortcuts {
    [CmdletBinding()]
    param()

    $paths = @(
        "$env:USERPROFILE\\Desktop\\Microsoft Edge.lnk",
        "$env:PUBLIC\\Desktop\\Microsoft Edge.lnk",
        "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\Microsoft Edge.lnk",
        "$env:ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Microsoft Edge.lnk"
    )

    foreach ($path in $paths) {
        try {
            if (Test-Path -LiteralPath $path) {
                Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
            }
        } catch { }
    }
}

function Uninstall-MicrosoftEdge {
    [CmdletBinding(SupportsShouldProcess)]
    param()

    Write-Log -Level Info -Message 'Attempting to uninstall Microsoft Edge...'
    if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin }

    $setupCandidates = Get-EdgeSetupCandidates
    if (-not $setupCandidates -or $setupCandidates.Count -eq 0) {
        Write-Log -Level Warn -Message 'Edge setup.exe not found. Edge may already be removed or protected by this Windows build.'
    }

    $removed = $false
    foreach ($setup in $setupCandidates) {
        try {
            if (Invoke-EdgeSetupUninstall -SetupPath $setup -SystemLevel) {
                $removed = $true
            }
        } catch { }
        try {
            if (Invoke-EdgeSetupUninstall -SetupPath $setup) {
                $removed = $true
            }
        } catch { }
    }

    try { Disable-EdgeUpdateServices } catch { }
    try { Remove-EdgeShortcuts } catch { }

    $edgeExeCandidates = @(
        "$env:ProgramFiles(x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        "$env:ProgramFiles\\Microsoft\\Edge\\Application\\msedge.exe"
    )
    $stillPresent = $edgeExeCandidates | Where-Object { Test-Path -LiteralPath $_ }

    if ($stillPresent.Count -gt 0) {
        Write-Log -Level Warn -Message 'Edge executable still present. This Windows build may prevent full removal; update services were disabled and shortcuts cleaned.'
    } elseif ($removed) {
        Write-Log -Level Success -Message 'Microsoft Edge uninstall completed.'
    } else {
        Write-Log -Level Info -Message 'No removable Edge installation detected.'
    }
}

# Dot-sourced by orchestrator; not auto-executed.
