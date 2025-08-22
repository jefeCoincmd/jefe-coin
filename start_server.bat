@echo off
title JEFE COIN Server
color 0B

echo.
echo ========================================
echo         JEFE COIN Server Launcher
echo ========================================
echo.

REM Check if Python 3.11 is accessible via py launcher
echo Checking for Python 3.11...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11 is not available via 'py -3.11'.
    echo Please ensure Python 3.11 is installed and the Python Launcher for Windows is in your PATH.
    echo You can download it from https://python.org
    pause
    exit /b 1
)
echo Python 3.11 found!

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please create a .env file with your Upstash Redis credentials:
    echo.
    echo UPSTASH_REDIS_REST_URL=your-redis-url
    echo UPSTASH_REDIS_REST_PORT=your-redis-port
    echo UPSTASH_REDIS_REST_PASSWORD=your-redis-password
    echo SECRET_KEY=your-secret-key-here
    echo.
    echo The server will use default values if .env is not found.
    echo.
)

REM Install dependencies
echo Installing dependencies using Python 3.11...
py -3.11 -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully!
echo.
echo Starting CryptoSim Server with Python 3.11...
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Run the server
py -3.11 backend/main.py

echo.
echo Server stopped.
pause
