#!/usr/bin/env python3
"""
Dolibarr API Connection Tester
Tests the connection to your Dolibarr instance
"""

import os
import sys
import json
import requests
from typing import Dict, Any

def load_env():
    """Load .env file manually."""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📄 Loading environment from {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ[key] = value
    else:
        print(f"⚠️  No .env file found")

def test_connection():
    """Test Dolibarr API connection."""
    load_env()
    
    url = os.getenv("DOLIBARR_URL", "").rstrip('/')
    api_key = os.getenv("DOLIBARR_API_KEY", "")
    
    print("=" * 70)
    print("🔍 DOLIBARR API CONNECTION TEST")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"API Key: {'*' * min(len(api_key), 10)}... (length: {len(api_key)})")
    print("-" * 70)
    
    if not url or not api_key:
        print("❌ Missing configuration in .env file!")
        return False
    
    # Test different endpoints
    test_endpoints = [
        ("users?limit=1", "Users endpoint"),
        ("status", "Status endpoint"),
        ("thirdparties?limit=1", "Third parties endpoint"),
        ("products?limit=1", "Products endpoint"),
    ]
    
    headers = {
        "DOLAPIKEY": api_key,
        "Accept": "application/json",
        "User-Agent": "Dolibarr-Test/1.0"
    }
    
    success_count = 0
    
    for endpoint, name in test_endpoints:
        test_url = f"{url}/{endpoint}"
        print(f"\n📍 Testing {name}:")
        print(f"   URL: {test_url}")
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10, verify=True)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - {name} is accessible")
                success_count += 1
                
                # Try to parse response
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   Data: List with {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   Data: Dictionary with keys: {list(data.keys())[:5]}")
                except:
                    print(f"   Data: Non-JSON response")
                    
            elif response.status_code == 401:
                print(f"   ❌ UNAUTHORIZED - Check your API key")
            elif response.status_code == 403:
                print(f"   ❌ FORBIDDEN - API key may not have permissions for {name}")
            elif response.status_code == 404:
                print(f"   ⚠️  NOT FOUND - {name} might not be available")
            else:
                print(f"   ❌ ERROR - HTTP {response.status_code}")
                
        except requests.exceptions.SSLError as e:
            print(f"   ❌ SSL ERROR - Certificate issue: {str(e)[:100]}")
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ CONNECTION ERROR - Cannot reach server: {str(e)[:100]}")
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT - Server took too long to respond")
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)[:100]}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {success_count}/{len(test_endpoints)} endpoints working")
    
    if success_count > 0:
        print("✅ API connection is working!")
        return True
    else:
        print("❌ API connection failed - please check your configuration")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if the URL is correct (should end with /api/index.php)")
        print("2. Verify your API key is valid")
        print("3. Ensure the API module is enabled in Dolibarr")
        print("4. Check if your user has API permissions")
        print("5. Try accessing the URL in your browser")
        return False

if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test error: {e}")
        sys.exit(1)
