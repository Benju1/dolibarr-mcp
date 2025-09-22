@echo off
:: Dolibarr MCP Setup Script - Fixed Version 2.0
:: Uses dedicated environment setup to avoid conflicts

echo.
echo ======================================
echo Dolibarr MCP Development Setup v2.0
echo ======================================
echo.

:: First, clean up any old build artifacts
echo Cleaning up old build artifacts...

:: Remove ALL egg-info directories recursively
for /f "delims=" %%i in ('dir /s /b /a:d *.egg-info 2^>nul') do (
    rmdir /s /q "%%i" 2>nul
)

:: Clean other build directories
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist .eggs rmdir /s /q .eggs 2>nul

:: Remove old virtual environment if exists
if exist venv_dolibarr (
    echo Removing old virtual environment...
    rmdir /s /q venv_dolibarr
)

echo.
echo Running environment setup...
echo.

:: Run the Python setup script
python setup_env.py

if errorlevel 1 (
    echo.
    echo ======================================
    echo Setup failed!
    echo ======================================
    echo.
    echo Troubleshooting tips:
    echo 1. Make sure Python 3.8+ is installed
    echo 2. Try running: python --version
    echo 3. If issues persist, run cleanup.bat first
    echo.
    pause
    exit /b 1
)

echo.
pause
