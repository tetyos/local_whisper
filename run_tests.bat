@echo off
setlocal

REM Enable delayed expansion
setlocal enabledelayedexpansion

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found! Please run run_dev.bat first to set up the environment.
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo ========================================================
echo Installing/Updating Test Dependencies...
echo ========================================================
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo Running Test Suite...
echo ========================================================
echo.

REM Run pytest with verbose output and coverage
pytest src/tests/ -v --cov=src/local_whisper --cov-report=term-missing --cov-report=html

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo ALL TESTS PASSED!
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo TESTS FAILED!
    echo ========================================================
)

REM Deactivate virtual environment
call deactivate

endlocal

