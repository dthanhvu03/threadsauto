#!/usr/bin/env python3
"""
Script để test username extraction từ Threads profile page.

Usage:
    python scripts/test_username_extraction.py <account_id>

Example:
    python scripts/test_username_extraction.py account_01
"""

# Standard library
import sys
import asyncio
from pathlib import Path

# Setup path using common utility
from scripts.common import setup_path, get_logger, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()

# Third-party
from playwright.async_api import async_playwright

# Local
from browser.manager import BrowserManager
from services.analytics.username_service import UsernameService


async def test_username_extraction(account_id: str):
    """Test username extraction."""
    logger = get_logger("test_username_extraction")
    
    print_header(f"🔍 Testing username extraction for account: {account_id}", width=60)
    
    # Step 1: Start browser với profile
    print(f"\n1️⃣ Starting browser với profile: {account_id}")
    browser_manager = BrowserManager(account_id=account_id, logger=logger)
    
    try:
        await browser_manager.start()
        page = browser_manager.page
        
        if not page:
            print("❌ Failed to get page from browser manager")
            return
        
        print("✅ Browser started successfully")
        
        # Step 2: Extract username
        print(f"\n2️⃣ Extracting username từ Threads profile page...")
        print("   (This may take 30-60 seconds)")
        
        username_service = UsernameService(logger=logger)
        
        username = await username_service.extract_and_save_username(
            page=page,
            account_id=account_id,
            timeout=30,
            save_to_metadata=True
        )
        
        if username:
            print(f"✅ Username extracted: @{username}")
            try:
                print(f"✅ Username saved to account metadata")
            except Exception:
                print(f"⚠️  Username extracted but might not be saved to metadata (database issue)")
        else:
            print("❌ Failed to extract username")
            print("   Possible reasons:")
            print("   - User not logged in to Threads")
            print("   - Profile link XPath does not match current UI")
            print("   - Page did not load correctly")
            print("\n   Check logs for more details.")
            print("   Browser will stay open for manual inspection...")
        
        # Step 3: Verify username trong metadata
        print(f"\n3️⃣ Verifying username trong account metadata...")
        try:
            # Use common utility to get account storage
            from scripts.common import get_account_storage
            
            account_storage = get_account_storage()
                logger=logger
            )
            account = account_storage.get_account(account_id)
        except Exception as e:
            print(f"⚠️  Could not verify username trong metadata: {str(e)}")
            print("   (Username extraction might have succeeded, but database verification failed)")
            account = None
        
        if account and account.get("metadata"):
            metadata = account.get("metadata", {})
            stored_username = metadata.get("username") or metadata.get("threads_username")
            
            if stored_username:
                print(f"✅ Username trong metadata: @{stored_username}")
                if username and stored_username == username:
                    print("✅ Username match!")
                else:
                    print(f"⚠️  Username mismatch: extracted={username}, stored={stored_username}")
            else:
                print("❌ Username không có trong metadata")
        else:
            print("❌ Account metadata không tìm thấy")
        
        print("\n" + "=" * 60)
        print("✅ Test completed!")
        
        # Keep browser open for manual inspection
        print("\n⏸️  Browser sẽ mở trong 10 giây để bạn kiểm tra...")
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Close browser
        print("\n🔒 Closing browser...")
        await browser_manager.close()
        print("✅ Browser closed")


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_username_extraction.py <account_id>")
        print("Example: python scripts/test_username_extraction.py account_01")
        sys.exit(1)
    
    account_id = sys.argv[1]
    
    await test_username_extraction(account_id)


if __name__ == "__main__":
    asyncio.run(main())
