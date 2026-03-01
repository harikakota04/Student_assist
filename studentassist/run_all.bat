@echo off
REM Start both backend and frontend in separate windows (Windows only)
REM Usage: run_all.bat

setlocal enabledelayedexpansion

echo.
echo ========================================================
echo StudentAssist - Full Startup (Backend + Frontend)
echo ========================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

REM Start backend in new window
echo Starting Backend...
start "StudentAssist Backend" cmd /k "cd /d "%~dp0backend" && python startup_check.py"

REM Wait a moment for backend to start
echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak

REM Start frontend in new window
echo Starting Frontend...
start "StudentAssist Frontend" cmd /k "cd /d "%~dp0frontend" && streamlit run app.py"

REM Wait and show message
timeout /t 3 /nobreak

echo.
echo ========================================================
echo ✅ Both services started!
echo.
echo Frontend will open at: http://localhost:8501
echo Backend is running on: http://localhost:8000
echo.
echo To stop, close both windows.
echo ========================================================
echo.
