"""
Post callback factory for scheduler.

Creates platform-specific post callbacks for scheduler execution.
"""

# Standard library
from typing import Callable, Any, Optional

# Local
from services.scheduler.models import Platform


def create_post_callback_factory() -> Callable[[Platform], Callable[[str, str, Callable[[str], None], Optional[str]], Any]]:
    """
    Create post_callback_factory for scheduler.
    
    Returns:
        Factory function that returns platform-specific callbacks
    """
    async def post_thread_callback(
        account_id: str,
        content: str,
        status_updater: Optional[Callable[[str], None]] = None,
        link_aff: Optional[str] = None
    ):
        """
        Post thread callback for Threads platform.
        
        Args:
            account_id: Account ID
            content: Content to post
            status_updater: Optional status updater callback
            link_aff: Optional affiliate link
        
        Returns:
            PostResult
        """
        from config import Config, RunMode
        from browser.manager import BrowserManager
        from browser.login_guard import LoginGuard
        from threads.composer import ThreadComposer
        
        config = Config(mode=RunMode.SAFE)
        
        # Create WebSocketLogger for realtime logging
        from services.websocket_logger import WebSocketLogger
        from services.logger import StructuredLogger
        
        base_logger = StructuredLogger(name=f"thread_composer_{account_id}")
        ws_logger = WebSocketLogger(
            logger=base_logger,
            room="scheduler",
            account_id=account_id
        )
        
        if status_updater:
            status_updater("🌐 Đang khởi động browser...")
        
        async with BrowserManager(
            account_id=account_id,
            config=config,
            logger=ws_logger
        ) as browser:
            if status_updater:
                status_updater("🔍 Đang kiểm tra trạng thái đăng nhập...")
            
            # Navigate to Threads
            await browser.navigate("https://www.threads.com/?hl=vi")
            
            # Check login state
            login_guard = LoginGuard(browser.page, config=config, logger=ws_logger)
            is_logged_in = await login_guard.check_login_state()
            
            if not is_logged_in:
                if status_updater:
                    status_updater("🔐 Đang mở form đăng nhập...")
                
                # Auto-click Instagram login button
                instagram_clicked = await login_guard.click_instagram_login()
                if instagram_clicked:
                    print("✅ Đã mở form đăng nhập Instagram")
                else:
                    print("⚠️  Không tìm thấy nút Instagram login, vui lòng đăng nhập thủ công")
                
                if status_updater:
                    status_updater("⏳ Đang chờ đăng nhập thủ công...")
                
                # Wait for manual login
                login_success = await login_guard.wait_for_manual_login(timeout=300)
                if not login_success:
                    print("❌ Đăng nhập thất bại. Thoát.")
                    from types import SimpleNamespace
                    return SimpleNamespace(success=False, error="Login failed", thread_id=None)
            
            if status_updater:
                status_updater("✍️ Đang chuẩn bị đăng bài...")
            
            # Post thread
            composer = ThreadComposer(
                browser.page,
                config=config,
                logger=ws_logger,
                status_updater=status_updater
            )
            result = await composer.post_thread(content, link_aff=link_aff)
            
            return result
    
    async def post_facebook_callback(
        account_id: str,
        content: str,
        status_updater: Optional[Callable[[str], None]] = None,
        link_aff: Optional[str] = None
    ):
        """
        Post callback for Facebook platform (not implemented yet).
        
        Args:
            account_id: Account ID
            content: Content to post
            status_updater: Optional status updater callback
            link_aff: Optional affiliate link
        
        Returns:
            PostResult
        """
        from types import SimpleNamespace
        return SimpleNamespace(
            success=False,
            error="Facebook platform not implemented yet",
            thread_id=None
        )
    
    def factory(platform: Platform) -> Callable[[str, str, Callable[[str], None], Optional[str]], Any]:
        """
        Factory function that returns platform-specific callback.
        
        Args:
            platform: Platform enum
        
        Returns:
            Platform-specific post callback
        """
        if platform == Platform.THREADS:
            return post_thread_callback
        elif platform == Platform.FACEBOOK:
            return post_facebook_callback
        else:
            # Default to Threads
            return post_thread_callback
    
    return factory
