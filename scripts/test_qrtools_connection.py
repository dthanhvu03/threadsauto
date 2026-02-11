#!/usr/bin/env python3
"""
Test Qrtools API Connection.

Script để test và verify kết nối giữa Python backend và Qrtools API server.
"""

# Standard library
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Third-party
import httpx

# Local
from backend.app.modules.feed.services.qrtools_client import QrtoolsClient
from services.logger import StructuredLogger


async def test_health_check(client: QrtoolsClient) -> bool:
    """Test health check endpoint."""
    print("\n[TEST] Health Check Endpoint")
    print("-" * 50)
    try:
        result = await client.get_health()
        print(f"✅ Health check successful")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Timestamp: {result.get('timestamp', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


async def test_stats(client: QrtoolsClient) -> bool:
    """Test stats endpoint."""
    print("\n[TEST] Stats Endpoint")
    print("-" * 50)
    try:
        result = await client.get_stats()
        print(f"✅ Stats endpoint successful")
        if 'data' in result:
            data = result['data']
            print(f"   Cache enabled: {data.get('cache', {}).get('enabled', 'unknown')}")
            print(f"   Total items: {data.get('feed', {}).get('totalItems', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Stats endpoint failed: {str(e)}")
        return False


async def test_config(client: QrtoolsClient) -> bool:
    """Test config endpoint."""
    print("\n[TEST] Config Endpoint")
    print("-" * 50)
    try:
        result = await client.get_config()
        print(f"✅ Config endpoint successful")
        if 'data' in result:
            data = result['data']
            api_config = data.get('api', {})
            print(f"   API Port: {api_config.get('port', 'unknown')}")
            print(f"   Cache TTL: {api_config.get('cache', {}).get('ttlFormatted', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Config endpoint failed: {str(e)}")
        return False


async def test_feed_extraction(client: QrtoolsClient, account_id: str = None) -> bool:
    """Test feed extraction endpoint."""
    print("\n[TEST] Feed Extraction Endpoint")
    print("-" * 50)
    try:
        if not account_id:
            print("⚠️  Skipping feed extraction test (no account_id provided)")
            print("   To test: python scripts/test_qrtools_connection.py --account-id account_01")
            return True
        
        result = await client.get_feed(filters={'limit': 5}, account_id=account_id)
        print(f"✅ Feed extraction successful")
        if 'data' in result:
            items = result['data']
            print(f"   Items returned: {len(items) if isinstance(items, list) else 'N/A'}")
        return True
    except Exception as e:
        print(f"❌ Feed extraction failed: {str(e)}")
        return False


async def test_connection_status(client: QrtoolsClient) -> bool:
    """Test basic connection status."""
    print("\n[TEST] Connection Status")
    print("-" * 50)
    try:
        # Try to connect to base URL
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.get(f"{client.base_url}/health")
            response.raise_for_status()
            print(f"✅ Connection successful")
            print(f"   Base URL: {client.base_url}")
            print(f"   Status Code: {response.status_code}")
            return True
    except httpx.ConnectError:
        print(f"❌ Connection failed: Cannot connect to {client.base_url}")
        print(f"   Make sure Qrtools API server is running on port 3000")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False


async def main():
    """Main test function."""
    print("=" * 60)
    print("Qrtools API Connection Test")
    print("=" * 60)
    
    # Parse command line arguments
    account_id = None
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == '--account-id' and i + 1 < len(sys.argv):
                account_id = sys.argv[i + 1]
            elif arg.startswith('--account-id='):
                account_id = arg.split('=', 1)[1]
    
    # Initialize client
    base_url = os.getenv("QRTOOLS_API_URL", "http://localhost:3000/api")
    print(f"\n[CONFIG]")
    print(f"   Base URL: {base_url}")
    print(f"   Account ID: {account_id or 'Not provided'}")
    
    client = QrtoolsClient(base_url=base_url)
    
    # Run tests
    results = []
    
    # Test 1: Connection Status
    results.append(await test_connection_status(client))
    
    # Test 2: Health Check
    if results[0]:  # Only test if connection is successful
        results.append(await test_health_check(client))
        results.append(await test_stats(client))
        results.append(await test_config(client))
        results.append(await test_feed_extraction(client, account_id))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        print("\nTroubleshooting:")
        print("1. Make sure Qrtools API server is running:")
        print("   cd qrtools && npm run api")
        print("2. Check if port 3000 is available:")
        print("   lsof -i :3000")
        print("3. Verify QRTOOLS_API_URL environment variable:")
        print("   echo $QRTOOLS_API_URL")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
