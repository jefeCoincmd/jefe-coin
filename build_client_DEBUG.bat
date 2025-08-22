@echo ON
title JEFE COIN Client Builder - DEBUG MODE
color 0C

echo.
echo ========================================
echo      JEFE COIN Client .exe Builder
echo --- FINAL ATTEMPT ---
echo ========================================
echo.

echo --- STEP 1: Set Python 3.11 Path ---
set "PYTHON_EXE=C:\Users\larue\AppData\Local\Programs\Python\Python311\python.exe"
echo Using hardcoded Python 3.11 path: %PYTHON_EXE%
echo.

echo --- STEP 2: Verify Python Path ---
if not exist "%PYTHON_EXE%" (
    echo ERROR: The specified Python executable was not found at the path:
    echo %PYTHON_EXE%
    echo Please verify the path is correct and try again.
    pause
    exit /b 1
)
echo Python executable found!
echo.
pause
echo.

echo --- STEP 3: Install/Update PyInstaller ---
echo Running command: "%PYTHON_EXE%" -m pip install --upgrade pyinstaller
"%PYTHON_EXE%" -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo.
    echo DEBUG: PyInstaller installation FAILED.
    echo ERROR: Failed to install PyInstaller.
    pause
    exit /b 1
)
echo DEBUG: PyInstaller installation PASSED.
echo.
pause
echo.

echo --- STEP 4: Build the Executable ---
echo The build command is: "%PYTHON_EXE%" -m PyInstaller --onefile --name "JEFE_COIN_Client" --clean --noconsole client/crypto_client.py
echo Starting the build process... This may take a few moments.
echo.
pause

"%PYTHON_EXE%" -m PyInstaller --onefile --name "JEFE_COIN_Client" --clean --noconsole client/crypto_client.py

if errorlevel 1 (
    echo.
    echo ----------------------------------------
    echo DEBUG: Build process FAILED.
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
