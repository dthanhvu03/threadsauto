"""
Module: threads/metrics_scraper.py

Thread metrics scraper cho Threads automation.
Scrape metrics (views, likes, replies, shares) từ Threads post page.
"""

# Standard library
import asyncio
import re
from typing import Optional, Dict, Any
from datetime import datetime

# Third-party
from playwright.async_api import Page, TimeoutError

# Local
from services.logger import StructuredLogger
from config import Config
from threads.selectors import SELECTORS

# Constants
XPATH_PREFIX = 'xpath='


class ThreadMetricsScraper:
    """
    Scraper để lấy metrics từ Threads post page.
    
    Navigate đến thread URL và scrape 5 metrics:
    1. Views (Lượt xem)
    2. Likes (Thích)
    3. Replies (Trả lời)
    4. Reposts (Đăng lại)
    5. Shares (Chia sẻ)
    """
    
    def __init__(
        self,
        page: Page,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Khởi tạo metrics scraper.
        
        Args:
            page: Playwright page instance
            config: Config object
            logger: Structured logger
        """
        self.page = page
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="thread_metrics_scraper")
    
    async def fetch_metrics(
        self,
        thread_id: str,
        account_id: str,
        username: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch metrics từ Threads post page.
        
        Args:
            thread_id: Thread ID (số hoặc alphanumeric)
            account_id: Account ID
            username: Threads username (optional - sẽ extract từ page nếu không có)
            timeout: Timeout in seconds (optional - sẽ dùng từ config nếu không có)
        
        Returns:
            Dict với metrics:
            {
                "thread_id": str,
                "account_id": str,
                "views": Optional[int],      # Lượt xem
                "likes": int,                # Thích
                "replies": int,              # Trả lời
                "reposts": int,              # Đăng lại
                "shares": int,               # Chia sẻ
                "fetched_at": datetime,
                "success": bool,
                "error": Optional[str]
            }
        """
        start_time = asyncio.get_event_loop().time()
        
        # Get timeout từ config nếu không được cung cấp
        if timeout is None:
            timeout = self.config.analytics.fetch_metrics_timeout_seconds
        
        try:
            self.logger.log_step(
                step="FETCH_METRICS",
                result="IN_PROGRESS",
                thread_id=thread_id,
                account_id=account_id,
                username=username,
                timeout=timeout
            )
            
            # ⚠️ CRITICAL: Build thread URL
            # 
            # REQUIREMENTS:
            # 1. thread_id PHẢI lấy từ DATABASE (jobs.thread_id) - không được lấy từ feed hay nguồn khác
            # 2. username PHẢI lấy từ account metadata (không được lấy từ page hay nguồn khác)
            # 3. URL format: https://www.threads.com/@{username}/post/{thread_id}
            #
            # thread_id parameter đến từ jobs table trong database,
            # được truyền vào function này qua fetch_and_save_metrics() → fetch_metrics()
            # KHÔNG được extract từ feed, từ page, hoặc từ nguồn khác
            #
            # Sử dụng URL template từ config
            if username:
                thread_url = self.config.platform.threads_post_url_template.format(
                    username=username,
                    thread_id=thread_id
                )
                self.logger.log_step(
                    step="FETCH_METRICS_BUILD_URL",
                    result="SUCCESS",
                    thread_url=thread_url,
                    thread_id=thread_id,
                    username=username,
                    note=f"Building URL: thread_id from DATABASE, username from metadata"
                )
            else:
                # Try without username first, sẽ extract username từ page
                thread_url = self.config.platform.threads_post_fallback_template.format(
                    thread_id=thread_id
                )
                self.logger.log_step(
                    step="FETCH_METRICS_BUILD_URL",
                    result="WARNING",
                    thread_url=thread_url,
                    thread_id=thread_id,
                    note="Building URL without username (may not work). thread_id is from DATABASE."
                )
            
            try:
                await self.page.goto(thread_url, wait_until="networkidle", timeout=timeout * 1000)
                await asyncio.sleep(self.config.analytics.page_load_delay_seconds)  # Wait for page to fully load
                
                # ⚠️ CRITICAL VALIDATION: Check xem có đang ở đúng thread page không
                # Nếu không có thread_id trong URL → đã redirect về newsfeed hoặc trang khác
                current_url = self.page.url
                
                # Check xem URL có chứa thread_id không
                if thread_id not in current_url:
                    error_msg = f"Thread ID '{thread_id}' not found in URL after navigation. Current URL: {current_url}. Page may have redirected to newsfeed or different page."
                    self.logger.log_step(
                        step="FETCH_METRICS_VALIDATE_URL",
                        result="ERROR",
                        error=error_msg,
                        expected_thread_id=thread_id,
                        current_url=current_url,
                        thread_url=thread_url,
                        account_id=account_id
                    )
                    return {
                        "thread_id": thread_id,
                        "account_id": account_id,
                        "views": None,
                        "likes": 0,
                        "replies": 0,
                        "reposts": 0,
                        "shares": 0,
                        "fetched_at": datetime.now(),
                        "success": False,
                        "error": error_msg
                    }
                
                # ⚠️ CRITICAL VALIDATION: Check username trong URL match với username đã cung cấp
                # Nếu username không match → ERROR (browser profile đang login sai account)
                url_match = re.search(r'@([^/]+)/post', current_url)
                if url_match:
                    url_username = url_match.group(1)
                    
                    # ⚠️ SKIP: Nếu có username từ metadata nhưng URL username khác
                    # Thread_id thuộc về account khác (được gán nhầm trong database)
                    # Bỏ qua thread này và tiếp tục fetch thread tiếp theo
                    if username and username != url_username:
                        skip_msg = f"Username mismatch! Expected '{username}' (from account metadata) but URL shows '{url_username}'. Thread belongs to different account - skipping this thread."
                        self.logger.log_step(
                            step="FETCH_METRICS_USERNAME_MISMATCH",
                            result="SKIPPED",
                            expected_username=username,
                            actual_username=url_username,
                            thread_id=thread_id,
                            account_id=account_id,
                            url=current_url,
                            profile_path=f"./profiles/{account_id}/",
                            note=skip_msg
                        )
                        # Return success=False với error message để caller biết skip
                        return {
                            "thread_id": thread_id,
                            "account_id": account_id,
                            "views": None,
                            "likes": 0,
                            "replies": 0,
                            "reposts": 0,
                            "shares": 0,
                            "fetched_at": datetime.now(),
                            "success": False,
                            "error": skip_msg,
                            "skipped": True  # Flag để biết đây là skip, không phải error thật
                        }
                    
                    # Nếu không có username từ metadata, extract từ URL
                    if not username:
                        extracted_username = url_username
                        self.logger.log_step(
                            step="FETCH_METRICS_EXTRACT_USERNAME",
                            result="SUCCESS",
                            username=extracted_username,
                            thread_id=thread_id,
                            account_id=account_id,
                            url=current_url,
                            note=f"Extracted username '{extracted_username}' from URL. Saved to account metadata for future use."
                        )
                        username = extracted_username
                    else:
                        # Log để confirm username match
                        self.logger.log_step(
                            step="FETCH_METRICS_USERNAME_MATCH",
                            result="SUCCESS",
                            username=username,
                            url_username=url_username,
                            thread_id=thread_id,
                            account_id=account_id,
                            note="Username from metadata matches URL username - browser profile is correct"
                        )
                else:
                    # URL không có format @username/post/... → có thể là trang khác
                    self.logger.log_step(
                        step="FETCH_METRICS_VALIDATE_URL",
                        result="WARNING",
                        warning=f"URL does not match expected format @username/post/... Current URL: {current_url}",
                        thread_id=thread_id,
                        account_id=account_id
                    )
            except TimeoutError:
                # Try with load state instead
                await self.page.goto(thread_url, wait_until="domcontentloaded", timeout=timeout * 1000)
                await asyncio.sleep(self.config.analytics.page_load_alt_delay_seconds)
                
                # ⚠️ CRITICAL VALIDATION: Check xem có đang ở đúng thread page không
                current_url = self.page.url
                
                # Check xem URL có chứa thread_id không
                if thread_id not in current_url:
                    error_msg = f"Thread ID '{thread_id}' not found in URL after navigation (timeout). Current URL: {current_url}. Page may have redirected to newsfeed or different page."
                    self.logger.log_step(
                        step="FETCH_METRICS_VALIDATE_URL_ALT",
                        result="ERROR",
                        error=error_msg,
                        expected_thread_id=thread_id,
                        current_url=current_url,
                        thread_url=thread_url,
                        account_id=account_id
                    )
                    return {
                        "thread_id": thread_id,
                        "account_id": account_id,
                        "views": None,
                        "likes": 0,
                        "replies": 0,
                        "reposts": 0,
                        "shares": 0,
                        "fetched_at": datetime.now(),
                        "success": False,
                        "error": error_msg
                    }
                
                # ⚠️ CRITICAL VALIDATION: Check username trong URL sau timeout
                url_match = re.search(r'@([^/]+)/post', current_url)
                if url_match:
                    url_username = url_match.group(1)
                    
                    # ⚠️ CRITICAL: Nếu có username từ metadata nhưng URL username khác → ERROR
                    if username and username != url_username:
                        error_msg = f"Username mismatch after timeout! Expected '{username}' (from account metadata) but URL shows '{url_username}'. Browser profile for account_id='{account_id}' is logged into different account. Profile path: ./profiles/{account_id}/ may be logged into wrong account."
                        self.logger.log_step(
                            step="FETCH_METRICS_USERNAME_MISMATCH_ALT",
                            result="ERROR",
                            expected_username=username,
                            actual_username=url_username,
                            thread_id=thread_id,
                            account_id=account_id,
                            url=current_url,
                            profile_path=f"./profiles/{account_id}/",
                            error=error_msg
                        )
                        return {
                            "thread_id": thread_id,
                            "account_id": account_id,
                            "views": None,
                            "likes": 0,
                            "replies": 0,
                            "reposts": 0,
                            "shares": 0,
                            "fetched_at": datetime.now(),
                            "success": False,
                            "error": error_msg
                        }
                    
                    # Extract nếu chưa có username từ metadata
                    if not username:
                        extracted_username = url_username
                        self.logger.log_step(
                            step="FETCH_METRICS_EXTRACT_USERNAME_ALT",
                            result="SUCCESS",
                            username=extracted_username,
                            thread_id=thread_id,
                            account_id=account_id,
                            url=current_url,
                            note=f"Extracted username '{extracted_username}' from URL after timeout. Saved to account metadata for future use."
                        )
                        username = extracted_username
                    else:
                        # Log để confirm username match
                        self.logger.log_step(
                            step="FETCH_METRICS_USERNAME_MATCH_ALT",
                            result="SUCCESS",
                            username=username,
                            url_username=url_username,
                            thread_id=thread_id,
                            account_id=account_id,
                            note="Username from metadata matches URL username after timeout - browser profile is correct"
                        )
                else:
                    # URL không có format @username/post/... → có thể là trang khác
                    self.logger.log_step(
                        step="FETCH_METRICS_VALIDATE_URL_ALT",
                        result="WARNING",
                        warning=f"URL does not match expected format @username/post/... Current URL: {current_url}",
                        thread_id=thread_id,
                        account_id=account_id
                    )
            except Exception as e:
                self.logger.log_step(
                    step="FETCH_METRICS_NAVIGATE",
                    result="ERROR",
                    error=f"Failed to navigate to thread URL: {str(e)}",
                    error_type=type(e).__name__,
                    thread_id=thread_id
                )
                return {
                    "thread_id": thread_id,
                    "account_id": account_id,
                    "views": None,
                    "likes": 0,
                    "replies": 0,
                    "reposts": 0,  # Đăng lại
                    "shares": 0,   # Chia sẻ
                    "fetched_at": datetime.now(),
                    "success": False,
                    "error": f"Navigation failed: {str(e)}"
                }
            
            # Scrape metrics
            metrics = await self._scrape_metrics()
            
            elapsed = asyncio.get_event_loop().time() - start_time
            
            result = {
                "thread_id": thread_id,
                "account_id": account_id,
                "views": metrics.get("views"),
                "likes": metrics.get("likes", 0),
                "replies": metrics.get("replies", 0),
                "shares": metrics.get("shares", 0),
                "fetched_at": datetime.now(),
                "success": True,
                "error": None
            }
            
            # Log success (avoid duplicate named parameters)
            # Exclude fields that are already passed as named parameters to log_step
            excluded_fields = ["fetched_at", "success", "error", "thread_id", "account_id", "step", "result", "time_ms"]
            log_data = {k: v for k, v in result.items() if k not in excluded_fields}
            self.logger.log_step(
                step="FETCH_METRICS",
                result="SUCCESS",
                time_ms=elapsed * 1000,
                thread_id=thread_id,
                account_id=account_id,
                **log_data
            )
            
            return result
            
        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            self.logger.log_step(
                step="FETCH_METRICS",
                result="ERROR",
                time_ms=elapsed * 1000,
                error=f"Failed to fetch metrics: {str(e)}",
                error_type=type(e).__name__,
                thread_id=thread_id
            )
            
            return {
                "thread_id": thread_id,
                "account_id": account_id,
                "views": None,
                "likes": 0,
                "replies": 0,
                "shares": 0,  # Reposts
                "fetched_at": datetime.now(),
                "success": False,
                "error": str(e)
            }
    
    async def _scrape_metrics(self) -> Dict[str, Optional[int]]:
        """
        Scrape metrics từ current page.
        
        Returns:
            Dict với 5 metrics: views, likes, replies, reposts, shares
        """
        metrics = {
            "views": None,
            "likes": 0,
            "replies": 0,
            "reposts": 0,  # Đăng lại
            "shares": 0    # Chia sẻ
        }
        
        try:
            # Try multiple selectors for each metric
            
            # Likes (Tim) - Try multiple selectors
            # Xpath từ user: //*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[1]/div/div
            likes_selectors = [
                'xpath=//*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[1]/div/div',  # User's xpath
                'button[aria-label*="like"]',
                'button[aria-label*="Like"]',
                'a[aria-label*="like"]',
                'a[aria-label*="Like"]',
                'span[aria-label*="like"]',
                '[data-testid*="like"]',
                'button:has(svg[aria-label*="like"])',
                'button:has(svg[aria-label*="Like"])',
                'a:has(svg[aria-label*="like"])',
                'a[href*="/post"] div:has-text("like")',
                'a div:has-text("like")'
            ]
            
            for selector in likes_selectors:
                try:
                    # Handle xpath selector
                    if selector.startswith(XPATH_PREFIX):
                        xpath = selector.replace(XPATH_PREFIX, '')
                        element = await self.page.query_selector(f'{XPATH_PREFIX}{xpath}')
                    else:
                        element = await self.page.query_selector(selector)
                    
                    if element:
                        text = await element.text_content()
                        if text:
                            # Handle text like "Like397" - remove "Like" prefix if exists
                            likes_text = text.strip()
                            if likes_text.lower().startswith('like'):
                                likes_text = likes_text[4:].strip()
                            
                            likes = self._parse_number(likes_text)
                            if likes is not None:
                                metrics["likes"] = likes
                                self.logger.debug(f"Scraped likes: {text} -> {likes} (from selector: {selector})")
                                break
                except Exception as e:
                    self.logger.debug(f"Failed selector {selector}: {str(e)}")
                    continue
            
            # Replies - Try multiple selectors
            # Xpath từ user: //*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[2]/div/div
            # Full xpath: /html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[2]/div/div
            replies_selectors = [
                'xpath=//*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[2]/div/div',  # User's relative xpath
                'xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[2]/div/div',  # User's full xpath
                'button[aria-label*="reply"]',
                'button[aria-label*="Reply"]',
                'a[aria-label*="reply"]',
                'a[aria-label*="Reply"]',
                'span[aria-label*="reply"]',
                '[data-testid*="reply"]'
            ]
            
            for selector in replies_selectors:
                try:
                    # Handle xpath selector
                    if selector.startswith(XPATH_PREFIX):
                        xpath = selector.replace(XPATH_PREFIX, '')
                        element = await self.page.query_selector(f'{XPATH_PREFIX}{xpath}')
                    else:
                        element = await self.page.query_selector(selector)
                    
                    if element:
                        text = await element.text_content()
                        if text:
                            # Handle text like "Reply5" or "5 replies" - remove prefix/suffix if exists
                            replies_text = text.strip()
                            if replies_text.lower().startswith('reply'):
                                replies_text = replies_text[5:].strip()
                            if 'reply' in replies_text.lower() and not replies_text.lower().startswith('reply'):
                                # Remove "replies" suffix
                                replies_text = replies_text.lower().replace('replies', '').replace('reply', '').strip()
                            
                            replies = self._parse_number(replies_text)
                            if replies is not None:
                                metrics["replies"] = replies
                                self.logger.debug(f"Scraped replies: {text} -> {replies} (from selector: {selector})")
                                break
                except Exception as e:
                    self.logger.debug(f"Failed selector {selector}: {str(e)}")
                    continue
            
            # Reposts (Đăng lại) - Try multiple selectors
            # Xpath từ user: //*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[3]/div/div/div
            # Full xpath: /html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[3]/div/div/div
            reposts_selectors = [
                'xpath=//*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[3]/div/div/div',  # User's relative xpath
                'xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[3]/div/div/div',  # User's full xpath
                'button[aria-label*="share"]',
                'button[aria-label*="Share"]',
                'a[aria-label*="share"]',
                'a[aria-label*="Share"]',
                'span[aria-label*="share"]',
                '[data-testid*="share"]',
                'button[aria-label*="repost"]',
                'button[aria-label*="Repost"]',
                'a[aria-label*="repost"]',
                'a[aria-label*="Repost"]'
            ]
            
            for selector in reposts_selectors:
                try:
                    # Handle xpath selector
                    if selector.startswith(XPATH_PREFIX):
                        xpath = selector.replace(XPATH_PREFIX, '')
                        element = await self.page.query_selector(f'{XPATH_PREFIX}{xpath}')
                    else:
                        element = await self.page.query_selector(selector)
                    
                    if element:
                        text = await element.text_content()
                        if text:
                            # Handle text like "Repost5", "5 reposts", "Đăng lại 5", etc.
                            reposts_text = text.strip()
                            # Remove common prefixes
                            if reposts_text.lower().startswith('repost'):
                                reposts_text = reposts_text[6:].strip()
                            elif reposts_text.lower().startswith('share'):
                                reposts_text = reposts_text[5:].strip()
                            elif 'đăng lại' in reposts_text.lower():
                                reposts_text = reposts_text.lower().replace('đăng lại', '').strip()
                            
                            # Remove suffixes (prioritize repost over share)
                            if 'repost' in reposts_text.lower() and not reposts_text.lower().startswith('repost'):
                                reposts_text = reposts_text.lower().replace('reposts', '').replace('repost', '').strip()
                            if 'share' in reposts_text.lower() and not reposts_text.lower().startswith('share'):
                                reposts_text = reposts_text.lower().replace('shares', '').replace('share', '').strip()
                            
                            reposts = self._parse_number(reposts_text)
                            if reposts is not None:
                                metrics["reposts"] = reposts  # Đăng lại
                                self.logger.debug(f"Scraped reposts: {text} -> {reposts} (from selector: {selector})")
                                break
                except Exception as e:
                    self.logger.debug(f"Failed selector {selector}: {str(e)}")
                    continue
            
            # Shares (Chia sẻ) - Try multiple selectors
            # Xpath từ user: //*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[4]/div/div/div
            # Full xpath: /html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[4]/div/div/div
            # Note: div[4] = Shares (Chia sẻ), div[3] = Reposts (Đăng lại)
            shares_selectors = [
                'xpath=//*[@id="barcelona-page-layout"]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[4]/div/div/div',  # User's relative xpath
                'xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div/div[1]/div[1]/div/div/div[3]/div/div[2]/div/div[4]/div/div/div',  # User's full xpath
                'button[aria-label*="share"]',
                'button[aria-label*="Share"]',
                'a[aria-label*="share"]',
                'a[aria-label*="Share"]',
                'span[aria-label*="share"]',
                '[data-testid*="share"]'
            ]
            
            for selector in shares_selectors:
                try:
                    # Handle xpath selector
                    if selector.startswith(XPATH_PREFIX):
                        xpath = selector.replace(XPATH_PREFIX, '')
                        element = await self.page.query_selector(f'{XPATH_PREFIX}{xpath}')
                    else:
                        element = await self.page.query_selector(selector)
                    
                    if element:
                        text = await element.text_content()
                        if text:
                            # Handle text like "Share5", "5 shares", "Chia sẻ 5", etc.
                            shares_text = text.strip()
                            # Remove common prefixes
                            if shares_text.lower().startswith('share'):
                                shares_text = shares_text[5:].strip()
                            elif 'chia sẻ' in shares_text.lower():
                                shares_text = shares_text.lower().replace('chia sẻ', '').strip()
                            
                            # Remove suffixes
                            if 'share' in shares_text.lower() and not shares_text.lower().startswith('share'):
                                shares_text = shares_text.lower().replace('shares', '').replace('share', '').strip()
                            
                            shares = self._parse_number(shares_text)
                            if shares is not None:
                                metrics["shares"] = shares  # Chia sẻ
                                self.logger.debug(f"Scraped shares: {text} -> {shares} (from selector: {selector})")
                                break
                except Exception as e:
                    self.logger.debug(f"Failed selector {selector}: {str(e)}")
                    continue
            
            # Views - Usually harder to find, optional
            # Xpath từ user: //*[@id="barcelona-page-layout"]/div/div/div[1]/div[4]/div[2]/a/div
            views_selectors = [
                'xpath=//*[@id="barcelona-page-layout"]/div/div/div[1]/div[4]/div[2]/a/div',  # User's xpath (updated)
                'xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div/div[1]/div[4]/div[2]/a/div',  # Old full xpath (fallback)
                'span[aria-label*="view"]',
                'span[aria-label*="View"]',
                '[data-testid*="view"]',
                'span:has-text("views")',
                'span:has-text("Views")',
                'a[href*="/post"] div:has-text("views")',
                'a div:has-text("views")'
            ]
            
            for selector in views_selectors:
                try:
                    # Handle xpath selector
                    if selector.startswith(XPATH_PREFIX):
                        xpath = selector.replace(XPATH_PREFIX, '')
                        element = await self.page.query_selector(f'{XPATH_PREFIX}{xpath}')
                    else:
                        element = await self.page.query_selector(selector)
                    
                    if element:
                        text = await element.text_content()
                        if text:
                            # Handle text like "10.9K views" - remove "views" suffix if exists
                            views_text = text.strip()
                            if 'views' in views_text.lower():
                                # Extract number part before "views"
                                views_text = views_text.lower().replace('views', '').strip()
                            
                            views = self._parse_number(views_text)
                            if views is not None:
                                metrics["views"] = views
                                self.logger.debug(f"Scraped views: {text} -> {views} (from selector: {selector})")
                                break
                except Exception as e:
                    self.logger.debug(f"Failed selector {selector}: {str(e)}")
                    continue
            
            # Fallback: Try to get from page text content
            if metrics["likes"] == 0 or metrics["replies"] == 0 or metrics["reposts"] == 0 or metrics["shares"] == 0:
                page_content = await self.page.content()
                metrics = self._parse_from_html(page_content, metrics)
            
        except Exception as e:
            self.logger.log_step(
                step="SCRAPE_METRICS",
                result="WARNING",
                error=f"Error scraping metrics: {str(e)}",
                error_type=type(e).__name__
            )
        
        return metrics
    
    def _parse_number(self, text: str) -> Optional[int]:
        """
        Parse number từ text (handle K, M suffixes).
        
        Examples:
            "1.2K" -> 1200
            "5M" -> 5000000
            "123" -> 123
        """
        if not text:
            return None
        
        # Remove whitespace and common characters
        text = text.strip().replace(',', '').replace(' ', '')
        
        # Try direct number first
        try:
            return int(float(text))
        except ValueError:
            pass
        
        # Try with K/M suffixes
        match = re.search(r'([\d.]+)\s*([KMkm]?)', text)
        if match:
            number = float(match.group(1))
            suffix = match.group(2).upper()
            
            if suffix == 'K':
                return int(number * 1000)
            elif suffix == 'M':
                return int(number * 1000000)
            else:
                return int(number)
        
        return None
    
    def _parse_from_html(self, html: str, current_metrics: Dict[str, Optional[int]]) -> Dict[str, Optional[int]]:
        """
        Fallback: Parse metrics from HTML content.
        
        Args:
            html: HTML content
            current_metrics: Current metrics dict
        
        Returns:
            Updated metrics dict
        """
        # Look for patterns like "1.2K likes", "5 replies", etc.
        patterns = {
            "likes": [
                r'([\d.]+[KMkm]?)\s*likes?',
                r'likes?\s*([\d.]+[KMkm]?)',
            ],
            "replies": [
                r'([\d.]+[KMkm]?)\s*repl(?:ies|y)',
                r'repl(?:ies|y)\s*([\d.]+[KMkm]?)',
            ],
            "shares": [
                r'([\d.]+[KMkm]?)\s*shares?',
                r'shares?\s*([\d.]+[KMkm]?)',
            ],
            "views": [
                r'([\d.]+[KMkm]?)\s*views?',
                r'views?\s*([\d.]+[KMkm]?)',
            ]
        }
        
        for metric_name, pattern_list in patterns.items():
            if current_metrics.get(metric_name) == 0 or current_metrics.get(metric_name) is None:
                for pattern in pattern_list:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        number_str = match.group(1)
                        parsed = self._parse_number(number_str)
                        if parsed is not None:
                            current_metrics[metric_name] = parsed
                            break
        
        return current_metrics
