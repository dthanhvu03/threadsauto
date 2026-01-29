"""
Module: facebook/verification.py

Verification helpers cho Facebook automation.
"""

# Standard library
import asyncio
from typing import Optional

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from threads.types import UIState, PostResult
from threads.ui_state import UIStateDetector
from facebook.constants import FACEBOOK_POST_URL_PATTERN


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
    await asyncio.sleep(5.0)
    
    # Check shadow fail
    shadow_fail = await ui_detector.check_shadow_fail()
    if shadow_fail:
        elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        logger.log_step(
            step="POST_FACEBOOK",
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
    
    # Check UI state
    state = await ui_detector.detect_ui_state()
    await asyncio.sleep(2.0)
    
    # Verify post success
    current_url = page.url
    post_id = None
    
    # Try to extract post ID from URL
    if FACEBOOK_POST_URL_PATTERN in current_url:
        parts = current_url.split(FACEBOOK_POST_URL_PATTERN)
        if len(parts) > 1:
            post_id = parts[-1].split('/')[0]
    
    elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
    
    if state == UIState.SUCCESS:
        logger.log_step(
            step="POST_FACEBOOK",
            result="SUCCESS",
            time_ms=elapsed_time,
            thread_id=post_id,
            url=current_url,
            content_hash=hash(content)
        )
        
        return PostResult(
            success=True,
            thread_id=post_id,
            state=UIState.SUCCESS
        )
    elif state == UIState.ERROR:
        logger.log_step(
            step="POST_FACEBOOK",
            result="FAILED",
            time_ms=elapsed_time,
            error="Phát hiện trạng thái lỗi",
            content_hash=hash(content)
        )
        
        return PostResult(
            success=False,
            state=UIState.ERROR,
            error="Phát hiện trạng thái lỗi"
        )
    else:
        logger.log_step(
            step="POST_FACEBOOK",
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

