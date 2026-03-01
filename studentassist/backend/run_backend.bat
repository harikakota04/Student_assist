@echo off
REM Backend startup script for Windows
REM Usage: run_backend.bat
REM This will run the diagnostic check and start the server

cd /d "%~dp0"
echo.
echo ========================================
echo Starting StudentAssist Backend...
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Run the diagnostic check
python startup_check.py
