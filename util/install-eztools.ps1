<#
.SYNOPSIS
  Install Eric Zimmerman's Tools with clearer progress, richer logging, and an optional minimal GUI.

.NOTES
  - Requires Windows and Administrator (for PATH Machine scope and shortcuts).
  - Uses Holmes.Common.psm1 helpers if available in ..\modules.
  - When run directly (not dot-sourced), will auto-start with a minimal GUI by default.
#>

# Try to import common module for logging/helpers if not already available
try {
    if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) {
        $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'
        if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue }
    }
} catch { }

# Script-scoped logging context
$script:InstallerName = "Eric Zimmerman's Tools"
$script:LogDirDefault = Join-Path $env:ProgramData 'HolmesVM/Logs'
$script:LogFilePath = $null

function Initialize-Logging {
    [CmdletBinding()]
    param(
        [string]$LogDir
    )
    try {
        if (-not $LogDir) { $LogDir = $script:LogDirDefault }
        if (-not (Test-Path -LiteralPath $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
        $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $script:LogFilePath = Join-Path $LogDir ("EZTools-install-$timestamp.log")
        # Start transcript to capture all console output
        try { Start-Transcript -Path $script:LogFilePath -Append -ErrorAction Stop | Out-Null } catch { }
    } catch { }
}

function Add-LogLine {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][ValidateSet('Info','Warn','Error','Success')]
        [string]$Level,
        [Parameter(Mandatory)][string]$Message
    )
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    try {
        if ($script:LogFilePath) { Add-Content -Path $script:LogFilePath -Value "[$ts] [$($Level.ToUpper())] $Message" -ErrorAction SilentlyContinue }
    } catch { }
    try { if (Get-Command Write-Log -ErrorAction SilentlyContinue) { Write-Log -Level $Level -Message $Message } else { Write-Host $Message } } catch { }
    # GUI removed for unified setup; no per-installer UI updates
}

function Update-InstallProgress {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][int]$Percent,
        [Parameter(Mandatory)][string]$Status,
        [string]$CurrentTask
    )
    $activity = "Installing $script:InstallerName"
    $statusMsg = if ($CurrentTask) { "$Status - $CurrentTask" } else { $Status }
    try { Write-Progress -Activity $activity -Status $statusMsg -PercentComplete $Percent } catch { }
    # GUI removed for unified setup; progress is console-only here
}

function Invoke-ProgressStep {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Action,
        [Parameter(Mandatory)][int]$StepIndex,
        [Parameter(Mandatory)][int]$TotalSteps,
        [switch]$ContinueOnError
    )
    $percent = [int](($StepIndex / [double]$TotalSteps) * 100)
    Update-InstallProgress -Percent $percent -Status "Working ($StepIndex/$TotalSteps)" -CurrentTask $Name
    Add-LogLine -Level Info -Message "$Name..."
    try {
        & $Action
        Add-LogLine -Level Success -Message "$Name completed."
        return $true
    } catch {
        Add-LogLine -Level Error -Message "$Name failed: $($_.Exception.Message)"
        if ($ContinueOnError) { return $false }
        throw
    }
}

function New-MinimalInstallerWindow { throw 'Per-installer GUI was removed. Use setup.ps1 unified GUI.' }

function Install-EZTools {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\\Tools\\EricZimmermanTools',
        [string]$NetVersion = '6',
        [string]$LogDir
    )

    Initialize-Logging -LogDir $LogDir
    Add-LogLine -Level Info -Message "Starting installation of $script:InstallerName"

    if (-not $PSCmdlet.ShouldProcess($Destination, "Install $script:InstallerName")) {
        Add-LogLine -Level Info -Message "WhatIf: Would install $script:InstallerName to $Destination (Net=$NetVersion)"
        return
    }

    $total = 8
    $step = 0

    $ezToolsDir = $Destination
    $ezToolsZip = Join-Path $env:TEMP 'Get-ZimmermanTools.zip'
    $ezToolsScript = Join-Path $ezToolsDir 'Get-ZimmermanTools.ps1'
    $ezToolsNetDir = Join-Path $ezToolsDir ("net$NetVersion")
    $desktopShortcutDir = Join-Path (Join-Path $env:USERPROFILE 'Desktop') 'EricZimmermanTools'

    Invoke-ProgressStep -Name 'Check OS and Admin' -StepIndex (++$step) -TotalSteps $total -Action {
        if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin } else { Add-LogLine -Level Warn -Message 'Common module not loaded; proceeding without explicit admin check.' }
    } | Out-Null

    Invoke-ProgressStep -Name 'Prepare directories' -StepIndex (++$step) -TotalSteps $total -Action {
        if (Get-Command Ensure-Directory -ErrorAction SilentlyContinue) {
            Ensure-Directory -Path $ezToolsDir
            Ensure-Directory -Path $desktopShortcutDir
        } else {
            if (-not (Test-Path -LiteralPath $ezToolsDir)) { New-Item -ItemType Directory -Path $ezToolsDir -Force | Out-Null }
            if (-not (Test-Path -LiteralPath $desktopShortcutDir)) { New-Item -ItemType Directory -Path $desktopShortcutDir -Force | Out-Null }
        }
    } | Out-Null

    Invoke-ProgressStep -Name 'Download Get-ZimmermanTools.zip' -StepIndex (++$step) -TotalSteps $total -Action {
        if (Get-Command Invoke-SafeDownload -ErrorAction SilentlyContinue) {
            Invoke-SafeDownload -Uri 'https://f001.backblazeb2.com/file/EricZimmermanTools/Get-ZimmermanTools.zip' -OutFile $ezToolsZip
        } else {
            Invoke-WebRequest -Uri 'https://f001.backblazeb2.com/file/EricZimmermanTools/Get-ZimmermanTools.zip' -OutFile $ezToolsZip -UseBasicParsing
        }
    } | Out-Null

    Invoke-ProgressStep -Name 'Extract and unblock' -StepIndex (++$step) -TotalSteps $total -Action {
        if (Get-Command Expand-Zip -ErrorAction SilentlyContinue) {
            Expand-Zip -ZipPath $ezToolsZip -Destination $ezToolsDir
        } else {
            Expand-Archive -Path $ezToolsZip -DestinationPath $ezToolsDir -Force
        }
        if (Test-Path -LiteralPath $ezToolsScript) { Unblock-File -Path $ezToolsScript }
    } | Out-Null

    Invoke-ProgressStep -Name 'Run Get-ZimmermanTools.ps1' -StepIndex (++$step) -TotalSteps $total -Action {
        Push-Location $ezToolsDir
        try {
            if ($PSCmdlet.ShouldProcess('Get-ZimmermanTools.ps1', 'Execute')) {
                .\Get-ZimmermanTools.ps1 -Dest $ezToolsDir -NetVersion $NetVersion
            }
        } finally { Pop-Location }
    } | Out-Null

    Invoke-ProgressStep -Name 'Add base directory to PATH' -StepIndex (++$step) -TotalSteps $total -Action {
        if (Test-Path -LiteralPath $ezToolsDir) {
            if (Get-Command Add-PathIfMissing -ErrorAction SilentlyContinue) { Add-PathIfMissing -Path $ezToolsDir -Scope Machine } else { $env:Path = "$env:Path;$ezToolsDir" }
        }
    } | Out-Null

    Invoke-ProgressStep -Name "Add net$NetVersion directory to PATH" -StepIndex (++$step) -TotalSteps $total -Action {
        if (Test-Path -LiteralPath $ezToolsNetDir) {
            if (Get-Command Add-PathIfMissing -ErrorAction SilentlyContinue) { Add-PathIfMissing -Path $ezToolsNetDir -Scope Machine } else { $env:Path = "$env:Path;$ezToolsNetDir" }
        } else {
            Add-LogLine -Level Warn -Message "Expected tools directory not found: $ezToolsNetDir"
        }
    } | Out-Null

    Invoke-ProgressStep -Name 'Create desktop shortcuts' -StepIndex (++$step) -TotalSteps $total -Action {
        if (Test-Path -LiteralPath $ezToolsNetDir) {
            if (Get-Command New-ShortcutsFromFolder -ErrorAction SilentlyContinue) {
                New-ShortcutsFromFolder -Folder $ezToolsNetDir -ShortcutDir $desktopShortcutDir -WorkingDir $ezToolsNetDir
            } else {
                $shell = New-Object -ComObject WScript.Shell
                Get-ChildItem -Path $ezToolsNetDir -Filter '*.exe' -File | ForEach-Object {
                    $lnk = Join-Path $desktopShortcutDir ("$($_.Name).lnk")
                    $sc = $shell.CreateShortcut($lnk)
                    $sc.TargetPath = $_.FullName
                    $sc.WorkingDirectory = $_.Directory.FullName
                    $sc.WindowStyle = 1
                    $sc.Description = $_.BaseName
                    $sc.Save()
                }
            }
        }
        # Ensure MFTExplorer shortcut exists even if not under netX
        $mft = Get-ChildItem -Path $ezToolsDir -Recurse -Filter 'MFTExplorer.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($mft) {
            $shell = New-Object -ComObject WScript.Shell
            $lnk = Join-Path $desktopShortcutDir 'MFTExplorer.exe.lnk'
            $sc = $shell.CreateShortcut($lnk)
            $sc.TargetPath = $mft.FullName
            $sc.WorkingDirectory = $mft.Directory.FullName
            $sc.WindowStyle = 1
            $sc.Description = 'MFT Explorer'
            $sc.Save()
        }
    } | Out-Null

    Invoke-ProgressStep -Name 'Cleanup temporary files' -StepIndex (++$step) -TotalSteps $total -Action {
        if (Test-Path -LiteralPath $ezToolsZip) { Remove-Item -Path $ezToolsZip -Force -ErrorAction SilentlyContinue }
    } | Out-Null

    Update-InstallProgress -Percent 100 -Status 'Completed' -CurrentTask ''
    Add-LogLine -Level Success -Message "Installation finished. Shortcuts created on Desktop."
    try { Stop-Transcript | Out-Null } catch { }
}

function Start-EZToolsInstaller { throw 'Per-installer GUI was removed. Use setup.ps1 unified GUI.' }

# Removed auto-run; unified setup GUI in setup.ps1 is the single entrypoint
