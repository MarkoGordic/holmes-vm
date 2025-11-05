try { if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) { $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'; if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue } } } catch { }
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }

$script:InstallerName = "NetworkMiner"
$script:LogDirDefault = Join-Path $env:ProgramData 'HolmesVM/Logs'
$script:LogFilePath = $null

function Initialize-Logging { [CmdletBinding()] param([string]$LogDir) try { if (-not $LogDir) { $LogDir = $script:LogDirDefault } if (-not (Test-Path -LiteralPath $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null } $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'; $script:LogFilePath = Join-Path $LogDir ("NetworkMiner-install-$timestamp.log"); try { Start-Transcript -Path $script:LogFilePath -Append -ErrorAction Stop | Out-Null } catch { } } catch { } }
function Add-LogLine { [CmdletBinding()] param([Parameter(Mandatory)][ValidateSet('Info','Warn','Error','Success')][string]$Level,[Parameter(Mandatory)][string]$Message) $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'; try { if ($script:LogFilePath) { Add-Content -Path $script:LogFilePath -Value "[$ts] [$($Level.ToUpper())] $Message" -ErrorAction SilentlyContinue } } catch { } try { if (Get-Command Write-Log -ErrorAction SilentlyContinue) { Write-Log -Level $Level -Message $Message } else { Write-Host $Message } } catch { } }
function Update-InstallProgress { [CmdletBinding()] param([Parameter(Mandatory)][int]$Percent,[Parameter(Mandatory)][string]$Status,[string]$CurrentTask) $activity = "Installing $script:InstallerName"; $statusMsg = if ($CurrentTask) { "$Status - $CurrentTask" } else { $Status }; try { Write-Progress -Activity $activity -Status $statusMsg -PercentComplete $Percent } catch { } }
function Invoke-ProgressStep { [CmdletBinding()] param([Parameter(Mandatory)][string]$Name,[Parameter(Mandatory)][scriptblock]$Action,[Parameter(Mandatory)][int]$StepIndex,[Parameter(Mandatory)][int]$TotalSteps,[switch]$ContinueOnError) $percent = [int](($StepIndex / [double]$TotalSteps) * 100); Update-InstallProgress -Percent $percent -Status "Working ($StepIndex/$TotalSteps)" -CurrentTask $Name; Add-LogLine -Level Info -Message "$Name..."; try { & $Action; Add-LogLine -Level Success -Message "$Name completed."; return $true } catch { Add-LogLine -Level Error -Message "$Name failed: $($_.Exception.Message)"; if ($ContinueOnError) { return $false } throw } }

function Test-ChocoPackageInstalled { param([Parameter(Mandatory)][string]$Name) try { $pkg = choco list --local-only --exact $Name 2>$null | Select-String "^$Name\s"; return [bool]$pkg } catch { return $false } }
function Install-ViaChocolatey { [CmdletBinding(SupportsShouldProcess)] param([Parameter(Mandatory)][string]$PackageName) if (Test-ChocoPackageInstalled -Name $PackageName) { Add-LogLine -Level Success -Message "$PackageName already installed via Chocolatey"; return $true } try { if ($PSCmdlet.ShouldProcess($PackageName,'choco install')) { choco install $PackageName -y --no-progress | Out-Null } return (Test-ChocoPackageInstalled -Name $PackageName) } catch { Add-LogLine -Level Warn -Message "Chocolatey install failed: $($_.Exception.Message)"; return $false } }

function Invoke-SafeDownload { [CmdletBinding()] param([Parameter(Mandatory)][string]$Uri,[Parameter(Mandatory)][string]$OutFile) try { Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing -ErrorAction Stop; return $true } catch { try { (New-Object System.Net.WebClient).DownloadFile($Uri,$OutFile); return $true } catch { return $false } } }
function Expand-Zip { param([Parameter(Mandatory)][string]$ZipPath,[Parameter(Mandatory)][string]$Destination) Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force }
function Ensure-Directory { param([Parameter(Mandatory)][string]$Path) if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }

function Install-NetworkMiner {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [string]$Destination = 'C:\Tools\NetworkMiner',
        [string]$LogDir
    )

    Initialize-Logging -LogDir $LogDir
    Add-LogLine -Level Info -Message "Starting installation of $script:InstallerName"

    if (-not $PSCmdlet.ShouldProcess($Destination, "Install $script:InstallerName")) { Add-LogLine -Level Info -Message "WhatIf: Would install $script:InstallerName to $Destination"; return }

    $total = 9; $step = 0
    $nmZip = Join-Path $env:TEMP 'NetworkMiner-latest.zip'
    $nmUrlPrimary = 'https://chocolatey.org/api/v2/package/networkminer' # placeholder if Choco exists
    $nmDirectUrl = 'https://www.netresec.com/?download=NetworkMiner' # landing page, will redirect; we will use versioned link below

    Invoke-ProgressStep -Name 'Check OS and Admin' -StepIndex (++$step) -TotalSteps $total -Action { if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin } else { Add-LogLine -Level Warn -Message 'Common module not loaded; proceeding without explicit admin check.' } } | Out-Null

    # Manual install first
    $manualOk = $false
    try {
        Invoke-ProgressStep -Name 'Prepare destination' -StepIndex (++$step) -TotalSteps $total -Action { Ensure-Directory -Path $Destination } | Out-Null

        $nmVersionedUrl = $null
        Invoke-ProgressStep -Name 'Resolve latest direct URL' -StepIndex (++$step) -TotalSteps $total -Action {
            try {
                $landing = Invoke-WebRequest -Uri 'https://www.netresec.com/?page=NetworkMiner' -UseBasicParsing -ErrorAction Stop
                $link = ($landing.Links | Where-Object { $_.href -match 'NetworkMiner_.*?\.zip$' } | Select-Object -First 1).href
                if ($link -and ($link -match '^https?://')) { $script:nmVersionedUrl = $link } else {
                    # fallback known pattern (may need update over time)
                    $script:nmVersionedUrl = 'https://www.netresec.com/?download=NetworkMiner'
                }
            } catch { $script:nmVersionedUrl = 'https://www.netresec.com/?download=NetworkMiner' }
        } | Out-Null

        Invoke-ProgressStep -Name 'Download (direct)' -StepIndex (++$step) -TotalSteps $total -Action { if (-not (Invoke-SafeDownload -Uri $script:nmVersionedUrl -OutFile $nmZip)) { throw 'Download failed' } } | Out-Null
        Invoke-ProgressStep -Name 'Extract' -StepIndex (++$step) -TotalSteps $total -Action { Expand-Zip -ZipPath $nmZip -Destination $Destination } | Out-Null
        Invoke-ProgressStep -Name 'Unblock files' -StepIndex (++$step) -TotalSteps $total -Action { Get-ChildItem -Path $Destination -Recurse -File | Unblock-File -ErrorAction SilentlyContinue } | Out-Null
        Invoke-ProgressStep -Name 'Cleanup' -StepIndex (++$step) -TotalSteps $total -Action { if (Test-Path -LiteralPath $nmZip) { Remove-Item -Path $nmZip -Force -ErrorAction SilentlyContinue } } | Out-Null
        $manualOk = $true
    } catch {
        Add-LogLine -Level Warn -Message "Manual install failed, will try Chocolatey: $($_.Exception.Message)"
        $manualOk = $false
    }

    if (-not $manualOk) {
        Invoke-ProgressStep -Name 'Try Chocolatey' -StepIndex (++$step) -TotalSteps $total -Action { $script:chocoOk = Install-ViaChocolatey -PackageName 'networkminer' } | Out-Null
        if ($script:chocoOk) {
            Invoke-ProgressStep -Name 'Locate install path' -StepIndex (++$step) -TotalSteps $total -Action {
                try {
                    $pkgInfo = choco info networkminer --exact --limit-output 2>$null
                    # Chocolatey typically installs portable packages under C:\tools or ProgramData\chocolatey\lib
                    if (Test-Path 'C:\tools\NetworkMiner') { $Destination = 'C:\tools\NetworkMiner' }
                    elseif (Test-Path 'C:\ProgramData\chocolatey\lib\networkminer') {
                        $cand = Get-ChildItem 'C:\ProgramData\chocolatey\lib\networkminer' -Recurse -Filter 'NetworkMiner.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
                        if ($cand) { $Destination = $cand.Directory.FullName }
                    }
                } catch { }
            } | Out-Null
        } else {
            Add-LogLine -Level Error -Message 'NetworkMiner installation failed (manual and Chocolatey).'
        }
    }

    # Create desktop shortcut if executable found
    $exe = Get-ChildItem -Path $Destination -Recurse -Filter 'NetworkMiner.exe' -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) {
        try {
            $desktop = [Environment]::GetFolderPath('Desktop')
            $lnkPath = Join-Path $desktop 'NetworkMiner.lnk'
            $wsh = New-Object -ComObject WScript.Shell
            $sc = $wsh.CreateShortcut($lnkPath)
            $sc.TargetPath = $exe.FullName
            $sc.WorkingDirectory = $exe.Directory.FullName
            $sc.WindowStyle = 1
            $sc.Description = 'NetworkMiner'
            $sc.Save()
            Add-LogLine -Level Success -Message "Shortcut created: $lnkPath"
        } catch { Add-LogLine -Level Warn -Message "Failed to create shortcut: $($_.Exception.Message)" }
    } else {
        Add-LogLine -Level Warn -Message 'NetworkMiner.exe not found after installation.'
    }

    Update-InstallProgress -Percent 100 -Status 'Completed' -CurrentTask ''
    Add-LogLine -Level Success -Message "$script:InstallerName installation finished."
    try { Stop-Transcript | Out-Null } catch { }
}
