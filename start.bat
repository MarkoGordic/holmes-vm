@echo off
setlocal EnableDelayedExpansion

REM Holmes VM Quick Start Script
REM This script installs Chocolatey and Python, then runs bootstrap

REM Change to the script's directory
cd /d "%~dp0"

REM Disable any weird behaviors
set ERRORLEVEL=

echo.
echo ========================================================================
echo   Holmes VM - Quick Start
echo ========================================================================
echo.
echo [INFO] Script is starting...
echo [INFO] Working directory: %CD%
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
) else (
    echo [WARNING] Not running as Administrator!
    echo.
    echo Holmes VM requires Administrator privileges.
    echo Please right-click this file and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo.

REM Check and install Chocolatey if needed
where choco >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Chocolatey is installed
) else (
    echo [INFO] Chocolatey not found, installing...
    echo.
    
    REM Install Chocolatey
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    
    echo.
    echo [OK] Chocolatey installed successfully
    echo [INFO] Updating PATH for current session...
    
    REM Manually update PATH for current session
    set "PATH=%PATH%;C:\ProgramData\chocolatey\bin"
    
    REM Verify choco is now available
    where choco >nul 2>&1
    if %errorLevel% NEQ 0 (
        echo [ERROR] Chocolatey installed but not found in PATH!
        echo Please close this window and run the script again.
        pause
        exit /b 1
    )
)

echo.

REM Check and install Python if needed
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python is installed
    python --version
) else (
    echo [INFO] Python not found, installing via Chocolatey...
    echo.
    
    REM Install Python via Chocolatey
    choco install python -y
    
    REM Exit codes: 0 = success, 3010 = success but reboot required
    if %errorLevel% == 0 (
        echo.
        echo [OK] Python installed successfully
    ) else if %errorLevel% == 3010 (
        echo.
        echo [OK] Python installed successfully (reboot recommended but not required)
    ) else (
        echo.
        echo [ERROR] Failed to install Python (exit code: %errorLevel%)
        echo.
        echo Please install manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo [INFO] Refreshing environment variables...
    
    REM Manually refresh PATH for Python
    set "PATH=%PATH%;C:\Python314;C:\Python314\Scripts"
    set "PATH=%PATH%;C:\ProgramData\chocolatey\bin"
    
    REM Verify Python is now available
    python --version >nul 2>&1
    if %errorLevel% NEQ 0 (
        echo [WARNING] Python installed but not immediately available in PATH
        echo [INFO] Trying alternative methods...
        
        REM Try using the choco shim
        C:\ProgramData\chocolatey\bin\python3.14.exe --version >nul 2>&1
        if %errorLevel% == 0 (
            echo [OK] Python is available via Chocolatey shim
            echo [INFO] Creating alias for this session...
            
            REM Create a doskey alias for this session
            doskey python=C:\ProgramData\chocolatey\bin\python3.14.exe $*
            
            REM Set a variable to track we're using the shim
            set USE_PYTHON_SHIM=1
        ) else (
            echo [ERROR] Python installed but cannot be found. Please reboot and try again.
            pause
            exit /b 1
        )
    ) else (
        echo [OK] Python is ready to use
        python --version
        set USE_PYTHON_SHIM=0
    )
)

echo.
echo Running bootstrap script...
echo.

REM Run the bootstrap script using appropriate Python command
if "%USE_PYTHON_SHIM%"=="1" (
    echo [DEBUG] Using Python shim: C:\ProgramData\chocolatey\bin\python3.14.exe
    C:\ProgramData\chocolatey\bin\python3.14.exe bootstrap.py
    set BOOTSTRAP_EXIT=!errorLevel!
) else (
    echo [DEBUG] Using system Python
    python bootstrap.py
    set BOOTSTRAP_EXIT=!errorLevel!
)

echo [DEBUG] Bootstrap exit code: !BOOTSTRAP_EXIT!

if !BOOTSTRAP_EXIT! == 0 (
    echo.
    echo ========================================================================
    echo   Bootstrap Complete!
    echo ========================================================================
    echo.
    echo Ready to run Holmes VM setup.
    echo.
    choice /C YN /M "Do you want to run the setup now"
    if errorlevel 2 goto :skip_setup
    if errorlevel 1 goto :run_setup
) else (
    echo.
    echo [ERROR] Bootstrap failed with exit code: !BOOTSTRAP_EXIT!
    echo Please check the error messages above.
    echo.
    echo Press any key to exit...
    pause
    exit /b !BOOTSTRAP_EXIT!
)

:run_setup
echo.
echo Starting Holmes VM Setup...
echo.
if "%USE_PYTHON_SHIM%"=="1" (
    echo [DEBUG] Using Python shim for setup
    C:\ProgramData\chocolatey\bin\python3.14.exe setup.py
    set SETUP_EXIT=!errorLevel!
) else (
    echo [DEBUG] Using system Python for setup
    python setup.py
    set SETUP_EXIT=!errorLevel!
)

echo [DEBUG] Setup exit code: !SETUP_EXIT!

if !SETUP_EXIT! == 0 (
    echo.
    echo ========================================================================
    echo   Setup Finished Successfully!
    echo ========================================================================
    echo.
) else (
    echo.
    echo ========================================================================
    echo   Setup Failed with exit code: !SETUP_EXIT!
    echo ========================================================================
    echo.
)
goto :end

:skip_setup
echo.
echo You can run the setup later with:
if "%USE_PYTHON_SHIM%"=="1" (
    echo   C:\ProgramData\chocolatey\bin\python3.14.exe setup.py
) else (
    echo   python setup.py
)
echo.

:end
echo.
echo ========================================================================
echo   Script execution completed
echo ========================================================================
echo.
echo If the setup didn't run, please check the error messages above.
echo.
echo Press any key to exit...
pause >nul
endlocal
exit /b 0
