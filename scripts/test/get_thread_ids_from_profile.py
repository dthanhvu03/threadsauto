#!/usr/bin/env python3
"""
Script để lấy danh sách thread_id từ profile page.

Usage:
    python3 scripts/get_thread_ids_from_profile.py account_id [limit]
    python3 scripts/get_thread_ids_from_profile.py 02
    python3 scripts/get_thread_ids_from_profile.py 02 10  # Lấy 10 bài đầu tiên
"""

import sys
from pathlib import Path

# Setup path using common utility
from scripts.common import (
    setup_path,
    get_account_storage,
    get_config,
    get_logger,
    print_header,
    print_section
)

# Add parent directory to path (must be after importing common)
setup_path()

import asyncio
from browser.manager import BrowserManager
from browser.login_guard import LoginGuard
from config import RunMode


async def get_thread_ids_from_profile(
    account_id: str,
    limit: int = 20,
    scroll_pages: int = 3
) -> list[dict]:
    """
    Lấy danh sách thread_id từ profile page.
    
    Args:
        account_id: Account ID
        limit: Số lượng bài post tối đa để lấy
        scroll_pages: Số lần scroll để load thêm bài post
    
    Returns:
        List of dicts với:
        - thread_id: Thread ID
        - href: Full URL của bài post
        - username: Username từ URL
        - index: Thứ tự bài post (1 = mới nhất)
    """
    config = get_config(RunMode.SAFE)
    logger = get_logger("get_thread_ids_from_profile")
    
    print_header("🔍 GET THREAD IDs FROM PROFILE")
    print(f"Account ID: {account_id}")
    print(f"Limit: {limit} posts")
    print(f"Scroll pages: {scroll_pages}")
    
    browser_manager = None
    try:
        # Step 1: Start browser
        print(f"\n📋 Step 1: Start browser...")
        browser_manager = BrowserManager(account_id=account_id, config=config)
        await browser_manager.start()
        print(f"   ✅ Browser started")
        print(f"   Profile path: {browser_manager.profile_path}")
        
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
                return []
            print(f"   ✅ Logged in")
        else:
            print(f"   ✅ Already logged in")
        
        # Step 4: Get username and navigate to profile
        print(f"\n📋 Step 4: Navigate to profile...")
        
        # Get username from metadata
        account_storage = get_account_storage()
        
        account = account_storage.get_account(account_id)
        username = None
        
        if account and account.get('metadata'):
            import json
            metadata = account.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            username = metadata.get('username') or metadata.get('threads_username')
        
        if username:
            print(f"   ✅ Username from metadata: {username}")
            profile_url = f"https://www.threads.com/@{username}"
        else:
            print(f"   ⚠️  No username in metadata, trying to extract...")
            # Try to find profile link on page
            try:
                profile_selectors = [
                    "a[aria-label*='Profile']",
                    "a[aria-label*='Trang cá nhân']",
                    "xpath=//a[contains(text(), 'Trang cá nhân')]",
                    "xpath=//a[contains(text(), 'Profile')]"
                ]
                
                profile_link = None
                for selector in profile_selectors:
                    try:
                        if selector.startswith("xpath="):
                            xpath = selector.replace("xpath=", "")
                            elements = await page.query_selector_all(f"xpath={xpath}")
                        else:
                            elements = await page.query_selector_all(selector)
                        
                        if elements:
                            href = await elements[0].get_attribute("href")
                            if href and '/@' in href:
                                profile_link = href
                                break
                    except Exception:
                        continue
                
                if profile_link:
                    if not profile_link.startswith('http'):
                        profile_link = f"https://www.threads.com{profile_link}" if profile_link.startswith('/') else f"https://www.threads.com/{profile_link}"
                    profile_url = profile_link
                    # Extract username from URL
                    import re
                    match = re.search(r'@([^/]+)', profile_url)
                    if match:
                        username = match.group(1)
                        print(f"   ✅ Extracted username: {username}")
                else:
                    print(f"   ❌ Could not find profile link")
                    return []
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return []
        
        # Navigate to profile
        print(f"   Navigating to: {profile_url}")
        await page.goto(profile_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        print(f"   ✅ Navigated to profile")
        
        # Step 5: Scroll và collect thread_ids
        print(f"\n📋 Step 5: Collecting thread_ids...")
        print(f"   Scrolling {scroll_pages} times to load posts...")
        
        thread_ids = []
        seen_thread_ids = set()
        scroll_count = 0
        
        # User-provided XPath cho bài post đầu tiên
        post_link_xpath = "//*[@id=\"barcelona-page-layout\"]/div/div/div[2]/div[1]/div[5]/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]/div/div/span/a"
        
        while len(thread_ids) < limit and scroll_count < scroll_pages:
            try:
                # Wait for posts to load
                await asyncio.sleep(2)
                
                # Find all post links với nhiều selectors
                post_selectors = [
                    # User-provided XPath (chỉ cho bài đầu tiên, cần tìm tất cả)
                    "xpath=//*[@id=\"barcelona-page-layout\"]//a[contains(@href, '/post/')]",
                    "xpath=//a[contains(@href, '/post/')]",
                    "article a[href*='/post/']",
                    "div[role='article'] a[href*='/post/']",
                ]
                
                all_post_links = []
                for selector in post_selectors:
                    try:
                        if selector.startswith("xpath="):
                            xpath = selector.replace("xpath=", "")
                            try:
                                elements = await page.query_selector_all(f"xpath={xpath}")
                            except Exception:
                                try:
                                    result = await page.evaluate(f"""
                                        () => {{
                                            const result = document.evaluate({repr(xpath)}, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                                            const elements = [];
                                            for (let i = 0; i < result.snapshotLength; i++) {{
                                                elements.push(result.snapshotItem(i));
                                            }}
                                            return elements.map(el => ({{
                                                href: el.href || el.getAttribute('href'),
                                                text: el.textContent?.trim().substring(0, 50) || ''
                                            }}));
                                        }}
                                    """)
                                    if result:
                                        all_post_links = result
                                        break
                                except Exception:
                                    continue
                        else:
                            elements = await page.query_selector_all(selector)
                            # Convert to list of dicts
                            for el in elements:
                                try:
                                    href = await el.get_attribute("href")
                                    text = await el.text_content()
                                    if href:
                                        all_post_links.append({"href": href, "text": text[:50] if text else ""})
                                except Exception:
                                    continue
                        
                        if all_post_links:
                            break
                    except Exception as e:
                        logger.log_step(
                            step="GET_THREAD_IDS_FROM_PROFILE",
                            result="WARNING",
                            error=f"Error with selector {selector}: {str(e)}"
                        )
                        continue
                
                # Process post links
                for idx, post_link in enumerate(all_post_links):
                    if len(thread_ids) >= limit:
                        break
                    
                    href = post_link.get('href') if isinstance(post_link, dict) else None
                    if not href and hasattr(post_link, 'get_attribute'):
                        href = await post_link.get_attribute("href")
                    
                    if href and '/post/' in href:
                        # Extract thread_id
                        if '/post/' in href:
                            parts = href.split('/post/')
                            if len(parts) > 1:
                                thread_id = parts[-1].split('/')[0].split('?')[0]
                                
                                if thread_id and (thread_id.isdigit() or thread_id.isalnum()) and thread_id not in seen_thread_ids:
                                    seen_thread_ids.add(thread_id)
                                    
                                    # Extract username from href
                                    username_from_href = None
                                    import re
                                    match = re.search(r'@([^/]+)', href)
                                    if match:
                                        username_from_href = match.group(1)
                                    
                                    thread_ids.append({
                                        'thread_id': thread_id,
                                        'href': href,
                                        'username': username_from_href or username,
                                        'index': len(thread_ids) + 1
                                    })
                                    
                                    print(f"   [{len(thread_ids)}] Thread ID: {thread_id}")
                
                # Scroll để load thêm
                if len(thread_ids) < limit and scroll_count < scroll_pages - 1:
                    print(f"   Scrolling... ({scroll_count + 1}/{scroll_pages})")
                    await page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
                    await asyncio.sleep(2)
                    scroll_count += 1
                else:
                    break
                    
            except Exception as e:
                logger.log_step(
                    step="GET_THREAD_IDS_FROM_PROFILE",
                    result="ERROR",
                    error=f"Error collecting thread_ids: {str(e)}"
                )
                break
        
        print(f"\n📋 Step 6: Results")
        print(f"   ✅ Collected {len(thread_ids)} thread_ids")
        
        return thread_ids
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if browser_manager:
            try:
                await browser_manager.close()
                print(f"\n   ✅ Browser closed")
            except Exception:
                pass


async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} account_id [limit] [scroll_pages]")
        print(f"  {sys.argv[0]} 02")
        print(f"  {sys.argv[0]} 02 10")
        print(f"  {sys.argv[0]} 02 20 5")
        sys.exit(1)
    
    account_id = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    scroll_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    thread_ids = await get_thread_ids_from_profile(account_id, limit=limit, scroll_pages=scroll_pages)
    
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print_header("")
    print(f"Total thread_ids collected: {len(thread_ids)}")
    print("\nThread IDs:")
    for item in thread_ids:
        print(f"  {item['index']}. {item['thread_id']} - {item['href']}")
    print_header("")


if __name__ == "__main__":
    asyncio.run(main())
