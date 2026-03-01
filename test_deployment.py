#!/usr/bin/env python3
"""
Diagnostic script to test Vantage API deployment.
Tests all critical endpoints and environment variables.

Usage:
    python test_deployment.py https://your-project.vercel.app
"""

import sys
import asyncio
import os
from urllib.parse import urljoin
import json

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


async def test_endpoint(client: httpx.AsyncClient, base_url: str, path: str, name: str):
    """Test a single endpoint."""
    url = urljoin(base_url, path)
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {name}")
    print(f"📍 URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = await client.get(url, timeout=30.0)
        print(f"✅ Status: {response.status_code}")
        
        try:
            data = response.json()
            print(f"📦 Response:")
            print(json.dumps(data, indent=2)[:500])  # First 500 chars
            
            if response.status_code >= 400:
                print(f"❌ ERROR: {data.get('detail', 'Unknown error')}")
                return False
            return True
            
        except Exception as e:
            print(f"📄 Response (raw): {response.text[:500]}")
            return False
            
    except httpx.TimeoutException:
        print(f"⏱️  TIMEOUT: Request took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_mongodb_connection(base_url: str):
    """Test if MongoDB is accessible."""
    url = urljoin(base_url, "/api/health")
    print(f"\n{'='*60}")
    print(f"🗄️  Testing MongoDB Connection")
    print(f"📍 URL: {url}")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            data = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"📦 Health Check Response:")
            print(json.dumps(data, indent=2))
            
            if data.get("status") == "healthy":
                print(f"✅ Backend is healthy")
                if data.get("demo_mode"):
                    print(f"ℹ️  Demo mode is ENABLED")
                else:
                    print(f"ℹ️  Demo mode is DISABLED")
                return True
            else:
                print(f"❌ Backend is not healthy")
                return False
                
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False


async def diagnose_deployment(base_url: str):
    """Run full diagnostic suite."""
    print("\n" + "="*60)
    print("🔍 VANTAGE DEPLOYMENT DIAGNOSTICS")
    print("="*60)
    print(f"Target: {base_url}")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        results = {}
        
        # Test 1: Root endpoint
        results['root'] = await test_endpoint(
            client, base_url, "/api/", "Root API Endpoint"
        )
        
        # Test 2: Health check
        results['health'] = await test_mongodb_connection(base_url)
        
        # Test 3: Businesses endpoint (the one failing)
        results['businesses'] = await test_endpoint(
            client, base_url, "/api/businesses", "Businesses Endpoint"
        )
        
        # Test 4: Deals endpoint
        results['deals'] = await test_endpoint(
            client, base_url, "/api/deals", "Deals Endpoint"
        )
        
    # Summary
    print(f"\n{'='*60}")
    print("📊 DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name.upper()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n📈 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"✅ All tests passed! Your deployment is working correctly.")
    else:
        print(f"\n❌ Some tests failed. Check the errors above.")
        print(f"\n💡 Common issues:")
        print(f"   1. Environment variables not set in Vercel")
        print(f"   2. MongoDB connection string incorrect")
        print(f"   3. MongoDB network access not configured")
        print(f"   4. Database is empty (enable DEMO_MODE=true)")
        print(f"\n🔍 Next steps:")
        print(f"   1. Check Vercel logs: Deployments → Click deployment → View Function Logs")
        print(f"   2. Verify environment variables in Vercel Settings")
        print(f"   3. Test MongoDB connection with MongoDB Compass")
    
    return passed == total


def print_vercel_debug_instructions():
    """Print instructions for checking Vercel logs."""
    print(f"\n{'='*60}")
    print("📝 HOW TO CHECK VERCEL LOGS")
    print(f"{'='*60}")
    print(f"""
1. Go to your Vercel Dashboard
2. Click on your project
3. Go to the "Deployments" tab
4. Click on your latest deployment
5. Click "View Function Logs" or "Runtime Logs"

Look for errors like:
- MongoDB connection errors
- Missing environment variables
- Python import errors
- Authentication failures

Common error patterns:
- "No module named..." → Missing Python dependency
- "Authentication failed" → Wrong MongoDB credentials
- "Network timeout" → MongoDB network access not configured
- "KeyError" or "None" → Missing environment variable
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: Please provide your Vercel deployment URL")
        print(f"\nUsage:")
        print(f"    python test_deployment.py https://your-project.vercel.app")
        print(f"\nExample:")
        print(f"    python test_deployment.py https://vantage-abc123.vercel.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    try:
        success = asyncio.run(diagnose_deployment(base_url))
        print_vercel_debug_instructions()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
