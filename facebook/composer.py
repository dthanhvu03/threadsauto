"""
Module: facebook/composer.py

Facebook composer cho Facebook automation.
Xử lý đăng post với anti-detection behavior và UI state handling.
"""

# Standard library
import asyncio
import random
import re
from typing import Optional, Union, Callable

# Third-party
from playwright.async_api import Page, TimeoutError

# Local
from services.logger import StructuredLogger
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message,
    format_exception
)
from config import Config
from threads.types import UIState, PostResult  # Reuse types from threads
from facebook.selectors import SELECTORS, XPATH_PREFIX
from threads.behavior import BehaviorHelper  # Reuse behavior helper
from threads.ui_state import UIStateDetector  # Reuse UI state detector

# Facebook helper modules
from facebook.constants import (
    FACEBOOK_URL,
    FACEBOOK_POST_URL_PATTERN,
    FACEBOOK_MAX_CONTENT_LENGTH,
    TAG_NAME_EVAL
)
from facebook.navigation import navigate_to_facebook
from facebook.input_handler import find_and_type_input
from facebook.button_handler import (
    click_compose_button,
    click_next_button,
    click_post_button,
    click_element_with_retry
)
from facebook.verification import verify_post_success


class FacebookComposer:
    """
    Facebook composer cho Facebook automation.
    
    Xử lý đăng post với:
    - Mô phỏng hành vi anti-detection
    - Phát hiện và xử lý trạng thái UI
    - Logic retry với exponential backoff
    - Phát hiện shadow fail
    
    Attributes:
        page: Instance Playwright page
        config: Đối tượng cấu hình
        logger: Instance structured logger
        behavior: Behavior helper cho anti-detection
        ui_detector: UI state detector
    """
    
    def __init__(
        self,
        page: Page,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None,
        status_updater: Optional[Callable[[str], None]] = None
    ):
        """
        Khởi tạo Facebook composer.
        
        Args:
            page: Instance Playwright page
            config: Đối tượng cấu hình (tùy chọn)
            logger: Instance structured logger (tùy chọn)
            status_updater: Optional callback để update status message real-time cho UI
        """
        self.page = page
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="facebook_composer")
        self.behavior = BehaviorHelper(self.logger)
        self.status_updater = status_updater
        # Reuse UIStateDetector với Facebook selectors
        # Lấy Facebook selectors và inject vào UIStateDetector
        try:
            if not hasattr(self.config, 'selectors'):
                selector_version = "v1"
            elif not hasattr(self.config.selectors, 'version'):
                selector_version = "v1"
            else:
                selector_version = self.config.selectors.version
            
            facebook_selectors = SELECTORS.get(selector_version, SELECTORS["v1"])
        except Exception:
            facebook_selectors = SELECTORS.get("v1", {})
        
        # Inject Facebook selectors vào UIStateDetector
        self.ui_detector = UIStateDetector(page, self.config, self.logger, selectors=facebook_selectors)
    
    async def post_thread(
        self,
        content: str,
        max_retries: int = 3  # Unused, kept for API compatibility
    ) -> PostResult:
        """
        Đăng post lên Facebook với anti-detection behavior.
        
        Args:
            content: Nội dung post (tối đa 63,206 ký tự cho Facebook)
            max_retries: Số lần retry tối đa (unused, kept for compatibility)
        
        Returns:
            PostResult với trạng thái thành công và post_id
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="POST_FACEBOOK",
                result="IN_PROGRESS",
                content_length=len(content),
                content_hash=hash(content)
            )
            
            # Validate độ dài content
            if len(content) > FACEBOOK_MAX_CONTENT_LENGTH:
                raise ValueError(
                    f"Độ dài content {len(content)} vượt quá tối đa {FACEBOOK_MAX_CONTENT_LENGTH} ký tự"
                )
            
            # Điều hướng đến Facebook
            if self.status_updater:
                self.status_updater("🌐 Đang điều hướng đến Facebook...")
            await navigate_to_facebook(self.page, self.behavior, self.logger)
            
            # Click nút compose với safe access
            if self.status_updater:
                self.status_updater("🔘 Đang tìm nút tạo bài viết mới...")
            try:
                if not hasattr(self.config, 'selectors'):
                    selector_version = "v1"
                elif not hasattr(self.config.selectors, 'version'):
                    selector_version = "v1"
                else:
                    selector_version = self.config.selectors.version
                
                selectors = SELECTORS.get(selector_version, SELECTORS["v1"])
            except Exception as e:
                self.logger.log_step(
                    step="POST_FACEBOOK",
                    result="WARNING",
                    error=f"Error getting selector version: {safe_get_exception_message(e)}, using v1",
                    error_type=safe_get_exception_type_name(e)
                )
                selectors = SELECTORS.get("v1", {})
            
            # Click nút compose
            if self.status_updater:
                self.status_updater("🔘 Đang click nút tạo bài viết mới...")
            compose_clicked = click_compose_button(
                self.page,
                self.behavior,
                self.logger,
                selectors.get("compose_button", [])
            )
            
            if not compose_clicked:
                raise RuntimeError("Không thể click nút compose với tất cả selectors")
            
            # Chờ form compose xuất hiện (modal/dialog)
            if self.status_updater:
                self.status_updater("⏳ Đang chờ form soạn bài xuất hiện...")
            self.logger.log_step(
                step="WAIT_FOR_COMPOSE_FORM",
                result="IN_PROGRESS",
                note="Waiting for compose modal/dialog to appear"
            )
            await asyncio.sleep(1.5)
            await self.behavior.human_like_delay(1.0, 2.0)
            
            # Chờ modal/dialog xuất hiện
            try:
                # Tìm modal/dialog
                modal_selectors = [
                    "div[role='dialog']",
                    "div[aria-modal='true']",
                    "div[data-pagelet='Composer']"
                ]
                modal_found = False
                for modal_selector in modal_selectors:
                    try:
                        modal = await self.page.wait_for_selector(
                            modal_selector,
                            state="visible",
                            timeout=10000
                        )
                        if modal:
                            modal_found = True
                            self.logger.log_step(
                                step="WAIT_FOR_COMPOSE_FORM",
                                result="SUCCESS",
                                modal_selector=modal_selector,
                                note="Compose modal/dialog found"
                            )
                            break
                    except Exception:
                        continue
                
                if not modal_found:
                    self.logger.log_step(
                        step="WAIT_FOR_COMPOSE_FORM",
                        result="WARNING",
                        note="Modal/dialog not found, continuing anyway"
                    )
            except Exception as e:
                self.logger.log_step(
                    step="WAIT_FOR_COMPOSE_FORM",
                    result="WARNING",
                    error=str(e),
                    note="Error waiting for modal, continuing anyway"
                )
            
            # Tìm và gõ vào input compose
            if self.status_updater:
                self.status_updater("✍️ Đang nhập nội dung...")
            input_found = False
            
            self.logger.log_step(
                step="FIND_COMPOSE_INPUT",
                result="IN_PROGRESS"
            )
            
            for selector in selectors["compose_input"]:
                try:
                    self.logger.log_step(
                        step="TRY_COMPOSE_INPUT_SELECTOR",
                        result="IN_PROGRESS",
                        selector=selector
                    )
                    
                    # Hỗ trợ XPath selector
                    if selector.startswith(XPATH_PREFIX):
                        xpath = selector.replace(XPATH_PREFIX, "")
                        locator = self.page.locator(f"{XPATH_PREFIX}{xpath}")
                        await locator.wait_for(state="visible", timeout=10000)
                        element = await locator.element_handle()
                    else:
                        element = await self.page.wait_for_selector(
                            selector,
                            state="visible",
                            timeout=10000
                        )
                    
                    if element:
                        # Get element attributes với error handling
                        is_visible = False
                        is_editable = None
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
                            aria_placeholder = await element.get_attribute("aria-placeholder")
                        except Exception:
                            aria_placeholder = None
                        
                        # Lấy text content thực sự (không tính placeholder overlay)
                        try:
                            existing_text = await element.evaluate("""
                                el => {
                                    // Lấy text từ element chính, bỏ qua các element aria-hidden
                                    const walker = document.createTreeWalker(
                                        el,
                                        NodeFilter.SHOW_TEXT,
                                        {
                                            acceptNode: function(node) {
                                                // Skip text trong element có aria-hidden="true"
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
                            self.logger.log_step(
                                step="TRY_COMPOSE_INPUT_SELECTOR",
                                result="WARNING",
                                error=f"Error evaluating existing text: {safe_get_exception_message(e)}",
                                error_type=safe_get_exception_type_name(e)
                            )
                            existing_text_trimmed = ""
                        
                        self.logger.log_step(
                            step="TRY_COMPOSE_INPUT_SELECTOR",
                            result="FOUND",
                            selector=selector,
                            is_visible=is_visible,
                            is_editable=is_editable,
                            aria_placeholder=aria_placeholder,
                            existing_text_length=len(existing_text_trimmed),
                            existing_text_preview=existing_text_trimmed[:50] if existing_text_trimmed and len(existing_text_trimmed) > 50 else (existing_text_trimmed if existing_text_trimmed else "(empty)")
                        )
                        
                        if is_visible:
                            # Validate element: Check nếu có text thực sự (không phải placeholder)
                            if existing_text_trimmed:
                                # Nếu có text thực sự dài > 15 chars - có thể là content cũ
                                # Check aria-placeholder để confirm đây có phải compose input không
                                if len(existing_text_trimmed) > 15:
                                    aria_lower = aria_placeholder.lower() if aria_placeholder else ""
                                    is_compose_input = (
                                        "nghĩ gì" in aria_lower or
                                        "what" in aria_lower or
                                        "review" in aria_lower
                                    )
                                    
                                    if not is_compose_input:
                                        self.logger.log_step(
                                            step="VALIDATE_INPUT_ELEMENT",
                                            result="SKIPPED",
                                            selector=selector,
                                            reason=f"Element has existing text (length={len(existing_text_trimmed)}) and aria-placeholder doesn't match compose input pattern",
                                            existing_text_preview=existing_text_trimmed[:50],
                                            aria_placeholder=aria_placeholder,
                                            note="Skipping this selector, trying next"
                                        )
                                        continue
                            
                            await element.scroll_into_view_if_needed()
                            await self.behavior.human_like_delay(0.3, 0.6)
                            
                            # Thử click để activate input
                            try:
                                await element.click(timeout=5000)
                                self.logger.log_step(
                                    step="ACTIVATE_INPUT",
                                    result="SUCCESS",
                                    method="click"
                                )
                            except Exception as click_error:
                                self.logger.log_step(
                                    step="ACTIVATE_INPUT",
                                    result="WARNING",
                                    error=f"Click failed: {str(click_error)}, trying focus"
                                )
                                try:
                                    await element.focus()
                                    await asyncio.sleep(0.2)
                                    await element.click(timeout=3000)
                                except Exception:
                                    await element.focus()
                                    self.logger.log_step(
                                        step="ACTIVATE_INPUT",
                                        result="WARNING",
                                        method="focus_only"
                                    )
                            
                            await self.behavior.human_like_delay(0.2, 0.4)
                            
                            # Type content
                            await self.behavior.type_in_chunks(element, content)
                            
                            # Verify content đã được type vào input
                            try:
                                await asyncio.sleep(0.5)  # Chờ content được render
                                actual_content = await element.evaluate("el => el.textContent || el.innerText || el.value || ''")
                                actual_length = len(actual_content.strip())
                                expected_length = len(content)
                                
                                # Tính toán độ chênh lệch (cho phép sai lệch ~10% do emoji/unicode encoding)
                                length_diff = abs(actual_length - expected_length)
                                length_diff_percent = (length_diff / expected_length * 100) if expected_length > 0 else 0
                                
                                # Nếu actual_length khác expected_length quá nhiều (>20%), có thể element sai
                                if length_diff_percent > 20:
                                    self.logger.log_step(
                                        step="VERIFY_TYPED_CONTENT",
                                        result="FAILED",
                                        expected_length=expected_length,
                                        actual_length=actual_length,
                                        length_diff=length_diff,
                                        length_diff_percent=round(length_diff_percent, 2),
                                        content_preview=actual_content[:50] if len(actual_content) > 50 else actual_content,
                                        note=f"Content length mismatch ({length_diff_percent:.1f}% difference) - likely wrong element, will try next selector"
                                    )
                                    # FAIL và thử selector tiếp theo
                                    continue
                                elif actual_length == 0:
                                    self.logger.log_step(
                                        step="VERIFY_TYPED_CONTENT",
                                        result="WARNING",
                                        expected_length=expected_length,
                                        actual_length=0,
                                        note="Input appears empty after typing - content may not have been entered, trying next selector"
                                    )
                                    # Thử selector tiếp theo
                                    continue
                                else:
                                    # SUCCESS: length match (sai lệch <20%)
                                    self.logger.log_step(
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
                                self.logger.log_step(
                                    step="VERIFY_TYPED_CONTENT",
                                    result="WARNING",
                                    error=f"Could not verify content: {safe_get_exception_message(e)}, trying next selector",
                                    error_type=safe_get_exception_type_name(e)
                                )
                                # Thử selector tiếp theo nếu verification fail
                                continue
                            
                            # Chỉ đến đây nếu verification SUCCESS
                            input_found = True
                            
                            self.logger.log_step(
                                step="FIND_COMPOSE_INPUT",
                                result="SUCCESS",
                                selector=selector,
                                note="Found and verified - content typed correctly"
                            )
                            break
                except (TimeoutError, RuntimeError) as e:
                    self.logger.log_step(
                        step="TRY_COMPOSE_INPUT_SELECTOR",
                        result="FAILED",
                        selector=selector,
                        error=f"{format_exception(e)}"
                    )
                    continue
                except Exception as e:
                    self.logger.log_step(
                        step="TRY_COMPOSE_INPUT_SELECTOR",
                        result="FAILED",
                        selector=selector,
                        error=f"{format_exception(e)}"
                    )
                    continue
            
            if not input_found:
                raise RuntimeError("Không thể tìm thấy input compose với tất cả selectors")
            
            await self.behavior.human_like_delay(0.5, 1.0)
            
            # Click nút "Tiếp" (Next) - CÁCH CHUẨN NHẤT: Dùng getByRole (Playwright best practice)
            # ✅ Facebook luôn render: role="button" + aria-label="Tiếp"
            # ✅ Playwright ưu tiên accessibility → cực bền, ít gãy
            next_button_clicked = False
            
            self.logger.log_step(
                step="CLICK_NEXT_BUTTON",
                result="IN_PROGRESS",
                note="Looking for 'Tiếp' (Next) button using getByRole (Playwright best practice)"
            )
            
            # 🧠 TIP CHỐNG FAIL FACEBOOK: Chờ popup Create Post xuất hiện
            try:
                await self.page.get_by_role("dialog").wait_for(state="visible", timeout=5000)
                self.logger.debug("Create Post dialog is visible")
            except Exception:
                self.logger.debug("Create Post dialog not found or already visible, continuing...")
            
            # 🧠 TIP CHỐNG FAIL FACEBOOK: Chờ network idle (tránh click quá sớm)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                self.logger.debug("Network idle timeout, continuing...")
            
            # 🧠 TIP CHỐNG FAIL FACEBOOK: Human-like delay trước khi tìm button
            await self.behavior.human_like_delay(0.5, 1.0)
            
            # ✅ CÁCH CHUẨN NHẤT: Dùng getByRole với name="Tiếp"
            # Element có: <div role="button" aria-label="Tiếp" tabindex="0">
            # → Selector bền nhất, Facebook đổi class cũng không gãy
            # Fallback đa ngôn ngữ: Tiếp|Next|Continue (khi Facebook đổi text)
            next_button_names: list[Union[str, re.Pattern]] = [
                "Tiếp",  # Tiếng Việt (ưu tiên cao nhất)
                re.compile(r"Tiếp|Next|Continue", re.IGNORECASE),  # Regex fallback đa ngôn ngữ (case-insensitive)
            ]
            
            for button_name in next_button_names:
                try:
                    self.logger.log_step(
                        step="FIND_NEXT_BUTTON",
                        result="TRYING",
                        button_name=str(button_name),
                        method="getByRole",
                        note="Using Playwright getByRole (best practice - accessibility-based)"
                    )
                    
                    # ✅ KÈM WAIT ĐÚNG CÁCH: Facebook render chậm & async
                    # ✅ SELECTOR TỐT NHẤT: page.get_by_role("button", name="Tiếp")
                    # Vì element có: <div role="button" aria-label="Tiếp" tabindex="0">
                    # → Đây là selector bền nhất, Facebook đổi class cũng không gãy
                    next_btn = self.page.get_by_role("button", name=button_name)
                    
                    # Wait for button to be visible (timeout 15s như user khuyến nghị)
                    await next_btn.wait_for(state="visible", timeout=15000)
                    
                    self.logger.log_step(
                        step="FIND_NEXT_BUTTON",
                        result="FOUND",
                        button_name=str(button_name),
                        note="Button found and visible"
                    )
                    
                    # ✅ CHỜ NÚT ENABLE: Tránh click khi còn disabled
                    # Nếu click không ăn (Facebook hay làm vậy) - đợi nút enable
                    # Dùng selector chính xác: div[role="button"][aria-label="Tiếp"]
                    await self.page.wait_for_function(
                        """
                        () => {
                            const btn = document.querySelector('div[role="button"][aria-label="Tiếp"], div[role="button"][aria-label*="Next"], div[role="button"][aria-label*="Continue"], button[aria-label="Tiếp"], button[aria-label*="Next"], button[aria-label*="Continue"]');
                            return btn && !btn.getAttribute('aria-disabled') && !btn.hasAttribute('disabled');
                        }
                        """,
                        timeout=10000
                    )
                    
                    self.logger.log_step(
                        step="FIND_NEXT_BUTTON",
                        result="ENABLED",
                        button_name=str(button_name),
                        note="Button is enabled and ready to click"
                    )
                    
                    # Scroll into view
                    await next_btn.scroll_into_view_if_needed()
                    
                    # 🧠 TIP CHỐNG FAIL FACEBOOK: Human-like delay trước khi click
                    await self.behavior.human_like_delay(0.3, 0.6)
                    
                    # Click button
                    await next_btn.click(timeout=10000)
                    
                    next_button_clicked = True
                    self.logger.log_step(
                        step="CLICK_NEXT_BUTTON",
                        result="SUCCESS",
                        button_name=str(button_name),
                        method="getByRole",
                        note="Successfully clicked 'Tiếp' button using getByRole (Playwright best practice)"
                    )
                    break
                    
                except TimeoutError as e:
                    self.logger.log_step(
                        step="FIND_NEXT_BUTTON",
                        result="TIMEOUT",
                        button_name=str(button_name),
                        error=f"Timeout waiting for button: {safe_get_exception_message(e)}",
                        note="Trying next button name variant"
                    )
                    continue
                except Exception as e:
                    self.logger.log_step(
                        step="FIND_NEXT_BUTTON",
                        result="ERROR",
                        button_name=str(button_name),
                        error=f"Error finding/clicking button: {safe_get_exception_message(e)}",
                        note="Trying next button name variant"
                    )
                    continue
            
            # Fallback: Nếu getByRole không tìm thấy, thử dùng selectors cũ
            if not next_button_clicked and "next_button" in selectors:
                self.logger.log_step(
                    step="CLICK_NEXT_BUTTON",
                    result="FALLBACK",
                    note="getByRole failed, trying fallback selectors"
                )
                
                for selector in selectors["next_button"]:
                    try:
                        self.logger.debug(f"Trying next button selector: {selector}")
                        
                        # DEBUG: Log selector đang thử
                        self.logger.log_step(
                            step="FIND_NEXT_BUTTON",
                            result="TRYING",
                            selector=selector,
                            note="Attempting to find 'Tiếp' button"
                        )
                        
                        # Hỗ trợ XPath selector
                        if selector.startswith(XPATH_PREFIX):
                            xpath = selector.replace(XPATH_PREFIX, "")
                            
                            # Kiểm tra xem XPath đã có //div[@role='button'] chưa
                            # Nếu chưa có, đây có thể là container - cần tìm button con
                            if "//div[@role='button']" in xpath or "//button" in xpath:
                                # XPath đã trỏ đến button - dùng trực tiếp
                                locator = self.page.locator(f"{XPATH_PREFIX}{xpath}")
                                await locator.wait_for(state="visible", timeout=10000)
                                element = await locator.element_handle()
                            else:
                                # XPath trỏ đến container - TÌM BUTTON CON BÊN TRONG
                                container_locator = self.page.locator(f"{XPATH_PREFIX}{xpath}")
                                await container_locator.wait_for(state="visible", timeout=10000)
                                container = await container_locator.element_handle()
                                
                                # Tìm button "Tiếp" bên trong container
                                # Ưu tiên: aria-label="Tiếp"
                                button_selectors = [
                                    "div[role='button'][aria-label='Tiếp']",
                                    "div[role='button'][aria-label*='Tiếp']",
                                    "button[aria-label='Tiếp']",
                                    "button[aria-label*='Tiếp']",
                                    "div[role='button']:has-text('Tiếp')",
                                    "button:has-text('Tiếp')"
                                ]
                                
                                element = None
                                for btn_selector in button_selectors:
                                    try:
                                        button_inside = await container.query_selector(btn_selector)
                                        if button_inside:
                                            # Validate không phải file input
                                            tag_name = await button_inside.evaluate(TAG_NAME_EVAL)
                                            input_type = await button_inside.get_attribute("type")
                                            if not (tag_name == "input" and input_type == "file"):
                                                element = button_inside
                                                self.logger.log_step(
                                                    step="FIND_NEXT_BUTTON",
                                                    result="FOUND_CHILD",
                                                    selector=selector,
                                                    child_selector=btn_selector,
                                                    note="Found button 'Tiếp' inside container"
                                                )
                                                break
                                    except Exception:
                                        continue
                                
                                if not element:
                                    # Không tìm thấy button con - skip selector này
                                    self.logger.log_step(
                                        step="FIND_NEXT_BUTTON",
                                        result="SKIPPED",
                                        selector=selector,
                                        note="Container found but no button 'Tiếp' inside"
                                    )
                                    continue
                        else:
                            # ✅ CSS SELECTOR FALLBACK (nếu KHÔNG dùng get_by_role)
                            # Dùng: div[role="button"][aria-label="Tiếp"]
                            # ❌ TUYỆT ĐỐI KHÔNG DÙNG: .x1i10hfl, div.x78zum5 (class hash động - gãy sớm)
                            element = await self.page.wait_for_selector(
                                selector,
                                state="visible",
                                timeout=10000
                            )
                        
                        if element:
                            is_visible = await element.is_visible()
                            is_disabled = await element.get_attribute("disabled")
                            aria_disabled = await element.get_attribute("aria-disabled")
                            
                            # DEBUG: Log thông tin element trước khi validate
                            tag_name_debug = await element.evaluate(TAG_NAME_EVAL)
                            aria_label_debug = await element.get_attribute("aria-label") or ""
                            text_content_debug = await element.evaluate("el => el.textContent || el.innerText || ''")
                            
                            self.logger.log_step(
                                step="FIND_NEXT_BUTTON",
                                result="ELEMENT_FOUND",
                                selector=selector,
                                tag_name=tag_name_debug,
                                aria_label=aria_label_debug,
                                text_content=text_content_debug[:50],
                                is_visible=is_visible,
                                is_disabled=bool(is_disabled),
                                aria_disabled=aria_disabled,
                                note="Element found, validating..."
                            )
                            
                            if is_visible and not is_disabled and aria_disabled != "true":
                                # VALIDATION: Đảm bảo element là button "Tiếp", không phải file input
                                try:
                                    tag_name = await element.evaluate(TAG_NAME_EVAL)
                                    role = await element.get_attribute("role")
                                    aria_label = await element.get_attribute("aria-label")
                                    input_type = await element.get_attribute("type")
                                    text_content = await element.evaluate("el => el.textContent || el.innerText || ''")
                                    
                                    # Skip nếu là input[type="file"]
                                    if tag_name == "input" and input_type == "file":
                                        self.logger.log_step(
                                            step="VALIDATE_NEXT_BUTTON",
                                            result="SKIPPED",
                                            selector=selector,
                                            reason="Element is file input, not button",
                                            tag_name=tag_name,
                                            input_type=input_type
                                        )
                                        continue
                                    
                                    # Validate: Phải là button hoặc có role="button"
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
                                    
                                    if not is_button:
                                        self.logger.log_step(
                                            step="VALIDATE_NEXT_BUTTON",
                                            result="SKIPPED",
                                            selector=selector,
                                            reason="Element is not a button",
                                            tag_name=tag_name,
                                            role=role
                                        )
                                        continue
                                    
                                    if not has_next_text:
                                        self.logger.log_step(
                                            step="VALIDATE_NEXT_BUTTON",
                                            result="SKIPPED",
                                            selector=selector,
                                            reason="Element does not contain 'Tiếp' text",
                                            aria_label=aria_label,
                                            text_content=text_content[:50]
                                        )
                                        continue
                                    
                                    # Element đã được validate - là button "Tiếp"
                                    self.logger.log_step(
                                        step="VALIDATE_NEXT_BUTTON",
                                        result="SUCCESS",
                                        selector=selector,
                                        tag_name=tag_name,
                                        role=role,
                                        aria_label=aria_label,
                                        text_content=text_content[:50]
                                    )
                                    
                                except Exception as validation_error:
                                    self.logger.log_step(
                                        step="VALIDATE_NEXT_BUTTON",
                                        result="WARNING",
                                        selector=selector,
                                        error=f"Validation error: {str(validation_error)}",
                                        note="Skipping validation, trying to click anyway"
                                    )
                                    # Continue với click nếu validation fail (fallback)
                                
                                await element.scroll_into_view_if_needed()
                                await self.behavior.human_like_delay(0.3, 0.6)
                                
                                # Click nút "Tiếp" - DÙNG JAVASCRIPT CLICK để tránh trigger file input
                                # JavaScript click không trigger file input event như Playwright click
                                try:
                                    # Thử JavaScript click trước (an toàn nhất - không trigger file input)
                                    await element.evaluate("el => el.click()")
                                    next_button_clicked = True
                                    self.logger.log_step(
                                        step="CLICK_NEXT_BUTTON",
                                        result="SUCCESS",
                                        selector=selector,
                                        method="javascript_click",
                                        note="Clicked 'Tiếp' button using JavaScript (avoids file input trigger)"
                                    )
                                    break
                                except Exception as js_click_error:
                                    self.logger.log_step(
                                        step="CLICK_NEXT_BUTTON",
                                        result="WARNING",
                                        selector=selector,
                                        error=f"JavaScript click failed: {str(js_click_error)}, trying Playwright click"
                                    )
                                    try:
                                        # Fallback: Playwright click với offset (tránh click vào file input)
                                        await self.behavior.click_with_offset(element)
                                        next_button_clicked = True
                                        self.logger.log_step(
                                            step="CLICK_NEXT_BUTTON",
                                            result="SUCCESS",
                                            selector=selector,
                                            method="playwright_click_with_offset"
                                        )
                                        break
                                    except Exception as offset_error:
                                        self.logger.log_step(
                                            step="CLICK_NEXT_BUTTON",
                                            result="WARNING",
                                            selector=selector,
                                            error=f"Click with offset failed: {str(offset_error)}, trying direct click"
                                        )
                                        try:
                                            # Last resort: Direct click
                                            await element.click(timeout=10000)
                                            next_button_clicked = True
                                            self.logger.log_step(
                                                step="CLICK_NEXT_BUTTON",
                                                result="SUCCESS",
                                                selector=selector,
                                                method="direct_click"
                                            )
                                            break
                                        except Exception as direct_error:
                                            self.logger.log_step(
                                                step="CLICK_NEXT_BUTTON",
                                                result="FAILED",
                                                selector=selector,
                                                error=f"Direct click also failed: {str(direct_error)}"
                                            )
                                            continue
                    except (TimeoutError, RuntimeError) as e:
                        self.logger.debug(f"Next button selector '{selector}' failed: {format_exception(e)}")
                        continue
                    except Exception as e:
                        self.logger.debug(f"Next button selector '{selector}' failed: {format_exception(e)}")
                        continue
                
            # ✅ FLOW TUẦN TỰ: Phải click "Tiếp" thành công mới được tìm nút "Đăng"
            # Nếu chưa pass flow "Tiếp" → không được qua flow "Đăng"
            if not next_button_clicked:
                self.logger.log_step(
                    step="CLICK_NEXT_BUTTON",
                    result="FAILED",
                    error="Không tìm thấy hoặc không click được nút 'Tiếp'",
                    note="Flow 'Tiếp' chưa pass - không được tiếp tục tìm nút 'Đăng'"
                )
                raise RuntimeError(
                    "Không thể click nút 'Tiếp'. Flow bắt buộc phải pass bước này trước khi tìm nút 'Đăng'."
                )
            
            # Chờ UI cập nhật sau khi click "Tiếp"
            self.logger.log_step(
                step="CLICK_NEXT_BUTTON",
                result="SUCCESS",
                note="Flow 'Tiếp' đã pass - Waiting for UI to update before finding 'Đăng' button"
            )
            
            # Chờ network idle để đảm bảo Facebook đã load xong
            try:
                await self.page.wait_for_load_state("networkidle", timeout=5000)
                self.logger.debug("Network idle after clicking 'Tiếp'")
            except Exception:
                self.logger.debug("Network idle timeout after clicking 'Tiếp', continuing...")
            
            # Human-like delay để đảm bảo UI đã update
            await asyncio.sleep(1.0)
            await self.behavior.human_like_delay(0.5, 1.0)
            
            # Click nút "Đăng" (Post)
            if self.status_updater:
                self.status_updater("🔍 Đang tìm nút đăng...")
            post_button = await click_post_button(
                self.page,
                self.behavior,
                self.logger,
                selectors
            )
            
            if not post_button:
                raise RuntimeError("Không tìm thấy nút post hoặc nút bị disabled")
            
            # Click post button với retry logic
            if self.status_updater:
                self.status_updater("📤 Đang đăng bài...")
            click_success = await click_element_with_retry(
                post_button,
                self.behavior,
                self.logger,
                "POST_BUTTON"
            )
            
            if not click_success:
                raise RuntimeError("Không thể click nút post sau tất cả methods")
            
            # Verify post success
            if self.status_updater:
                self.status_updater("⏳ Đang xác minh bài đăng...")
            result = await verify_post_success(
                self.page,
                self.ui_detector,
                self.logger,
                start_time,
                content
            )
            
            if self.status_updater:
                if result.success:
                    self.status_updater(f"✅ Đăng bài thành công! Post ID: {result.thread_id or 'N/A'}")
                else:
                    self.status_updater(f"❌ Đăng bài thất bại: {result.error or 'Không rõ lỗi'}")
            
            return result
        
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="POST_FACEBOOK",
                result="ERROR",
                time_ms=elapsed_time,
                error=f"Lỗi không mong đợi: {safe_get_exception_message(e)}",
                error_type=safe_get_exception_type_name(e),
                content_hash=hash(content)
            )
            
            return PostResult(
                success=False,
                state=UIState.UNKNOWN,
                error=f"Lỗi không mong đợi: {format_exception(e)}"
            )

