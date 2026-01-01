@echo off
echo ========================================
echo Building Luca Whisper
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Build executable
echo.
echo Building executable...
pyinstaller build.spec --clean

echo.
echo ========================================
echo Build complete!
echo Executable is in: dist\luca-whisper.exe
echo ========================================
pause

