@echo off
REM EMERGENCY DEBUG VERSION - Simple and verbose
REM Use this if start.bat closes immediately

REM Change to the script's directory FIRST!
cd /d "%~dp0"

echo.
echo ========================================================================
echo   Holmes VM - DEBUG MODE
echo ========================================================================
echo.

REM Test 1: Check if we're in the right directory
echo [TEST 1] Script directory changed to:
cd
echo.

REM Test 2: Check if files exist
echo [TEST 2] Checking for required files...
if exist "bootstrap.py" (
    echo [OK] bootstrap.py found
) else (
    echo [ERROR] bootstrap.py NOT FOUND!
    pause
    exit /b 1
)

if exist "setup.py" (
    echo [OK] setup.py found
) else (
    echo [ERROR] setup.py NOT FOUND!
    pause
    exit /b 1
)
echo.

REM Test 3: Check for Python
echo [TEST 3] Checking for Python...
python --version 2>nul
if %errorLevel% == 0 (
    echo [OK] Python is available
    python --version
) else (
    echo [WARNING] Python not found in PATH
    echo.
    echo Trying to install Python via Chocolatey...
    
    REM Check for Chocolatey
    where choco >nul 2>&1
    if %errorLevel% == 0 (
        echo [OK] Chocolatey is available
        echo Installing Python...
        choco install python -y
        
        echo.
        echo Python installation complete. Trying to use it...
        set "PATH=%PATH%;C:\Python314;C:\Python314\Scripts;C:\ProgramData\chocolatey\bin"
        
        python --version 2>nul
        if %errorLevel% == 0 (
            echo [OK] Python is now available
        ) else (
            echo [WARNING] Python installed but not in PATH yet
            echo Please close this window and run the script again.
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] Chocolatey is not available
        echo Please run start.bat to install prerequisites first
        pause
        exit /b 1
    )
)
echo.

REM Test 4: Try running bootstrap
echo [TEST 4] Running bootstrap.py...
echo.
python bootstrap.py
set BOOTSTRAP_EXIT=%errorLevel%
echo.
echo [DEBUG] Bootstrap exit code: %BOOTSTRAP_EXIT%
if %BOOTSTRAP_EXIT% NEQ 0 (
    echo [ERROR] Bootstrap failed!
    pause
    exit /b 1
)
echo.

REM Test 5: Ask to run setup
echo [TEST 5] Ready to run setup
echo.
choice /C YN /M "Do you want to run the setup now"
if errorlevel 2 goto :end

echo.
echo Running setup.py...
echo.
python setup.py
set SETUP_EXIT=%errorLevel%
echo.
echo [DEBUG] Setup exit code: %SETUP_EXIT%

:end
echo.
echo ========================================================================
echo   Debug script complete
echo ========================================================================
echo.
echo Press any key to exit...
pause >nul
