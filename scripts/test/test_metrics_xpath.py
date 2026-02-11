"""
Test script để verify xpath selectors cho metrics scraping.
"""

import asyncio
import sys
from pathlib import Path

# Setup path using common utility
from scripts.common import (
    setup_path,
    get_logger,
    print_header,
    print_section
)

# Add parent directory to path (must be after importing common)
setup_path()

from playwright.async_api import async_playwright
from threads.metrics_scraper import ThreadMetricsScraper


async def test_xpath_selectors():
    """Test xpath selectors cho Views và Likes."""
    
    # Input từ user
    username = input("Enter Threads username (without @): ").strip()
    # Remove @ if user accidentally included it
    if username.startswith('@'):
        username = username[1:]
        print(f"📝 Removed @ prefix, using username: {username}")
    
    thread_id = input("Enter thread ID: ").strip()
    account_id = input("Enter account ID (for profile): ").strip()
    
    if not username or not thread_id or not account_id:
        print("❌ All fields are required!")
        return
    
    logger = get_logger("test_metrics_xpath")
    
    async with async_playwright() as p:
        # Launch browser với profile
        from browser.manager import BrowserManager
        browser_manager = BrowserManager(account_id=account_id)
        
        try:
            await browser_manager.start()
            page = browser_manager.page
            
            if not page:
                page = await browser_manager.context.new_page()
            
            # Test URL
            thread_url = f"https://www.threads.com/@{username}/post/{thread_id}"
            print(f"\n🌐 Navigating to: {thread_url}")
            
            await page.goto(thread_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3.0)  # Wait for page load
            
            print(f"✅ Page loaded: {page.url}\n")
            
            # Test Views xpath (updated from user)
            views_xpath = '//*[@id="barcelona-page-layout"]/div/div/div[1]/div[4]/div[2]/a/div'
            print(f"🔍 Testing Views xpath...")
            print(f"   XPath: {views_xpath}")
            
            try:
                views_element = await page.query_selector(f'xpath={views_xpath}')
                if views_element:
                    views_text = await views_element.text_content()
                    print(f"   ✅ Found element!")
                    print(f"   📝 Text content: '{views_text}'")
                    
                    # Try to parse number
                    from threads.metrics_scraper import ThreadMetricsScraper
                    scraper = ThreadMetricsScraper(page, logger=logger)
                    views_number = scraper._parse_number(views_text)
                    print(f"   🔢 Parsed number: {views_number}")
                else:
                    print(f"   ❌ Element not found!")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            print()
            
            # Test Likes xpath (from user)
            likes_xpath = '//*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[1]/div/div'
            print(f"🔍 Testing Likes (Tim) xpath...")
            print(f"   XPath: {likes_xpath}")
            
            try:
                likes_element = await page.query_selector(f'xpath={likes_xpath}')
                if likes_element:
                    likes_text = await likes_element.text_content()
                    print(f"   ✅ Found element!")
                    print(f"   📝 Text content: '{likes_text}'")
                    
                    # Try to parse number
                    scraper = ThreadMetricsScraper(page, logger=logger)
                    likes_number = scraper._parse_number(likes_text)
                    print(f"   🔢 Parsed number: {likes_number}")
                else:
                    print(f"   ❌ Element not found!")
                    print(f"   Testing fallback selectors...")
                    
                    likes_selectors = [
                        'button[aria-label*="like"]',
                        'button[aria-label*="Like"]',
                        'a[aria-label*="like"]',
                        'span[aria-label*="like"]'
                    ]
                    
                    for selector in likes_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.text_content()
                                if text:
                                    print(f"   ✅ Found with fallback: {selector}")
                                    print(f"   📝 Text: '{text}'")
                                    break
                        except Exception:
                            continue
                    else:
                        print(f"   ❌ Could not find Likes element with fallback")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            print()
            
            # Test Replies xpath (from user)
            replies_xpath = '//*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[2]/div/div'
            print(f"🔍 Testing Replies xpath...")
            print(f"   XPath: {replies_xpath}")
            
            try:
                replies_element = await page.query_selector(f'xpath={replies_xpath}')
                if replies_element:
                    replies_text = await replies_element.text_content()
                    print(f"   ✅ Found element!")
                    print(f"   📝 Text content: '{replies_text}'")
                    
                    # Try to parse number
                    scraper = ThreadMetricsScraper(page, logger=logger)
                    replies_number = scraper._parse_number(replies_text)
                    print(f"   🔢 Parsed number: {replies_number}")
                else:
                    print(f"   ❌ Element not found!")
                    print(f"   Testing fallback selectors...")
                    
                    replies_selectors = [
                        'button[aria-label*="reply"]',
                        'a[aria-label*="reply"]',
                        'span[aria-label*="reply"]'
                    ]
                    
                    for selector in replies_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.text_content()
                                if text:
                                    print(f"   ✅ Found with fallback: {selector}")
                                    print(f"   📝 Text: '{text}'")
                                    break
                        except Exception:
                            continue
                    else:
                        print(f"   ❌ Could not find Replies element with fallback")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            print()
            
            # Test Shares (Chia sẻ) xpath (from user)
            shares_xpath = '//*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[4]/div/div/div'
            print(f"🔍 Testing Shares (Chia sẻ) xpath...")
            print(f"   XPath: {shares_xpath}")
            
            try:
                shares_element = await page.query_selector(f'xpath={shares_xpath}')
                if shares_element:
                    shares_text = await shares_element.text_content()
                    print(f"   ✅ Found element!")
                    print(f"   📝 Text content: '{shares_text}'")
                    
                    # Try to parse number
                    scraper = ThreadMetricsScraper(page, logger=logger)
                    shares_number = scraper._parse_number(shares_text)
                    print(f"   🔢 Parsed number: {shares_number}")
                else:
                    print(f"   ❌ Element not found!")
                    print(f"   Testing fallback selectors...")
                    
                    shares_selectors = [
                        'button[aria-label*="share"]',
                        'a[aria-label*="share"]',
                        'span[aria-label*="share"]'
                    ]
                    
                    for selector in shares_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.text_content()
                                if text:
                                    print(f"   ✅ Found with fallback: {selector}")
                                    print(f"   📝 Text: '{text}'")
                                    break
                        except Exception:
                            continue
                    else:
                        print(f"   ❌ Could not find Shares element with fallback")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            
            print()
            
            # Full metrics scrape test
            print(f"🔍 Testing full metrics scrape...")
            scraper = ThreadMetricsScraper(page, logger=logger)
            result = await scraper.fetch_metrics(thread_id, account_id, username=username, timeout=30)
            
            print(f"\n📊 Results:")
            print(f"   Success: {result.get('success')}")
            print(f"   Views: {result.get('views')}")
            print(f"   Likes: {result.get('likes')}")
            print(f"   Replies: {result.get('replies')}")
            print(f"   Shares: {result.get('shares')}")
            if result.get('error'):
                print(f"   Error: {result.get('error')}")
            
        finally:
            await browser_manager.close()


if __name__ == "__main__":
    print_header("", width=60)
    print("🧪 TEST METRICS XPATH SELECTORS")
    print_header("", width=60)
    print()
    asyncio.run(test_xpath_selectors())
