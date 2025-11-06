@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Holmes VM Unified Start Script
REM - Elevates to Administrator if needed
REM - Installs Chocolatey (choco) if missing
REM - Installs Python if missing
REM - Runs bootstrap then immediately runs setup (installer)

REM Change to the script's directory
cd /d "%~dp0"

REM Optional color support to align with UI palette (teal-blue). Use only if ANSI likely works.
set "USE_COLOR="
reg query HKCU\Console /v VirtualTerminalLevel 2>nul | find /I "0x1" >nul && set "USE_COLOR=1"
if not defined USE_COLOR if defined WT_SESSION set "USE_COLOR=1"
if not defined USE_COLOR if /I "%ConEmuANSI%"=="ON" set "USE_COLOR=1"

if defined USE_COLOR (
    for /f "delims=" %%A in ('echo prompt $E^| cmd') do set "ESC=%%A"
    set "C_ACC=%ESC%[38;2;47;155;193m"    REM #2F9BC1
    set "C_SUCC=%ESC%[38;2;102;194;163m"  REM #66C2A3
    set "C_WARN=%ESC%[38;2;224;184;96m"   REM #E0B860
    set "C_ERR=%ESC%[38;2;226;122;122m"   REM #E27A7A
    set "C_MUTED=%ESC%[38;2;155;179;197m" REM #9BB3C5
    set "C_BOLD=%ESC%[1m"
    set "C_DIM=%ESC%[2m"
    set "C_RESET=%ESC%[0m"
) else (
    set "C_ACC="
    set "C_SUCC="
    set "C_WARN="
    set "C_ERR="
    set "C_MUTED="
    set "C_BOLD="
    set "C_DIM="
    set "C_RESET="
)

echo.
echo %C_ACC%=======================================================================%C_RESET%
echo   %C_BOLD%Holmes VM - Unified Start%C_RESET%
echo %C_ACC%=======================================================================%C_RESET%
echo.
echo %C_MUTED%[INFO]%C_RESET% Working directory: %CD%

REM Auto-elevate if not running as Administrator
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo.
    echo [INFO] Elevating to Administrator...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

echo %C_SUCC%[OK]%C_RESET% Running as Administrator
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
    echo %C_SUCC%[OK]%C_RESET% Chocolatey is installed
)

echo.
echo %C_MUTED%[INFO]%C_RESET% Checking Python...

REM Start with no python resolved
set "PYTHON_EXE="

REM Does a usable python.exe exist in PATH?
where python >nul 2>&1
if %errorlevel% EQU 0 (
    set "PYTHON_EXE=python"
    "%PYTHON_EXE%" --version >nul 2>&1
    if errorlevel 1 set "PYTHON_EXE="
)

REM If not found, try installing via Chocolatey in a simple, linear flow
if not defined PYTHON_EXE (
    echo %C_MUTED%[INFO]%C_RESET% Python not found, attempting to install via Chocolatey...
    choco install python -y
    set "CHOCO_EXIT=!errorlevel!"
    if "!CHOCO_EXIT!"=="0" (
    echo %C_SUCC%[OK]%C_RESET% Python installed successfully
    ) else (
        if "!CHOCO_EXIT!"=="3010" (
            echo %C_SUCC%[OK]%C_RESET% Python installed ^(reboot recommended, continuing^)
        ) else (
            echo %C_WARN%[WARNING]%C_RESET% 'choco install python' failed ^(exit code: !CHOCO_EXIT!^). Trying 'python3'...
            choco install python3 -y
            set "CHOCO_EXIT=!errorlevel!"
            if "!CHOCO_EXIT!"=="0" (
                echo %C_SUCC%[OK]%C_RESET% Python3 installed successfully
            ) else (
                if "!CHOCO_EXIT!"=="3010" (
                    echo %C_SUCC%[OK]%C_RESET% Python3 installed ^(reboot recommended, continuing^)
                ) else (
                    echo %C_ERR%[ERROR]%C_RESET% Failed to install Python ^(exit code: !CHOCO_EXIT!^)
                    rem Do not abort here; we'll verify availability below and abort only if truly missing
                )
            )
        )
    )
)

REM Try common Chocolatey shim locations and 'where' again
if not defined PYTHON_EXE (
    if exist "C:\ProgramData\chocolatey\bin\python.exe" set "PYTHON_EXE=C:\ProgramData\chocolatey\bin\python.exe"
)
if not defined PYTHON_EXE (
    for %%P in (C:\ProgramData\chocolatey\bin\python3*.exe) do if exist "%%~fP" set "PYTHON_EXE=%%~fP"
)
if not defined PYTHON_EXE (
    where python >nul 2>&1
    if %errorlevel% EQU 0 (
        set "PYTHON_EXE=python"
        "%PYTHON_EXE%" --version >nul 2>&1
        if errorlevel 1 set "PYTHON_EXE="
    )
)

REM Try Python Launcher as a fallback if python.exe not resolved
set "USE_PY_LAUNCHER="
py -3 --version >nul 2>&1
if %errorlevel% EQU 0 set "USE_PY_LAUNCHER=1"

if not defined PYTHON_EXE (
    if not defined USE_PY_LAUNCHER (
        echo [ERROR] Could not locate Python after installation.
        echo        Please close this window and run the script again.
        call :HANG 1
    )
)

if defined PYTHON_EXE (
    echo %C_SUCC%[OK]%C_RESET% Using Python: %PYTHON_EXE%
    "%PYTHON_EXE%" --version
) else if defined USE_PY_LAUNCHER (
    echo %C_SUCC%[OK]%C_RESET% Using Python Launcher: py -3
    py -3 --version
)

echo.
echo %C_ACC%=======================================================================%C_RESET%
echo   %C_BOLD%Running bootstrap.py%C_RESET%
echo %C_ACC%=======================================================================%C_RESET%
echo.
if defined USE_PY_LAUNCHER (
    py -3 -m holmes_vm.bootstrap
) else (
    "%PYTHON_EXE%" -m holmes_vm.bootstrap
)
set "BOOTSTRAP_EXIT=%errorlevel%"
echo %C_DIM%[DEBUG] Bootstrap exit code: %BOOTSTRAP_EXIT%%C_RESET%
if not "%BOOTSTRAP_EXIT%"=="0" (
    echo %C_ERR%[ERROR]%C_RESET% Bootstrap failed.
    call :HANG %BOOTSTRAP_EXIT%
)

echo.
echo %C_ACC%=======================================================================%C_RESET%
echo   %C_BOLD%Running setup.py (installer)%C_RESET%
echo %C_ACC%=======================================================================%C_RESET%
echo.
if defined USE_PY_LAUNCHER (
    py -3 -m holmes_vm.setup
) else (
    "%PYTHON_EXE%" -m holmes_vm.setup
)
set "SETUP_EXIT=%errorlevel%"
echo %C_DIM%[DEBUG] Setup exit code: %SETUP_EXIT%%C_RESET%

if "%SETUP_EXIT%"=="0" (
    echo.
    echo %C_ACC%=======================================================================%C_RESET%
    echo   %C_SUCC%Setup Finished Successfully!%C_RESET%
    echo %C_ACC%=======================================================================%C_RESET%
) else (
    echo.
    echo %C_ACC%=======================================================================%C_RESET%
    echo   %C_ERR%Setup Failed with exit code: %SETUP_EXIT%%C_RESET%
    echo %C_ACC%=======================================================================%C_RESET%
)

call :HANG %SETUP_EXIT%

:HANG
echo.
echo %C_ACC%=======================================================================%C_RESET%
echo   %C_MUTED%Script is holding (exit code: %~1)%C_RESET%
echo   %C_MUTED%Close this window, or press any key to exit.%C_RESET%
echo %C_ACC%=======================================================================%C_RESET%
echo.
set "_exit=%~1"
if not defined _exit set "_exit=1"
echo Press any key to exit...
pause >nul
endlocal & exit /b %_exit%
