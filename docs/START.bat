@echo off
REM Pitch Analyzer Quick Start Script - Windows

cls
echo.
echo ========================================
echo   Pitch Analyzer Pro - Quick Start
echo ========================================
echo.

REM Check if running from correct directory
if not exist "app\presentation\page.tsx" (
    echo ERROR: Please run this script from the ScaleUp root directory
    pause
    exit /b 1
)

echo Checking prerequisites...
echo.

REM Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
) else (
    echo [OK] Python is installed
)

REM Check Node/pnpm
pnpm --version > nul 2>&1
if errorlevel 1 (
    echo [WARNING] pnpm is not installed. Installing it now...
    call npm install -g pnpm
) else (
    echo [OK] pnpm is installed
)

echo.
echo ========================================
echo   Starting services in NEW TERMINALS
echo ========================================
echo.

REM Start Frontend
echo [1] Starting Frontend (Next.js on http://localhost:3000)...
start "Pitch Analyzer - Frontend" cmd /k "pnpm dev"
timeout /t 3 > nul

REM Check and start Backend
if exist "backend\app.py" (
    echo [2] Starting Backend (Flask on http://localhost:5000)...
    
    REM Check if virtual environment exists
    if not exist "backend\venv" (
        echo [*] Creating Python virtual environment...
        pushd backend
        python -m venv venv
        call venv\Scripts\activate
        echo [*] Installing dependencies...
        pip install -r requirements.txt -q
        popd
    )
    
    REM Start backend in new terminal
    start "Pitch Analyzer - Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"
) else (
    echo [ERROR] Backend not found at backend\app.py
    echo Please follow the setup instructions in SETUP.md
)

echo.
echo ========================================
echo   Opening browser...
echo ========================================
echo.

timeout /t 5 > nul
start "http://localhost:3000/presentation"

echo.
echo ========================================
echo   Services started!
echo ========================================
echo.
echo Frontend: http://localhost:3000/presentation
echo Backend:  http://localhost:5000/api/health
echo.
echo Press Ctrl+C in the terminal to stop any service.
echo.
pause
