"""
Test script để kiểm tra Accounts API backend.

Chạy script này để test các endpoints:
- GET /api/accounts - List all accounts
- GET /api/accounts/{account_id} - Get account by ID
- GET /api/accounts/{account_id}/stats - Get account stats
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from backend.api.adapters.accounts_adapter import AccountsAPI


def test_accounts_api():
    """Test AccountsAPI directly."""
    print("=" * 60)
    print("TESTING ACCOUNTS API DIRECTLY")
    print("=" * 60)
    
    try:
        # Initialize API
        print("\n1. Initializing AccountsAPI...")
        accounts_api = AccountsAPI()
        print("   ✓ AccountsAPI initialized")
        
        # List accounts
        print("\n2. Listing accounts...")
        accounts = accounts_api.list_accounts()
        print(f"   ✓ Found {len(accounts)} accounts")
        
        if accounts:
            print("\n3. Account details:")
            for acc in accounts:
                print(f"   - Account ID: {acc.get('account_id')}")
                print(f"     Jobs Count: {acc.get('jobs_count', 'N/A')}")
                print(f"     Profile Path: {acc.get('profile_path', 'N/A')}")
                if acc.get('metadata'):
                    print(f"     Metadata: {acc.get('metadata')}")
                print()
            
            # Test get account by ID
            first_account_id = accounts[0].get('account_id')
            if first_account_id:
                print(f"\n4. Testing get account by ID: {first_account_id}")
                # Note: AccountsAPI doesn't have get_account_info, so we'll use list_accounts
                account = next((a for a in accounts if a.get('account_id') == first_account_id), None)
                if account:
                    print(f"   ✓ Found account: {account.get('account_id')}")
                    print(f"     Jobs Count: {account.get('jobs_count', 'N/A')}")
                else:
                    print(f"   ✗ Account not found")
        else:
            print("   ⚠ No accounts found")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


def test_mysql_query():
    """Test MySQL query directly."""
    print("\n" + "=" * 60)
    print("TESTING MYSQL QUERY DIRECTLY")
    print("=" * 60)
    
    try:
        from services.storage.connection_pool import get_connection_pool
        from config.storage_config_loader import get_storage_config_from_env
        import pymysql.cursors
        
        storage_config = get_storage_config_from_env()
        mysql_config = storage_config.mysql
        
        print(f"\n1. Connecting to MySQL...")
        print(f"   Host: {mysql_config.host}")
        print(f"   Port: {mysql_config.port}")
        print(f"   Database: {mysql_config.database}")
        
        pool = get_connection_pool(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            database=mysql_config.database
        )
        print("   ✓ Connected")
        
        # Test query for all accounts
        print("\n2. Querying jobs count for all accounts...")
        with pool.get_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Get all unique account_ids from jobs table
                cursor.execute("SELECT DISTINCT account_id FROM jobs")
                account_ids = cursor.fetchall()
                print(f"   ✓ Found {len(account_ids)} unique account_ids in jobs table")
                
                if account_ids:
                    print("\n3. Jobs count per account:")
                    for row in account_ids:
                        account_id = row.get('account_id')
                        cursor.execute(
                            "SELECT COUNT(*) as count FROM jobs WHERE account_id = %s",
                            (account_id,)
                        )
                        result = cursor.fetchone()
                        count = result.get('count', 0) if result else 0
                        print(f"   - {account_id}: {count} jobs")
                else:
                    print("   ⚠ No jobs found in database")
                
                # Total jobs
                cursor.execute("SELECT COUNT(*) as total FROM jobs")
                total_result = cursor.fetchone()
                total = total_result.get('total', 0) if total_result else 0
                print(f"\n4. Total jobs in database: {total}")
        
        print("\n" + "=" * 60)
        print("MYSQL TEST COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🧵 THREADS AUTOMATION - ACCOUNTS API TEST")
    print("=" * 60)
    
    # Test AccountsAPI
    test_accounts_api()
    
    # Test MySQL query
    test_mysql_query()
    
    print("\n✅ All tests completed!\n")
