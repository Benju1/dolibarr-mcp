@echo off
echo 🚀 Run Dolibarr MCP Server (Direct Source)
echo.

REM Set environment variables for Python path and encoding
set PYTHONPATH=%cd%\src
set PYTHONIOENCODING=utf-8

REM Check if virtual environment exists
if not exist venv_dolibarr\Scripts\python.exe (
    echo ❌ Virtual environment not found!
    echo 💡 Run setup.bat first to create the environment
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo ❌ Configuration file .env not found!
    echo 💡 Please create .env file with your Dolibarr credentials
    echo.
    echo Example .env content:
    echo DOLIBARR_URL=https://your-dolibarr-instance.com/api/index.php
    echo DOLIBARR_API_KEY=your_api_key_here
    echo LOG_LEVEL=INFO
    echo.
    pause
    exit /b 1
)

echo 🎯 Starting Dolibarr MCP Server...
echo 📡 Server will run until you press Ctrl+C
echo ⚙️  Using direct source execution (no package installation required)
echo.

REM Start the server with direct Python execution
cd /d "%~dp0"
venv_dolibarr\Scripts\python.exe -c "
import sys
import os
sys.path.insert(0, 'src')
from dolibarr_mcp.dolibarr_mcp_server import main
import asyncio
asyncio.run(main())
"

echo.
echo 🛑 Server stopped
pause
