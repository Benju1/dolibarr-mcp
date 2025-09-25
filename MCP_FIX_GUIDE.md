# MCP Server Installation Fix Guide

## Quick Fix (Recommended)

If you're experiencing the "ModuleNotFoundError: No module named 'dolibarr_mcp'" error, follow these steps:

### Step 1: Run Diagnostic Tool
```bash
python diagnose_and_fix.py
```
This will automatically identify and fix most issues.

### Step 2: Run Installation Fix
```bash
fix_installation.bat
```
This ensures the package is properly installed.

### Step 3: Test the Server
```bash
python mcp_server_launcher.py
```

## Manual Fix Steps

If the automatic fixes don't work:

### 1. Ensure You're in the Right Directory
```bash
cd C:\Users\[YOUR_USERNAME]\GitHub\dolibarr-mcp
```

### 2. Create/Activate Virtual Environment
```bash
python -m venv venv_dolibarr
venv_dolibarr\Scripts\activate
```

### 3. Install Package in Development Mode
```bash
pip install -e .
```

### 4. Install Required Dependencies
```bash
pip install requests python-dotenv mcp
```

### 5. Configure Environment
Create a `.env` file with your Dolibarr credentials:
```
DOLIBARR_URL=https://your-dolibarr.com/api/index.php
DOLIBARR_API_KEY=your-api-key-here
```

### 6. Update Claude Desktop Configuration

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dolibarr-python": {
      "command": "C:\\Users\\[YOUR_USERNAME]\\GitHub\\dolibarr-mcp\\venv_dolibarr\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\[YOUR_USERNAME]\\GitHub\\dolibarr-mcp\\mcp_server_launcher.py"
      ]
    }
  }
}
```

## Common Issues and Solutions

### Issue: ModuleNotFoundError
**Solution**: The package isn't installed. Run:
```bash
pip install -e .
```

### Issue: ImportError for dependencies
**Solution**: Install missing dependencies:
```bash
pip install requests python-dotenv mcp aiohttp pydantic
```

### Issue: Server starts but immediately stops
**Solution**: Check your `.env` file has valid credentials

### Issue: "No module named 'src'"
**Solution**: You're running from wrong directory. Navigate to project root:
```bash
cd C:\Users\[YOUR_USERNAME]\GitHub\dolibarr-mcp
```

## Testing the Installation

### Test 1: Check Module Import
```bash
python -c "from src.dolibarr_mcp import __version__; print(f'Version: {__version__}')"
```

### Test 2: Run Server Directly
```bash
python src/dolibarr_mcp/dolibarr_mcp_server.py
```

### Test 3: Check MCP Connection
```bash
python test_connection.py
```

## File Structure Verification

Ensure these files exist:
```
dolibarr-mcp/
├── src/
│   └── dolibarr_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── dolibarr_mcp_server.py
│       ├── dolibarr_client.py
│       └── config.py
├── .env (with your credentials)
├── setup.py
├── pyproject.toml
├── mcp_server_launcher.py
├── diagnose_and_fix.py
└── fix_installation.bat
```

## Support

If you continue to experience issues:
1. Run `diagnose_and_fix.py` and share the output
2. Check the [GitHub Issues](https://github.com/latinogino/dolibarr-mcp/issues)
3. Ensure you have Python 3.8+ installed
4. Try the alternative ultra-simple server: `python src/dolibarr_mcp/ultra_simple_server.py`

## Alternative: Docker Installation

If local installation continues to fail, use Docker:
```bash
docker-compose up
```

This will run the server in an isolated container with all dependencies pre-configured.
