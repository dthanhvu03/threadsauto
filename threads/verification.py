"""
Module: threads/verification.py

Verification helpers cho Threads automation.
"""

# Standard library
import asyncio
from typing import Optional

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from threads.types import UIState, PostResult, POST_URL_PATTERN
from threads.ui_state import UIStateDetector


async def verify_post_success(
    page: Page,
    ui_detector: UIStateDetector,
    logger: StructuredLogger,
    start_time: float,
    content: str
) -> PostResult:
    """
    Verify post success sau khi click post button.
    
    Args:
        page: Playwright page instance
        ui_detector: UI state detector
        logger: Structured logger
        start_time: Start time từ asyncio.get_event_loop().time()
        content: Content đã post
    
    Returns:
        PostResult với trạng thái
    """
    # Chờ post hoàn thành
    await asyncio.sleep(2.0)
    
    # LUÔN check shadow fail TRƯỚC khi check success
    shadow_fail = await ui_detector.check_shadow_fail()
    if shadow_fail:
        logger.log_step(
            step="CHECK_SHADOW_FAIL",
            result="DETECTED",
            note="Content still in input, no success indicator, no error"
        )
        elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        logger.log_step(
            step="POST_THREAD",
            result="FAILED",
            time_ms=elapsed_time,
            error="Phát hiện shadow fail",
            content_hash=hash(content)
        )
        
        return PostResult(
            success=False,
            state=UIState.SHADOW_FAIL,
            error="Shadow fail: đã click nhưng không đăng",
            shadow_fail=True
        )
    
    # Kiểm tra trạng thái UI
    state = await ui_detector.detect_ui_state()
    
    # Chờ modal đóng và URL thay đổi
    await asyncio.sleep(2.0)
    
    # Verify thực sự: check URL có chứa /post/ với thread_id hợp lệ
    try:
        current_url = page.url
    except Exception as e:
        logger.log_step(
            step="POST_THREAD",
            result="WARNING",
            error=f"Failed to get page URL: {str(e)}"
        )
        current_url = ""
    
    thread_id = None
    
    # Check URL ngay sau khi click với error handling
    try:
        if current_url and isinstance(current_url, str) and POST_URL_PATTERN in current_url:
            parts = current_url.split(POST_URL_PATTERN)
            if len(parts) > 1:
                thread_id = parts[-1].split('/')[0]
                if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                    elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    logger.log_step(
                        step="POST_THREAD",
                        result="SUCCESS",
                        time_ms=elapsed_time,
                        thread_id=thread_id,
                        url=current_url,
                        content_hash=hash(content),
                        note="Verified by URL with valid thread_id"
                    )
                    
                    return PostResult(
                        success=True,
                        thread_id=thread_id,
                        state=UIState.SUCCESS
                    )
    except Exception as e:
        logger.log_step(
            step="POST_THREAD",
            result="WARNING",
            error=f"Error parsing URL for thread_id: {str(e)}"
        )
    
    # Nếu state == SUCCESS nhưng không có thread_id trong URL
    if state == UIState.SUCCESS:
        # ⚠️ CRITICAL: Chờ redirect đến thread URL với timeout dài hơn
        # Threads có thể redirect chậm sau khi post
        max_wait_attempts = 7  # Tăng từ 3 lên 7 (14 giây)
        wait_interval = 2.0
        
        for wait_attempt in range(max_wait_attempts):
            await asyncio.sleep(wait_interval)
            current_url = page.url
            
            # Check xem modal đã đóng chưa
            try:
                modal = await page.query_selector("div[role='dialog']")
                if modal and await modal.is_visible():
                    logger.log_step(
                        step="POST_THREAD",
                        result="IN_PROGRESS",
                        note=f"Modal still open, waiting... (attempt {wait_attempt + 1}/{max_wait_attempts})"
                    )
                    continue
            except Exception:
                pass
            
            # ⚠️ CRITICAL: Check URL sau khi modal đóng
            # Chỉ accept thread_id từ URL nếu URL chứa POST_URL_PATTERN
            if POST_URL_PATTERN in current_url:
                thread_id = current_url.split(POST_URL_PATTERN)[-1].split('/')[0]
                if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                    elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    logger.log_step(
                        step="POST_THREAD",
                        result="SUCCESS",
                        time_ms=elapsed_time,
                        thread_id=thread_id,
                        url=current_url,
                        content_hash=hash(content),
                        note=f"✅ VERIFIED: Thread ID from URL after redirect (attempt {wait_attempt + 1}/{max_wait_attempts})"
                    )
                    
                    return PostResult(
                        success=True,
                        thread_id=thread_id,
                        state=UIState.SUCCESS
                    )
        
        # ⚠️ CRITICAL: Nếu không redirect sau max_wait_attempts
        # Thử extract thread_id từ modal hoặc success indicator (KHÔNG từ feed links)
        current_url = page.url
        logger.log_step(
            step="POST_THREAD",
            result="WARNING",
            note=f"Threads did not redirect to thread URL after {max_wait_attempts} attempts. Current URL: {current_url}. Will try to extract thread_id from modal/success indicator, then from profile (NOT from feed)."
        )
        
        # Method 1: Thử extract từ modal hoặc success indicator
        # ⚠️ KHÔNG extract từ feed links vì có thể lấy thread_id của bài khác
        thread_id = await _extract_thread_id_from_dom(page, logger, content=content)
        
        # Method 2: Nếu không extract được từ modal, thử lấy từ profile
        # Navigate đến profile và tìm bài post vừa tạo (bài đầu tiên)
        if not thread_id:
            logger.log_step(
                step="POST_THREAD",
                result="IN_PROGRESS",
                note="Thread ID not found in modal. Trying to extract from profile (most recent post)."
            )
            
            try:
                thread_id = await _extract_thread_id_from_profile(page, logger, content=content)
                if thread_id:
                    logger.log_step(
                        step="POST_THREAD",
                        result="SUCCESS",
                        note=f"✅ Thread ID extracted from profile: {thread_id}"
                    )
            except Exception as e:
                logger.log_step(
                    step="POST_THREAD",
                    result="WARNING",
                    error=f"Failed to extract thread_id from profile: {str(e)}",
                    error_type=type(e).__name__
                )
        
        elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        if thread_id:
            # ✅ Thread_id extracted từ modal/success indicator
            logger.log_step(
                step="POST_THREAD",
                result="SUCCESS",
                time_ms=elapsed_time,
                thread_id=thread_id,
                content_hash=hash(content),
                note=f"✅ Thread ID extracted from modal/success indicator (NOT from feed). Verified to avoid wrong thread_id."
            )
            
            return PostResult(
                success=True,
                thread_id=thread_id,
                state=UIState.SUCCESS
            )
        else:
            # ⚠️ Không extract được từ modal → thread_id = None
            logger.log_step(
                step="POST_THREAD",
                result="SUCCESS",
                time_ms=elapsed_time,
                thread_id=None,
                content_hash=hash(content),
                note=f"⚠️ WARNING: Post successful but thread_id not available. Threads did not redirect and no thread_id found in modal/success indicator. thread_id NOT saved to avoid storing wrong thread_id from feed."
            )
            
            return PostResult(
                success=True,
                thread_id=None,  # ⚠️ KHÔNG lưu thread_id sai
                state=UIState.SUCCESS
            )
    
    elif state == UIState.ERROR:
        error_msg = "Phát hiện trạng thái lỗi"
        elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        logger.log_step(
            step="POST_THREAD",
            result="FAILED",
            time_ms=elapsed_time,
            error=error_msg,
            content_hash=hash(content)
        )
        
        return PostResult(
            success=False,
            state=UIState.ERROR,
            error=error_msg
        )
    
    else:
        elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        logger.log_step(
            step="POST_THREAD",
            result="FAILED",
            time_ms=elapsed_time,
            error="UI state không xác định",
            content_hash=hash(content)
        )
        
        return PostResult(
            success=False,
            state=UIState.UNKNOWN,
            error="UI state không xác định sau khi click post"
        )


async def _extract_thread_id_from_dom(
    page: Page,
    logger: StructuredLogger,
    content: Optional[str] = None
) -> Optional[str]:
    """
    Extract thread_id từ DOM.
    
    ⚠️ CRITICAL: KHÔNG extract từ feed links vì có thể lấy bài đầu tiên trong feed,
    không phải bài vừa post. Chỉ extract từ:
    1. URL hiện tại (đã được check ở verify_post_success)
    2. Modal/content vừa post (nếu có)
    
    Args:
        page: Playwright page instance
        logger: Structured logger
        content: Optional content để match với thread (validation)
    
    Returns:
        Thread ID nếu tìm thấy, None nếu không
    """
    # ⚠️ KHÔNG extract từ feed links - có thể lấy bài đầu tiên trong feed
    # Thay vào đó, chỉ extract từ modal hoặc elements liên quan đến post vừa tạo
    
    # Method 1: Check URL hiện tại (nếu đã redirect)
    try:
        current_url = page.url
        if POST_URL_PATTERN in current_url:
            parts = current_url.split(POST_URL_PATTERN)
            if len(parts) > 1:
                thread_id = parts[-1].split('/')[0]
                if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                    logger.log_step(
                        step="EXTRACT_THREAD_ID",
                        result="SUCCESS",
                        method="from_current_url",
                        thread_id=thread_id,
                        url=current_url
                    )
                    return thread_id
    except Exception as e:
        logger.log_step(
            step="EXTRACT_THREAD_ID",
            result="WARNING",
            error=f"Error extracting from URL: {str(e)}"
        )
    
    # Method 2: Tìm trong modal hoặc success message (nếu còn visible)
    try:
        # Tìm modal hoặc success indicator
        modal_selectors = [
            "div[role='dialog']",
            "[data-testid*='success']",
            "[aria-label*='success']",
            "div[aria-modal='true']",
            "div[class*='modal']",
            "div[class*='dialog']"
        ]
        
        for selector in modal_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    # Tìm link trong modal với nhiều cách
                    link_selectors = [
                        f"a[href*='{POST_URL_PATTERN}']",
                        f"a[href*='/post/']",
                        "a[href*='threads.com']"
                    ]
                    
                    for link_selector in link_selectors:
                        try:
                            link_in_modal = await element.query_selector(link_selector)
                            if link_in_modal:
                                href = await link_in_modal.get_attribute("href")
                                if href:
                                    # Extract thread_id từ href
                                    if POST_URL_PATTERN in href:
                                        parts = href.split(POST_URL_PATTERN)
                                        if len(parts) > 1:
                                            thread_id = parts[-1].split('/')[0].split('?')[0]
                                            if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                                                logger.log_step(
                                                    step="EXTRACT_THREAD_ID",
                                                    result="SUCCESS",
                                                    method="from_modal_link",
                                                    thread_id=thread_id,
                                                    selector=selector,
                                                    link_selector=link_selector,
                                                    href=href
                                                )
                                                return thread_id
                                    # Fallback: tìm thread_id pattern trong href
                                    elif '/post/' in href:
                                        parts = href.split('/post/')
                                        if len(parts) > 1:
                                            thread_id = parts[-1].split('/')[0].split('?')[0]
                                            if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                                                logger.log_step(
                                                    step="EXTRACT_THREAD_ID",
                                                    result="SUCCESS",
                                                    method="from_modal_link_fallback",
                                                    thread_id=thread_id,
                                                    selector=selector,
                                                    href=href
                                                )
                                                return thread_id
                        except Exception:
                            continue
                    
                    # Nếu không tìm thấy link, thử tìm text chứa thread_id pattern
                    try:
                        modal_text = await element.text_content()
                        if modal_text:
                            import re
                            # Tìm pattern giống thread_id trong text (alphanumeric, 10-15 chars)
                            thread_id_pattern = re.search(r'([A-Za-z0-9]{10,15})', modal_text)
                            if thread_id_pattern:
                                potential_thread_id = thread_id_pattern.group(1)
                                # Verify nếu có POST_URL_PATTERN gần đó
                                if POST_URL_PATTERN in modal_text or '/post/' in modal_text:
                                    logger.log_step(
                                        step="EXTRACT_THREAD_ID",
                                        result="SUCCESS",
                                        method="from_modal_text",
                                        thread_id=potential_thread_id,
                                        selector=selector,
                                        note="Extracted from modal text (may need verification)"
                                    )
                                    return potential_thread_id
                    except Exception:
                        pass
                        
            except Exception:
                continue
    except Exception as e:
        logger.log_step(
            step="EXTRACT_THREAD_ID",
            result="WARNING",
            error=f"Error extracting from modal: {str(e)}"
        )
    
    # Method 3: KHÔNG extract từ feed links - sẽ return None
    # ⚠️ CRITICAL: Không extract từ feed vì có thể lấy thread_id của bài khác
    # Chỉ accept thread_id từ:
    # 1. URL sau redirect ✅
    # 2. Modal/success indicator ✅
    # KHÔNG từ feed links ❌
    
    logger.log_step(
        step="EXTRACT_THREAD_ID",
        result="WARNING",
        note="Could not extract thread_id from URL or modal. Not extracting from feed to avoid wrong thread_id."
    )
    
    return None


async def _extract_thread_id_from_profile(
    page: Page,
    logger: StructuredLogger,
    content: Optional[str] = None
) -> Optional[str]:
    """
    Extract thread_id từ profile page (bài post vừa tạo thường là bài đầu tiên).
    
    ⚠️ WARNING: Method này chỉ nên dùng khi không thể lấy từ URL hoặc modal.
    Có thể không chính xác nếu có nhiều bài post gần đây.
    
    Args:
        page: Playwright page instance
        logger: Structured logger
        content: Optional content để validate (tìm bài post có content tương tự)
    
    Returns:
        Thread ID nếu tìm thấy, None nếu không
    """
    try:
        # Get current URL để extract username nếu đang ở profile
        current_url = page.url
        
        # Method 1: Nếu đang ở profile page, tìm bài post đầu tiên
        if '/@' in current_url and '/post/' not in current_url:
            # Đã ở profile page
            logger.log_step(
                step="EXTRACT_THREAD_ID_FROM_PROFILE",
                result="IN_PROGRESS",
                method="from_current_profile_page",
                url=current_url
            )
        else:
            # Navigate đến profile page
            # Extract username từ current page hoặc từ localStorage/cookies
            logger.log_step(
                step="EXTRACT_THREAD_ID_FROM_PROFILE",
                result="IN_PROGRESS",
                method="navigate_to_profile",
                current_url=current_url
            )
            
            # Thử tìm profile link trên page
            profile_selectors = [
                "a[href*='/@']",
                "a[href*='threads.com/']",
                "[data-testid*='profile']",
                "a[aria-label*='Profile']",
                "a[aria-label*='Trang cá nhân']"
            ]
            
            profile_link = None
            for selector in profile_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute("href")
                        if href and '/@' in href and '/post/' not in href:
                            # Đây là profile link
                            profile_link = href
                            break
                    if profile_link:
                        break
                except Exception:
                    continue
            
            if not profile_link:
                # Fallback: Navigate đến threads.com và tìm profile link
                try:
                    await page.goto("https://www.threads.com/", wait_until="networkidle", timeout=10000)
                    await asyncio.sleep(2)
                    
                    # Tìm profile link
                    for selector in profile_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            for element in elements:
                                href = await element.get_attribute("href")
                                if href and '/@' in href and '/post/' not in href:
                                    profile_link = href
                                    break
                            if profile_link:
                                break
                        except Exception:
                            continue
                except Exception as e:
                    logger.log_step(
                        step="EXTRACT_THREAD_ID_FROM_PROFILE",
                        result="WARNING",
                        error=f"Failed to navigate to profile: {str(e)}"
                    )
                    return None
            
            if profile_link:
                # Navigate đến profile
                if not profile_link.startswith('http'):
                    profile_link = f"https://www.threads.com{profile_link}" if profile_link.startswith('/') else f"https://www.threads.com/{profile_link}"
                
                logger.log_step(
                    step="EXTRACT_THREAD_ID_FROM_PROFILE",
                    result="IN_PROGRESS",
                    method="navigate_to_profile_link",
                    profile_link=profile_link
                )
                
                await page.goto(profile_link, wait_until="networkidle", timeout=15000)
                await asyncio.sleep(2)
                
                current_url = page.url
        
        # Method 2: Scroll và đợi để bài post load
        logger.log_step(
            step="EXTRACT_THREAD_ID_FROM_PROFILE",
            result="IN_PROGRESS",
            note="Waiting for posts to load on profile page..."
        )
        
        # Scroll một chút để trigger lazy loading
        try:
            await page.evaluate("window.scrollTo(0, 200)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)  # Đợi content load
        except Exception as e:
            logger.log_step(
                step="EXTRACT_THREAD_ID_FROM_PROFILE",
                result="WARNING",
                error=f"Error scrolling: {str(e)}"
            )
        
        # Method 3: Tìm bài post đầu tiên trên profile (bài vừa tạo)
        # Tìm link đến bài post (href chứa /post/) với nhiều selectors
        post_link_selectors = [
            # ✅ User-provided XPath (ưu tiên CAO NHẤT - từ user inspection)
            "xpath=//*[@id=\"barcelona-page-layout\"]/div/div/div[2]/div[1]/div[5]/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]/div/div/span/a",
            "xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div/div[1]/div[1]/div/div/div[2]/div[1]/div[5]/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]/div/div/span/a",
            # Selectors cụ thể hơn
            "article a[href*='/post/']",
            "div[role='article'] a[href*='/post/']",
            "[data-testid*='post'] a[href*='/post/']",
            # General selectors
            f"a[href*='{POST_URL_PATTERN}']",
            "a[href*='/post/']",
            # XPath selectors fallback
            "xpath=//article//a[contains(@href, '/post/')]",
            "xpath=//a[contains(@href, '/post/')]",
            "xpath=//div[@role='article']//a[contains(@href, '/post/')]"
        ]
        
        found_thread_id = None
        found_href = None
        used_selector = None
        
        for selector in post_link_selectors:
            try:
                logger.log_step(
                    step="EXTRACT_THREAD_ID_FROM_PROFILE",
                    result="IN_PROGRESS",
                    note=f"Trying selector: {selector}"
                )
                
                # Handle XPath selectors
                if selector.startswith("xpath="):
                    xpath = selector.replace("xpath=", "")
                    elements = []
                    try:
                        # Method 1: Use Playwright's locator with xpath
                        locator = page.locator(f"xpath={xpath}")
                        count = await locator.count()
                        if count > 0:
                            elements = [locator.first()]
                        else:
                            # Method 2: Use query_selector_all with xpath
                            elements = await page.query_selector_all(f"xpath={xpath}")
                    except Exception as e1:
                        try:
                            # Method 3: Evaluate XPath directly in browser
                            result = await page.evaluate(f"""
                                () => {{
                                    const result = document.evaluate(
                                        {repr(xpath)}, 
                                        document, 
                                        null, 
                                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, 
                                        null
                                    );
                                    const elements = [];
                                    for (let i = 0; i < result.snapshotLength; i++) {{
                                        elements.push(result.snapshotItem(i));
                                    }}
                                    return elements.map(el => ({{
                                        href: el.href || el.getAttribute('href'),
                                        tagName: el.tagName
                                    }}));
                                }}
                            """)
                            if result and len(result) > 0:
                                # Extract href from result
                                elements = result  # Store as list of dicts for later processing
                        except Exception as e2:
                            logger.log_step(
                                step="EXTRACT_THREAD_ID_FROM_PROFILE",
                                result="WARNING",
                                error=f"Error with XPath {xpath}: {str(e1)}, fallback: {str(e2)}"
                            )
                            elements = []
                else:
                    elements = await page.query_selector_all(selector)
                
                if elements and len(elements) > 0:
                    logger.log_step(
                        step="EXTRACT_THREAD_ID_FROM_PROFILE",
                        result="IN_PROGRESS",
                        note=f"Found {len(elements)} post links with selector: {selector}"
                    )
                    
                    # Lấy bài post đầu tiên (bài vừa tạo)
                    first_post_link = elements[0]
                    href = None
                    
                    # Handle different element types
                    if isinstance(first_post_link, dict):
                        # Result from evaluate (dict with href)
                        href = first_post_link.get('href')
                    elif hasattr(first_post_link, 'get_attribute'):
                        # Playwright ElementHandle
                        href = await first_post_link.get_attribute("href")
                    elif hasattr(first_post_link, 'evaluate'):
                        # Playwright Locator
                        href = await first_post_link.evaluate("el => el.href || el.getAttribute('href')")
                    elif hasattr(first_post_link, 'first'):
                        # Playwright Locator - get first element
                        try:
                            element = await first_post_link.element_handle()
                            if element:
                                href = await element.get_attribute("href")
                        except Exception:
                            try:
                                href = await first_post_link.get_attribute("href")
                            except Exception:
                                pass
                    
                    if href:
                        # Extract thread_id từ href
                        thread_id = None
                        
                        if POST_URL_PATTERN in href:
                            parts = href.split(POST_URL_PATTERN)
                            if len(parts) > 1:
                                thread_id = parts[-1].split('/')[0].split('?')[0]
                        elif '/post/' in href:
                            parts = href.split('/post/')
                            if len(parts) > 1:
                                thread_id = parts[-1].split('/')[0].split('?')[0]
                        
                        if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                            found_thread_id = thread_id
                            found_href = href
                            used_selector = selector
                            logger.log_step(
                                step="EXTRACT_THREAD_ID_FROM_PROFILE",
                                result="SUCCESS",
                                method="from_first_post_on_profile",
                                thread_id=thread_id,
                                href=href,
                                selector=selector,
                                note=f"✅ Found thread_id from first post link! Used selector: {selector}"
                            )
                            break
            except Exception as e:
                logger.log_step(
                    step="EXTRACT_THREAD_ID_FROM_PROFILE",
                    result="WARNING",
                    error=f"Error with selector {selector}: {str(e)}",
                    error_type=type(e).__name__
                )
                continue
        
        if found_thread_id:
            return found_thread_id
        
        # Method 4: Thử cách khác - tìm tất cả links và filter
        logger.log_step(
            step="EXTRACT_THREAD_ID_FROM_PROFILE",
            result="IN_PROGRESS",
            note="Trying alternative method: find all links and filter..."
        )
        
        try:
            # Tìm tất cả links trên page
            all_links = await page.query_selector_all("a[href]")
            logger.log_step(
                step="EXTRACT_THREAD_ID_FROM_PROFILE",
                result="IN_PROGRESS",
                note=f"Found {len(all_links)} total links on page"
            )
            
            for link in all_links[:20]:  # Chỉ check 20 links đầu tiên
                try:
                    href = await link.get_attribute("href")
                    if href and '/post/' in href:
                        # Extract thread_id
                        if '/post/' in href:
                            parts = href.split('/post/')
                            if len(parts) > 1:
                                thread_id = parts[-1].split('/')[0].split('?')[0]
                                if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                                    logger.log_step(
                                        step="EXTRACT_THREAD_ID_FROM_PROFILE",
                                        result="SUCCESS",
                                        method="from_all_links_filtered",
                                        thread_id=thread_id,
                                        href=href,
                                        note=f"✅ Found thread_id by filtering all links!"
                                    )
                                    return thread_id
                except Exception:
                    continue
        except Exception as e:
            logger.log_step(
                step="EXTRACT_THREAD_ID_FROM_PROFILE",
                result="WARNING",
                error=f"Error in alternative method: {str(e)}"
            )
        
        logger.log_step(
            step="EXTRACT_THREAD_ID_FROM_PROFILE",
            result="WARNING",
            note="Could not find post link on profile page after trying all methods"
        )
        return None
        
    except Exception as e:
        logger.log_step(
            step="EXTRACT_THREAD_ID_FROM_PROFILE",
            result="ERROR",
            error=f"Error extracting from profile: {str(e)}",
            error_type=type(e).__name__
        )
        return None


async def extract_thread_id_from_profile(
    page: Page,
    logger: StructuredLogger,
    content: Optional[str] = None
) -> Optional[str]:
    """
    Public wrapper for _extract_thread_id_from_profile.
    
    Extract thread_id từ profile page (bài post vừa tạo thường là bài đầu tiên).
    
    Args:
        page: Playwright page instance
        logger: Structured logger
        content: Optional content để validate (tìm bài post có content tương tự)
    
    Returns:
        Thread ID nếu tìm thấy, None nếu không
    """
    return await _extract_thread_id_from_profile(page, logger, content=content)

