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
    [switch]$ForceReinstall
)

$ErrorActionPreference = 'Stop'

Write-Host '==== Holmes VM: Blue Team Swiss Knife ====' -ForegroundColor Magenta

try {
    # Import common module
    $modulePath = Join-Path $PSScriptRoot 'modules/Holmes.Common.psm1'
    if (-not (Test-Path -LiteralPath $modulePath)) { throw "Common module not found at $modulePath" }
    Import-Module $modulePath -Force

    Assert-WindowsAndAdmin

    # Ensure Chocolatey
    Ensure-Chocolatey

    if (-not $SkipWireshark) {
        Write-Log -Level Info -Message 'Installing Wireshark...'
        Install-ChocoPackage -Name 'wireshark' -ForceReinstall:$ForceReinstall
    } else { Write-Log -Level Info -Message 'Skipping Wireshark.' }

    if (-not $SkipDotNetDesktop) {
        Write-Log -Level Info -Message 'Installing .NET 6.0 Desktop Runtime...'
        Install-ChocoPackage -Name 'dotnet-6.0-desktopruntime' -ForceReinstall:$ForceReinstall
    } else { Write-Log -Level Info -Message 'Skipping .NET Desktop Runtime.' }

    if (-not $SkipDnSpyEx) {
        Write-Log -Level Info -Message 'Installing DnSpyEx...'
        Install-ChocoPackage -Name 'dnspyex' -ForceReinstall:$ForceReinstall
    } else { Write-Log -Level Info -Message 'Skipping DnSpyEx.' }

    if (-not $SkipPeStudio) {
        Write-Log -Level Info -Message 'Installing PeStudio...'
        Install-ChocoPackage -Name 'pestudio' -ForceReinstall:$ForceReinstall
    } else { Write-Log -Level Info -Message 'Skipping PeStudio.' }

    # Install EZ Tools
    if (-not $SkipEZTools) {
        . "$PSScriptRoot\util\install-eztools.ps1"
        $useVerbose = ($PSBoundParameters.ContainsKey('Verbose') -or $VerbosePreference -eq 'Continue')
        $useWhatIf = ($WhatIfPreference -eq $true)
        if ($useVerbose -and $useWhatIf) { Install-EZTools -Verbose -WhatIf }
        elseif ($useVerbose) { Install-EZTools -Verbose }
        elseif ($useWhatIf) { Install-EZTools -WhatIf }
        else { Install-EZTools }
    } else { Write-Log -Level Info -Message 'Skipping EZ Tools.' }

    # Install RegRipper
    if (-not $SkipRegRipper) {
        . "$PSScriptRoot\util\install-regripper.ps1"
        $useVerbose = ($PSBoundParameters.ContainsKey('Verbose') -or $VerbosePreference -eq 'Continue')
        $useWhatIf = ($WhatIfPreference -eq $true)
        if ($useVerbose -and $useWhatIf) { Install-RegRipper -Verbose -WhatIf }
        elseif ($useVerbose) { Install-RegRipper -Verbose }
        elseif ($useWhatIf) { Install-RegRipper -WhatIf }
        else { Install-RegRipper }
    } else { Write-Log -Level Info -Message 'Skipping RegRipper.' }

    # Set Wallpaper
    if (-not $SkipWallpaper) {
        $assetPath = Join-Path $PSScriptRoot 'assets/wallpaper.jpg'
        if (Test-Path -LiteralPath $assetPath) {
            $wallDir = 'C:\\Tools\\Wallpapers'
            Ensure-Directory -Path $wallDir
            $destPath = Join-Path $wallDir 'holmes-wallpaper.jpg'
            if ($PSCmdlet.ShouldProcess($destPath, 'Copy wallpaper')) {
                Copy-Item -Path $assetPath -Destination $destPath -Force
            }
            Set-Wallpaper -ImagePath $destPath -Style Fill
        } else {
            Write-Log -Level Warn -Message "Wallpaper not found at $assetPath; skipping."
        }
    } else { Write-Log -Level Info -Message 'Skipping wallpaper setup.' }

    Write-Host "`nSetup complete! Welcome to Holmes VM!" -ForegroundColor Magenta
}
catch {
    Write-Log -Level Error -Message "Setup failed: $($_.Exception.Message)"
    if ($PSBoundParameters['Verbose']) { Write-Error -ErrorRecord $_ }
    exit 1
}
