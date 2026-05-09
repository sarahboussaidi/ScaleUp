#!/bin/bash

# Pitch Analyzer Quick Start Script - macOS/Linux

clear
echo ""
echo "========================================"
echo "  Pitch Analyzer Pro - Quick Start"
echo "========================================"
echo ""

# Check if running from correct directory
if [ ! -f "app/presentation/page.tsx" ]; then
    echo "ERROR: Please run this script from the ScaleUp root directory"
    exit 1
fi

echo "Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
else
    echo "[OK] Python is installed"
fi

# Check pnpm
if ! command -v pnpm &> /dev/null; then
    echo "[WARNING] pnpm is not installed. Installing it now..."
    npm install -g pnpm
else
    echo "[OK] pnpm is installed"
fi

echo ""
echo "========================================"
echo "  Starting services..."
echo "========================================"
echo ""

# Start Frontend
echo "[1] Starting Frontend (Next.js on http://localhost:3000)..."
pnpm dev &
FRONTEND_PID=$!
sleep 3

# Start Backend
if [ -f "backend/app.py" ]; then
    echo "[2] Starting Backend (Flask on http://localhost:5000)..."
    
    # Check if virtual environment exists
    if [ ! -d "backend/venv" ]; then
        echo "[*] Creating Python virtual environment..."
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        echo "[*] Installing dependencies..."
        pip install -r requirements.txt -q
        cd ..
    fi
    
    # Start backend
    cd backend
    source venv/bin/activate
    python app.py &
    BACKEND_PID=$!
    cd ..
else
    echo "[ERROR] Backend not found at backend/app.py"
    echo "Please follow the setup instructions in SETUP.md"
fi

echo ""
echo "========================================"
echo "  Opening browser..."
echo "========================================"
echo ""

sleep 5

# Open browser
if command -v open &> /dev/null; then
    # macOS
    open "http://localhost:3000/presentation"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "http://localhost:3000/presentation"
fi

echo ""
echo "========================================"
echo "  Services started!"
echo "========================================"
echo ""
echo "Frontend: http://localhost:3000/presentation"
echo "Backend:  http://localhost:5000/api/health"
echo ""
echo "Press Ctrl+C to stop services."
echo ""

# Wait for services
wait

# Cleanup on exit
kill $FRONTEND_PID 2>/dev/null
kill $BACKEND_PID 2>/dev/null
