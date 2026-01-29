"""
Module: threads/input_handler.py

Input handling helpers cho Threads automation.
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


async def find_and_type_input(
    page: Page,
    behavior: BehaviorHelper,
    logger: StructuredLogger,
    selectors: list[str],
    content: str
) -> tuple[bool, Optional[ElementHandle]]:
    """
    Tìm và type vào compose input với validation.
    
    Args:
        page: Playwright page instance
        behavior: Behavior helper
        logger: Structured logger
        selectors: List of selectors để thử
        content: Content để type
    
    Returns:
        Tuple (success: bool, element: Optional[ElementHandle])
    """
    # #region agent log
    try:
        import json
        with open('.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"input_handler.py:find_and_type_input","message":"About to call logger.log_step","data":{"logger_type":type(logger).__name__,"has_log_step":hasattr(logger,"log_step")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    logger.log_step(
        step="FIND_COMPOSE_INPUT",
        result="IN_PROGRESS",
        note="Trying selectors in priority order (no retry)"
    )
    # #region agent log
    try:
        import json
        with open('.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"input_handler.py:find_and_type_input","message":"After calling logger.log_step","data":{"step":"FIND_COMPOSE_INPUT"},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    
    for selector in selectors:
        try:
            logger.log_step(
                step="TRY_COMPOSE_INPUT_SELECTOR",
                result="IN_PROGRESS",
                selector=selector
            )
            
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
            
            if not element:
                continue
            
            # Get element attributes với error handling
            is_visible = False
            is_editable = None
            aria_label = None
            aria_placeholder = None
            existing_text_trimmed = ""
            
            try:
                is_visible = await element.is_visible()
            except Exception:
                is_visible = False
            
            try:
                is_editable = await element.get_attribute("contenteditable")
            except Exception:
                is_editable = None
            
            try:
                aria_label = await element.get_attribute("aria-label")
            except Exception:
                aria_label = None
            
            try:
                aria_placeholder = await element.get_attribute("aria-placeholder")
            except Exception:
                aria_placeholder = None
            
            # Lấy text content thực sự (không tính placeholder overlay)
            try:
                existing_text = await element.evaluate("""
                    el => {
                        const walker = document.createTreeWalker(
                            el,
                            NodeFilter.SHOW_TEXT,
                            {
                                acceptNode: function(node) {
                                    let parent = node.parentElement;
                                    while (parent && parent !== el) {
                                        if (parent.getAttribute('aria-hidden') === 'true') {
                                            return NodeFilter.FILTER_REJECT;
                                        }
                                        parent = parent.parentElement;
                                    }
                                    return NodeFilter.FILTER_ACCEPT;
                                }
                            }
                        );
                        let text = '';
                        let node;
                        while (node = walker.nextNode()) {
                            text += node.textContent;
                        }
                        return text.trim();
                    }
                """)
                if existing_text and isinstance(existing_text, str):
                    existing_text_trimmed = existing_text.strip()
                else:
                    existing_text_trimmed = ""
            except Exception as e:
                logger.log_step(
                    step="TRY_COMPOSE_INPUT_SELECTOR",
                    result="WARNING",
                    error=f"Error evaluating existing text: {safe_get_exception_message(e)}",
                    error_type=safe_get_exception_type_name(e)
                )
                existing_text_trimmed = ""
            
            logger.log_step(
                step="TRY_COMPOSE_INPUT_SELECTOR",
                result="FOUND",
                selector=selector,
                is_visible=is_visible,
                is_editable=is_editable,
                aria_label=aria_label,
                aria_placeholder=aria_placeholder,
                existing_text_length=len(existing_text_trimmed),
                existing_text_preview=existing_text_trimmed[:50] if existing_text_trimmed and len(existing_text_trimmed) > 50 else (existing_text_trimmed if existing_text_trimmed else "(empty)")
            )
            
            if not is_visible:
                continue
            
            # Validate element: Check nếu có text thực sự (không phải placeholder)
            if existing_text_trimmed:
                if len(existing_text_trimmed) > 15:
                    aria_lower = aria_label.lower() if aria_label else ""
                    is_compose_input = (
                        "compose" in aria_lower or 
                        "empty text field" in aria_lower or
                        "soạn bài viết" in aria_lower or
                        "type to compose" in aria_lower or
                        "trường văn bản trống" in aria_lower
                    )
                    
                    if not is_compose_input:
                        logger.log_step(
                            step="VALIDATE_INPUT_ELEMENT",
                            result="SKIPPED",
                            selector=selector,
                            reason=f"Element has existing text (length={len(existing_text_trimmed)}) and aria-label doesn't match compose input pattern",
                            existing_text_preview=existing_text_trimmed[:50],
                            aria_label=aria_label,
                            note="Skipping this selector, trying next"
                        )
                        continue
                    else:
                        logger.log_step(
                            step="VALIDATE_INPUT_ELEMENT",
                            result="INFO",
                            selector=selector,
                            existing_text_length=len(existing_text_trimmed),
                            aria_label=aria_label,
                            note="Element has existing text but aria-label matches - will try to type"
                        )
            else:
                logger.log_step(
                    step="VALIDATE_INPUT_ELEMENT",
                    result="SUCCESS",
                    selector=selector,
                    aria_label=aria_label,
                    aria_placeholder=aria_placeholder,
                    note="Element is empty - good candidate for compose input"
                )
            
            await element.scroll_into_view_if_needed()
            await behavior.human_like_delay(0.3, 0.6)
            
            # Thử click để activate input
            try:
                await element.click(timeout=5000)
                logger.log_step(
                    step="ACTIVATE_INPUT",
                    result="SUCCESS",
                    method="click"
                )
            except Exception as click_error:
                logger.log_step(
                    step="ACTIVATE_INPUT",
                    result="WARNING",
                    error=f"Click failed: {str(click_error)}, trying focus + click"
                )
                try:
                    await element.focus()
                    await asyncio.sleep(0.2)
                    await element.click(timeout=3000)
                except Exception:
                    await element.focus()
                    logger.log_step(
                        step="ACTIVATE_INPUT",
                        result="WARNING",
                        method="focus_only"
                    )
            
            await behavior.human_like_delay(0.2, 0.4)
            
            # Type content
            await behavior.type_in_chunks(element, content)
            
            # Verify content đã được type vào input
            try:
                await asyncio.sleep(0.5)  # Chờ content được render
                actual_content = await element.evaluate("el => el.textContent || el.innerText || ''")
                actual_length = len(actual_content.strip())
                expected_length = len(content)
                
                # Tính toán độ chênh lệch (cho phép sai lệch ~10% do emoji/unicode encoding)
                length_diff = abs(actual_length - expected_length)
                length_diff_percent = (length_diff / expected_length * 100) if expected_length > 0 else 0
                
                # Nếu actual_length khác expected_length quá nhiều (>20%), có thể element sai
                if length_diff_percent > 20:
                    logger.log_step(
                        step="VERIFY_TYPED_CONTENT",
                        result="FAILED",
                        expected_length=expected_length,
                        actual_length=actual_length,
                        length_diff=length_diff,
                        length_diff_percent=round(length_diff_percent, 2),
                        content_preview=actual_content[:50] if len(actual_content) > 50 else actual_content,
                        note=f"Content length mismatch ({length_diff_percent:.1f}% difference) - likely wrong element, will try next selector"
                    )
                    continue
                elif actual_length == 0:
                    logger.log_step(
                        step="VERIFY_TYPED_CONTENT",
                        result="WARNING",
                        expected_length=expected_length,
                        actual_length=0,
                        note="Input appears empty after typing - content may not have been entered, trying next selector"
                    )
                    continue
                else:
                    # SUCCESS: length match (sai lệch <20%)
                    logger.log_step(
                        step="VERIFY_TYPED_CONTENT",
                        result="SUCCESS",
                        expected_length=expected_length,
                        actual_length=actual_length,
                        length_diff=length_diff,
                        length_diff_percent=round(length_diff_percent, 2),
                        content_preview=actual_content[:50] if len(actual_content) > 50 else actual_content,
                        note="Content verified in input - length matches"
                    )
            except Exception as e:
                logger.log_step(
                    step="VERIFY_TYPED_CONTENT",
                    result="WARNING",
                    error=f"Could not verify content: {safe_get_exception_message(e)}, trying next selector",
                    error_type=safe_get_exception_type_name(e)
                )
                continue
            
            # Chỉ đến đây nếu verification SUCCESS
            logger.log_step(
                step="FIND_COMPOSE_INPUT",
                result="SUCCESS",
                selector=selector,
                note="Found and verified - content typed correctly"
            )
            return True, element
            
        except (TimeoutError, RuntimeError) as e:
            logger.log_step(
                step="TRY_COMPOSE_INPUT_SELECTOR",
                result="FAILED",
                selector=selector,
                error=f"{format_exception(e)}",
                error_type=safe_get_exception_type_name(e),
                note="Trying next selector"
            )
            continue
        except Exception as e:
            logger.log_step(
                step="TRY_COMPOSE_INPUT_SELECTOR",
                result="FAILED",
                selector=selector,
                error=f"{format_exception(e)}",
                error_type=safe_get_exception_type_name(e),
                note="Trying next selector"
            )
            continue
    
    logger.log_step(
        step="FIND_COMPOSE_INPUT",
        result="FAILED",
        error="Không thể tìm thấy input compose với tất cả selectors",
        selectors_tried=selectors
    )
    return False, None

