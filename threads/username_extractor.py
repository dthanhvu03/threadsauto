"""
Module: threads/username_extractor.py

Utility để extract username từ Threads profile page.
Navigate đến https://www.threads.com/, tìm "Trang cá nhân" link, và extract username.
"""

# Standard library
import asyncio
import re
from typing import Optional, Dict, Any

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from config import Config


class UsernameExtractor:
    """
    Extract username từ Threads profile page.
    
    Flow:
    1. Navigate đến https://www.threads.com/
    2. Tìm "Trang cá nhân" link (profile link)
    3. Extract username từ link href hoặc text
    4. Return username
    """
    
    def __init__(
        self,
        page: Page,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize username extractor.
        
        Args:
            page: Playwright page instance
            config: Config object
            logger: Structured logger instance
        """
        self.page = page
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="username_extractor")
    
    async def extract_username(
        self,
        account_id: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Extract username từ Threads profile page.
        
        Args:
            account_id: Account ID để log
            timeout: Timeout cho navigation và element waiting (seconds, optional - sẽ dùng từ config nếu không có)
        
        Returns:
            Username string (không có @ prefix) hoặc None nếu không tìm thấy
        
        Flow:
        1. Navigate đến https://www.threads.com/
        2. Tìm "Trang cá nhân" link với XPath
        3. Click vào link (hoặc extract từ href)
        4. Extract username từ link href hoặc profile page URL
        """
        start_time = asyncio.get_event_loop().time()
        
        # Get timeout từ config nếu không được cung cấp
        if timeout is None:
            timeout = self.config.analytics.username_extraction_timeout_seconds
        
        try:
            self.logger.log_step(
                step="EXTRACT_USERNAME",
                result="IN_PROGRESS",
                account_id=account_id,
                timeout=timeout
            )
            
            # Step 1: Navigate đến profile URL từ config
            try:
                await self.page.goto(
                    self.config.platform.threads_profile_url,
                    wait_until="networkidle",
                    timeout=timeout * 1000
                )
                await asyncio.sleep(self.config.analytics.username_page_load_delay_seconds)  # Wait for page to fully load
                
                # Check if page loaded correctly (not login page)
                current_url = self.page.url
                page_title = await self.page.title()
                
                self.logger.log_step(
                    step="EXTRACT_USERNAME_NAVIGATE",
                    result="SUCCESS",
                    url=current_url,
                    title=page_title,
                    account_id=account_id
                )
            except Exception as e:
                self.logger.log_step(
                    step="EXTRACT_USERNAME_NAVIGATE",
                    result="FAILED",
                    error=f"Failed to navigate to threads.com: {str(e)}",
                    error_type=type(e).__name__,
                    account_id=account_id
                )
                return None
            
            # Step 2: Tìm "Trang cá nhân" link với XPath
            # XPath: //*[@id="mount_0_0_8e"]/div/div/div[2]/div[1]/div[2]/div[5]/a/div
            profile_link_selectors = [
                # User-provided XPath
                "xpath=//*[@id=\"mount_0_0_8e\"]/div/div/div[2]/div[1]/div[2]/div[5]/a",
                # Fallback: Tìm link có text "Trang cá nhân" hoặc "Profile"
                "xpath=//a[contains(text(), 'Trang cá nhân')]",
                "xpath=//a[contains(text(), 'Profile')]",
                # Fallback: Tìm link trong navigation menu
                "xpath=//a[contains(@href, '/') and contains(@href, '@')]",
                # Fallback: Tìm avatar/profile icon link
                "a[aria-label*='Profile']",
                "a[aria-label*='Trang cá nhân']",
            ]
            
            profile_element = None
            profile_href = None
            used_selector = None
            
            for selector in profile_link_selectors:
                try:
                    if selector.startswith("xpath="):
                        xpath = selector.replace("xpath=", "")
                        profile_element = self.page.locator(xpath).first
                    else:
                        profile_element = self.page.locator(selector).first
                    
                    # Check if element exists and is visible
                    count = await profile_element.count()
                    if count > 0:
                        # Wait for element to be visible
                        try:
                            await profile_element.wait_for(
                                state="visible",
                                timeout=self.config.analytics.username_element_wait_timeout_ms
                            )
                        except Exception:
                            # Element exists but not visible, try next
                            self.logger.log_step(
                                step="EXTRACT_USERNAME_SELECTOR_NOT_VISIBLE",
                                result="WARNING",
                                selector=selector,
                                account_id=account_id
                            )
                            continue
                        
                        # Get href attribute
                        profile_href = await profile_element.get_attribute("href")
                        if profile_href:
                            used_selector = selector
                            self.logger.log_step(
                                step="EXTRACT_USERNAME_FOUND_PROFILE_LINK",
                                result="SUCCESS",
                                selector=selector,
                                href=profile_href,
                                account_id=account_id
                            )
                            break
                        else:
                            self.logger.log_step(
                                step="EXTRACT_USERNAME_NO_HREF",
                                result="WARNING",
                                selector=selector,
                                account_id=account_id
                            )
                    else:
                        self.logger.log_step(
                            step="EXTRACT_USERNAME_SELECTOR_NOT_FOUND",
                            result="WARNING",
                            selector=selector,
                            count=count,
                            account_id=account_id
                        )
                except Exception as e:
                    # Try next selector
                    self.logger.log_step(
                        step="EXTRACT_USERNAME_SELECTOR_ERROR",
                        result="WARNING",
                        selector=selector,
                        error=str(e),
                        error_type=type(e).__name__,
                        account_id=account_id
                    )
                    continue
            
            if not profile_href:
                # Try to get page content for debugging
                try:
                    page_content = await self.page.content()
                    # Check if page is login page
                    if "login" in page_content.lower() or "sign in" in page_content.lower():
                        self.logger.log_step(
                            step="EXTRACT_USERNAME_PROFILE_LINK_NOT_FOUND",
                            result="FAILED",
                            error="Page appears to be login page - user not logged in",
                            account_id=account_id
                        )
                    else:
                        self.logger.log_step(
                            step="EXTRACT_USERNAME_PROFILE_LINK_NOT_FOUND",
                            result="FAILED",
                            error="Could not find profile link on page - selectors did not match",
                            account_id=account_id,
                            current_url=self.page.url,
                            page_title=await self.page.title()
                        )
                except Exception:
                    self.logger.log_step(
                        step="EXTRACT_USERNAME_PROFILE_LINK_NOT_FOUND",
                        result="FAILED",
                        error="Could not find profile link on page",
                        account_id=account_id
                    )
                return None
            
            # Step 3: Extract username từ href
            # Href format: /@username hoặc https://www.threads.com/@username
            username = None
            
            # Pattern 1: /@username hoặc /@username/
            match = re.search(r'/@([^/?]+)', profile_href)
            if match:
                username = match.group(1)
            
            # Pattern 2: Extract từ full URL
            if not username:
                match = re.search(r'@([^/?]+)', profile_href)
                if match:
                    username = match.group(1)
            
            # Pattern 3: Extract từ text content nếu href không có @
            if not username and profile_element:
                try:
                    text = await profile_element.text_content()
                    if text:
                        # Tìm @username trong text
                        match = re.search(r'@([^\s]+)', text)
                        if match:
                            username = match.group(1)
                except Exception:
                    pass
            
            # Step 4: Alternative: Click vào profile link và extract từ URL
            if not username and profile_element:
                try:
                    # Click vào profile link
                    await profile_element.click(timeout=self.config.analytics.username_click_timeout_ms)
                    await asyncio.sleep(self.config.analytics.username_navigation_delay_seconds)  # Wait for navigation
                    
                    # Extract username từ current URL
                    current_url = self.page.url
                    # URL format: https://www.threads.com/@username
                    match = re.search(r'/@([^/?]+)', current_url)
                    if match:
                        username = match.group(1)
                        self.logger.log_step(
                            step="EXTRACT_USERNAME_FROM_URL",
                            result="SUCCESS",
                            url=current_url,
                            username=username,
                            account_id=account_id
                        )
                except Exception as e:
                    self.logger.log_step(
                        step="EXTRACT_USERNAME_CLICK_FAILED",
                        result="WARNING",
                        error=f"Failed to click profile link: {str(e)}",
                        error_type=type(e).__name__,
                        account_id=account_id
                    )
            
            if username:
                # Clean username (remove @ prefix nếu có)
                username = username.lstrip('@').strip()
                
                elapsed_time = asyncio.get_event_loop().time() - start_time
                self.logger.log_step(
                    step="EXTRACT_USERNAME",
                    result="SUCCESS",
                    time_ms=elapsed_time * 1000,
                    username=username,
                    account_id=account_id
                )
                return username
            else:
                self.logger.log_step(
                    step="EXTRACT_USERNAME",
                    result="FAILED",
                    time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                    error="Could not extract username from profile link",
                    account_id=account_id
                )
                return None
                
        except Exception as e:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.logger.log_step(
                step="EXTRACT_USERNAME",
                result="ERROR",
                time_ms=elapsed_time * 1000,
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return None
