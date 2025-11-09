try { if (-not (Get-Command Write-Log -ErrorAction SilentlyContinue)) { $commonPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'modules/Holmes.Common.psm1'; if (Test-Path -LiteralPath $commonPath) { Import-Module $commonPath -ErrorAction SilentlyContinue } } } catch { }
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }

$script:InstallerName = "Eric Zimmerman's Tools"
$script:LogDirDefault = Join-Path $env:ProgramData 'HolmesVM/Logs'
$script:LogFilePath = $null

function Initialize-Logging { [CmdletBinding()] param([string]$LogDir) try { if (-not $LogDir) { $LogDir = $script:LogDirDefault } if (-not (Test-Path -LiteralPath $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null } $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'; $script:LogFilePath = Join-Path $LogDir ("EZTools-install-$timestamp.log"); try { Start-Transcript -Path $script:LogFilePath -Append -ErrorAction Stop | Out-Null } catch { } } catch { } }

function Add-LogLine { [CmdletBinding()] param([Parameter(Mandatory)][ValidateSet('Info','Warn','Error','Success')][string]$Level,[Parameter(Mandatory)][string]$Message) $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'; try { if ($script:LogFilePath) { Add-Content -Path $script:LogFilePath -Value "[$ts] [$($Level.ToUpper())] $Message" -ErrorAction SilentlyContinue } } catch { } try { if (Get-Command Write-Log -ErrorAction SilentlyContinue) { Write-Log -Level $Level -Message $Message } else { Write-Host $Message } } catch { } }

function Update-InstallProgress { [CmdletBinding()] param([Parameter(Mandatory)][int]$Percent,[Parameter(Mandatory)][string]$Status,[string]$CurrentTask) $activity = "Installing $script:InstallerName"; $statusMsg = if ($CurrentTask) { "$Status - $CurrentTask" } else { $Status }; try { Write-Progress -Activity $activity -Status $statusMsg -PercentComplete $Percent } catch { } }

function Invoke-ProgressStep { [CmdletBinding()] param([Parameter(Mandatory)][string]$Name,[Parameter(Mandatory)][scriptblock]$Action,[Parameter(Mandatory)][int]$StepIndex,[Parameter(Mandatory)][int]$TotalSteps,[switch]$ContinueOnError) $percent = [int](($StepIndex / [double]$TotalSteps) * 100); Update-InstallProgress -Percent $percent -Status "Working ($StepIndex/$TotalSteps)" -CurrentTask $Name; Add-LogLine -Level Info -Message "$Name..."; try { & $Action; Add-LogLine -Level Success -Message "$Name completed."; return $true } catch { Add-LogLine -Level Error -Message "$Name failed: $($_.Exception.Message)"; if ($ContinueOnError) { return $false } throw } }

function New-MinimalInstallerWindow { throw 'Per-installer GUI was removed. Use setup.ps1 unified GUI.' }
function Start-EZToolsInstaller { throw 'Per-installer GUI was removed. Use setup.ps1 unified GUI.' }

function Ensure-Directory { param([Parameter(Mandatory)][string]$Path) if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }

function Add-PathIfMissing { [CmdletBinding()] param([Parameter(Mandatory)][string]$Path,[ValidateSet('Machine','User')][string]$Scope='Machine') try { $target = if ($Scope -eq 'Machine') { 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment' } else { 'HKCU:\Environment' }; $cur = (Get-ItemProperty -Path $target -Name Path -ErrorAction SilentlyContinue).Path; if ($cur -notmatch [regex]::Escape($Path)) { $new = if ($cur) { "$cur;$Path" } else { $Path }; Set-ItemProperty -Path $target -Name Path -Value $new } } catch { } }

function Expand-Zip { param([Parameter(Mandatory)][string]$ZipPath,[Parameter(Mandatory)][string]$Destination) Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force }

function Invoke-SafeDownload { [CmdletBinding()] param([Parameter(Mandatory)][string]$Uri,[Parameter(Mandatory)][string]$OutFile) try { Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing -ErrorAction Stop; return $true } catch { try { (New-Object System.Net.WebClient).DownloadFile($Uri,$OutFile); return $true } catch { return $false } } }

function Install-EZTools {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$Destination = 'C:\\Tools\\EricZimmermanTools',[int]$NetVersion = 0,[string]$LogDir,[string]$ShortcutCategory,[switch]$SkipShortcuts)
    Initialize-Logging -LogDir $LogDir
    Add-LogLine -Level Info -Message "Starting installation of $script:InstallerName"
    if (-not $PSCmdlet.ShouldProcess($Destination, "Install $script:InstallerName")) { Add-LogLine -Level Info -Message "WhatIf: Would install $script:InstallerName to $Destination (Net=$NetVersion)"; return }
    $total = 9
    $step = 0
    $ezToolsDir = $Destination
    $ezToolsZip = Join-Path $env:TEMP 'Get-ZimmermanTools.zip'
    $ezToolsScript = Join-Path $ezToolsDir 'Get-ZimmermanTools.ps1'
    $ezToolsNet4Dir = Join-Path $ezToolsDir 'net4'
    $ezToolsNet6Dir = Join-Path $ezToolsDir 'net6'
    $ezToolsNet9Dir = Join-Path $ezToolsDir 'net9'
    $desktopRoot = Join-Path $env:USERPROFILE 'Desktop'
    $desktopShortcutDir = if ($PSBoundParameters.ContainsKey('ShortcutCategory') -and $ShortcutCategory) { Join-Path $desktopRoot $ShortcutCategory } else { Join-Path $desktopRoot 'EricZimmermanTools' }

    Invoke-ProgressStep -Name 'Check OS and Admin' -StepIndex (++$step) -TotalSteps $total -Action { if (Get-Command Assert-WindowsAndAdmin -ErrorAction SilentlyContinue) { Assert-WindowsAndAdmin } else { Add-LogLine -Level Warn -Message 'Common module not loaded; proceeding without explicit admin check.' } } | Out-Null
    Invoke-ProgressStep -Name 'Prepare directories' -StepIndex (++$step) -TotalSteps $total -Action { Ensure-Directory -Path $ezToolsDir; Ensure-Directory -Path $desktopShortcutDir } | Out-Null
    Invoke-ProgressStep -Name 'Download updater' -StepIndex (++$step) -TotalSteps $total -Action { Invoke-SafeDownload -Uri 'https://f001.backblazeb2.com/file/EricZimmermanTools/Get-ZimmermanTools.zip' -OutFile $ezToolsZip | Out-Null } | Out-Null
    Invoke-ProgressStep -Name 'Extract updater' -StepIndex (++$step) -TotalSteps $total -Action { Expand-Zip -ZipPath $ezToolsZip -Destination $ezToolsDir; if (Test-Path -LiteralPath $ezToolsScript) { Unblock-File -Path $ezToolsScript } } | Out-Null
    Invoke-ProgressStep -Name 'Run updater' -StepIndex (++$step) -TotalSteps $total -Action { Push-Location $ezToolsDir; try { if ($PSCmdlet.ShouldProcess('Get-ZimmermanTools.ps1','Execute')) { .\Get-ZimmermanTools.ps1 -Dest $ezToolsDir -NetVersion $NetVersion } } finally { Pop-Location } } | Out-Null
    Invoke-ProgressStep -Name 'Add base PATH' -StepIndex (++$step) -TotalSteps $total -Action { if (Test-Path -LiteralPath $ezToolsDir) { Add-PathIfMissing -Path $ezToolsDir -Scope Machine } } | Out-Null
    Invoke-ProgressStep -Name 'Add net PATHs' -StepIndex (++$step) -TotalSteps $total -Action { $netDirs = @(); if (Test-Path -LiteralPath $ezToolsNet4Dir) { $netDirs += $ezToolsNet4Dir }; if (Test-Path -LiteralPath $ezToolsNet6Dir) { $netDirs += $ezToolsNet6Dir }; if (Test-Path -LiteralPath $ezToolsNet9Dir) { $netDirs += $ezToolsNet9Dir }; if ($netDirs.Count -eq 0) { Add-LogLine -Level Warn -Message "No net-specific directories found under $ezToolsDir (expected net4/net6/net9)." }; foreach ($dir in $netDirs) { Add-PathIfMissing -Path $dir -Scope Machine; Add-LogLine -Level Success -Message "Added to PATH: $dir" } } | Out-Null
    Invoke-ProgressStep -Name 'Create only foldered shortcuts' -StepIndex (++$step) -TotalSteps $total -Action {
        if (-not $SkipShortcuts) {
            $priorityDirs = @(); if (Test-Path -LiteralPath $ezToolsNet9Dir) { $priorityDirs += $ezToolsNet9Dir }; if (Test-Path -LiteralPath $ezToolsNet6Dir) { $priorityDirs += $ezToolsNet6Dir }; if (Test-Path -LiteralPath $ezToolsNet4Dir) { $priorityDirs += $ezToolsNet4Dir }
            $seen = @{}
            $shell = New-Object -ComObject WScript.Shell
            foreach ($p in $priorityDirs) {
                Get-ChildItem -Path $p -Recurse -Filter '*.exe' -File -ErrorAction SilentlyContinue | ForEach-Object {
                    $name = $_.Name
                    if (-not $seen.ContainsKey($name)) {
                        $lnk = Join-Path $desktopShortcutDir ($name + '.lnk')
                        $sc = $shell.CreateShortcut($lnk)
                        $sc.TargetPath = $_.FullName
                        $sc.WorkingDirectory = $_.Directory.FullName
                        $sc.WindowStyle = 1
                        $sc.Description = $_.BaseName
                        $sc.Save()
                        $seen[$name] = $true
                    }
                }
            }
        }
    } | Out-Null
    Invoke-ProgressStep -Name 'Cleanup' -StepIndex (++$step) -TotalSteps $total -Action { if (Test-Path -LiteralPath $ezToolsZip) { Remove-Item -Path $ezToolsZip -Force -ErrorAction SilentlyContinue } } | Out-Null
    Update-InstallProgress -Percent 100 -Status 'Completed' -CurrentTask ''
    Add-LogLine -Level Success -Message "Installation finished."
    if (-not $SkipShortcuts) { Add-LogLine -Level Success -Message "Shortcuts created in $desktopShortcutDir." }
    try { Stop-Transcript | Out-Null } catch { }
}
