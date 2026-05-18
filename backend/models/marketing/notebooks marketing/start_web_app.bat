@echo off
setlocal enabledelayedexpansion

REM Screenshot Engagement Evaluator - Windows Startup Script

echo.
echo ==============================================================
echo.  Screenshot Engagement Evaluator - Web Interface
echo.                    Startup Script
echo.
echo ==============================================================
echo.

REM Check if engagement_pipeline exists
if not exist engagement_pipeline.py (
    echo [ERROR] engagement_pipeline.py not found
    echo Please run this script from the project root folder
    pause
    exit /b 1
)

REM Get Python executable from venv
if exist .venv\Scripts\python.exe (
    set PYTHON=.venv\Scripts\python.exe
    echo [OK] Virtual environment found
) else (
    echo [ERROR] Virtual environment not found at .venv
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Check Flask installation
%PYTHON% -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Flask not found. Installing...
    %PYTHON% -m pip install -q flask werkzeug
)

echo [OK] All dependencies verified
echo [START] Launching Flask server...
echo.
echo =============================================================
echo.  WEB INTERFACE READY
echo.
echo  Open your browser: http://localhost:5000
echo.
echo  To stop: Press Ctrl+C
echo.
echo =============================================================
echo.

REM Start Flask app with full path
%PYTHON% app.py

REM Show error if app exits
if errorlevel 1 (
    echo.
    echo [ERROR] Flask server exited with error
    pause
    exit /b 1
)
