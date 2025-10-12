<#
.SYNOPSIS
  Common helper functions for Holmes VM setup scripts.

.NOTES
  Designed for Windows hosts with Administrator privileges.
  Supports -Verbose and -WhatIf via ShouldProcess where applicable.
#>

Set-StrictMode -Version Latest

function Test-IsWindows {
    [CmdletBinding()] param()
    try {
        if ($env:OS -eq 'Windows_NT') { return $true }
    } catch { }
    try {
        return ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT)
    } catch { return $false }
}

function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][ValidateSet('Info','Warn','Error','Success')]
        [string]$Level,
        [Parameter(Mandatory)][string]$Message
    )
    switch ($Level) {
        'Info'    { Write-Host $Message -ForegroundColor Cyan }
        'Warn'    { Write-Warning $Message }
        'Error'   { Write-Host $Message -ForegroundColor Red }
        'Success' { Write-Host $Message -ForegroundColor Green }
    }
}

function Assert-WindowsAndAdmin {
    [CmdletBinding()] param()
    if (-not (Test-IsWindows)) {
        throw 'This script must be run on Windows.'
    }
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        throw 'Please run this script in an elevated PowerShell session (Run as Administrator).'
    }
}

function Ensure-Directory {
    [CmdletBinding(SupportsShouldProcess)]
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        if ($PSCmdlet.ShouldProcess($Path, 'Create directory')) {
            New-Item -ItemType Directory -Path $Path -Force | Out-Null
        }
    }
}

function Set-Tls12IfNeeded {
    [CmdletBinding()] param()
    try {
        # 3072 is SslProtocols.Tls12
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    } catch { }
}

function Invoke-SafeDownload {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Uri,
        [Parameter(Mandatory)][string]$OutFile,
        [int]$RetryCount = 3,
        [int]$RetryDelaySec = 3
    )
    if ($PSCmdlet.ShouldProcess($Uri, "Download to $OutFile")) {
        Set-Tls12IfNeeded
        for ($i = 1; $i -le $RetryCount; $i++) {
            try {
                Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing -ErrorAction Stop
                if (Test-Path -LiteralPath $OutFile) { return $true }
            }
            catch {
                if ($i -ge $RetryCount) { throw }
                Start-Sleep -Seconds $RetryDelaySec
            }
        }
    }
}

function Expand-Zip {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$ZipPath,
        [Parameter(Mandatory)][string]$Destination
    )
    if ($PSCmdlet.ShouldProcess($Destination, "Expand $ZipPath")) {
        Ensure-Directory -Path $Destination
        Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force
    }
}

function Add-PathIfMissing {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Path,
        [ValidateSet('Machine','User')][string]$Scope = 'Machine'
    )
    $current = [Environment]::GetEnvironmentVariable('Path', $Scope)
    $contains = $current -split ';' | Where-Object { $_.TrimEnd('\') -ieq $Path.TrimEnd('\\') }
    if (-not $contains) {
        if ($PSCmdlet.ShouldProcess($Path, "Add to $Scope PATH")) {
            $new = if ([string]::IsNullOrWhiteSpace($current)) { $Path } else { "$current;$Path" }
            [Environment]::SetEnvironmentVariable('Path', $new, $Scope)
            # Update current session as well
            $env:Path = "$env:Path;$Path"
            Write-Log -Level Success -Message "Added to $Scope PATH: $Path"
        }
    } else {
        Write-Log -Level Info -Message "Path already present: $Path"
    }
}

function Ensure-Chocolatey {
    [CmdletBinding(SupportsShouldProcess)] param()
    if (Get-Command choco.exe -ErrorAction SilentlyContinue) { return $true }
    if ($PSCmdlet.ShouldProcess('Chocolatey', 'Install')) {
        Write-Log -Level Info -Message 'Installing Chocolatey...'
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
        Set-Tls12IfNeeded
        $installScript = 'https://community.chocolatey.org/install.ps1'
        try {
            Invoke-Expression ((New-Object System.Net.WebClient).DownloadString($installScript))
        } catch {
            throw "Chocolatey installation failed: $($_.Exception.Message)"
        }
        Start-Sleep -Seconds 3
        if (-not (Get-Command choco.exe -ErrorAction SilentlyContinue)) {
            throw 'Chocolatey installation did not complete successfully.'
        }
        Write-Log -Level Success -Message 'Chocolatey is ready.'
    }
}

function Test-ChocoPackageInstalled {
    [CmdletBinding()] param([Parameter(Mandatory)][string]$Name)
    # --limit-output prints name|version; safer to parse than default formatted output
    $line = choco list --local-only --exact --limit-output $Name 2>$null | Select-Object -First 1
    if (-not $line) { return $false }
    return ($line -split '\|')[0].Trim().ToLower() -eq $Name.ToLower()
}

function Install-ChocoPackage {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Name,
        [string]$Version,
        [switch]$ForceReinstall
    )
    if (-not $ForceReinstall -and (Test-ChocoPackageInstalled -Name $Name)) {
        Write-Log -Level Success -Message "Package already installed: $Name"
        return $true
    }
    $args = @('install', $Name, '-y', '--no-progress')
    if ($Version) { $args += @('--version', $Version) }
    if ($ForceReinstall) { $args += '--force' }
    if ($PSCmdlet.ShouldProcess($Name, 'choco install')) {
        & choco @args | Out-Null
        # 0 = success, 3010 = success with reboot required
        if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 3010) {
            if (-not (Test-ChocoPackageInstalled -Name $Name)) {
                Write-Log -Level Warn -Message "$Name reported success but not detected as installed."
                return $false
            }
            if ($LASTEXITCODE -eq 3010) {
                Write-Log -Level Warn -Message "$Name installed; reboot required (exit code 3010)."
            } else {
                Write-Log -Level Success -Message "$Name installed."
            }
            return $true
        }
        Write-Log -Level Error -Message "Failed to install $Name via Chocolatey. ExitCode=$LASTEXITCODE"
        return $false
    }
}

function New-ShortcutsFromFolder {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Folder,
        [string]$Filter = '*.exe',
        [Parameter(Mandatory)][string]$ShortcutDir,
        [string]$WorkingDir
    )
    Ensure-Directory -Path $ShortcutDir
    $shell = New-Object -ComObject WScript.Shell
    Get-ChildItem -Path $Folder -Filter $Filter -File | ForEach-Object {
        $lnk = Join-Path $ShortcutDir ("$($_.Name).lnk")
        if ($PSCmdlet.ShouldProcess($lnk, 'Create shortcut')) {
            $sc = $shell.CreateShortcut($lnk)
            $sc.TargetPath = $_.FullName
            $sc.WorkingDirectory = if ($WorkingDir) { $WorkingDir } else { $_.Directory.FullName }
            $sc.WindowStyle = 1
            $sc.Description = $_.BaseName
            $sc.Save()
        }
    }
}

function Invoke-Step {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Action,
        [switch]$ContinueOnError
    )
    try {
        & $Action
        Write-Log -Level Success -Message "$Name completed."
        return $true
    } catch {
        Write-Log -Level Error -Message "$Name failed: $($_.Exception.Message)"
        if ($ContinueOnError) { return $false }
        throw
    }
}

function Set-RegistryDword {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][int]$Value
    )
    New-Item -Path $Path -Force -ErrorAction SilentlyContinue | Out-Null
    if ($PSCmdlet.ShouldProcess("$Path\\$Name", "Set DWORD=$Value")) {
        New-ItemProperty -Path $Path -Name $Name -Value $Value -PropertyType DWord -Force | Out-Null
    }
}

function Convert-HexToArgbInt {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Hex # formats: "#RRGGBB" or "RRGGBB" or "#AARRGGBB"
    )
    $clean = $Hex.Trim()
    if ($clean.StartsWith('#')) { $clean = $clean.Substring(1) }
    if ($clean.Length -eq 6) { $clean = "FF$clean" }
    if ($clean.Length -ne 8) { throw "Invalid hex color: $Hex" }
    return [int]([uint32]::Parse($clean, [System.Globalization.NumberStyles]::HexNumber))
}

function Convert-ArgbToAbgrInt {
    [CmdletBinding()]
    param([Parameter(Mandatory)][int]$Argb)
    $a = ($Argb -band 0xFF000000)
    $r = ($Argb -band 0x00FF0000) -shl 0
    $g = ($Argb -band 0x0000FF00) -shl 0
    $b = ($Argb -band 0x000000FF) -shl 0
    $abgr = $a -bor (($Argb -band 0x0000FF00) -shl 8) -bor (($Argb -band 0x00FF0000) -shr 16) -bor (($Argb -band 0x000000FF) -shl 16)
    return [int]$abgr
}

function Invoke-SettingsChangedBroadcast {
    [CmdletBinding()] param()
    $typeDefined = [System.AppDomain]::CurrentDomain.GetAssemblies() | ForEach-Object { $_.GetTypes() } | Where-Object { $_.Name -eq 'Win32Native' }
    if (-not $typeDefined) {
        $sig = @'
using System;
using System.Runtime.InteropServices;
public class Win32Native {
    [DllImport("user32.dll", SetLastError=true, CharSet=CharSet.Auto)]
    public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
}
'@
        Add-Type -TypeDefinition $sig -ErrorAction SilentlyContinue
    }
    $HWND_BROADCAST = [IntPtr]0xffff
    $WM_SETTINGCHANGE = 0x1A
    $SMTO_ABORTIFHUNG = 0x2
    $result = [UIntPtr]::Zero
    [void][Win32Native]::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, 'ImmersiveColorSet', $SMTO_ABORTIFHUNG, 5000, [ref]$result)
    # Also broadcast generic setting change to prompt more components
    [void][Win32Native]::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, $null, $SMTO_ABORTIFHUNG, 5000, [ref]$result)
}

function Set-WindowsAppearance {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [switch]$DarkMode = $true,
        [string]$AccentHex = '#0078D7',
        [switch]$ShowAccentOnTaskbar = $true
    )
    try {
        $personalize = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
        if ($DarkMode) {
            Set-RegistryDword -Path $personalize -Name 'AppsUseLightTheme' -Value 0
            Set-RegistryDword -Path $personalize -Name 'SystemUsesLightTheme' -Value 0
        }
        # Also set machine defaults for future accounts (best effort)
        if ($DarkMode) {
            $personalizeM = 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
            try {
                Set-RegistryDword -Path $personalizeM -Name 'AppsUseLightTheme' -Value 0
                Set-RegistryDword -Path $personalizeM -Name 'SystemUsesLightTheme' -Value 0
            } catch { Write-Log -Level Warn -Message "Could not set machine default dark mode: $($_.Exception.Message)" }
        }
        if ($ShowAccentOnTaskbar) {
            Set-RegistryDword -Path $personalize -Name 'ColorPrevalence' -Value 1
        }

        $argb = Convert-HexToArgbInt -Hex $AccentHex
        $abgr = Convert-ArgbToAbgrInt -Argb $argb

        $dwm = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\DWM'
        Set-RegistryDword -Path $dwm -Name 'AccentColor' -Value $abgr
        Set-RegistryDword -Path $dwm -Name 'ColorizationColor' -Value $argb
        Set-RegistryDword -Path $dwm -Name 'ColorPrevalence' -Value 1

        $explorerAccent = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Accent'
        Set-RegistryDword -Path $explorerAccent -Name 'AccentColorMenu' -Value $abgr
        Set-RegistryDword -Path $explorerAccent -Name 'StartColorMenu' -Value $abgr

        Invoke-SettingsChangedBroadcast
        Write-Log -Level Success -Message "Windows appearance applied: DarkMode=$($DarkMode.IsPresent), Accent=$AccentHex"
    }
    catch {
        Write-Log -Level Warn -Message "Failed to apply Windows appearance: $($_.Exception.Message)"
    }
}

function Pin-TaskbarItem {
    [CmdletBinding(SupportsShouldProcess)]
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Item not found: $Path" }
    try {
        $shell = New-Object -ComObject Shell.Application
        $folderPath = Split-Path -Parent $Path
        $leaf = Split-Path -Leaf $Path
        $folder = $shell.Namespace($folderPath)
        $item = $folder.ParseName($leaf)
        if (-not $item) { throw 'Shell item not found.' }
        $verbs = @($item.Verbs())
        # If already pinned, an unpin verb may be present
        $unpin = $verbs | Where-Object { ($_.Name -replace '&','') -match 'Unpin from taskbar' -or $_.Name -match 'taskbarunpin' }
        if ($unpin) { return $true }
        $pin = $verbs | Where-Object { ($_.Name -replace '&','') -match 'Pin to taskbar' -or $_.Name -match 'taskbarpin' -or ($_.Name -replace '&','') -match 'Taskbar' }
        if ($pin) {
            if ($PSCmdlet.ShouldProcess($Path, 'Pin to taskbar')) { $pin.DoIt() }
            return $true
        } else {
            Write-Log -Level Warn -Message 'Taskbar pin verb not available (OS may block programmatic pinning).'
            return $false
        }
    } catch {
        Write-Log -Level Warn -Message "Failed to pin to taskbar: $($_.Exception.Message)"
        return $false
    }
}

function Test-UrlReachable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Url,
        [int]$TimeoutSec = 5
    )
    Set-Tls12IfNeeded
    try {
        $resp = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400)
    } catch {
        return $false
    }
}

function Assert-NetworkConnectivity {
    [CmdletBinding()]
    param(
        [string[]]$Urls = @('https://www.google.com/generate_204','https://github.com'),
        [int]$TimeoutSec = 5,
        [int]$MinimumSuccess = 0
    )
    if ($MinimumSuccess -le 0) { $MinimumSuccess = $Urls.Count }
    $success = 0
    foreach ($u in $Urls) {
        $ok = Test-UrlReachable -Url $u -TimeoutSec $TimeoutSec
        if ($ok) {
            $success++
            Write-Log -Level Success -Message "Reachable: $u"
        } else {
            Write-Log -Level Warn -Message "Not reachable: $u"
        }
    }
    if ($success -lt $MinimumSuccess) {
        throw "Network connectivity check failed. Reached $success of $($Urls.Count) required endpoints."
    }
    Write-Log -Level Success -Message "Network connectivity OK ($success/$($Urls.Count))."
}

function Set-Wallpaper {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$ImagePath,
        [ValidateSet('Fill','Fit','Stretch','Tile','Center','Span')]
        [string]$Style = 'Fill'
    )
    if (-not (Test-Path -LiteralPath $ImagePath)) {
        throw "Wallpaper image not found: $ImagePath"
    }

    $regPath = 'HKCU:\\Control Panel\\Desktop'
    $styleMap = @{
        'Center'  = @{ WallpaperStyle = '0';  TileWallpaper = '0' }
        'Tile'    = @{ WallpaperStyle = '0';  TileWallpaper = '1' }
        'Stretch' = @{ WallpaperStyle = '2';  TileWallpaper = '0' }
        'Fit'     = @{ WallpaperStyle = '6';  TileWallpaper = '0' }
        'Fill'    = @{ WallpaperStyle = '10'; TileWallpaper = '0' }
        'Span'    = @{ WallpaperStyle = '22'; TileWallpaper = '0' }
    }
    $values = $styleMap[$Style]

    if ($PSCmdlet.ShouldProcess($ImagePath, "Set desktop wallpaper ($Style)")) {
        New-Item -Path $regPath -Force -ErrorAction SilentlyContinue | Out-Null
        Set-ItemProperty -Path $regPath -Name Wallpaper -Value $ImagePath
        Set-ItemProperty -Path $regPath -Name WallpaperStyle -Value $values.WallpaperStyle
        Set-ItemProperty -Path $regPath -Name TileWallpaper -Value $values.TileWallpaper

        $sig = @'
using System.Runtime.InteropServices;
public class NativeMethods {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
}
'@
        if (-not ([System.AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.GetTypes().Name -contains 'NativeMethods' })) {
            Add-Type -TypeDefinition $sig -ErrorAction Stop
        }
        $SPI_SETDESKWALLPAPER = 20
        $SPIF_UPDATEINIFILE = 0x01
        $SPIF_SENDWININICHANGE = 0x02
        [void]([NativeMethods]::SystemParametersInfo($SPI_SETDESKWALLPAPER, 0, $ImagePath, $SPIF_UPDATEINIFILE -bor $SPIF_SENDWININICHANGE))
        Write-Log -Level Success -Message "Wallpaper applied: $ImagePath ($Style)"
    }
}

Export-ModuleMember -Function *
