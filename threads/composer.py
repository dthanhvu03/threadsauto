"""
Module: threads/composer.py

Thread composer cho Threads automation.
Xử lý đăng thread với anti-detection behavior và UI state handling.
"""

# Standard library
import asyncio
import random
from typing import Optional, Callable

# Third-party
from playwright.async_api import Page, TimeoutError

# Local
from services.logger import StructuredLogger
from config import Config
from threads.types import UIState, PostResult
from threads.selectors import SELECTORS
from threads.behavior import BehaviorHelper
from threads.ui_state import UIStateDetector
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message,
    format_exception
)

# Threads helper modules
from threads.constants import THREADS_MAX_CONTENT_LENGTH
from threads.navigation import navigate_to_threads, navigate_to_compose
from threads.input_handler import find_and_type_input
from threads.button_handler import (
    click_compose_button,
    find_post_button,
    click_post_button_with_retry,
    click_add_to_thread_button
)
from threads.verification import verify_post_success


class ThreadComposer:
    """
    Thread composer cho Threads automation.
    
    Xử lý đăng thread với:
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
        Khởi tạo thread composer.
        
        Args:
            page: Instance Playwright page
            config: Đối tượng cấu hình (tùy chọn)
            logger: Instance structured logger (tùy chọn)
            status_updater: Optional callback để update status message real-time cho UI
        """
        self.page = page
        self.config = config or Config()
        # #region agent log
        try:
            import json
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"composer.py:__init__","message":"ThreadComposer.__init__ called","data":{"logger_param_type":type(logger).__name__ if logger else "None","logger_param_has_broadcast":hasattr(logger,"_broadcast") if logger else False},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        self.logger = logger or StructuredLogger(name="thread_composer")
        # #region agent log
        try:
            import json
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"composer.py:__init__","message":"After setting self.logger","data":{"self_logger_type":type(self.logger).__name__,"self_logger_has_broadcast":hasattr(self.logger,"_broadcast")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        self.behavior = BehaviorHelper(self.logger)
        self.ui_detector = UIStateDetector(page, self.config, self.logger)
        self.status_updater = status_updater
    
    async def post_thread(
        self,
        content: str,
        link_aff: Optional[str] = None,
        max_retries: int = 3  # Unused, kept for API compatibility
    ) -> PostResult:
        """
        Đăng thread với anti-detection behavior.
        
        Args:
            content: Nội dung thread chính (tối đa 500 ký tự)
            link_aff: Link affiliate để đăng trong comment (tùy chọn)
            max_retries: Số lần retry tối đa (unused, kept for compatibility)
        
        Returns:
            PostResult với trạng thái thành công và thread_id
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # #region agent log
            try:
                import json
                with open('.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"composer.py:post_thread","message":"About to call logger.log_step","data":{"logger_type":type(self.logger).__name__,"has_log_step":hasattr(self.logger,"log_step")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            self.logger.log_step(
                step="POST_THREAD",
                result="IN_PROGRESS",
                content_length=len(content),
                content_hash=hash(content)
            )
            # #region agent log
            try:
                import json
                with open('.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"composer.py:post_thread","message":"After calling logger.log_step","data":{"step":"POST_THREAD"},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            # Validate độ dài content
            if len(content) > THREADS_MAX_CONTENT_LENGTH:
                raise ValueError(
                    f"Độ dài content {len(content)} vượt quá tối đa {THREADS_MAX_CONTENT_LENGTH} ký tự"
                )
            
            # Navigate đến Threads
            if self.status_updater:
                self.status_updater("🌐 Đang điều hướng đến Threads...")
            await navigate_to_threads(self.page, self.behavior, self.logger)
            
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
                    step="POST_THREAD",
                    result="WARNING",
                    error=f"Error getting selector version: {safe_get_exception_message(e)}, using v1",
                    error_type=safe_get_exception_type_name(e)
                )
                selectors = SELECTORS.get("v1", {})
            
            # Click compose button hoặc navigate trực tiếp
            if self.status_updater:
                self.status_updater("🔘 Đang click nút tạo bài viết mới...")
            # #region agent log
            try:
                import json
                with open('.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"composer.py:post_thread","message":"Before calling click_compose_button","data":{"logger_type":type(self.logger).__name__,"logger_is_websocket":hasattr(self.logger,"_broadcast")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            compose_clicked = await click_compose_button(
                self.page,
                self.behavior,
                self.logger,
                selectors["compose_button"]
            )
            
            if not compose_clicked:
                # Thử navigate trực tiếp đến /compose nếu click button không work
                self.logger.log_step(
                    step="CLICK_COMPOSE_BUTTON",
                    result="FAILED",
                    note="Trying direct navigation to /compose"
                )
                try:
                    await navigate_to_compose(self.page, self.logger)
                except Exception as e:
                    raise RuntimeError(
                        f"Không thể click nút compose và không thể navigate đến /compose: {safe_get_exception_message(e)}"
                    ) from e
            else:
                # Nếu click button thành công nhưng không tìm thấy input, thử navigate trực tiếp
                await asyncio.sleep(1.5)
                
                # Kiểm tra xem có input không (quick check)
                quick_check = False
                for quick_selector in ["div[contenteditable='true']", "textarea"]:
                    try:
                        element = await self.page.query_selector(quick_selector)
                        if element and await element.is_visible():
                            quick_check = True
                            break
                    except Exception:
                        continue
                
                if not quick_check:
                    # Nếu không tìm thấy input sau khi click, thử navigate trực tiếp
                    self.logger.log_step(
                        step="COMPOSE_INPUT_NOT_FOUND",
                        result="WARNING",
                        note="Input not found after button click, trying direct navigation"
                    )
                    await navigate_to_compose(self.page, self.logger)
            
            # Chờ lâu hơn sau khi click compose để form load
            if compose_clicked:
                self.logger.log_step(
                    step="WAIT_FOR_COMPOSE_FORM",
                    result="IN_PROGRESS",
                    note="Waiting for compose form to appear after button click"
                )
                await self.behavior.human_like_delay(1.0, 2.0)
                
                # Chờ page load hoàn toàn
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=15000)
                    self.logger.log_step(
                        step="WAIT_FOR_COMPOSE_FORM",
                        result="SUCCESS"
                    )
                except Exception as e:
                    self.logger.log_step(
                        step="WAIT_FOR_COMPOSE_FORM",
                        result="WARNING",
                        error=f"Networkidle timeout: {safe_get_exception_message(e)}"
                    )
                    # Không bắt buộc, tiếp tục
            
            # Tìm và type vào input compose
            if self.status_updater:
                self.status_updater("✍️ Đang nhập nội dung...")
            # #region agent log
            try:
                import json
                with open('.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"composer.py:post_thread","message":"Before calling find_and_type_input","data":{"logger_type":type(self.logger).__name__,"logger_is_websocket":hasattr(self.logger,"_broadcast")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            input_found, _ = await find_and_type_input(
                self.page,
                self.behavior,
                self.logger,
                selectors["compose_input"],
                content
            )
            
            if not input_found:
                raise RuntimeError("Không thể tìm thấy input compose với tất cả selectors")
            
            await self.behavior.human_like_delay(0.5, 1.0)
            
            # ✅ THREADS WORKFLOW: Chỉ click "Thêm vào thread" khi có link_aff
            # Workflow có link_aff: Type content → Click "Thêm vào thread" → Type link_aff → Click Post
            # Workflow không có link_aff: Type content → Click Post (đăng bình thường)
            
            # Kiểm tra link_aff có nội dung không
            has_link_aff = link_aff and link_aff.strip() and link_aff.strip().lower() not in ["nan", "none", ""]
            
            if has_link_aff:
                # Có link_aff → click "Thêm vào thread" → type link_aff → post
                self.logger.log_step(
                    step="CHECK_LINK_AFF",
                    result="FOUND",
                    note="Link affiliate detected, will add to thread"
                )
                
                # Lấy selectors cho "Thêm vào thread" button
                add_to_thread_selectors = selectors.get("add_to_thread_button", [])
                if add_to_thread_selectors:
                    try:
                        if self.status_updater:
                            self.status_updater("💬 Đang tìm nút Thêm vào thread...")
                        
                        await self.behavior.human_like_delay(0.5, 1.0)
                        
                        # Click "Thêm vào thread" button
                        click_success = await click_add_to_thread_button(
                            self.page,
                            self.behavior,
                            self.logger,
                            add_to_thread_selectors
                        )
                        
                        if click_success:
                            if self.status_updater:
                                self.status_updater("✅ Đã click nút Thêm vào thread!")
                            self.logger.log_step(
                                step="CLICK_ADD_TO_THREAD_BUTTON",
                                result="SUCCESS",
                                note="Comment input should be visible now"
                            )
                            
                            # Chờ comment input xuất hiện
                            await asyncio.sleep(random.uniform(1.0, 1.5))
                            
                            # Type link_aff vào comment input
                            comment_input_selectors = selectors.get("comment_input", [])
                            if comment_input_selectors:
                                if self.status_updater:
                                    self.status_updater("💬 Đang nhập link affiliate vào comment...")
                                
                                comment_input_found, _ = await find_and_type_input(
                                    self.page,
                                    self.behavior,
                                    self.logger,
                                    comment_input_selectors,
                                    link_aff.strip()
                                )
                                
                                if comment_input_found:
                                    if self.status_updater:
                                        self.status_updater("✅ Đã nhập link affiliate vào comment!")
                                    self.logger.log_step(
                                        step="TYPE_LINK_AFF_IN_COMMENT",
                                        result="SUCCESS",
                                        note="Link affiliate typed in comment input"
                                    )
                                    await self.behavior.human_like_delay(0.5, 1.0)
                                else:
                                    if self.status_updater:
                                        self.status_updater("⚠️ Không tìm thấy comment input, bỏ qua link affiliate")
                                    self.logger.log_step(
                                        step="TYPE_LINK_AFF_IN_COMMENT",
                                        result="FAILED",
                                        note="Comment input not found, skipping link_aff"
                                    )
                            else:
                                self.logger.log_step(
                                    step="TYPE_LINK_AFF_IN_COMMENT",
                                    result="WARNING",
                                    note="No selectors configured for comment_input"
                                )
                        else:
                            if self.status_updater:
                                self.status_updater("⚠️ Không tìm thấy nút Thêm vào thread, tiếp tục post bình thường")
                            self.logger.log_step(
                                step="CLICK_ADD_TO_THREAD_BUTTON",
                                result="FAILED",
                                note="Button not found, continuing without comment"
                            )
                    except Exception as e:
                        # Không fail toàn bộ post nếu click "Thêm vào thread" thất bại
                        self.logger.log_step(
                            step="CLICK_ADD_TO_THREAD_BUTTON",
                            result="ERROR",
                            error=f"Error clicking Add to thread button: {safe_get_exception_message(e)}",
                            error_type=safe_get_exception_type_name(e),
                            note="Continuing without comment"
                        )
                        if self.status_updater:
                            self.status_updater(f"⚠️ Không click được nút Thêm vào thread: {safe_get_exception_message(e)}, tiếp tục post bình thường")
                else:
                    self.logger.log_step(
                        step="CLICK_ADD_TO_THREAD_BUTTON",
                        result="WARNING",
                        note="No selectors configured for add_to_thread_button, skipping"
                    )
            else:
                # Không có link_aff → đăng bình thường (bỏ qua bước "Thêm vào thread")
                self.logger.log_step(
                    step="CHECK_LINK_AFF",
                    result="NOT_FOUND",
                    note="No link affiliate, posting normally without comment"
                )
                if self.status_updater:
                    self.status_updater("📝 Không có link affiliate, đăng bài bình thường...")
            
            await self.behavior.human_like_delay(0.5, 1.0)
            
            # Tìm modal compose trước
            modal = None
            try:
                modal_selectors = [
                    "div[role='dialog']",
                    "div[aria-modal='true']",
                    "div:has-text('New thread')"
                ]
                for modal_selector in modal_selectors:
                    try:
                        modal = await self.page.query_selector(modal_selector)
                        if modal and await modal.is_visible():
                            self.logger.log_step(
                                step="FIND_MODAL",
                                result="SUCCESS",
                                selector=modal_selector,
                                note="Found compose modal"
                            )
                            break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.log_step(
                    step="FIND_MODAL",
                    result="WARNING",
                    error=str(e),
                    note="Could not find modal, will search in entire page"
                )
            
            # Tìm và click post button
            if self.status_updater:
                self.status_updater("🔍 Đang tìm nút đăng...")
            await asyncio.sleep(1.0)
            post_button = await find_post_button(
                self.page,
                self.logger,
                selectors["post_button"],
                modal
            )
            
            if not post_button:
                raise RuntimeError("Không tìm thấy nút post hoặc nút bị disabled")
            
            # Click post button với retry logic
            if self.status_updater:
                self.status_updater("📤 Đang đăng bài...")
            click_success = await click_post_button_with_retry(
                post_button,
                self.behavior,
                self.logger
            )
            
            if not click_success:
                raise RuntimeError("Không thể click nút post sau tất cả methods")
            
            # Chờ post hoàn thành
            if self.status_updater:
                self.status_updater("⏳ Đang xác minh bài đăng...")
            await asyncio.sleep(random.uniform(5.0, 8.0))
            
            # Verify post success
            result = await verify_post_success(
                self.page,
                self.ui_detector,
                self.logger,
                start_time,
                content
            )
            
            if self.status_updater:
                if result.success:
                    self.status_updater(f"✅ Đăng bài thành công! Thread ID: {result.thread_id or 'N/A'}")
                else:
                    self.status_updater(f"❌ Đăng bài thất bại: {result.error or 'Không rõ lỗi'}")
            
            return result
        
        except TimeoutError as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="POST_THREAD",
                result="ERROR",
                time_ms=elapsed_time,
                error=f"Timeout: {safe_get_exception_message(e)}",
                error_type="TimeoutError",
                content_hash=hash(content)
            )
            raise
            
        except RuntimeError as e:
            # RuntimeError từ code của chúng ta (ví dụ: không tìm thấy element)
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="POST_THREAD",
                result="ERROR",
                time_ms=elapsed_time,
                error=f"Runtime error: {safe_get_exception_message(e)}",
                error_type="RuntimeError",
                content_hash=hash(content)
            )
            
            return PostResult(
                success=False,
                state=UIState.UNKNOWN,
                error=f"Runtime error: {safe_get_exception_message(e)}"
            )
            
        except ValueError as e:
            # Validation errors
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="POST_THREAD",
                result="ERROR",
                time_ms=elapsed_time,
                error=f"Validation error: {safe_get_exception_message(e)}",
                error_type="ValueError",
                content_hash=hash(content)
            )
            
            return PostResult(
                success=False,
                state=UIState.UNKNOWN,
                error=f"Validation error: {safe_get_exception_message(e)}"
            )
            
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="POST_THREAD",
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
