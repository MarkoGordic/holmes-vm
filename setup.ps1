#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
    Holmes VM: Blue Team Swiss Knife
    Safe, idempotent setup with modular installers and Chocolatey packages.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$SkipWireshark,
    [switch]$SkipDotNetDesktop,
    [switch]$SkipDnSpyEx,
    [switch]$SkipPeStudio,
    [switch]$SkipEZTools,
    [switch]$SkipRegRipper,
    [switch]$SkipWallpaper,
    [switch]$SkipNetworkCheck,
    [switch]$SkipChainsaw,
    [switch]$ForceReinstall
)

$ErrorActionPreference = 'Stop'

Write-Host '==== Holmes VM: Blue Team Swiss Knife ====' -ForegroundColor Magenta

try {
    # Import common module
    $modulePath = Join-Path $PSScriptRoot 'modules/Holmes.Common.psm1'
    if (-not (Test-Path -LiteralPath $modulePath)) { throw "Common module not found at $modulePath" }
    Import-Module $modulePath -Force -DisableNameChecking

    Assert-WindowsAndAdmin

    if (-not $SkipNetworkCheck) {
        Write-Log -Level Info -Message 'Checking network connectivity (GitHub + Google)...'
        # Require at least 1 out of 2 endpoints to be reachable to proceed
        Assert-NetworkConnectivity -Urls @('https://www.google.com/generate_204','https://github.com') -MinimumSuccess 1 -TimeoutSec 7
    } else {
        Write-Log -Level Warn -Message 'Skipping network connectivity check.'
    }

    # Ensure Chocolatey
    Invoke-Step -Name 'Ensure Chocolatey' -ContinueOnError -Action { Ensure-Chocolatey }

    if (-not $SkipWireshark) {
        Write-Log -Level Info -Message 'Installing Wireshark...'
        Invoke-Step -Name 'Install Wireshark' -ContinueOnError -Action { Install-ChocoPackage -Name 'wireshark' -ForceReinstall:$ForceReinstall | Out-Null }
    } else { Write-Log -Level Info -Message 'Skipping Wireshark.' }

    if (-not $SkipDotNetDesktop) {
        Write-Log -Level Info -Message 'Installing .NET 6.0 Desktop Runtime...'
        Invoke-Step -Name 'Install .NET Desktop Runtime' -ContinueOnError -Action { Install-ChocoPackage -Name 'dotnet-6.0-desktopruntime' -ForceReinstall:$ForceReinstall | Out-Null }
    } else { Write-Log -Level Info -Message 'Skipping .NET Desktop Runtime.' }

    if (-not $SkipDnSpyEx) {
        Write-Log -Level Info -Message 'Installing DnSpyEx...'
        Invoke-Step -Name 'Install DnSpyEx' -ContinueOnError -Action { Install-ChocoPackage -Name 'dnspyex' -ForceReinstall:$ForceReinstall | Out-Null }
    } else { Write-Log -Level Info -Message 'Skipping DnSpyEx.' }

    if (-not $SkipPeStudio) {
        Write-Log -Level Info -Message 'Installing PeStudio...'
        Invoke-Step -Name 'Install PeStudio' -ContinueOnError -Action { Install-ChocoPackage -Name 'pestudio' -ForceReinstall:$ForceReinstall | Out-Null }
    } else { Write-Log -Level Info -Message 'Skipping PeStudio.' }

    # Install EZ Tools
    if (-not $SkipEZTools) {
        . "$PSScriptRoot\util\install-eztools.ps1"
        Invoke-Step -Name 'Install EZ Tools' -ContinueOnError -Action {
            $useVerbose = ($PSBoundParameters.ContainsKey('Verbose') -or $VerbosePreference -eq 'Continue')
            $useWhatIf = ($WhatIfPreference -eq $true)
            if ($useVerbose -and $useWhatIf) { Install-EZTools -Verbose -WhatIf }
            elseif ($useVerbose) { Install-EZTools -Verbose }
            elseif ($useWhatIf) { Install-EZTools -WhatIf }
            else { Install-EZTools }
        }
    } else { Write-Log -Level Info -Message 'Skipping EZ Tools.' }

    # Install RegRipper
    if (-not $SkipRegRipper) {
        . "$PSScriptRoot\util\install-regripper.ps1"
        Invoke-Step -Name 'Install RegRipper' -ContinueOnError -Action {
            $useVerbose = ($PSBoundParameters.ContainsKey('Verbose') -or $VerbosePreference -eq 'Continue')
            $useWhatIf = ($WhatIfPreference -eq $true)
            if ($useVerbose -and $useWhatIf) { Install-RegRipper -Verbose -WhatIf }
            elseif ($useVerbose) { Install-RegRipper -Verbose }
            elseif ($useWhatIf) { Install-RegRipper -WhatIf }
            else { Install-RegRipper }
        }
    } else { Write-Log -Level Info -Message 'Skipping RegRipper.' }

    # Install Chainsaw
    if (-not $SkipChainsaw) {
        . "$PSScriptRoot\util\install-chainsaw.ps1"
        Invoke-Step -Name 'Install Chainsaw' -ContinueOnError -Action {
            $useVerbose = ($PSBoundParameters.ContainsKey('Verbose') -or $VerbosePreference -eq 'Continue')
            $useWhatIf = ($WhatIfPreference -eq $true)
            if ($useVerbose -and $useWhatIf) { Install-Chainsaw -Verbose -WhatIf }
            elseif ($useVerbose) { Install-Chainsaw -Verbose }
            elseif ($useWhatIf) { Install-Chainsaw -WhatIf }
            else { Install-Chainsaw }
        }
    } else { Write-Log -Level Info -Message 'Skipping Chainsaw.' }

    # Set Wallpaper
    if (-not $SkipWallpaper) {
        $assetPath = Join-Path $PSScriptRoot 'assets/wallpaper.jpg'
        if (Test-Path -LiteralPath $assetPath) {
            $wallDir = 'C:\\Tools\\Wallpapers'
            Invoke-Step -Name 'Prepare wallpaper directory' -ContinueOnError -Action { Ensure-Directory -Path $wallDir }
            $destPath = Join-Path $wallDir 'holmes-wallpaper.jpg'
            Invoke-Step -Name 'Copy wallpaper' -ContinueOnError -Action {
                if ($PSCmdlet.ShouldProcess($destPath, 'Copy wallpaper')) {
                    Copy-Item -Path $assetPath -Destination $destPath -Force
                }
            }
            Invoke-Step -Name 'Apply wallpaper' -ContinueOnError -Action { Set-Wallpaper -ImagePath $destPath -Style Fill }
        } else {
            Write-Log -Level Warn -Message "Wallpaper not found at $assetPath; skipping."
        }
    } else { Write-Log -Level Info -Message 'Skipping wallpaper setup.' }

    # Apply Windows appearance (Dark mode + blue accent)
    Invoke-Step -Name 'Apply Windows appearance' -ContinueOnError -Action {
        Set-WindowsAppearance -DarkMode -AccentHex '#0078D7' -ShowAccentOnTaskbar
    }

    Write-Host "`nSetup complete! Welcome to Holmes VM!" -ForegroundColor Magenta
}
catch {
    Write-Log -Level Error -Message "Setup failed: $($_.Exception.Message)"
    if ($PSBoundParameters['Verbose']) { Write-Error -ErrorRecord $_ }
    exit 1
}
