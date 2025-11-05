@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Holmes VM Unified Start Script
REM - Elevates to Administrator if needed
REM - Installs Chocolatey (choco) if missing
REM - Installs Python if missing
REM - Runs bootstrap then immediately runs setup (installer)

REM Change to the script's directory
cd /d "%~dp0"

echo.
echo ========================================================================
echo   Holmes VM - Unified Start
echo ========================================================================
echo.
echo [INFO] Working directory: %CD%

REM Auto-elevate if not running as Administrator
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo.
    echo [INFO] Elevating to Administrator...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

echo [OK] Running as Administrator
echo.

REM Ensure PowerShell can run our one-liners
reg add HKLM\SOFTWARE\Microsoft\PowerShell\1\ShellIds\Microsoft.PowerShell /v ExecutionPolicy /t REG_SZ /d Unrestricted /f >nul 2>&1

REM Install Chocolatey if needed
where choco >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [INFO] Chocolatey not found, installing...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" || (
        echo [ERROR] Failed to install Chocolatey.
        echo        Please check your internet connection and try again.
        call :HANG 1
    )
    set "PATH=%PATH%;C:\ProgramData\chocolatey\bin"
) else (
    echo [OK] Chocolatey is installed
)

echo.
echo [INFO] Checking Python...

set "PYTHON_EXE="
where python >nul 2>&1 && set "PYTHON_EXE=python"

REM Validate that resolved python actually runs (avoid WindowsApps alias)
if defined PYTHON_EXE (
    "%PYTHON_EXE%" --version >nul 2>&1
    if errorlevel 1 (
        set "PYTHON_EXE="
    )
)

if not defined PYTHON_EXE (
    echo [INFO] Python not found, installing via Chocolatey...
    choco install python -y
    set "CHOCO_EXIT=!errorlevel!"
    if "!CHOCO_EXIT!"=="3010" (
        echo [OK] Python installed (reboot recommended, continuing)
    ) else if not "!CHOCO_EXIT!"=="0" (
        echo [WARNING] 'choco install python' failed (exit code: !CHOCO_EXIT!). Trying 'python3'...
        choco install python3 -y
        set "CHOCO_EXIT=!errorlevel!"
        if "!CHOCO_EXIT!"=="3010" (
            echo [OK] Python3 installed (reboot recommended, continuing)
        ) else if not "!CHOCO_EXIT!"=="0" (
            echo [ERROR] Failed to install Python (exit code: !CHOCO_EXIT!)
            call :HANG !CHOCO_EXIT!
        ) else (
            echo [OK] Python3 installed successfully
        )
    ) else (
        echo [OK] Python installed successfully
    )

    REM end of python install attempt
)

REM Try common Chocolatey shim locations (outside previous parentheses to avoid parser issues)
if not defined PYTHON_EXE (
    if exist "C:\ProgramData\chocolatey\bin\python.exe" set "PYTHON_EXE=C:\ProgramData\chocolatey\bin\python.exe"
)
if not defined PYTHON_EXE (
    for %%P in (C:\ProgramData\chocolatey\bin\python3*.exe) do if exist "%%~fP" set "PYTHON_EXE=%%~fP"
)
if not defined PYTHON_EXE (
    REM Last attempt: use whatever 'python' resolves to now
    where python >nul 2>&1 && set "PYTHON_EXE=python"
    REM Validate again to avoid picking the WindowsApps alias stub
    if defined PYTHON_EXE (
        "%PYTHON_EXE%" --version >nul 2>&1
        if errorlevel 1 set "PYTHON_EXE="
    )
)

REM Try Python Launcher as a fallback if python.exe not resolved
set "USE_PY_LAUNCHER="
if not defined PYTHON_EXE (
    py -3 --version >nul 2>&1
    if !errorlevel! EQU 0 set "USE_PY_LAUNCHER=1"
)

if not defined PYTHON_EXE (
    if not defined USE_PY_LAUNCHER (
        echo [ERROR] Could not locate Python after installation.
        echo        Please close this window and run the script again.
        call :HANG 1
    )
)

if defined USE_PY_LAUNCHER (
    echo [OK] Using Python Launcher: py -3
    py -3 --version
)
if defined PYTHON_EXE (
    echo [OK] Using Python: %PYTHON_EXE%
    "%PYTHON_EXE%" --version
)

echo.
echo ========================================================================
echo   Running bootstrap.py
echo ========================================================================
echo.
if defined USE_PY_LAUNCHER (
    py -3 holmes_vm\bootstrap.py
) else (
    "%PYTHON_EXE%" holmes_vm\bootstrap.py
)
set "BOOTSTRAP_EXIT=%errorlevel%"
echo [DEBUG] Bootstrap exit code: %BOOTSTRAP_EXIT%
if not "%BOOTSTRAP_EXIT%"=="0" (
    echo [ERROR] Bootstrap failed.
    call :HANG %BOOTSTRAP_EXIT%
)

echo.
echo ========================================================================
echo   Running setup.py (installer)
echo ========================================================================
echo.
if defined USE_PY_LAUNCHER (
    py -3 holmes_vm\setup.py
) else (
    "%PYTHON_EXE%" holmes_vm\setup.py
)
set "SETUP_EXIT=%errorlevel%"
echo [DEBUG] Setup exit code: %SETUP_EXIT%

if "%SETUP_EXIT%"=="0" (
    echo.
    echo ========================================================================
    echo   Setup Finished Successfully!
    echo ========================================================================
) else (
    echo.
    echo ========================================================================
    echo   Setup Failed with exit code: %SETUP_EXIT%
    echo ========================================================================
)

call :HANG %SETUP_EXIT%

:HANG
echo.
echo ========================================================================
echo   Script is holding (exit code: %~1)
echo   Close this window, or press any key to exit.
echo ========================================================================
echo.
timeout /t -1 >nul
endlocal
exit /b %~1
