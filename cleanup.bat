@echo off
:: Dolibarr MCP - Complete Clean Build Artifacts
:: Run this before setup if you have installation issues

echo.
echo ======================================
echo Complete Cleanup for Dolibarr MCP
echo ======================================
echo.

:: Remove all egg-info directories anywhere in the project
echo Searching and removing ALL egg-info directories...
for /f "delims=" %%i in ('dir /s /b /a:d *.egg-info 2^>nul') do (
    echo   - Removing %%i
    rmdir /s /q "%%i" 2>nul
)

:: Remove specific known egg-info patterns
if exist "dolibarr_mcp.egg-info" rmdir /s /q "dolibarr_mcp.egg-info" 2>nul
if exist "src\dolibarr_mcp.egg-info" rmdir /s /q "src\dolibarr_mcp.egg-info" 2>nul
if exist "dolibarr-mcp.egg-info" rmdir /s /q "dolibarr-mcp.egg-info" 2>nul
if exist "src\dolibarr-mcp.egg-info" rmdir /s /q "src\dolibarr-mcp.egg-info" 2>nul

:: Remove build directories
if exist build (
    echo Removing build directory...
    rmdir /s /q build 2>nul
)

if exist dist (
    echo Removing dist directory...
    rmdir /s /q dist 2>nul
)

if exist .eggs (
    echo Removing .eggs directory...
    rmdir /s /q .eggs 2>nul
)

:: Remove Python cache everywhere
echo Removing ALL Python cache directories...
for /f "delims=" %%i in ('dir /s /b /a:d __pycache__ 2^>nul') do (
    echo   - Removing %%i
    rmdir /s /q "%%i" 2>nul
)

:: Remove compiled Python files
echo Removing compiled Python files...
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
del /s /q *.pyd 2>nul

:: Remove pip cache related to this project
if exist pip-wheel-metadata rmdir /s /q pip-wheel-metadata 2>nul
if exist .pytest_cache rmdir /s /q .pytest_cache 2>nul

:: Remove virtual environment
if exist venv_dolibarr (
    echo Removing virtual environment...
    rmdir /s /q venv_dolibarr 2>nul
)

:: Remove any other common virtual environment directories
if exist venv rmdir /s /q venv 2>nul
if exist env rmdir /s /q env 2>nul
if exist .venv rmdir /s /q .venv 2>nul

echo.
echo ======================================
echo Cleanup complete!
echo ======================================
echo.
echo You can now run setup.bat for a fresh installation.
echo.
pause
