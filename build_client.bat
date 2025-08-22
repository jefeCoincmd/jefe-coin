@echo off
title JEFE COIN Client Builder
color 0A

echo.
echo ========================================
echo      JEFE COIN Client .exe Builder
echo ========================================
echo.

REM --- Set the explicit path to your Python 3.11 executable ---
set "PYTHON_EXE=C:\Users\larue\AppData\Local\Programs\Python\Python311\python.exe"
echo Using Python 3.11 from: %PYTHON_EXE%
echo.

REM --- Verify the Python path ---
if not exist "%PYTHON_EXE%" (
    echo ERROR: The specified Python executable was not found at the path:
    echo %PYTHON_EXE%
    echo Please verify the path is correct and try again.
    pause
    exit /b 1
)
echo Python executable verified.
echo.

REM --- Install/Update PyInstaller ---
echo Checking for PyInstaller...
"%PYTHON_EXE%" -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    pause
    exit /b 1
)
echo PyInstaller is ready.
echo.

REM --- Build the Executable ---
echo Starting the build process... This may take a few moments.
echo.

"%PYTHON_EXE%" -m PyInstaller --onefile --name "JEFE_COIN_Client" --clean client/crypto_client.py

if errorlevel 1 (
    echo.
    echo ----------------------------------------
    echo ERROR: The build process failed.
    echo ----------------------------------------
    pause
    exit /b 1
)

echo.
echo -----------------------------------------------------------------
echo SUCCESS! Your executable has been created.
echo.
echo You can find it in the 'dist' folder:
echo dist\JEFE_COIN_Client.exe
echo.
echo This single .exe file is all you need to send to your users.
echo -----------------------------------------------------------------
echo.
pause
