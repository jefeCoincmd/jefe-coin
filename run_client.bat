@echo off
title JEFE COIN Client
color 0A

echo.
echo ========================================
echo         JEFE COIN Client Launcher
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

REM Check if required packages are installed
echo Checking dependencies...
py -3.11 -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    py -3.11 -m pip install requests
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        pause
        exit /b 1
    )
)

echo Dependencies OK!
echo.
echo Starting CryptoSim Client with Python 3.11...
echo.

REM Run the client
py -3.11 client/crypto_client.py

echo.
echo Press any key to exit...
pause >nul
