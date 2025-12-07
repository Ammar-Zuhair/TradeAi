@echo off
REM ========================================
REM Quick Start Script for Dual Account Trading System
REM ========================================

echo ========================================
echo Starting Dual Account Trading System
echo ========================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Install/Update dependencies
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt --quiet

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo Please create .env file from .env.example
    echo.
    pause
    exit /b 1
)

echo [2/3] Environment file found
echo.

REM Run the system
echo [3/3] Starting trading system...
echo.
python Run_System_Dual.py

REM If script exits, pause to see any errors
pause
