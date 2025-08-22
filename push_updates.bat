@echo off
title JEFE COIN - Deploy Updates
color 0B

echo.
echo ========================================
echo      JEFE COIN - Deploy Updates
echo ========================================
echo This script will commit and push all
echo current changes to your GitHub repo,
echo triggering a new deployment on Render.
echo ========================================
echo.

REM --- Check for uncommitted changes ---
git diff-index --quiet HEAD --
if errorlevel 1 (
    echo Changes detected. Proceeding with deployment...
) else (
    echo No changes to deploy. Your repository is up to date.
    pause
    exit /b 0
)
echo.

REM --- Prompt for a commit message ---
set /p commit_message="Enter a short description for this update: "
if not defined commit_message (
    echo No commit message entered. Using 'Routine update'.
    set "commit_message=Routine update"
)
echo.

REM --- Stage, Commit, and Push ---
echo Staging all changes...
git add .
if errorlevel 1 (
    echo ERROR: Failed to stage changes.
    pause
    exit /b 1
)

echo Committing changes with message: "%commit_message%"
git commit -m "%commit_message%"
if errorlevel 1 (
    echo ERROR: Failed to commit changes.
    pause
    exit /b 1
)

echo Pushing changes to GitHub...
git push
if errorlevel 1 (
    echo.
    echo ----------------------------------------
    echo ERROR: Failed to push changes to GitHub.
    echo Please check your internet connection
    echo and authentication token.
    echo ----------------------------------------
    pause
    exit /b 1
)

echo.
echo -----------------------------------------------------------------
echo SUCCESS! Your updates have been sent to GitHub.
echo.
echo Render will now automatically start a new deployment.
echo You can monitor its progress on your Render dashboard.
echo -----------------------------------------------------------------
echo.
pause
