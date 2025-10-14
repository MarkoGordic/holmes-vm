@echo off
REM Wrapper to ensure window stays open
REM This calls the actual start.bat and catches any errors

REM Change to the script's directory
cd /d "%~dp0"

echo Starting Holmes VM Setup...
echo Working directory: %CD%
echo.

REM Call the actual start script
call "%~dp0start.bat"

REM Capture the exit code
set EXIT_CODE=%errorLevel%

echo.
echo.
echo ========================================================================
if %EXIT_CODE% == 0 (
    echo   Script completed with exit code: %EXIT_CODE% ^(SUCCESS^)
) else (
    echo   Script completed with exit code: %EXIT_CODE% ^(ERROR^)
)
echo ========================================================================
echo.
echo This window will stay open so you can see any errors.
echo Press any key to close...
pause >nul
exit /b %EXIT_CODE%
