"""
Module: threads/verifier.py

Thread verifier cho Threads automation.
Xác minh thành công đăng bài và trích xuất thông tin thread.
"""

# Standard library
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from config import Config


class ThreadVerifier:
    """
    Thread verifier cho Threads automation.
    
    Xác minh thành công đăng bài và trích xuất thông tin thread.
    """
    
    def __init__(
        self,
        page: Page,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Khởi tạo thread verifier.
        
        Args:
            page: Instance Playwright page
            config: Đối tượng cấu hình (tùy chọn)
            logger: Instance structured logger (tùy chọn)
        """
        self.page = page
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="thread_verifier")
    
    async def verify_post_success(self, timeout: int = 30) -> Dict[str, Any]:
        """
        Xác minh thành công đăng bài bằng cách kiểm tra URL và DOM.
        
        Args:
            timeout: Thời gian tối đa chờ tính bằng giây
        
        Returns:
            Dict với kết quả xác minh:
            - success: bool
            - thread_id: Optional[str]
            - url: Optional[str]
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="VERIFY_POST_SUCCESS",
                result="IN_PROGRESS",
                timeout=timeout
            )
            
            # Chờ thay đổi URL hoặc chỉ báo thành công
            await asyncio.sleep(2.0)  # Chờ ban đầu
            
            # Get current URL với error handling
            try:
                current_url = self.page.url
            except Exception as e:
                self.logger.log_step(
                    step="VERIFY_POST_SUCCESS",
                    result="WARNING",
                    error=f"Failed to get page URL: {str(e)}",
                    error_type=type(e).__name__
                )
                current_url = ""
            
            thread_id = None
            
            # Trích xuất thread ID từ URL với error handling
            try:
                if current_url and isinstance(current_url, str) and '/post/' in current_url:
                    parts = current_url.split('/post/')
                    if len(parts) > 1:
                        thread_id = parts[-1].split('/')[0]
                        # Validate thread_id (should be alphanumeric)
                        if thread_id and (thread_id.isdigit() or thread_id.isalnum()):
                            pass
                        else:
                            thread_id = None
            except Exception as e:
                self.logger.log_step(
                    step="VERIFY_POST_SUCCESS",
                    result="WARNING",
                    error=f"Failed to extract thread_id from URL: {str(e)}",
                    error_type=type(e).__name__
                )
                thread_id = None
            
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            result = {
                "success": thread_id is not None,
                "thread_id": thread_id,
                "url": current_url if thread_id else None
            }
            
            self.logger.log_step(
                step="VERIFY_POST_SUCCESS",
                result="SUCCESS" if result["success"] else "FAILED",
                time_ms=elapsed_time,
                thread_id=thread_id
            )
            
            return result
            
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="VERIFY_POST_SUCCESS",
                result="ERROR",
                time_ms=elapsed_time,
                error=f"Xác minh thất bại: {str(e)}"
            )
            
            return {
                "success": False,
                "thread_id": None,
                "url": None,
                "error": str(e)
            }
