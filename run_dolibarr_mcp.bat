@echo off
REM Simple script to run Dolibarr MCP Server

echo ========================================
echo Starting Dolibarr MCP Server
echo ========================================

REM Check if virtual environment exists
if not exist "venv_dolibarr\Scripts\python.exe" (
    echo Virtual environment not found!
    echo Please run setup.py first.
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo .env file not found!
    echo Creating from template...
    copy .env.example .env
    echo Please edit .env with your Dolibarr credentials
    exit /b 1
)

REM Activate virtual environment and run server
echo Running server...
venv_dolibarr\Scripts\python.exe -m dolibarr_mcp

pause
