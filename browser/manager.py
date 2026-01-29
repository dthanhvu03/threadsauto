"""
Module: browser/manager.py

Quản lý browser cho Threads automation.
Xử lý vòng đời browser, quản lý profile, và duy trì session.
"""

# Standard library
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import random
import os

# Third-party
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright
)

# Local
from services.logger import StructuredLogger
from config import Config


class BrowserManager:
    """
    Quản lý browser cho automation.
    
    Xử lý vòng đời browser, quản lý profile,
    và duy trì session sử dụng Playwright.
    
    Attributes:
        account_id: Mã định danh tài khoản
        browser: Instance browser
        context: Browser context (với persistent profile)
        page: Instance trang hiện tại
        playwright: Instance Playwright
        config: Đối tượng cấu hình
        logger: Instance structured logger
    """
    
    def __init__(
        self,
        account_id: str,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Khởi tạo browser manager.
        
        Args:
            account_id: Mã định danh tài khoản (ví dụ: "account_01")
            config: Đối tượng cấu hình (tùy chọn)
            logger: Instance structured logger (tùy chọn)
        """
        self.account_id = account_id
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="browser_manager")
        
        # Các instance browser
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Đường dẫn profile
        self.profile_path = Path(f"./profiles/{account_id}")
        self.profile_path.mkdir(parents=True, exist_ok=True)
    
    async def start(self) -> None:
        """
        Khởi động browser với persistent profile.
        
        Sử dụng launch_persistent_context để tự động lưu cookie/localStorage.
        Browser chạy ở chế độ headed (không headless).
        
        Raises:
            RuntimeError: Nếu browser không khởi động được
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="BROWSER_START",
                result="IN_PROGRESS",
                account_id=self.account_id,
                profile_path=str(self.profile_path)
            )
            
            # Cleanup SingletonLock file nếu có (tránh lỗi "profile already in use")
            singleton_lock_path = self.profile_path / "SingletonLock"
            singleton_socket_path = self.profile_path / "SingletonSocket"
            singleton_cookie_path = self.profile_path / "SingletonCookie"
            
            if singleton_lock_path.exists():
                try:
                    singleton_lock_path.unlink()
                    self.logger.log_step(
                        step="CLEANUP_SINGLETON_LOCK",
                        result="SUCCESS",
                        note="Removed stale SingletonLock file"
                    )
                except Exception as e:
                    self.logger.log_step(
                        step="CLEANUP_SINGLETON_LOCK",
                        result="WARNING",
                        error=str(e),
                        note="Could not remove SingletonLock (may be in use)"
                    )
            
            # Cleanup other singleton files
            for singleton_file in [singleton_socket_path, singleton_cookie_path]:
                if singleton_file.exists():
                    try:
                        singleton_file.unlink()
                    except Exception:
                        pass  # Ignore cleanup errors
            
            # Khởi động Playwright
            self.playwright = await async_playwright().start()
            
            # Khởi động browser với persistent context
            # Tự động xử lý lưu cookie/localStorage
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_path),
                headless=False,  # Chế độ headed (bắt buộc)
                slow_mo=self.config.browser.slow_mo,  # Làm chậm để debug
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ],
                viewport={
                    'width': 1280,
                    'height': 720
                },
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Lấy hoặc tạo page
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()
            
            # Đặt timeout mặc định
            self.page.set_default_timeout(self.config.browser.timeout)
            
            # Bật request interception để debug (tùy chọn)
            if self.config.browser.debug:
                self.page.on("request", lambda request: self.logger.debug(
                    f"Request: {request.method} {request.url}"
                ))
                self.page.on("response", lambda response: self.logger.debug(
                    f"Response: {response.status} {response.url}"
                ))
            
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="BROWSER_START",
                result="SUCCESS",
                time_ms=elapsed_time,
                account_id=self.account_id
            )
            
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="BROWSER_START",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Failed to start browser: {str(e)}",
                account_id=self.account_id
            )
            raise RuntimeError(f"Không thể khởi động browser: {str(e)}") from e
    
    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        Điều hướng đến URL với xử lý lỗi.
        
        Args:
            url: URL cần điều hướng đến
            wait_until: Điều kiện chờ (mặc định: "networkidle")
        
        Raises:
            RuntimeError: Nếu điều hướng thất bại
        """
        if not self.page:
            raise RuntimeError("Browser chưa khởi động. Gọi start() trước.")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="NAVIGATE",
                result="IN_PROGRESS",
                account_id=self.account_id,
                url=url
            )
            
            await self.page.goto(url, wait_until=wait_until)
            
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="NAVIGATE",
                result="SUCCESS",
                time_ms=elapsed_time,
                account_id=self.account_id,
                url=url
            )
            
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="NAVIGATE",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Navigation failed: {str(e)}",
                account_id=self.account_id,
                url=url
            )
            raise RuntimeError(f"Điều hướng thất bại: {str(e)}") from e
    
    async def close(self) -> None:
        """
        Đóng browser và dọn dẹp tài nguyên.
        
        Đảm bảo dọn dẹp đúng cách browser, context, và các instance playwright.
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="BROWSER_CLOSE",
                result="IN_PROGRESS",
                account_id=self.account_id
            )
            
            # Đóng page
            if self.page:
                await self.page.close()
                self.page = None
            
            # Đóng context (tự động lưu cookies/localStorage)
            if self.context:
                await self.context.close()
                self.context = None
            
            # Đóng browser
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            # Dừng playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="BROWSER_CLOSE",
                result="SUCCESS",
                time_ms=elapsed_time,
                account_id=self.account_id
            )
            
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="BROWSER_CLOSE",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Close failed: {str(e)}",
                account_id=self.account_id
            )
            # Không raise - cleanup nên là best effort
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
    
    def __str__(self) -> str:
        """Biểu diễn chuỗi."""
        return f"BrowserManager(account={self.account_id})"

