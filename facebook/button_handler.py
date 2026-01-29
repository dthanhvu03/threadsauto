"""
Module: facebook/button_handler.py

Button handling helpers cho Facebook automation.
"""

# Standard library
import asyncio
import re
from typing import Optional, Union

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
from facebook.selectors import XPATH_PREFIX
from facebook.constants import TAG_NAME_EVAL


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
    logger.log_step(
        step="CLICK_COMPOSE_BUTTON",
        result="IN_PROGRESS"
    )
    
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


async def click_next_button(
    page: Page,
    behavior: BehaviorHelper,
    logger: StructuredLogger,
    selectors: Optional[dict] = None
) -> bool:
    """
    Click "Tiếp" (Next) button với getByRole (best practice) và fallback.
    
    Args:
        page: Playwright page instance
        behavior: Behavior helper
        logger: Structured logger
        selectors: Optional selectors dict với "next_button" key
    
    Returns:
        True nếu thành công, False nếu không
    """
    logger.log_step(
        step="CLICK_NEXT_BUTTON",
        result="IN_PROGRESS",
        note="Looking for 'Tiếp' (Next) button using getByRole (Playwright best practice)"
    )
    
    # Chờ popup Create Post xuất hiện
    try:
        await page.get_by_role("dialog").wait_for(state="visible", timeout=5000)
        logger.debug("Create Post dialog is visible")
    except Exception:
        logger.debug("Create Post dialog not found or already visible, continuing...")
    
    # Chờ network idle
    try:
        await page.wait_for_load_state("networkidle", timeout=3000)
    except Exception:
        logger.debug("Network idle timeout, continuing...")
    
    await behavior.human_like_delay(0.5, 1.0)
    
    # Ưu tiên: Dùng getByRole với name="Tiếp"
    next_button_names: list[Union[str, re.Pattern]] = [
        "Tiếp",  # Tiếng Việt (ưu tiên cao nhất)
        re.compile(r"Tiếp|Next|Continue", re.IGNORECASE),  # Regex fallback
    ]
    
    for button_name in next_button_names:
        try:
            logger.log_step(
                step="FIND_NEXT_BUTTON",
                result="TRYING",
                button_name=str(button_name),
                method="getByRole",
                note="Using Playwright getByRole (best practice - accessibility-based)"
            )
            
            next_btn = page.get_by_role("button", name=button_name)
            await next_btn.wait_for(state="visible", timeout=15000)
            
            logger.log_step(
                step="FIND_NEXT_BUTTON",
                result="FOUND",
                button_name=str(button_name),
                note="Button found and visible"
            )
            
            # Chờ nút enable
            await page.wait_for_function(
                """
                () => {
                    const btn = document.querySelector('div[role="button"][aria-label="Tiếp"], div[role="button"][aria-label*="Next"], div[role="button"][aria-label*="Continue"], button[aria-label="Tiếp"], button[aria-label*="Next"], button[aria-label*="Continue"]');
                    return btn && !btn.getAttribute('aria-disabled') && !btn.hasAttribute('disabled');
                }
                """,
                timeout=10000
            )
            
            logger.log_step(
                step="FIND_NEXT_BUTTON",
                result="ENABLED",
                button_name=str(button_name),
                note="Button is enabled and ready to click"
            )
            
            await next_btn.scroll_into_view_if_needed()
            await behavior.human_like_delay(0.3, 0.6)
            await next_btn.click(timeout=10000)
            
            logger.log_step(
                step="CLICK_NEXT_BUTTON",
                result="SUCCESS",
                button_name=str(button_name),
                method="getByRole",
                note="Successfully clicked 'Tiếp' button using getByRole (Playwright best practice)"
            )
            return True
            
        except TimeoutError as e:
            logger.log_step(
                step="FIND_NEXT_BUTTON",
                result="TIMEOUT",
                button_name=str(button_name),
                error=f"Timeout waiting for button: {safe_get_exception_message(e)}",
                note="Trying next button name variant"
            )
            continue
        except Exception as e:
            logger.log_step(
                step="FIND_NEXT_BUTTON",
                result="ERROR",
                button_name=str(button_name),
                error=f"Error finding/clicking button: {safe_get_exception_message(e)}",
                note="Trying next button name variant"
            )
            continue
    
    # Fallback: Nếu getByRole không tìm thấy, thử dùng selectors cũ
    if selectors and "next_button" in selectors:
        logger.log_step(
            step="CLICK_NEXT_BUTTON",
            result="FALLBACK",
            note="getByRole failed, trying fallback selectors"
        )
        
        for selector in selectors["next_button"]:
            try:
                logger.debug(f"Trying next button selector: {selector}")
                
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
                    is_visible = await element.is_visible()
                    is_disabled = await element.get_attribute("disabled")
                    aria_disabled = await element.get_attribute("aria-disabled")
                    
                    if is_visible and not is_disabled and aria_disabled != "true":
                        # Validate element
                        try:
                            tag_name = await element.evaluate(TAG_NAME_EVAL)
                            role = await element.get_attribute("role")
                            aria_label = await element.get_attribute("aria-label")
                            input_type = await element.get_attribute("type")
                            text_content = await element.evaluate("el => el.textContent || el.innerText || ''")
                            
                            # Skip nếu là input[type="file"]
                            if tag_name == "input" and input_type == "file":
                                continue
                            
                            # Validate: Phải là button
                            is_button = (
                                tag_name == "button" or 
                                role == "button" or
                                (tag_name == "div" and role == "button")
                            )
                            
                            # Validate: Phải có aria-label="Tiếp" hoặc text chứa "Tiếp"
                            has_next_text = (
                                (aria_label and "Tiếp" in aria_label) or
                                "Tiếp" in text_content or
                                "Next" in text_content
                            )
                            
                            if not is_button or not has_next_text:
                                continue
                        except Exception:
                            pass  # Continue với click nếu validation fail
                        
                        await element.scroll_into_view_if_needed()
                        await behavior.human_like_delay(0.3, 0.6)
                        
                        # Thử JavaScript click trước
                        try:
                            await element.evaluate("el => el.click()")
                            logger.log_step(
                                step="CLICK_NEXT_BUTTON",
                                result="SUCCESS",
                                selector=selector,
                                method="javascript_click"
                            )
                            return True
                        except Exception:
                            try:
                                await behavior.click_with_offset(element)
                                logger.log_step(
                                    step="CLICK_NEXT_BUTTON",
                                    result="SUCCESS",
                                    selector=selector,
                                    method="playwright_click_with_offset"
                                )
                                return True
                            except Exception:
                                await element.click(timeout=10000)
                                logger.log_step(
                                    step="CLICK_NEXT_BUTTON",
                                    result="SUCCESS",
                                    selector=selector,
                                    method="direct_click"
                                )
                                return True
            except Exception:
                continue
    
    logger.log_step(
        step="CLICK_NEXT_BUTTON",
        result="FAILED",
        error="Không tìm thấy hoặc không click được nút 'Tiếp'"
    )
    return False


async def click_post_button(
    page: Page,
    behavior: BehaviorHelper,
    logger: StructuredLogger,
    selectors: Optional[dict] = None
) -> Optional[ElementHandle]:
    """
    Click "Đăng" (Post) button với getByRole (best practice) và fallback.
    
    Args:
        page: Playwright page instance
        behavior: Behavior helper
        logger: Structured logger
        selectors: Optional selectors dict với "post_button" key
    
    Returns:
        ElementHandle nếu tìm thấy, None nếu không
    """
    logger.log_step(
        step="FIND_POST_BUTTON",
        result="IN_PROGRESS",
        note="Looking for 'Đăng' (Post) button"
    )
    
    # Ưu tiên: Dùng getByRole
    post_button_names: list[Union[str, re.Pattern]] = [
        "Đăng",  # Tiếng Việt
        "Post",  # Tiếng Anh
        re.compile(r"Đăng|Post|Publish", re.IGNORECASE),
    ]
    
    for button_name in post_button_names:
        try:
            post_btn = page.get_by_role("button", name=button_name)
            await post_btn.wait_for(state="visible", timeout=10000)
            
            # Chờ nút enable
            await page.wait_for_function(
                f"""
                () => {{
                    const btn = document.querySelector('div[role="button"][aria-label*="{button_name}"], button[aria-label*="{button_name}"]');
                    return btn && !btn.getAttribute('aria-disabled') && !btn.hasAttribute('disabled');
                }}
                """,
                timeout=10000
            )
            
            is_disabled = await post_btn.get_attribute("disabled")
            aria_disabled = await post_btn.get_attribute("aria-disabled")
            tabindex = await post_btn.get_attribute("tabindex")
            
            if not is_disabled and aria_disabled != "true" and tabindex != "-1":
                element = await post_btn.element_handle()
                logger.log_step(
                    step="FIND_POST_BUTTON",
                    result="SUCCESS",
                    button_name=str(button_name),
                    method="getByRole"
                )
                return element
        except Exception:
            continue
    
    # Fallback: Dùng selectors cũ
    if selectors and "post_button" in selectors:
        for selector in selectors["post_button"]:
            try:
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
                    is_disabled = await element.get_attribute("disabled")
                    aria_disabled = await element.get_attribute("aria-disabled")
                    tabindex = await element.get_attribute("tabindex")
                    is_visible = await element.is_visible()
                    
                    if is_visible and not is_disabled and aria_disabled != "true" and tabindex != "-1":
                        logger.log_step(
                            step="FIND_POST_BUTTON",
                            result="SUCCESS",
                            selector=selector
                        )
                        return element
            except Exception:
                continue
    
    logger.log_step(
        step="FIND_POST_BUTTON",
        result="FAILED",
        error="Không tìm thấy nút post hoặc nút bị disabled"
    )
    return None


async def click_element_with_retry(
    element: ElementHandle,
    behavior: BehaviorHelper,
    logger: StructuredLogger,
    element_name: str = "element"
) -> bool:
    """
    Click element với nhiều methods retry.
    
    Args:
        element: ElementHandle để click
        behavior: Behavior helper
        logger: Structured logger
        element_name: Tên element để log
    
    Returns:
        True nếu thành công, False nếu không
    """
    await element.scroll_into_view_if_needed()
    await behavior.human_like_delay(0.3, 0.6)
    
    try:
        await behavior.click_with_offset(element)
        logger.log_step(
            step=f"CLICK_{element_name.upper()}",
            result="SUCCESS",
            method="click_with_offset"
        )
        return True
    except Exception as click_error:
        logger.log_step(
            step=f"CLICK_{element_name.upper()}",
            result="WARNING",
            error=f"Click with offset failed: {str(click_error)}, trying direct click"
        )
        try:
            await element.click(timeout=10000)
            logger.log_step(
                step=f"CLICK_{element_name.upper()}",
                result="SUCCESS",
                method="direct_click"
            )
            return True
        except Exception as direct_error:
            logger.log_step(
                step=f"CLICK_{element_name.upper()}",
                result="WARNING",
                error=f"Direct click failed: {str(direct_error)}, trying JavaScript click"
            )
            try:
                await element.evaluate("el => el.click()")
                logger.log_step(
                    step=f"CLICK_{element_name.upper()}",
                    result="SUCCESS",
                    method="javascript_click"
                )
                return True
            except Exception as js_error:
                logger.log_step(
                    step=f"CLICK_{element_name.upper()}",
                    result="ERROR",
                    error=f"All click methods failed: {str(js_error)}"
                )
                return False

