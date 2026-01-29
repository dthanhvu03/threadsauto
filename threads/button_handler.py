"""
Module: threads/button_handler.py

Button handling helpers cho Threads automation.
"""

# Standard library
import asyncio
from typing import Optional

# Third-party
from playwright.async_api import Page, ElementHandle, TimeoutError

# Local
from services.logger import StructuredLogger
from threads.behavior import BehaviorHelper
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message,
    format_exception
)
from threads.selectors import XPATH_PREFIX


async def click_compose_button(
    page: Page,
    behavior: BehaviorHelper,
    logger: StructuredLogger,
    selectors: list[str]
) -> bool:
    """
    Click compose button với fallback selectors.
    
    Args:
        page: Playwright page instance
        behavior: Behavior helper
        logger: Structured logger
        selectors: List of selectors để thử
    
    Returns:
        True nếu thành công, False nếu không
    """
    # #region agent log
    try:
        import json
        with open('.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"button_handler.py:click_compose_button","message":"About to call logger.log_step","data":{"logger_type":type(logger).__name__,"has_log_step":hasattr(logger,"log_step")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    logger.log_step(
        step="CLICK_COMPOSE_BUTTON",
        result="IN_PROGRESS"
    )
    # #region agent log
    try:
        import json
        with open('.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"button_handler.py:click_compose_button","message":"After calling logger.log_step","data":{"step":"CLICK_COMPOSE_BUTTON"},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    
    for selector in selectors:
        try:
            logger.debug(f"Trying compose button selector: {selector}")
            
            # Hỗ trợ XPath selector
            if selector.startswith(XPATH_PREFIX):
                xpath = selector.replace(XPATH_PREFIX, "")
                locator = page.locator(f"{XPATH_PREFIX}{xpath}")
                await locator.wait_for(state="visible", timeout=10000)
                element = await locator.element_handle()
            else:
                element = await page.wait_for_selector(
                    selector,
                    state="visible",
                    timeout=10000
                )
            
            if element:
                await element.scroll_into_view_if_needed()
                await behavior.human_like_delay(0.3, 0.6)
                await behavior.click_with_offset(element)
                
                logger.log_step(
                    step="CLICK_COMPOSE_BUTTON",
                    result="SUCCESS",
                    selector=selector
                )
                return True
        except (TimeoutError, RuntimeError) as e:
            logger.debug(f"Compose button selector '{selector}' failed: {format_exception(e)}")
            continue
        except Exception as e:
            logger.debug(f"Compose button selector '{selector}' failed: {format_exception(e)}")
            continue
    
    logger.log_step(
        step="CLICK_COMPOSE_BUTTON",
        result="FAILED",
        error="Không thể click nút compose với tất cả selectors"
    )
    return False


async def find_post_button(
    page: Page,
    logger: StructuredLogger,
    selectors: list[str],
    modal: Optional[ElementHandle] = None
) -> Optional[ElementHandle]:
    """
    Tìm post button trong modal hoặc page.
    
    Args:
        page: Playwright page instance
        logger: Structured logger
        selectors: List of selectors để thử
        modal: Optional modal element để tìm trong modal
    
    Returns:
        ElementHandle nếu tìm thấy, None nếu không
    """
    logger.log_step(
        step="FIND_POST_BUTTON",
        result="IN_PROGRESS",
        note="Looking for Post button in modal"
    )
    
    for selector in selectors:
        try:
            logger.log_step(
                step="FIND_POST_BUTTON",
                result="IN_PROGRESS",
                selector=selector,
                note="Looking for Post button in modal"
            )
            
            # Hỗ trợ XPath selector
            if selector.startswith(XPATH_PREFIX):
                xpath = selector.replace(XPATH_PREFIX, "")
                locator = page.locator(f"{XPATH_PREFIX}{xpath}")
                await locator.wait_for(state="visible", timeout=10000)
                element = await locator.element_handle()
            else:
                # Ưu tiên tìm trong modal nếu có
                element = None
                if modal:
                    try:
                        element = await modal.query_selector(selector)
                        if element and await element.is_visible():
                            logger.log_step(
                                step="FIND_POST_BUTTON",
                                result="FOUND_IN_MODAL",
                                selector=selector,
                                note="Found in modal"
                            )
                    except Exception:
                        pass
                
                # Nếu không tìm thấy trong modal, tìm toàn page
                if not element:
                    try:
                        element = await page.wait_for_selector(
                            selector,
                            state="visible",
                            timeout=10000
                        )
                    except TimeoutError:
                        # Thử tìm với state="attached" (có thể bị ẩn)
                        try:
                            element = await page.wait_for_selector(
                                selector,
                                state="attached",
                                timeout=5000
                            )
                            # Kiểm tra xem có visible không
                            if element and not await element.is_visible():
                                element = None
                        except TimeoutError:
                            element = None
            
            if element:
                is_disabled = await element.get_attribute("disabled")
                aria_disabled = await element.get_attribute("aria-disabled")
                tabindex = await element.get_attribute("tabindex")
                is_visible = await element.is_visible()
                
                if not is_visible:
                    logger.log_step(
                        step="FIND_POST_BUTTON",
                        result="WARNING",
                        selector=selector,
                        note="Element found but not visible"
                    )
                    continue
                
                # Nút Post phải không disabled và có thể click được
                if not is_disabled and aria_disabled != "true" and tabindex != "-1":
                    logger.log_step(
                        step="FIND_POST_BUTTON",
                        result="SUCCESS",
                        selector=selector,
                        is_disabled=is_disabled,
                        aria_disabled=aria_disabled,
                        tabindex=tabindex,
                        is_visible=is_visible,
                        note="Found Post button in modal - ready to click"
                    )
                    return element
                else:
                    logger.log_step(
                        step="FIND_POST_BUTTON",
                        result="WARNING",
                        selector=selector,
                        is_disabled=is_disabled,
                        aria_disabled=aria_disabled,
                        tabindex=tabindex,
                        note="Post button found but appears disabled"
                    )
        except (TimeoutError, RuntimeError) as e:
            logger.log_step(
                step="FIND_POST_BUTTON",
                result="FAILED",
                selector=selector,
                error=f"{format_exception(e)}",
                error_type=safe_get_exception_type_name(e),
                note="Trying next selector"
            )
            continue
        except Exception as e:
            logger.log_step(
                step="FIND_POST_BUTTON",
                result="FAILED",
                selector=selector,
                error=f"{format_exception(e)}",
                error_type=safe_get_exception_type_name(e),
                note="Trying next selector"
            )
            continue
    
    return None


async def click_post_button_with_retry(
    post_button: ElementHandle,
    behavior: BehaviorHelper,
    logger: StructuredLogger
) -> bool:
    """
    Click post button với nhiều methods retry.
    
    Args:
        post_button: Post button element
        behavior: Behavior helper
        logger: Structured logger
    
    Returns:
        True nếu thành công, False nếu không
    """
    await post_button.scroll_into_view_if_needed()
    await behavior.human_like_delay(0.3, 0.6)
    
    # Thử click với nhiều methods
    try:
        await behavior.click_with_offset(post_button)
        logger.log_step(
            step="CLICK_POST_BUTTON",
            result="SUCCESS",
            method="click_with_offset"
        )
        return True
    except Exception as click_error:
        logger.log_step(
            step="CLICK_POST_BUTTON",
            result="WARNING",
            error=f"Click with offset failed: {str(click_error)}, trying direct click"
        )
        try:
            await post_button.click(timeout=10000)
            logger.log_step(
                step="CLICK_POST_BUTTON",
                result="SUCCESS",
                method="direct_click"
            )
            return True
        except Exception as direct_error:
            logger.log_step(
                step="CLICK_POST_BUTTON",
                result="WARNING",
                error=f"Direct click failed: {str(direct_error)}, trying JavaScript click"
            )
            try:
                await post_button.evaluate("el => el.click()")
                logger.log_step(
                    step="CLICK_POST_BUTTON",
                    result="SUCCESS",
                    method="javascript_click"
                )
                return True
            except Exception as js_error:
                logger.log_step(
                    step="CLICK_POST_BUTTON",
                    result="ERROR",
                    error=f"All click methods failed: {str(js_error)}"
                )
                return False


async def find_add_to_thread_button(
    page: Page,
    logger: StructuredLogger,
    selectors: list[str],
    timeout: int = 10000
) -> Optional[ElementHandle]:
    """
    Tìm nút "Thêm vào thread" (Add to thread).
    
    Args:
        page: Playwright page instance
        logger: Structured logger
        selectors: List of selectors để thử
        timeout: Timeout cho mỗi selector (ms)
    
    Returns:
        ElementHandle nếu tìm thấy, None nếu không
    """
    logger.log_step(
        step="FIND_ADD_TO_THREAD_BUTTON",
        result="IN_PROGRESS",
        note="Looking for Add to thread button"
    )
    
    for selector in selectors:
        try:
            logger.debug(f"Trying add to thread button selector: {selector}")
            
            # Hỗ trợ XPath selector
            if selector.startswith(XPATH_PREFIX):
                xpath = selector.replace(XPATH_PREFIX, "")
                locator = page.locator(f"{XPATH_PREFIX}{xpath}")
                await locator.wait_for(state="visible", timeout=timeout)
                element = await locator.element_handle()
            else:
                element = await page.wait_for_selector(
                    selector,
                    state="visible",
                    timeout=timeout
                )
            
            if element and await element.is_visible():
                logger.log_step(
                    step="FIND_ADD_TO_THREAD_BUTTON",
                    result="SUCCESS",
                    selector=selector,
                    note="Found Add to thread button"
                )
                return element
        except (TimeoutError, RuntimeError) as e:
            logger.log_step(
                step="FIND_ADD_TO_THREAD_BUTTON",
                result="FAILED",
                selector=selector,
                error=f"{format_exception(e)}",
                error_type=safe_get_exception_type_name(e),
                note="Trying next selector"
            )
            continue
        except Exception as e:
            logger.log_step(
                step="FIND_ADD_TO_THREAD_BUTTON",
                result="FAILED",
                selector=selector,
                error=f"{format_exception(e)}",
                error_type=safe_get_exception_type_name(e),
                note="Trying next selector"
            )
            continue
    
    logger.log_step(
        step="FIND_ADD_TO_THREAD_BUTTON",
        result="FAILED",
        error="Không thể tìm thấy nút Add to thread với tất cả selectors"
    )
    return None


async def click_add_to_thread_button(
    page: Page,
    behavior: BehaviorHelper,
    logger: StructuredLogger,
    selectors: list[str]
) -> bool:
    """
    Click nút "Thêm vào thread" (Add to thread).
    
    Args:
        page: Playwright page instance
        behavior: Behavior helper
        logger: Structured logger
        selectors: List of selectors để thử
    
    Returns:
        True nếu thành công, False nếu không
    """
    logger.log_step(
        step="CLICK_ADD_TO_THREAD_BUTTON",
        result="IN_PROGRESS"
    )
    
    # Tìm button
    button = await find_add_to_thread_button(page, logger, selectors)
    
    if not button:
        logger.log_step(
            step="CLICK_ADD_TO_THREAD_BUTTON",
            result="FAILED",
            error="Không tìm thấy nút Add to thread"
        )
        return False
    
    # Click button với retry logic
    await button.scroll_into_view_if_needed()
    await behavior.human_like_delay(0.5, 1.0)
    
    try:
        await behavior.click_with_offset(button)
        logger.log_step(
            step="CLICK_ADD_TO_THREAD_BUTTON",
            result="SUCCESS",
            method="click_with_offset"
        )
        return True
    except Exception as click_error:
        logger.log_step(
            step="CLICK_ADD_TO_THREAD_BUTTON",
            result="WARNING",
            error=f"Click with offset failed: {str(click_error)}, trying direct click"
        )
        try:
            await button.click(timeout=10000)
            logger.log_step(
                step="CLICK_ADD_TO_THREAD_BUTTON",
                result="SUCCESS",
                method="direct_click"
            )
            return True
        except Exception as direct_error:
            logger.log_step(
                step="CLICK_ADD_TO_THREAD_BUTTON",
                result="WARNING",
                error=f"Direct click failed: {str(direct_error)}, trying JavaScript click"
            )
            try:
                await button.evaluate("el => el.click()")
                logger.log_step(
                    step="CLICK_ADD_TO_THREAD_BUTTON",
                    result="SUCCESS",
                    method="javascript_click"
                )
                return True
            except Exception as js_error:
                logger.log_step(
                    step="CLICK_ADD_TO_THREAD_BUTTON",
                    result="ERROR",
                    error=f"All click methods failed: {str(js_error)}"
                )
                return False

