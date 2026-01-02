@echo off
echo Starting Local Whisper (Development Mode)
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Starting application...
echo Press Ctrl+C to stop
echo.

python -m src.local_whisper.main

