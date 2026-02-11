#!/usr/bin/env python3
"""
Script để check username trong browser profile.

Usage:
    python scripts/utility/check_browser_profile.py <account_id>
"""

import sys
import asyncio
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.common import setup_path, get_account_username, print_header
setup_path()

from browser.manager import BrowserManager
from services.logger import StructuredLogger


async def check_browser_profile(account_id: str):
    """Check username trong browser profile."""
    print_header("")
    print(f"🔍 CHECK BROWSER PROFILE: {account_id}")
    print_header("")
    
    # Get username từ metadata
    metadata_username = get_account_username(account_id)
    print(f"📋 Username từ metadata: @{metadata_username if metadata_username else 'N/A'}")
    print_header("")
    
    # Start browser
    print("🚀 Đang mở browser...")
    browser_manager = BrowserManager(account_id=account_id)
    
    try:
        await browser_manager.start()
        page = browser_manager.page
        
        # Navigate to Threads
        print("📱 Đang navigate đến Threads...")
        await page.goto("https://www.threads.com/", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        # Get current URL
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        # Extract username từ URL nếu có
        import re
        url_match = re.search(r'/@([^/?]+)', current_url)
        if url_match:
            url_username = url_match.group(1)
            print(f"📋 Username từ URL: @{url_username}")
            
            if metadata_username:
                if url_username == metadata_username:
                    print(f"\n✅ MATCH! Browser profile đang login đúng account: @{url_username}")
                else:
                    print(f"\n❌ MISMATCH!")
                    print(f"   Metadata: @{metadata_username}")
                    print(f"   Browser:  @{url_username}")
                    print(f"\n⚠️  Browser profile đang login account khác!")
                    print(f"   Cần login lại với account @{metadata_username}")
                    print(f"\n💡 Hướng dẫn:")
                    print(f"   1. Browser đã mở, hãy login với account @{metadata_username}")
                    print(f"   2. Sau khi login xong, nhấn Enter để check lại")
                    print(f"   3. Hoặc đóng browser và chạy lại script")
            else:
                print(f"\n⚠️  Không có username trong metadata")
                print(f"   Browser đang login: @{url_username}")
                print(f"   💡 Có thể lưu username này vào metadata:")
                print(f"      python scripts/utility/fix_account_username.py {account_id} {url_username}")
        else:
            print(f"\n⚠️  Không tìm thấy username trong URL")
            print(f"   URL: {current_url}")
            print(f"   Có thể chưa login hoặc đang ở trang khác")
        
        print_header("")
        print("⏸️  Browser đang mở. Nhấn Enter để đóng...")
        input()
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_manager.close()
        print("\n✅ Đã đóng browser")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/utility/check_browser_profile.py <account_id>")
        sys.exit(1)
    
    account_id = sys.argv[1]
    
    # Run async
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(check_browser_profile(account_id))
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi user (Ctrl+C)")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
