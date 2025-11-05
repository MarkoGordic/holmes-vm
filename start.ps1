# Holmes VM Quick Start (PowerShell)
# This script checks prerequisites and runs the bootstrap

$ErrorActionPreference = 'Stop'

# Change to the script's directory
Set-Location -Path $PSScriptRoot

function Write-Header {
    param([string]$Text)
    Write-Host "`n$('=' * 70)"
    Write-Host "  $Text"
    Write-Host "$('=' * 70)`n"
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text"
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "[ERROR] $Text"
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "[WARNING] $Text"
}

function Write-Info {
    param([string]$Text)
    Write-Host "  -> $Text"
}

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Header "Holmes VM - Quick Start"

Write-Success "Working directory: $PWD"
Write-Host ""

if (-not $isAdmin) {
    Write-Warning-Custom "Not running as Administrator!"
    Write-Host ""
    Write-Host "Holmes VM requires Administrator privileges."
    Write-Host "Please run PowerShell as Administrator and try again."
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'"
    Write-Host ""
    pause
    exit 1
}

Write-Success "Running as Administrator"
Write-Host ""

# Check and install Chocolatey if needed
try {
    $null = Get-Command choco -ErrorAction Stop
    Write-Success "Chocolatey is installed"
} catch {
    Write-Info "Chocolatey not found, installing..."
    Write-Host ""
    
    try {
        # Install Chocolatey
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        Write-Host ""
        Write-Success "Chocolatey installed successfully"
        Write-Info "Updating PATH for current session..."
        
        # Manually update PATH for current session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # Verify choco is now available
        $null = Get-Command choco -ErrorAction Stop
        Write-Success "Chocolatey is ready to use"
    } catch {
        Write-Host ""
        Write-Error-Custom "Failed to verify Chocolatey installation!"
        Write-Info "Chocolatey was installed but may not be in PATH yet."
        Write-Info "Please close this window and run the script again."
        Write-Host ""
        pause
        exit 1
    }
}

Write-Host ""

# Check and install Python if needed
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python is installed: $pythonVersion"
} catch {
    Write-Info "Python not found, installing via Chocolatey..."
    Write-Host ""
    
    # Install Python via Chocolatey
    choco install python -y
    $exitCode = $LASTEXITCODE
    
    Write-Host ""
    
    # Exit codes: 0 = success, 3010 = success but reboot required
    if ($exitCode -eq 0) {
        Write-Success "Python installed successfully"
    } elseif ($exitCode -eq 3010) {
        Write-Success "Python installed successfully (reboot recommended but not required)"
    } else {
        Write-Error-Custom "Failed to install Python (exit code: $exitCode)"
        Write-Host ""
        Write-Info "Please install manually from: https://www.python.org/downloads/"
        Write-Host ""
        pause
        exit 1
    }
    
    Write-Info "Refreshing environment variables..."
    
    # Manually refresh PATH for Python
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Verify Python is now available
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python is ready to use: $pythonVersion"
        $script:UsePythonShim = $false
        $script:PythonCmd = "python"
    } catch {
        Write-Warning-Custom "Python installed but not immediately available in PATH"
        Write-Info "Trying alternative methods..."
        
        # Try using the choco shim
        try {
            $pythonVersion = & "C:\ProgramData\chocolatey\bin\python3.14.exe" --version 2>&1
            Write-Success "Python is available via Chocolatey shim: $pythonVersion"
            $script:UsePythonShim = $true
            $script:PythonCmd = "C:\ProgramData\chocolatey\bin\python3.14.exe"
        } catch {
            Write-Error-Custom "Python installed but cannot be found. Please reboot and try again."
            Write-Host ""
            pause
            exit 1
        }
    }
}

Write-Host ""
Write-Host "Running bootstrap script..."
Write-Host ""

# Run the bootstrap script
$bootstrapSuccess = $false
try {
    if ($script:UsePythonShim) {
        Write-Host "[DEBUG] Using Python shim: $($script:PythonCmd)"
        & $script:PythonCmd bootstrap.py
    } else {
        Write-Host "[DEBUG] Using system Python"
        python bootstrap.py
    }
    
    $bootstrapExitCode = $LASTEXITCODE
    Write-Host "[DEBUG] Bootstrap exit code: $bootstrapExitCode"
    
    if ($bootstrapExitCode -eq 0) {
        $bootstrapSuccess = $true
    } else {
        throw "Bootstrap script failed with exit code $bootstrapExitCode"
    }
} catch {
    Write-Host ""
    Write-Error-Custom "Bootstrap failed!"
    Write-Info "Error: $_"
    Write-Host ""
    Write-Host "Press any key to exit..."
    pause
    exit 1
}

if (-not $bootstrapSuccess) {
    Write-Host ""
    Write-Error-Custom "Bootstrap did not complete successfully"
    Write-Host ""
    Write-Host "Press any key to exit..."
    pause
    exit 1
}

# Ask if user wants to run setup now
Write-Host ""
Write-Header "Bootstrap Complete!"

$response = Read-Host "Do you want to run Holmes VM setup now? (Y/N)"

if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "Starting Holmes VM Setup..."
    Write-Host ""
    
    $setupSuccess = $false
    try {
        if ($script:UsePythonShim) {
            Write-Host "[DEBUG] Using Python shim for setup"
            & $script:PythonCmd setup.py
        } else {
            Write-Host "[DEBUG] Using system Python for setup"
            python setup.py
        }
        
        $setupExitCode = $LASTEXITCODE
        Write-Host "[DEBUG] Setup exit code: $setupExitCode"
        
        if ($setupExitCode -eq 0) {
            $setupSuccess = $true
        } else {
            Write-Host ""
            Write-Error-Custom "Setup failed with exit code: $setupExitCode"
        }
    } catch {
        Write-Host ""
        Write-Error-Custom "Setup failed!"
        Write-Info "Error: $_"
    }
    
    Write-Host ""
    if ($setupSuccess) {
        Write-Header "Setup Finished Successfully!"
    } else {
        Write-Host "========================================================================"
        Write-Host "  Setup Failed!"
        Write-Host "========================================================================"
        Write-Host ""
        Write-Host "Please check the error messages above."
    }
} else {
    Write-Host ""
    Write-Info "You can run the setup later with:"
    if ($script:UsePythonShim) {
        Write-Info "  $($script:PythonCmd) setup.py"
    } else {
        Write-Info "  python setup.py"
    }
    Write-Host ""
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
exit 0
