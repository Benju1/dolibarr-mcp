import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

try:
    from dolibarr_mcp.server import mcp
    print("✅ Successfully imported mcp server")
    print(f"Server name: {mcp.name}")
    # print(f"Tools: {[t.name for t in mcp._tools]}") # _tools might not exist
    print("Server object created successfully.")
except Exception as e:
    print(f"❌ Failed to import mcp server: {e}")
    sys.exit(1)
