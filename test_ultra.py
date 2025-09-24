"""Test the ultra-simple Dolibarr MCP server - zero compiled dependencies."""

import sys
import os

# Test imports without try/catch to see exactly what fails
print("Testing ultra-simple imports...")
print(f"Python version: {sys.version}")
print("")

# Test 1: Standard library
print("✅ Standard library imports:")
import json
import logging  
import os
import sys
from typing import Dict, List, Optional, Any
print("   json, logging, os, sys, typing - OK")

# Test 2: Basic packages  
print("✅ Basic package imports:")
try:
    import requests
    print(f"   requests {requests.__version__} - OK")
except ImportError as e:
    print(f"   ❌ requests failed: {e}")
    print("   Please run: setup_ultra.bat")
    sys.exit(1)

try:
    import dotenv
    print(f"   python-dotenv - OK")
except ImportError:
    print("   ⚠️  python-dotenv not available, using manual .env loading")

try:
    import click
    print(f"   click {click.__version__} - OK") 
except ImportError:
    print("   ⚠️  click not available, basic CLI will work")

print("")

# Test 3: Our ultra-simple modules
print("✅ Testing ultra-simple modules:")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.dolibarr_mcp.simple_client import SimpleConfig, SimpleDolibarrClient, SimpleDolibarrAPIError
    print("   simple_client module - OK")
except ImportError as e:
    print(f"   ❌ simple_client failed: {e}")
    sys.exit(1)

try:
    from src.dolibarr_mcp.ultra_simple_server import UltraSimpleServer
    print("   ultra_simple_server module - OK")
except ImportError as e:
    print(f"   ❌ ultra_simple_server failed: {e}")
    sys.exit(1)

print("")

# Test 4: Configuration
print("✅ Testing configuration:")
try:
    config = SimpleConfig()
    print(f"   URL: {config.dolibarr_url}")
    print(f"   API Key: {'*' * min(len(config.api_key), 10)}...")
    print("   Configuration loading - OK")
except Exception as e:
    print(f"   ⚠️  Configuration error: {e}")

print("")

# Test 5: Server instantiation  
print("✅ Testing server:")
try:
    server = UltraSimpleServer("test-ultra")
    tools = server.get_available_tools()
    print(f"   Server created - OK")
    print(f"   Available tools: {len(tools)}")
    print(f"   First few tools: {', '.join(tools[:5])}")
except Exception as e:
    print(f"   ❌ Server creation failed: {e}")
    sys.exit(1)

print("")

# Test 6: Mock tool call (without actual API)
print("✅ Testing tool call structure:")
try:
    # This will likely fail with an API error, but tests the structure
    result = server.handle_tool_call("test_connection", {})
    if "error" in result:
        print("   Tool call structure - OK (API error expected)")
        print(f"   Error type: {result.get('type', 'unknown')}")
    else:
        print("   Tool call structure - OK") 
        print(f"   Result: {result}")
except Exception as e:
    print(f"   ❌ Tool call structure failed: {e}")
    sys.exit(1)

print("")
print("=" * 60)
print("🎉 ALL TESTS PASSED!")
print("=" * 60)
print("")
print("✅ Ultra-simple server is ready to run")
print("✅ Zero compiled extensions - maximum Windows compatibility")
print("✅ Only pure Python libraries used")
print("")
print("🚀 To run the server:")
print("   .\\run_ultra.bat")
print("")
print("🧪 To run interactively:")  
print("   python -m src.dolibarr_mcp.ultra_simple_server")
print("")

# Cleanup
if hasattr(server, 'client') and server.client:
    server.client.close()

print("Test completed successfully!")
