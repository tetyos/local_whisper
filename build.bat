@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

echo ========================================
echo Building Local Whisper
echo ========================================
echo.

REM Detect if running in CI environment
if defined CI (
    set "IS_CI=1"
) else (
    set "IS_CI=0"
)

REM In CI, always create fresh venv; locally, reuse if exists
if "%IS_CI%"=="1" (
    if exist "venv" (
        echo Removing existing virtual environment for clean CI build...
        rmdir /s /q venv
    )
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv || exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat || exit /b 1

REM Upgrade pip
python -m pip install --upgrade pip || exit /b 1

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt || exit /b 1

REM Build executable
echo.
echo Building executable...
pyinstaller build.spec --clean || exit /b 1

echo.
echo ========================================
echo Build complete!
echo Executable is in: dist\local-whisper.exe
echo ========================================

REM Only pause if not in CI
if "%IS_CI%"=="0" (
    pause
)
