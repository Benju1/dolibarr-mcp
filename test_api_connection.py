#!/usr/bin/env python3
"""Test script to verify Dolibarr API connection."""

import os
import sys
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_dolibarr_connection():
    """Test Dolibarr API connection with different endpoints."""
    
    # Get configuration from environment
    base_url = os.getenv("DOLIBARR_URL", "")
    api_key = os.getenv("DOLIBARR_API_KEY", "")
    
    print("🔧 Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {'*' * 10 if api_key else 'NOT SET'}")
    print()
    
    if not base_url or not api_key:
        print("❌ Missing configuration!")
        print("   Please set DOLIBARR_URL and DOLIBARR_API_KEY in .env file")
        return False
    
    # Clean base URL - remove trailing slash if present
    base_url = base_url.rstrip('/')
    
    # Test different endpoints
    endpoints_to_test = [
        "status",          # API status
        "users",           # Users list
        "thirdparties",    # Customers/Suppliers
        "products",        # Products
        "invoices",        # Invoices
        "orders",          # Orders
        "contacts",        # Contacts
    ]
    
    # Headers for Dolibarr API
    headers = {
        "DOLAPIKEY": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print("🧪 Testing Dolibarr API endpoints:")
    print("=" * 50)
    
    working_endpoints = []
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_test:
            url = f"{base_url}/{endpoint}"
            
            try:
                print(f"\n📍 Testing: {endpoint}")
                print(f"   URL: {url}")
                
                async with session.get(url, headers=headers, timeout=10, ssl=False) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"   Status: {status}")
                    
                    if status == 200:
                        print(f"   ✅ Success!")
                        working_endpoints.append(endpoint)
                        try:
                            data = json.loads(text)
                            if isinstance(data, dict):
                                print(f"   Response keys: {list(data.keys())[:5]}")
                            elif isinstance(data, list):
                                print(f"   Response: List with {len(data)} items")
                                if len(data) > 0 and isinstance(data[0], dict):
                                    print(f"   First item keys: {list(data[0].keys())[:5]}")
                        except:
                            print(f"   Response preview: {text[:100]}...")
                    elif status == 401:
                        print(f"   ❌ Authentication failed - check API key")
                    elif status == 403:
                        print(f"   ❌ Access forbidden - check permissions")
                    elif status == 404:
                        print(f"   ❌ Endpoint not found")
                    elif status == 501:
                        print(f"   ⚠️ API module not found - endpoint may not be available")
                        if text:
                            print(f"   Response: {text[:200]}...")
                    else:
                        print(f"   ⚠️ Unexpected status: {status}")
                        if text:
                            print(f"   Response: {text[:200]}...")
                        
            except aiohttp.ClientError as e:
                print(f"   ❌ Connection error: {type(e).__name__}: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 50)
    
    if working_endpoints:
        print("\n✨ Working endpoints:")
        for endpoint in working_endpoints:
            print(f"   - {endpoint}")
    else:
        print("\n⚠️ No endpoints are working!")
    
    return len(working_endpoints) > 0


async def test_swagger_endpoint():
    """Test Swagger/Explorer endpoint specifically."""
    
    base_url = os.getenv("DOLIBARR_URL", "").rstrip('/')
    api_key = os.getenv("DOLIBARR_API_KEY", "")
    
    if not base_url or not api_key:
        return
    
    print("\n🔍 Testing Swagger/Explorer endpoints:")
    print("=" * 50)
    
    # Swagger endpoints to test
    swagger_endpoints = [
        "explorer",
        "explorer/index.html",
        f"explorer/swagger.json?DOLAPIKEY={api_key}",
    ]
    
    headers = {
        "DOLAPIKEY": api_key,
        "Accept": "application/json, text/html, */*"
    }
    
    async with aiohttp.ClientSession() as session:
        for endpoint in swagger_endpoints:
            url = f"{base_url}/{endpoint}"
            
            try:
                print(f"\nTesting: {url}")
                
                async with session.get(url, headers=headers, timeout=10, ssl=False) as response:
                    status = response.status
                    content_type = response.headers.get('Content-Type', '')
                    
                    print(f"   Status: {status}")
                    print(f"   Content-Type: {content_type}")
                    
                    if status == 200:
                        print(f"   ✅ Found!")
                        
                        # If it's the swagger.json, try to parse it
                        if 'swagger.json' in endpoint:
                            text = await response.text()
                            try:
                                swagger_data = json.loads(text)
                                if 'paths' in swagger_data:
                                    print(f"   Available API endpoints:")
                                    for path in list(swagger_data['paths'].keys())[:10]:
                                        print(f"      - {path}")
                                    if len(swagger_data['paths']) > 10:
                                        print(f"      ... and {len(swagger_data['paths']) - 10} more")
                            except:
                                print(f"   Could not parse Swagger JSON")
                    else:
                        text = await response.text()
                        print(f"   Response preview: {text[:100]}...")
                        
            except Exception as e:
                print(f"   Error: {type(e).__name__}: {e}")


async def test_login_endpoint():
    """Test the login endpoint to get a session token."""
    
    base_url = os.getenv("DOLIBARR_URL", "").rstrip('/')
    api_key = os.getenv("DOLIBARR_API_KEY", "")
    
    if not base_url or not api_key:
        return
    
    print("\n🔐 Testing Login endpoint:")
    print("=" * 50)
    
    # Test with API key in header (standard method)
    url = f"{base_url}/login"
    
    headers = {
        "DOLAPIKEY": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"Testing: {url}")
            print(f"Method: GET with DOLAPIKEY header")
            
            async with session.get(url, headers=headers, timeout=10, ssl=False) as response:
                status = response.status
                text = await response.text()
                
                print(f"   Status: {status}")
                
                if status == 200:
                    print(f"   ✅ Authentication successful!")
                    try:
                        data = json.loads(text)
                        print(f"   Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"   Response: {text}")
                else:
                    print(f"   Response: {text[:200]}...")
                    
        except Exception as e:
            print(f"   Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("🚀 Dolibarr API Connection Test")
    print("================================\n")
    
    try:
        # Run tests
        success = asyncio.run(test_dolibarr_connection())
        asyncio.run(test_swagger_endpoint())
        asyncio.run(test_login_endpoint())
        
        print("\n" + "=" * 50)
        print("\n📝 Summary:")
        if success:
            print("   ✅ API connection is working!")
            print("   You can proceed with MCP server implementation.")
        else:
            print("   ⚠️ API connection issues detected.")
            print("   Please check:")
            print("   1. Dolibarr Web Services API REST module is enabled")
            print("   2. API key is correct and has proper permissions")
            print("   3. URL format is: https://domain.com/api/index.php/")
            
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
