"""
Module: browser/facebook_login_guard.py

Facebook login guard cho Facebook automation.
Phát hiện trạng thái đăng nhập và xử lý luồng đăng nhập thủ công cho Facebook.
"""

# Standard library
import asyncio
from typing import Optional

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from config import Config

# Constants
XPATH_PREFIX = "xpath="


class FacebookLoginGuard:
    """
    Login guard cho Facebook automation.
    
    Phát hiện trạng thái đăng nhập sử dụng nhiều fallback selectors.
    Xử lý luồng đăng nhập thủ công khi chưa đăng nhập.
    
    Attributes:
        page: Instance Playwright page
        config: Đối tượng cấu hình
        logger: Instance structured logger
    """
    
    # Các phiên bản selector để phát hiện đăng nhập Facebook
    SELECTORS = {
        "v1": {
            "compose_button": [
                # Selector cho nút compose "Review ơi, bạn đang nghĩ gì thế?"
                # Full XPath từ user (ưu tiên cao nhất)
                f"{XPATH_PREFIX}/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[2]/div/div[2]/div/div/div/div/div[1]",
                # XPath với ID
                f"{XPATH_PREFIX}//*[@id='mount_0_0_SA']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[2]/div/div[2]/div/div/div/div/div[1]",
                # Selector dựa trên text
                "div[role='button']:has-text('Review ơi, bạn đang nghĩ gì thế?')",
                "div[role='button']:has-text('bạn đang nghĩ gì')",
                "div[role='button']:has-text('What')",
                # Selector dựa trên aria-label
                "div[role='button'][aria-label*='What']",
                "div[role='button'][aria-label*='nghĩ gì']",
            ],
            "login_button": [
                # Nút đăng nhập Facebook
                "button:has-text('Đăng nhập')",
                "button:has-text('Log in')",
                "a[href*='/login']",
                "a[href*='/login.php']",
                "button[data-testid='royal_login_button']",
            ],
            "profile_menu": [
                # Menu profile/user
                "div[aria-label*='Profile']",
                "div[aria-label*='Account']",
                "a[href*='/profile.php']",
                "a[href*='/me']",
                # Profile picture/icon
                "div[role='button'][aria-label*='Menu']",
                "div[data-testid='profile_pic']",
            ],
            "search_bar": [
                # Search bar (chỉ có khi đã đăng nhập)
                "input[placeholder*='Tìm kiếm trên Facebook']",
                "input[placeholder*='Search Facebook']",
                "input[aria-label*='Tìm kiếm']",
                "input[aria-label*='Search']",
            ]
        }
    }
    
    def __init__(
        self,
        page: Page,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Khởi tạo Facebook login guard.
        
        Args:
            page: Instance Playwright page
            config: Đối tượng cấu hình (tùy chọn)
            logger: Instance structured logger (tùy chọn)
        """
        self.page = page
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="facebook_login_guard")
    
    async def check_login_state(self) -> bool:
        """
        Kiểm tra xem user đã đăng nhập Facebook chưa.
        
        Sử dụng nhiều fallback selectors để phát hiện trạng thái đăng nhập.
        Kiểm tra sự hiện diện của:
        - Nút compose "Review ơi, bạn đang nghĩ gì thế?"
        - Search bar
        - Profile menu
        
        Returns:
            True nếu đã đăng nhập, False nếu chưa
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="CHECK_FACEBOOK_LOGIN_STATE",
                result="IN_PROGRESS"
            )
            
            # Lấy phiên bản selector từ config
            try:
                selector_version = self.config.selectors.version
            except AttributeError:
                selector_version = "v1"
            
            selectors = self.SELECTORS.get(selector_version, self.SELECTORS["v1"])
            
            # Chờ trang load
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                await asyncio.sleep(1.0)
            
            # ƯU TIÊN: Kiểm tra nút login trước (chỉ báo chưa đăng nhập)
            has_login_button = False
            for selector in selectors.get("login_button", []):
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            has_login_button = True
                            self.logger.log_step(
                                step="CHECK_FACEBOOK_LOGIN_STATE",
                                result="SUCCESS",
                                detected_by="login_button",
                                selector=selector,
                                logged_in=False
                            )
                            break
                except Exception:
                    continue
            
            # Nếu có login button → chắc chắn chưa đăng nhập
            if has_login_button:
                elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
                self.logger.log_step(
                    step="CHECK_FACEBOOK_LOGIN_STATE",
                    result="SUCCESS",
                    time_ms=elapsed_time,
                    logged_in=False
                )
                return False
            
            # Nếu không có login button, kiểm tra các chỉ báo đã đăng nhập
            logged_in = False
            
            # Thử tìm nút compose (ưu tiên cao nhất)
            for selector in selectors.get("compose_button", []):
                try:
                    # Hỗ trợ XPath selector
                    if selector.startswith(XPATH_PREFIX):
                        xpath = selector.replace(XPATH_PREFIX, "")
                        locator = self.page.locator(f"{XPATH_PREFIX}{xpath}")
                        try:
                            element = await locator.element_handle()
                            if element:
                                is_visible = await element.is_visible()
                                if is_visible:
                                    logged_in = True
                                    self.logger.log_step(
                                        step="CHECK_FACEBOOK_LOGIN_STATE",
                                        result="SUCCESS",
                                        detected_by="compose_button",
                                        selector=selector
                                    )
                                    break
                        except Exception:
                            continue
                    else:
                        element = await self.page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                logged_in = True
                                self.logger.log_step(
                                    step="CHECK_FACEBOOK_LOGIN_STATE",
                                    result="SUCCESS",
                                    detected_by="compose_button",
                                    selector=selector
                                )
                                break
                except Exception:
                    continue
            
            # Nếu không tìm thấy compose button, thử search bar
            if not logged_in:
                for selector in selectors.get("search_bar", []):
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                logged_in = True
                                self.logger.log_step(
                                    step="CHECK_FACEBOOK_LOGIN_STATE",
                                    result="SUCCESS",
                                    detected_by="search_bar",
                                    selector=selector
                                )
                                break
                    except Exception:
                        continue
            
            # Nếu không tìm thấy, thử profile menu
            if not logged_in:
                for selector in selectors.get("profile_menu", []):
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                logged_in = True
                                self.logger.log_step(
                                    step="CHECK_FACEBOOK_LOGIN_STATE",
                                    result="SUCCESS",
                                    detected_by="profile_menu",
                                    selector=selector
                                )
                                break
                    except Exception:
                        continue
            
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="CHECK_FACEBOOK_LOGIN_STATE",
                result="SUCCESS",
                time_ms=elapsed_time,
                logged_in=logged_in
            )
            
            return logged_in
            
        except TimeoutError as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="CHECK_FACEBOOK_LOGIN_STATE",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Timeout checking login state: {str(e)}",
                error_type="TimeoutError"
            )
            # Mặc định là chưa đăng nhập khi có lỗi (an toàn hơn)
            return False
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="CHECK_FACEBOOK_LOGIN_STATE",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Failed to check login state: {str(e)}",
                error_type=type(e).__name__
            )
            # Mặc định là chưa đăng nhập khi có lỗi (an toàn hơn)
            return False
    
    async def wait_for_manual_login(self, timeout: int = 300) -> bool:
        """
        Chờ user đăng nhập Facebook thủ công.
        
        Kiểm tra trạng thái đăng nhập mỗi 5 giây cho đến khi đăng nhập hoặc hết thời gian.
        
        Args:
            timeout: Thời gian tối đa chờ tính bằng giây (mặc định: 300 = 5 phút)
        
        Returns:
            True nếu đăng nhập trong thời gian chờ, False nếu không
        """
        start_time = asyncio.get_event_loop().time()
        
        self.logger.log_step(
            step="WAIT_FACEBOOK_MANUAL_LOGIN",
            result="IN_PROGRESS",
            timeout_seconds=timeout
        )
        
        print("\n" + "="*60)
        print("⚠️  CHƯA ĐĂNG NHẬP FACEBOOK - CẦN ĐĂNG NHẬP THỦ CÔNG")
        print("="*60)
        print("📝 Vui lòng nhập email/phone và password Facebook của bạn")
        print("🔐 Tool KHÔNG tự động nhập thông tin - bạn cần nhập thủ công")
        print(f"⏳ Đang chờ tối đa {timeout} giây để đăng nhập...")
        print("="*60 + "\n")
        
        # Kiểm tra mỗi 5 giây
        poll_interval = 5
        elapsed = 0
        
        while elapsed < timeout:
            is_logged_in = await self.check_login_state()
            
            if is_logged_in:
                elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                self.logger.log_step(
                    step="WAIT_FACEBOOK_MANUAL_LOGIN",
                    result="SUCCESS",
                    time_ms=elapsed_time
                )
                
                print("\n✅ Đã phát hiện đăng nhập Facebook! Tiếp tục automation...\n")
                return True
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            remaining = timeout - elapsed
            if remaining > 0:
                print(f"⏳ Vẫn đang chờ... (còn {remaining}s)")
        
        elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        self.logger.log_step(
            step="WAIT_FACEBOOK_MANUAL_LOGIN",
            result="FAILED",
            time_ms=elapsed_time,
            error="Hết thời gian chờ đăng nhập thủ công"
        )
        
        print("\n❌ Hết thời gian chờ đăng nhập. Vui lòng thử lại.\n")
        return False

