#!/usr/bin/env python3
"""Quick test script for Dolibarr MCP connection"""

import asyncio
import sys
import os

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dolibarr_mcp.config import Config
from dolibarr_mcp.dolibarr_client import DolibarrClient, DolibarrAPIError


async def test_connection():
    """Test the Dolibarr API connection"""
    print("🧪 Testing Dolibarr MCP Connection...")
    print()
    
    try:
        # Load config
        config = Config()
        print(f"📍 URL: {config.dolibarr_url}")
        print(f"🔑 API Key: {'*' * (len(config.api_key) - 4) + config.api_key[-4:] if config.api_key else 'NOT SET'}")
        print()
        
        # Test connection
        async with DolibarrClient(config) as client:
            print("📡 Testing API connection...")
            status = await client.get_status()
            
            print("✅ Connection successful!")
            print(f"📊 Status: {status}")
            print()
            
            # Test a simple query
            print("👥 Testing customer query...")
            customers = await client.get_customers(limit=1)
            print(f"✅ Found {len(customers)} customers")
            
            print()
            print("🎯 Dolibarr MCP server is ready!")
            print("🚀 Run the MCP server with: python -m dolibarr_mcp.dolibarr_mcp_server")
            
    except DolibarrAPIError as e:
        print(f"❌ Dolibarr API Error: {e.message}")
        if e.status_code:
            print(f"📊 Status Code: {e.status_code}")
        if e.response_data:
            print(f"📄 Response: {e.response_data}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
