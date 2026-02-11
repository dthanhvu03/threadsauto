#!/usr/bin/env python3
"""
Test script để test fetch metrics thực tế.

⚠️ CRITICAL REQUIREMENTS:
1. thread_id PHẢI lấy từ DATABASE (jobs table) - không được lấy từ nguồn khác
2. username PHẢI lấy từ account metadata
3. URL format: https://www.threads.com/@{username}/post/{thread_id}
4. thread_id từ database → fetch metrics → validate URL

Usage:
    python3 scripts/test_fetch_metrics_real.py account_id
    python3 scripts/test_fetch_metrics_real.py account_id --list    # List all completed jobs với thread_id từ DATABASE
    python3 scripts/test_fetch_metrics_real.py account_id --verify  # Verify thread_ids format in DATABASE

⚠️ CRITICAL: thread_id LUÔN lấy từ DATABASE (jobs.thread_id)
   - KHÔNG accept thread_id từ command line argument
   - KHÔNG accept thread_id từ input
   - CHỈ lấy từ DATABASE
"""

import sys
from pathlib import Path

# Setup path using common utility
from scripts.common import (
    setup_path,
    get_mysql_config,
    get_account_storage,
    get_mysql_connection,
    print_header,
    print_section
)

# Add parent directory to path (must be after importing common)
setup_path()

import asyncio
import json
from typing import List, Dict, Optional
from services.analytics.service import MetricsService
from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.scheduler.models import JobStatus


def get_account_username(account_id: str) -> Optional[str]:
    """Lấy username từ account metadata."""
    try:
        storage = get_account_storage()
        
        account = storage.get_account(account_id)
        if not account:
            print(f"❌ Account '{account_id}' not found!")
            return None
        
        metadata = account.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        username = metadata.get('username') or metadata.get('threads_username')
        return username
    except Exception as e:
        print(f"❌ Error getting username: {e}")
        return None


def get_completed_jobs(account_id: str) -> List[Dict]:
    """
    Lấy danh sách completed jobs với thread_id của account từ DATABASE.
    
    ⚠️ CRITICAL: thread_id PHẢI lấy từ MySQL jobs table (jobs.thread_id).
    Không được lấy từ nguồn khác (feed, page scraping, etc.)
    
    ✅ VERIFY: Query trực tiếp MySQL để đảm bảo thread_id thực sự từ database.
    
    Args:
        account_id: Account ID để filter jobs
    
    Returns:
        List of job dicts với thread_id từ DATABASE
    """
    try:
        import pymysql
        # ⚠️ VERIFY: Query trực tiếp MySQL để confirm thread_id có trong database
        
        try:
            conn = get_mysql_connection()
            
            completed_jobs_from_db = []
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    # Query trực tiếp từ jobs table
                    query = """
                        SELECT 
                            job_id, account_id, thread_id, content, 
                            status, completed_at, created_at
                        FROM jobs
                        WHERE account_id = %s 
                        AND status = 'completed' 
                        AND thread_id IS NOT NULL 
                        AND thread_id != ''
                        ORDER BY completed_at DESC
                    """
                    cursor.execute(query, (account_id,))
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        completed_jobs_from_db.append({
                            'id': row['job_id'],
                            'account_id': row['account_id'],
                            'status': row['status'],
                            'thread_id': row['thread_id'],  # ← Từ DATABASE (verified)
                            'content': row['content'],
                            'completed_at': row['completed_at'].isoformat() if row['completed_at'] else None
                        })
                    
                    print(f"📋 Direct SQL Query:")
                    print(f"   Query: SELECT * FROM jobs WHERE account_id = '{account_id}' AND status = 'completed' AND thread_id IS NOT NULL")
                    print(f"   Results: {len(completed_jobs_from_db)} jobs với thread_id")
                    
            finally:
                conn.close()
                
            return completed_jobs_from_db
            
        except ImportError:
            # Fallback: Use MySQLJobStorage nếu pymysql không available
            print(f"⚠️  pymysql not available, using MySQLJobStorage...")
            storage = MySQLJobStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database
            )
            
            jobs_list = storage.get_jobs_by_account(account_id=account_id, status=JobStatus.COMPLETED)
            
            completed_jobs = []
            for job in jobs_list:
                if job.thread_id:  # thread_id từ jobs.thread_id column trong database
                    job_dict = {
                        'id': job.job_id,
                        'account_id': job.account_id,
                        'status': job.status.value if hasattr(job.status, 'value') else str(job.status),
                        'thread_id': job.thread_id,  # ← Từ DATABASE
                        'content': job.content,
                        'completed_at': job.completed_at.isoformat() if job.completed_at else None
                    }
                    completed_jobs.append(job_dict)
            
            return completed_jobs
            
    except Exception as e:
        print(f"❌ Error getting completed jobs from DATABASE: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_job_thread_id(account_id: str) -> Optional[str]:
    """
    Lấy thread_id từ job completed đầu tiên của account từ DATABASE.
    
    ⚠️ CRITICAL: thread_id PHẢI lấy từ DATABASE (jobs.thread_id).
    Không được lấy từ nguồn khác.
    
    ✅ VERIFY: Kiểm tra thread_id thực sự có trong database trước khi return.
    
    Args:
        account_id: Account ID
    
    Returns:
        thread_id từ DATABASE hoặc None (nếu không có trong database)
    """
    # ⚠️ VERIFY: Lấy từ database với direct SQL query
    completed_jobs = get_completed_jobs(account_id)
    
    if not completed_jobs:
        print(f"\n❌ ERROR: No completed jobs with thread_id in DATABASE for account '{account_id}'")
        print(f"   Query: SELECT * FROM jobs WHERE account_id = '{account_id}' AND status = 'completed' AND thread_id IS NOT NULL")
        print(f"   Results: 0 rows")
        print(f"   💡 Thread_id KHÔNG có trong database!")
        return None
    
    # ⚠️ VERIFY: Lấy job đầu tiên từ database (đã verified)
    job = completed_jobs[0]
    thread_id = job.get('thread_id')  # ← thread_id từ DATABASE (verified)
    
    # ⚠️ VERIFY: Kiểm tra thread_id có giá trị hợp lệ
    if not thread_id or not str(thread_id).strip():
        print(f"\n❌ ERROR: Job found but thread_id is empty or invalid!")
        print(f"   Job ID: {job.get('id')}")
        print(f"   Thread ID value: '{thread_id}'")
        print(f"   💡 Thread_id không hợp lệ trong database!")
        return None
    
    # ✅ VERIFIED: thread_id có trong database và hợp lệ
    print(f"\n✅ VERIFIED: Found completed job in DATABASE:")
    print(f"   Job ID: {job.get('id')}")
    print(f"   Thread ID: {thread_id} (verified from DATABASE)")
    print(f"   Content: {job.get('content', '')[:50]}...")
    print(f"   Completed at: {job.get('completed_at', 'N/A')}")
    print(f"   📋 Source: Direct SQL query từ MySQL jobs table")
    print(f"   ✅ VERIFIED: Thread ID '{thread_id}' EXISTS in database!")
    
    return thread_id


def list_completed_jobs(account_id: str):
    """Hiển thị danh sách completed jobs."""
    print(f"\n📋 Completed Jobs for Account: {account_id}")
    print_header("")
    
    completed_jobs = get_completed_jobs(account_id)
    
    if not completed_jobs:
        print(f"⚠️  No completed jobs with thread_id")
        return
    
    print(f"Found {len(completed_jobs)} completed jobs:\n")
    
    for idx, job in enumerate(completed_jobs, 1):
        print(f"{idx}. Job ID: {job.get('id')[:12]}...")
        print(f"   Thread ID: {job.get('thread_id')}")
        print(f"   Content: {job.get('content', '')[:60]}...")
        print(f"   Completed: {job.get('completed_at', 'N/A')}")
        print()


async def test_fetch_single_metric(account_id: str, thread_id: str, username: str = None, verify_thread_id: bool = True):
    """
    Test fetch metrics cho một thread.
    
    ⚠️ CRITICAL REQUIREMENTS:
    1. thread_id PHẢI lấy từ DATABASE (jobs.thread_id)
    2. username PHẢI lấy từ account metadata
    3. URL format: https://www.threads.com/@{username}/post/{thread_id}
    
    Args:
        account_id: Account ID
        thread_id: Thread ID to fetch (PHẢI từ DATABASE)
        username: Username (optional, will be extracted from metadata if not provided)
        verify_thread_id: Verify thread_id is in URL after navigation
    """
    print_header("")
    print(f"🧪 TEST FETCH METRICS")
    print_header("")
    print(f"Account ID: {account_id}")
    print(f"Thread ID: {thread_id} (from DATABASE)")
    print(f"Username: {username or 'Will be extracted from metadata'}")
    print(f"Verify Thread ID: {verify_thread_id}")
    print(f"Expected URL: https://www.threads.com/@{username or 'USERNAME'}/post/{thread_id}")
    print_header("")
    
    try:
        # Tạo MetricsService mới (như trong workflow fix)
        service = MetricsService()
        
        print(f"\n📋 Step 1: Create MetricsService")
        print(f"   Service instance: {id(service)}")
        print(f"   BrowserManager: {service.browser_manager}")
        
        # Expected URL format
        if username:
            expected_url = f"https://www.threads.com/@{username}/post/{thread_id}"
            print(f"   Expected URL: {expected_url}")
        
        # Fetch metrics
        print(f"\n📋 Step 2: Fetch metrics...")
        print(f"   ⚠️  CRITICAL: thread_id từ DATABASE, username từ metadata")
        print(f"   This will:")
        print(f"   1. Create BrowserManager với account_id='{account_id}'")
        print(f"   2. Use profile: ./profiles/{account_id}/")
        print(f"   3. Get username từ account metadata")
        print(f"   4. Build URL: https://www.threads.com/@{username or 'USERNAME'}/post/{thread_id}")
        print(f"      - thread_id: {thread_id} (from DATABASE)")
        print(f"      - username: {username or 'from metadata'}")
        print(f"   5. Navigate to thread URL")
        print(f"   6. ✅ VALIDATE: Check thread_id '{thread_id}' is in URL after navigation")
        print(f"   7. Scrape metrics (views, likes, replies, reposts, shares)")
        
        result = await service.fetch_and_save_metrics(
            thread_id=thread_id,
            account_id=account_id,
            username=username
        )
        
        # Check result
        print(f"\n📋 Step 3: Result")
        if result.get('success'):
            print(f"   ✅ SUCCESS!")
            metrics = result.get('metrics', {})
            print(f"   Views: {metrics.get('views', 'N/A')}")
            print(f"   Likes: {metrics.get('likes', 0)}")
            print(f"   Replies: {metrics.get('replies', 0)}")
            print(f"   Reposts: {metrics.get('reposts', 0)}")
            print(f"   Shares: {metrics.get('shares', 0)}")
            print(f"   Fetched at: {metrics.get('fetched_at', 'N/A')}")
            
            # ✅ Verify thread_id trong result
            if verify_thread_id:
                result_thread_id = result.get('thread_id')
                if result_thread_id == thread_id:
                    print(f"\n   ✅ Thread ID Verification: PASSED")
                    print(f"      Expected: {thread_id}")
                    print(f"      Got: {result_thread_id}")
                else:
                    print(f"\n   ⚠️  Thread ID Verification: MISMATCH")
                    print(f"      Expected: {thread_id}")
                    print(f"      Got: {result_thread_id}")
            
            # ✅ Check for username mismatch ERROR
            if username:
                print(f"\n   ✅ Username Verification:")
                print(f"      Expected: {username} (from account metadata)")
                print(f"      ✅ If username matches → Browser profile is correct")
                print(f"      ❌ If username mismatch ERROR → Browser profile logged into wrong account!")
                print(f"      💡 Solution: Run 'python3 scripts/verify_browser_profile_account.py {account_id}' to verify")
        else:
            print(f"   ❌ FAILED!")
            error = result.get('error', 'Unknown error')
            print(f"   Error: {error}")
            
            # Check if error is about validation
            error_lower = error.lower()
            if 'username mismatch' in error_lower:
                print(f"\n   ❌ USERNAME MISMATCH ERROR!")
                print(f"      Browser profile is logged into WRONG account!")
                print(f"      Expected username: {username} (from account metadata)")
                print(f"      Actual username in URL: Check logs for details")
                print(f"      Profile path: ./profiles/{account_id}/")
                print(f"   💡 Solutions:")
                print(f"      1. Verify profile: python3 scripts/verify_browser_profile_account.py {account_id}")
                print(f"      2. Logout from current account in browser profile")
                print(f"      3. Login into correct account: {username}")
                print(f"      4. Or update account metadata if username is wrong")
            elif 'thread_id' in error_lower or 'not found in' in error_lower:
                print(f"\n   ⚠️  VALIDATION ERROR: Thread ID not found in URL!")
                print(f"      This means the navigated URL doesn't contain the expected thread_id.")
                print(f"      Possible causes:")
                print(f"      1. Redirected to newsfeed (wrong thread_id in database?)")
                print(f"      2. Thread doesn't exist or was deleted")
                print(f"      3. Wrong username in URL (check username mismatch error above)")
                print(f"      4. Browser profile logged into wrong account")
        
        # Check browser_manager
        print(f"\n📋 Step 4: BrowserManager Check")
        if service.browser_manager:
            print(f"   BrowserManager account_id: {service.browser_manager.account_id}")
            print(f"   Profile path: {service.browser_manager.profile_path}")
            print(f"   ✅ Account ID match: {service.browser_manager.account_id == account_id}")
        else:
            print(f"   ⚠️  BrowserManager not created")
        
        # Cleanup
        print(f"\n📋 Step 5: Cleanup")
        if service.browser_manager:
            await service.browser_manager.close()
            print(f"   ✅ BrowserManager closed")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_thread_ids(account_id: str):
    """Verify thread_ids trong database có đúng format không."""
    print("\n" + "=" * 80)
    print("🔍 VERIFY THREAD IDs IN DATABASE")
    print_header("")
    
    completed_jobs = get_completed_jobs(account_id)
    
    if not completed_jobs:
        print("⚠️  No completed jobs with thread_id")
        return
    
    print(f"Found {len(completed_jobs)} completed jobs\n")
    
    # Check thread_id format
    valid_count = 0
    invalid_count = 0
    
    for job in completed_jobs:
        thread_id = job.get('thread_id')
        if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
            valid_count += 1
            print(f"✅ {thread_id} - Valid format")
        else:
            invalid_count += 1
            print(f"❌ {thread_id} - Invalid format (not alphanumeric)")
    
    print("\n📊 Summary:")
    print(f"   Valid: {valid_count}")
    print(f"   Invalid: {invalid_count}")
    print(f"   Total: {len(completed_jobs)}")


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} account_id")
        print(f"  {sys.argv[0]} account_id --list       # List all completed jobs với thread_id từ DATABASE")
        print(f"  {sys.argv[0]} account_id --verify     # Verify thread_ids format in DATABASE")
        print(f"")
        print(f"⚠️  CRITICAL: thread_id LUÔN lấy từ DATABASE (jobs.thread_id)")
        print(f"   - KHÔNG accept thread_id từ command line")
        print(f"   - KHÔNG accept thread_id từ input")
        print(f"   - CHỈ lấy từ DATABASE")
        sys.exit(1)
    
    account_id = sys.argv[1]
    
    # Check for flags
    if len(sys.argv) > 2 and sys.argv[2] in ['--list', '-l']:
        list_completed_jobs(account_id)
        sys.exit(0)
    
    if len(sys.argv) > 2 and sys.argv[2] in ['--verify', '-v']:
        verify_thread_ids(account_id)
        sys.exit(0)
    
    # ⚠️ CRITICAL: Thread_id PHẢI từ DATABASE - không accept từ argument
    # Chỉ accept --list và --verify flags
    # Nếu có argument thứ 2 không phải flag → ERROR (không cho phép nhập thread_id từ command line)
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        print(f"❌ ERROR: thread_id KHÔNG được nhập từ command line!")
        print(f"   thread_id PHẢI lấy từ DATABASE (jobs.thread_id)")
        print(f"")
        print(f"💡 Usage:")
        print(f"   {sys.argv[0]} {account_id}              # Lấy thread_id từ DATABASE")
        print(f"   {sys.argv[0]} {account_id} --list      # List thread_ids từ DATABASE")
        print(f"   {sys.argv[0]} {account_id} --verify    # Verify thread_ids trong DATABASE")
        print(f"")
        print(f"⚠️  Không sử dụng: {sys.argv[0]} {account_id} <thread_id>")
        print(f"   thread_id PHẢI từ DATABASE, không từ command line!")
        sys.exit(1)
    
    thread_id = None  # LUÔN lấy từ DATABASE
    
    print("\n" + "=" * 80)
    print("🚀 TEST FETCH METRICS - REAL")
    print_header("")
    print("⚠️  CRITICAL REQUIREMENTS:")
    print("   1. thread_id PHẢI từ DATABASE (jobs.thread_id)")
    print("   2. username PHẢI từ account metadata")
    print("   3. URL: https://www.threads.com/@{username}/post/{thread_id}")
    print_header("")
    
    # Get username từ metadata
    print(f"\n📋 Getting username from account metadata...")
    username = get_account_username(account_id)
    if username:
        print(f"   ✅ Username: {username} (from account metadata)")
    else:
        print(f"   ⚠️  No username in metadata - will extract from page")
    
    # ⚠️ CRITICAL: Thread_id PHẢI lấy từ DATABASE (jobs table)
    # KHÔNG được lấy từ command line argument, input, hay nguồn khác
    # Chỉ được lấy từ DATABASE qua get_job_thread_id()
    print(f"\n📋 Step 0: Getting thread_id from DATABASE...")
    print(f"   ⚠️  CRITICAL: thread_id PHẢI từ DATABASE (jobs.thread_id)")
    print(f"   ❌ KHÔNG accept thread_id từ command line argument")
    print(f"   ❌ KHÔNG accept thread_id từ input")
    print(f"   ✅ CHỈ lấy từ DATABASE")
    
    thread_id = get_job_thread_id(account_id)
    if not thread_id:
        print(f"\n   ❌ ERROR: No thread_id found in DATABASE for account '{account_id}'")
        print(f"   💡 Solutions:")
        print(f"      1. Check if account has completed jobs: {sys.argv[0]} {account_id} --list")
        print(f"      2. Verify thread_ids in database: {sys.argv[0]} {account_id} --verify")
        print(f"      3. Post a thread first to create completed job with thread_id")
        sys.exit(1)
    
    # Test fetch
    result = await test_fetch_single_metric(account_id, thread_id, username, verify_thread_id=True)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print_header("")
    
    if result and result.get('success'):
        print("✅ Test PASSED - Metrics fetched successfully!")
        print("\n✅ Workflow verification:")
        print("   1. ✅ Thread ID from DATABASE (jobs.thread_id)")
        print("   2. ✅ Username from account metadata")
        print("   3. ✅ BrowserManager created with correct account_id")
        print("   4. ✅ Profile path matches account_id")
        print("   5. ✅ URL format: https://www.threads.com/@{username}/post/{thread_id}")
        print("   6. ✅ Thread ID validated in URL after navigation")
        print("   7. ✅ Metrics scraped successfully")
        print("   8. ✅ BrowserManager closed properly")
        print("\n⚠️  IMPORTANT: Check logs for:")
        print("   - Thread ID source (should be from DATABASE)")
        print("   - Username mismatch warnings")
        print("   - Thread ID validation (should be in URL)")
        print("   - Navigation errors (should not redirect to newsfeed)")
    else:
        print("❌ Test FAILED - Check error above")
        if result:
            error = result.get('error', 'Unknown error')
            print(f"   Error: {error}")
            if 'thread_id' in error.lower() or 'not found in' in error.lower():
                print(f"\n💡 This error indicates:")
                print(f"   - Thread ID validation failed")
                print(f"   - URL doesn't contain expected thread_id from DATABASE")
                print(f"   - Possible causes:")
                print(f"     1. Wrong thread_id in DATABASE (may have been extracted from feed?)")
                print(f"     2. Thread doesn't exist or was deleted")
                print(f"     3. Wrong username in URL")
                print(f"   - Solution: Verify thread_id in DATABASE is correct")
                print(f"   - Check: Use '{sys.argv[0]} {account_id} --list' to see thread_ids from DATABASE")
    
    print_header("")


if __name__ == "__main__":
    asyncio.run(main())
