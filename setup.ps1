Write-Host "==== Artemis VM: Blue Team Swiss Knife ====" -ForegroundColor Magenta

# Ensure running as Administrator
If (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "Please run this script as Administrator."
    exit 1
}

# Check for Chocolatey
if (-not (Get-Command choco.exe -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey..." -ForegroundColor Magenta
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')) > $null 2>&1
    # Wait briefly for choco.exe to be available
    Start-Sleep -Seconds 3
}

# After install attempt, check again
if (-not (Get-Command choco.exe -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey installation failed. Exiting." -ForegroundColor Red
    exit 2
}
else {
    Write-Host "Chocolatey is ready!" -ForegroundColor Green
}

Write-Host "Installing Wireshark..." -ForegroundColor Magenta
choco install wireshark -y > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Wireshark installed successfully!" -ForegroundColor Green
}
else {
    Write-Host "Wireshark installation failed." -ForegroundColor Red
}

Write-Host "Installing .NET 6.0 Desktop Runtime..." -ForegroundColor Magenta
choco install dotnet-6.0-desktopruntime -y > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host ".NET 6.0 Desktop Runtime installed successfully!" -ForegroundColor Green
}
else {
    Write-Host "Failed to install .NET 6.0 Desktop Runtime." -ForegroundColor Red
}

Write-Host "Installing DnSpyEx..." -ForegroundColor Magenta
choco install dnspyex -y > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "DnSpyEx installed successfully!" -ForegroundColor Green
}
else {
    Write-Host "DnSpyEx installation failed." -ForegroundColor Red
}

Write-Host "Installing PeStudio..." -ForegroundColor Magenta
choco install pestudio -y > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "PeStudio installed successfully!" -ForegroundColor Green
}
else {
    Write-Host "PeStudio installation failed." -ForegroundColor Red
}

# Dot-source the utility script and call the function
. "$PSScriptRoot\util\install-eztools.ps1"
Install-EZTools

# Install RegRipper
. "$PSScriptRoot\util\install-regripper.ps1"
Install-RegRipper

Write-Host "`nSetup complete! Welcome to Artemis VM!" -ForegroundColor Magenta
