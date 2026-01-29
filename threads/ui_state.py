"""
Module: threads/ui_state.py

UI state detection cho Threads automation.
"""

# Local
from threads.types import UIState
from threads.selectors import SELECTORS as THREADS_SELECTORS, XPATH_PREFIX


class UIStateDetector:
    """Detector cho UI state và shadow fail."""
    
    def __init__(self, page, config, logger, selectors=None):
        """
        Khởi tạo UI state detector.
        
        Args:
            page: Instance Playwright page
            config: Đối tượng cấu hình
            logger: Instance structured logger
            selectors: Selectors dict (tùy chọn, nếu None sẽ dùng threads.selectors)
        """
        self.page = page
        self.config = config
        self.logger = logger
        self.selectors = selectors  # Cho phép inject selectors từ bên ngoài
    
    async def detect_ui_state(self) -> UIState:
        """
        Phát hiện trạng thái UI hiện tại.
        
        Returns:
            Trạng thái UI hiện tại
        """
        try:
            # Nếu có selectors được inject từ bên ngoài, dùng nó
            if self.selectors is not None:
                selectors = self.selectors
            else:
                # Safe access cho config
                if not hasattr(self.config, 'selectors'):
                    selector_version = "v1"
                elif not hasattr(self.config.selectors, 'version'):
                    selector_version = "v1"
                else:
                    selector_version = self.config.selectors.version
                
                # Dùng threads selectors mặc định (backward compatible)
                selectors = THREADS_SELECTORS.get(selector_version, THREADS_SELECTORS["v1"])
        except Exception:
            # Fallback to v1 nếu có lỗi
            if self.selectors is not None:
                selectors = self.selectors
            else:
                selectors = THREADS_SELECTORS.get("v1", {})
        
        try:
            # Kiểm tra thông báo lỗi
            for selector in selectors["error_message"]:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        return UIState.ERROR
                except (TimeoutError, RuntimeError):
                    # Timeout hoặc runtime error - continue với selector tiếp theo
                    continue
                except Exception:
                    # Các lỗi khác - continue
                    continue
            
            # Kiểm tra chỉ báo thành công
            for selector in selectors["success_indicator"]:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        return UIState.SUCCESS
                except (TimeoutError, RuntimeError):
                    # Timeout hoặc runtime error - continue với selector tiếp theo
                    continue
                except Exception:
                    # Các lỗi khác - continue
                    continue
            
            # Kiểm tra trạng thái nút post
            post_button_selectors = selectors.get("post_button", [])
            for selector in post_button_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        try:
                            is_disabled = await element.get_attribute("disabled")
                            if is_disabled:
                                return UIState.DISABLED
                        except Exception:
                            pass
                        
                        # Kiểm tra chỉ báo loading
                        try:
                            text = await element.text_content()
                            if text and isinstance(text, str) and ("loading" in text.lower() or "posting" in text.lower()):
                                return UIState.LOADING
                        except Exception:
                            pass
                except Exception:
                    continue
            
            return UIState.UNKNOWN
            
        except Exception as e:
            self.logger.log_step(
                step="DETECT_UI_STATE",
                result="ERROR",
                error=f"Không thể phát hiện trạng thái UI: {str(e)}"
            )
            return UIState.UNKNOWN
    
    async def check_shadow_fail(self) -> bool:
        """
        Kiểm tra shadow fail (đã click nhưng không đăng, không có lỗi hiển thị).
        
        Returns:
            True nếu phát hiện shadow fail
        """
        try:
            # Nếu có selectors được inject từ bên ngoài, dùng nó
            if self.selectors is not None:
                selectors = self.selectors
            else:
                # Safe access cho config
                if not hasattr(self.config, 'selectors'):
                    selector_version = "v1"
                elif not hasattr(self.config.selectors, 'version'):
                    selector_version = "v1"
                else:
                    selector_version = self.config.selectors.version
                
                # Dùng threads selectors mặc định (backward compatible)
                selectors = THREADS_SELECTORS.get(selector_version, THREADS_SELECTORS["v1"])
        except Exception:
            # Fallback to v1 nếu có lỗi
            if self.selectors is not None:
                selectors = self.selectors
            else:
                selectors = THREADS_SELECTORS.get("v1", {})
        
        try:
            # Kiểm tra xem content còn trong input không
            compose_input_selectors = selectors.get("compose_input", [])
            for selector in compose_input_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        try:
                            content = await element.text_content()
                        except Exception:
                            content = None
                        
                        if content and isinstance(content, str) and len(content.strip()) > 0:
                            # Content vẫn còn trong input
                            # Kiểm tra xem có chỉ báo thành công không
                            has_success = False
                            success_selectors = selectors.get("success_indicator", [])
                            for success_selector in success_selectors:
                                try:
                                    success_element = await self.page.query_selector(success_selector)
                                    if success_element and await success_element.is_visible():
                                        has_success = True
                                        break
                                except Exception:
                                    continue
                            
                            # Kiểm tra xem có thông báo lỗi không
                            has_error = False
                            error_selectors = selectors.get("error_message", [])
                            for error_selector in error_selectors:
                                try:
                                    error_element = await self.page.query_selector(error_selector)
                                    if error_element and await error_element.is_visible():
                                        has_error = True
                                        break
                                except Exception:
                                    continue
                            
                            # Shadow fail: content còn trong input, không có success, không có error
                            if not has_success and not has_error:
                                return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.log_step(
                step="CHECK_SHADOW_FAIL",
                result="ERROR",
                error=f"Không thể kiểm tra shadow fail: {str(e)}"
            )
            return False

