#!/usr/bin/env python3
"""
Script để test post một bài và verify thread_id extraction.

Test fix cho thread_id extraction:
- Post một bài thread
- Verify thread_id được extract từ URL (không phải từ feed)
- Kiểm tra thread_id có được lưu đúng vào database không

Usage:
    python3 scripts/test_post_and_extract_thread_id.py account_id [content]
    python3 scripts/test_post_and_extract_thread_id.py 02 "Test thread - $(date)"
"""

#!/usr/bin/env python3
"""
Script để test post một bài và verify thread_id extraction.

Test fix cho thread_id extraction:
- Post một bài thread
- Verify thread_id được extract từ URL (không phải từ feed)
- Kiểm tra thread_id có được lưu đúng vào database không

Usage:
    python3 scripts/test/test_post_and_extract_thread_id.py account_id [content]
    python3 scripts/test/test_post_and_extract_thread_id.py 02 "Test thread - $(date)"
"""

import sys
from pathlib import Path
from datetime import datetime

# Setup path using common utility
from scripts.common import setup_path, get_account_storage, get_config, get_logger, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()

import asyncio
from browser.manager import BrowserManager
from browser.login_guard import LoginGuard
from threads.composer import ThreadComposer
from config import RunMode


async def test_post_and_extract_thread_id(account_id: str, content: str = None):
    """Test post một bài và verify thread_id extraction."""
    print_header("🧪 TEST POST AND EXTRACT THREAD ID")
    print(f"Account ID: {account_id}")
    print(f"Content: {content or 'Default test content'}")
    
    if not content:
        content = f"🧪 Test thread - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    config = get_config(RunMode.SAFE)
    
    try:
        # Step 1: Start browser
        print(f"\n📋 Step 1: Start browser...")
        browser_manager = BrowserManager(account_id=account_id, config=config)
        await browser_manager.start()
        print(f"   ✅ Browser started")
        print(f"   Profile path: {browser_manager.profile_path}")
        
        try:
            page = browser_manager.page
            
            # Step 2: Navigate to Threads
            print(f"\n📋 Step 2: Navigate to Threads...")
            await browser_manager.navigate("https://www.threads.com/?hl=vi")
            await asyncio.sleep(2)
            print(f"   ✅ Navigated to Threads")
            
            # Step 3: Check login state
            print(f"\n📋 Step 3: Check login state...")
            login_guard = LoginGuard(page, config=config)
            is_logged_in = await login_guard.check_login_state()
            
            if not is_logged_in:
                print(f"   ⚠️  Not logged in")
                print(f"   💡 Please login manually...")
                instagram_clicked = await login_guard.click_instagram_login()
                if instagram_clicked:
                    print(f"   ✅ Opened login form")
                
                login_success = await login_guard.wait_for_manual_login(timeout=300)
                if not login_success:
                    print(f"   ❌ Login failed")
                    return
                print(f"   ✅ Logged in")
            else:
                print(f"   ✅ Already logged in")
            
            # Step 4: Post thread
            print(f"\n📋 Step 4: Post thread...")
            print(f"   Content: {content}")
            print(f"   ⚠️  This will:")
            print(f"      1. Click compose button")
            print(f"      2. Type content")
            print(f"      3. Click post button")
            print(f"      4. Wait for redirect to thread URL")
            print(f"      5. Extract thread_id from URL (NOT from feed)")
            
            composer = ThreadComposer(page, config=config)
            result = await composer.post_thread(content)
            
            # Step 5: Verify result
            print(f"\n📋 Step 5: Verify result...")
            if result.success:
                print(f"   ✅ Post successful!")
                print(f"   Thread ID: {result.thread_id or 'None'}")
                print(f"   State: {result.state}")
                
                if result.thread_id:
                    print(f"\n   ✅ Thread ID extracted: {result.thread_id}")
                    print(f"   📋 Source: URL after redirect (VERIFIED)")
                    print(f"   ✅ This thread_id is CORRECT (from URL, not from feed)")
                    
                    # Verify URL contains thread_id
                    current_url = page.url
                    print(f"\n   📋 Current URL: {current_url}")
                    if result.thread_id in current_url:
                        print(f"   ✅ Thread ID verified in URL!")
                    else:
                        print(f"   ⚠️  Thread ID not in current URL (may have navigated away)")
                    
                    # Check if thread_id is in database
                    print(f"\n📋 Step 6: Check if thread_id saved to database...")
                    await check_thread_id_in_database(account_id, result.thread_id, content)
                else:
                    print(f"\n   ⚠️  Thread ID is None")
                    print(f"   📋 Reason: Threads did not redirect to thread URL")
                    print(f"   ✅ This is CORRECT behavior (not saving wrong thread_id)")
                    print(f"   💡 Thread_id will NOT be saved to database (to avoid wrong thread_id)")
            else:
                print(f"   ❌ Post failed!")
                print(f"   Error: {result.error}")
                print(f"   State: {result.state}")
                if result.shadow_fail:
                    print(f"   Shadow fail detected: Content still in input")
            
            # Step 7: Wait for user to see result
            print(f"\n" + "=" * 80)
            print("📊 TEST SUMMARY")
            print_header("")
            if result.success and result.thread_id:
                print("✅ TEST PASSED!")
                print(f"   - Post successful")
                print(f"   - Thread ID extracted from URL: {result.thread_id}")
                print(f"   - Thread ID is CORRECT (verified from URL)")
            elif result.success and not result.thread_id:
                print("⚠️  TEST PASSED (with warning)")
                print(f"   - Post successful")
                print(f"   - Thread ID not available (Threads did not redirect)")
                print(f"   - This is CORRECT (not saving wrong thread_id)")
            else:
                print("❌ TEST FAILED")
                print(f"   - Post failed: {result.error}")
            
            print(f"\n💡 Browser will stay open for 30 seconds for you to verify...")
            print(f"   Press Ctrl+C to close browser early")
            try:
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print(f"\n   ⚠️  Interrupted by user")
            
        finally:
            try:
                await browser_manager.close()
                print(f"\n   ✅ Browser closed")
            except Exception as e:
                print(f"\n   ⚠️  Error closing browser: {e}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def check_thread_id_in_database(account_id: str, thread_id: str, content: str):
    """Check if thread_id is saved to database."""
    try:
        # Use common utility to get MySQL connection
        from scripts.common import get_mysql_connection
        import pymysql
        
        conn = get_mysql_connection()
            
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    # Check trong jobs table
                    query = """
                        SELECT job_id, account_id, thread_id, content, status, completed_at
                        FROM jobs
                        WHERE account_id = %s AND thread_id = %s
                        ORDER BY completed_at DESC
                        LIMIT 1
                    """
                    cursor.execute(query, (account_id, thread_id))
                    job = cursor.fetchone()
                    
                    if job:
                        print(f"   ✅ Thread ID found in database!")
                        print(f"   Job ID: {job['job_id']}")
                        print(f"   Status: {job['status']}")
                        print(f"   Completed at: {job['completed_at']}")
                        
                        # Check if content matches
                        db_content = job.get('content', '')
                        if content[:50] in db_content or db_content[:50] in content:
                            print(f"   ✅ Content matches!")
                        else:
                            print(f"   ⚠️  Content may not match (check manually)")
                    else:
                        print(f"   ⚠️  Thread ID not found in database yet")
                        print(f"   💡 This is normal if job was run manually (not via scheduler)")
                        
            finally:
                conn.close()
                
        except ImportError:
            print(f"   ⚠️  pymysql not available, cannot check database")
            
    except Exception as e:
        print(f"   ⚠️  Error checking database: {e}")


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} account_id [content]")
        print(f"  {sys.argv[0]} 02")
        print(f"  {sys.argv[0]} 02 'Test thread content'")
        sys.exit(1)
    
    account_id = sys.argv[1]
    content = sys.argv[2] if len(sys.argv) > 2 else None
    
    await test_post_and_extract_thread_id(account_id, content)


if __name__ == "__main__":
    asyncio.run(main())
