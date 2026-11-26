@echo off
REM Windows batch script to build The Floor Is a Lie executable
REM Run this script in the project directory

echo Building Windows executable for "The Floor Is a Lie"...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install pyinstaller pygame pygame_gui pydub
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Building executable...
pyinstaller --clean game.spec
if errorlevel 1 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo SUCCESS! The executable has been created.
echo.
echo The game executable is located at: dist\TheFloorIsALie.exe
echo.
echo To distribute the game:
echo 1. Copy the entire 'dist' folder to your target machine
echo 2. Run TheFloorIsALie.exe - no Python installation required!
echo.
echo Press any key to exit...
pause >nul
