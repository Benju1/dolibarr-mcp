# Configuration Compatibility Notice

## Environment Variable Support

The Dolibarr MCP server now supports both naming conventions for the API URL:

- `DOLIBARR_URL` (recommended)
- `DOLIBARR_BASE_URL` (alternative, for backward compatibility)

Both will work correctly. The server automatically checks for both and uses whichever is set.

## Claude Desktop Configuration

Your existing configuration is **fully compatible** with the updated code:

```json
{
  "mcpServers": {
    "dolibarr-python": {
      "command": "C:\\Users\\gino\\GitHub\\dolibarr-mcp\\venv_dolibarr\\Scripts\\python.exe",
      "args": [
        "-m",
        "dolibarr_mcp.dolibarr_mcp_server"
      ],
      "cwd": "C:\\Users\\gino\\Github\\dolibarr-mcp",
      "env": {
        "DOLIBARR_BASE_URL": "https://db.ginos.cloud/api/index.php/",
        "DOLIBARR_API_KEY": "7cxAAO835BF7bXy6DsQ2j2a7nT6ectGY"
      }
    }
  }
}
```

## Quick Validation

To ensure everything works correctly, run:

```bash
validate_claude_config.bat
```

This will:
1. Check your virtual environment
2. Install/update all dependencies
3. Test module imports
4. Validate environment variables
5. Test server startup

## Installation Steps (if needed)

1. **Navigate to project directory:**
   ```bash
   cd C:\Users\gino\GitHub\dolibarr-mcp
   ```

2. **Run the validator:**
   ```bash
   validate_claude_config.bat
   ```

3. **Restart Claude Desktop** after any configuration changes

## Troubleshooting

If you encounter issues:

1. **Run diagnostic tool:**
   ```bash
   python diagnose_and_fix.py
   ```

2. **Check module installation:**
   ```bash
   venv_dolibarr\Scripts\python.exe -m pip install -e .
   ```

3. **Test server directly:**
   ```bash
   venv_dolibarr\Scripts\python.exe -m dolibarr_mcp.dolibarr_mcp_server
   ```

## URL Format Notes

The server automatically handles various URL formats:
- `https://db.ginos.cloud` → becomes `https://db.ginos.cloud/api/index.php`
- `https://db.ginos.cloud/api/index.php/` → trailing slash is removed
- `https://db.ginos.cloud/api/index.php` → used as-is

## Status

✅ Your configuration is **ready to use** without any changes needed.
