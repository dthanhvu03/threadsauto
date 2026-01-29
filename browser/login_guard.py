"""
Module: browser/login_guard.py

Login guard cho Threads automation.
Phát hiện trạng thái đăng nhập và xử lý luồng đăng nhập thủ công.
"""

# Standard library
import asyncio
from typing import Optional

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from config import Config


class LoginGuard:
    """
    Login guard cho Threads automation.
    
    Phát hiện trạng thái đăng nhập sử dụng nhiều fallback selectors.
    Xử lý luồng đăng nhập thủ công khi chưa đăng nhập.
    
    Attributes:
        page: Instance Playwright page
        config: Đối tượng cấu hình
        logger: Instance structured logger
    """
    
    # Các phiên bản selector để phát hiện đăng nhập
    SELECTORS = {
        "v1": {
            "new_thread_button": [
                # XPath từ user (ưu tiên cao nhất)
                "xpath=/html/body/div[1]/div/div/div[2]/div[2]/div[3]",
                # Selector dựa trên aria-label "Tạo" (tiếng Việt)
                "div[role='button']:has(svg[aria-label='Tạo'])",
                "div[role='button']:has(svg[title='Tạo'])",
                # Selector dựa trên aria-label "Create" (tiếng Anh)
                "div[role='button']:has(svg[aria-label='Create'])",
                "div[role='button']:has(svg[title='Create'])",
                # Fallback selectors
                "a[href*='/compose']",
                "a[href*='/post']",
                "button:has-text('New Thread')",
                "div[role='button']:has-text('New Thread')"
            ],
            "login_button": [
                "a[href*='/login']",
                "button:has-text('Log in')",
                "button:has-text('Sign in')"
            ],
            "instagram_login_button": [
                # XPath từ user (ưu tiên cao nhất)
                "xpath=/html/body/div[1]/div/div/div[3]/div/div/div/div[1]/div[1]/div/div[3]/div",
                # CSS Selector từ user
                "#barcelona-page-layout > div > div.xc26acl.x6s0dn4.xcw5jcc",
                # Tìm theo SVG aria-label (quan trọng - ổn định nhất)
                "div[role='button']:has(svg[aria-label='Instagram'])",
                "div[role='button']:has(svg[title='Instagram'])",
                # Tiếng Việt
                "div[role='button']:has-text('Tiếp tục bằng Instagram')",
                "button:has-text('Tiếp tục bằng Instagram')",
                "a:has-text('Tiếp tục bằng Instagram')",
                # Tiếng Anh
                "div[role='button']:has-text('Continue with Instagram')",
                "button:has-text('Continue with Instagram')",
                "a:has-text('Continue with Instagram')",
                # Tìm theo text chứa Instagram
                "div[role='button']:has-text('Instagram')",
                "button[aria-label*='Instagram']",
                "a[href*='instagram']",
                # Fallback
                "button:contains('Instagram')"
            ],
            "profile_menu": [
                "div[aria-label*='Profile']",
                "a[href*='/@']",
                "div[role='button'][aria-label*='Account']"
            ]
        },
        "v2": {
            "new_thread_button": [
                "button[aria-label*='New Thread']",
                "div[data-testid*='compose']",
                "a[data-testid*='new-thread']"
            ],
            "login_button": [
                "button[data-testid*='login']",
                "a[data-testid*='sign-in']"
            ],
            "instagram_login_button": [
                # Tiếng Việt
                "div[role='button']:has-text('Tiếp tục bằng Instagram')",
                "div[role='button']:has(svg[aria-label='Instagram'])",
                # Tiếng Anh
                "div[role='button']:has-text('Continue with Instagram')",
                # Data testid
                "button[data-testid*='instagram']",
                "a[data-testid*='instagram-login']",
                "button[aria-label*='Instagram']"
            ],
            "profile_menu": [
                "div[data-testid*='profile']",
                "button[data-testid*='account']"
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
        Khởi tạo login guard.
        
        Args:
            page: Instance Playwright page
            config: Đối tượng cấu hình (tùy chọn)
            logger: Instance structured logger (tùy chọn)
        """
        self.page = page
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="login_guard")
    
    async def check_login_state(self) -> bool:
        """
        Kiểm tra xem user đã đăng nhập chưa.
        
        Sử dụng nhiều fallback selectors để phát hiện trạng thái đăng nhập.
        Kiểm tra sự hiện diện của nút "New Thread" hoặc menu profile.
        
        Returns:
            True nếu đã đăng nhập, False nếu chưa
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="CHECK_LOGIN_STATE",
                result="IN_PROGRESS"
            )
            
            # Lấy phiên bản selector từ config
            selector_version = self.config.selectors.version
            selectors = self.SELECTORS.get(selector_version, self.SELECTORS["v1"])
            
            # Chờ trang load (dùng domcontentloaded thay vì networkidle để nhanh hơn)
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                # Thêm thời gian chờ để React/SPA render xong
                await asyncio.sleep(2.0)
            except Exception:
                # Fallback: chờ ít nhất 3s để DOM và React render
                await asyncio.sleep(3.0)
            
            # ƯU TIÊN: Kiểm tra nút login/Instagram login trước (chỉ báo chưa đăng nhập)
            # Nếu có nút login → chắc chắn chưa đăng nhập
            has_login_button = False
            for selector in selectors.get("login_button", []):
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            has_login_button = True
                            self.logger.log_step(
                                step="CHECK_LOGIN_STATE",
                                result="SUCCESS",
                                detected_by="login_button",
                                selector=selector,
                                logged_in=False
                            )
                            break
                except Exception:
                    continue
            
            # Kiểm tra nút Instagram login
            if not has_login_button:
                for selector in selectors.get("instagram_login_button", []):
                    try:
                        # Bỏ qua XPath trong quick check
                        if selector.startswith("xpath="):
                            continue
                        element = await self.page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                has_login_button = True
                                self.logger.log_step(
                                    step="CHECK_LOGIN_STATE",
                                    result="SUCCESS",
                                    detected_by="instagram_login_button",
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
                    step="CHECK_LOGIN_STATE",
                    result="SUCCESS",
                    time_ms=elapsed_time,
                    logged_in=False
                )
                return False
            
            # Nếu không có login button, kiểm tra các chỉ báo đã đăng nhập
            logged_in = False
            
            # METHOD 1: Kiểm tra URL - nếu đã ở trang threads.com (không phải login page) → có thể đã login
            current_url = self.page.url
            if "threads.com" in current_url and "login" not in current_url.lower():
                # Thử check thêm bằng cách tìm compose button hoặc profile
                self.logger.log_step(
                    step="CHECK_LOGIN_STATE",
                    result="INFO",
                    note=f"URL suggests logged in: {current_url}"
                )
            
            # METHOD 2: Thử các selector nút New Thread (phải click được, không chỉ là link)
            for selector in selectors["new_thread_button"]:
                try:
                    # Hỗ trợ XPath selector
                    if selector.startswith("xpath="):
                        xpath = selector.replace("xpath=", "")
                        locator = self.page.locator(f"xpath={xpath}")
                        try:
                            # Thử wait_for với timeout ngắn hơn
                            await locator.wait_for(state="visible", timeout=3000)
                            element = await locator.element_handle()
                        except Exception:
                            continue
                    else:
                        try:
                            element = await self.page.wait_for_selector(
                                selector,
                                state="visible",
                                timeout=3000
                            )
                        except Exception:
                            element = await self.page.query_selector(selector)
                            if not element:
                                continue
                    
                    if element:
                        is_visible = await element.is_visible()
                        # Kiểm tra thêm: element phải có thể click được
                        if is_visible:
                            # Kiểm tra xem có phải là button hoặc link có thể click
                            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                            role = await element.get_attribute("role")
                            
                            # Chỉ coi là đã login nếu là button hoặc link thực sự
                            if tag_name in ["button", "a", "div"] or role == "button":
                                logged_in = True
                                self.logger.log_step(
                                    step="CHECK_LOGIN_STATE",
                                    result="SUCCESS",
                                    detected_by="new_thread_button",
                                    selector=selector,
                                    tag_name=tag_name,
                                    role=role
                                )
                                break
                except Exception as e:
                    self.logger.debug(f"Selector '{selector}' failed: {str(e)}")
                    continue
            
            # METHOD 3: Nếu không tìm thấy, thử các selector menu profile
            if not logged_in:
                for selector in selectors["profile_menu"]:
                    try:
                        try:
                            element = await self.page.wait_for_selector(
                                selector,
                                state="visible",
                                timeout=3000
                            )
                        except Exception:
                            element = await self.page.query_selector(selector)
                            if not element:
                                continue
                        
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                logged_in = True
                                self.logger.log_step(
                                    step="CHECK_LOGIN_STATE",
                                    result="SUCCESS",
                                    detected_by="profile_menu",
                                    selector=selector
                                )
                                break
                    except Exception as e:
                        self.logger.debug(f"Profile menu selector '{selector}' failed: {str(e)}")
                        continue
            
            # METHOD 4: Fallback - Check bằng cách tìm bất kỳ element nào có text "compose" hoặc "tạo"
            if not logged_in:
                try:
                    # Tìm element có text chứa "compose" hoặc "tạo" (case insensitive)
                    compose_elements = await self.page.evaluate("""
                        () => {
                            const allElements = document.querySelectorAll('*');
                            for (let el of allElements) {
                                const text = el.textContent || el.innerText || '';
                                const ariaLabel = el.getAttribute('aria-label') || '';
                                const title = el.getAttribute('title') || '';
                                const combined = (text + ' ' + ariaLabel + ' ' + title).toLowerCase();
                                if (combined.includes('compose') || combined.includes('tạo') || combined.includes('new thread')) {
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    if compose_elements:
                        logged_in = True
                        self.logger.log_step(
                            step="CHECK_LOGIN_STATE",
                            result="SUCCESS",
                            detected_by="text_search",
                            note="Found 'compose' or 'tạo' text in page"
                        )
                except Exception as e:
                    self.logger.debug(f"Text search fallback failed: {str(e)}")
            
            # METHOD 5: Final fallback - Check cookies/localStorage
            if not logged_in:
                try:
                    # Check cookies có session token không
                    cookies = await self.page.context.cookies()
                    has_session_cookie = any(
                        'session' in cookie.get('name', '').lower() or
                        'auth' in cookie.get('name', '').lower() or
                        'token' in cookie.get('name', '').lower()
                        for cookie in cookies
                    )
                    
                    # Check localStorage
                    has_local_storage = await self.page.evaluate("""
                        () => {
                            try {
                                const keys = Object.keys(localStorage);
                                return keys.length > 0;
                            } catch (e) {
                                return false;
                            }
                        }
                    """)
                    
                    if has_session_cookie or has_local_storage:
                        # Nếu có cookies/localStorage và không có login button → có thể đã login
                        # Nhưng cần verify thêm bằng cách check URL
                        if "threads.com" in current_url and "login" not in current_url.lower():
                            logged_in = True
                            self.logger.log_step(
                                step="CHECK_LOGIN_STATE",
                                result="SUCCESS",
                                detected_by="cookies_localstorage",
                                has_session_cookie=has_session_cookie,
                                has_local_storage=has_local_storage,
                                url=current_url,
                                note="Found session cookies/localStorage and not on login page"
                            )
                except Exception as e:
                    self.logger.debug(f"Cookie/localStorage check failed: {str(e)}")
            
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="CHECK_LOGIN_STATE",
                result="SUCCESS",
                time_ms=elapsed_time,
                logged_in=logged_in
            )
            
            return logged_in
            
        except TimeoutError as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="CHECK_LOGIN_STATE",
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
                step="CHECK_LOGIN_STATE",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Failed to check login state: {str(e)}",
                error_type=type(e).__name__
            )
            # Mặc định là chưa đăng nhập khi có lỗi (an toàn hơn)
            return False
    
    async def click_instagram_login(self) -> bool:
        """
        Tự động click vào nút "Continue with Instagram" để mở flow đăng nhập.
        
        Không tự động nhập username/password - chỉ click để mở form đăng nhập.
        User sẽ tự nhập thông tin đăng nhập.
        
        Returns:
            True nếu click thành công, False nếu không tìm thấy nút
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.log_step(
                step="CLICK_INSTAGRAM_LOGIN",
                result="IN_PROGRESS"
            )
            
            # Lấy phiên bản selector từ config
            selector_version = self.config.selectors.version
            selectors = self.SELECTORS.get(selector_version, self.SELECTORS["v1"])
            
            # Chờ trang load (dùng domcontentloaded để nhanh hơn)
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                await asyncio.sleep(1.0)
            
            # Tìm và click nút "Continue with Instagram"
            clicked = False
            for selector in selectors.get("instagram_login_button", []):
                try:
                    # Hỗ trợ XPath selector
                    if selector.startswith("xpath="):
                        xpath = selector.replace("xpath=", "")
                        # Playwright dùng locator cho XPath
                        locator = self.page.locator(f"xpath={xpath}")
                        await locator.wait_for(state="visible", timeout=10000)
                        element = await locator.element_handle()
                    else:
                        element = await self.page.wait_for_selector(
                            selector,
                            state="visible",
                            timeout=10000
                        )
                    
                    if element:
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)  # Chờ một chút trước khi click
                        await element.click()
                        clicked = True
                        
                        self.logger.log_step(
                            step="CLICK_INSTAGRAM_LOGIN",
                            result="SUCCESS",
                            selector=selector
                        )
                        
                        # Chờ form đăng nhập xuất hiện
                        await asyncio.sleep(2.0)
                        break
                except Exception as e:
                    # Log lỗi để debug
                    self.logger.debug(f"Selector '{selector}' failed: {str(e)}")
                    continue
            
            if not clicked:
                elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
                self.logger.log_step(
                    step="CLICK_INSTAGRAM_LOGIN",
                    result="FAILED",
                    time_ms=elapsed_time,
                    error="Không tìm thấy nút Instagram login"
                )
                return False
            
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return True
            
        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.logger.log_step(
                step="CLICK_INSTAGRAM_LOGIN",
                result="ERROR",
                time_ms=elapsed_time,
                error=f"Lỗi khi click Instagram login: {str(e)}"
            )
            return False
    
    async def wait_for_manual_login(self, timeout: int = 300) -> bool:
        """
        Chờ user đăng nhập thủ công.
        
        Kiểm tra trạng thái đăng nhập mỗi 5 giây cho đến khi đăng nhập hoặc hết thời gian.
        Tạm dừng thực thi và chờ xác nhận từ user.
        
        Args:
            timeout: Thời gian tối đa chờ tính bằng giây (mặc định: 300 = 5 phút)
        
        Returns:
            True nếu đăng nhập trong thời gian chờ, False nếu không
        """
        start_time = asyncio.get_event_loop().time()
        
        self.logger.log_step(
            step="WAIT_MANUAL_LOGIN",
            result="IN_PROGRESS",
            timeout_seconds=timeout
        )
        
        print("\n" + "="*60)
        print("⚠️  CHƯA ĐĂNG NHẬP - CẦN ĐĂNG NHẬP THỦ CÔNG")
        print("="*60)
        print("📝 Vui lòng nhập username và password Instagram của bạn")
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
                    step="WAIT_MANUAL_LOGIN",
                    result="SUCCESS",
                    time_ms=elapsed_time
                )
                
                print("\n✅ Đã phát hiện đăng nhập! Tiếp tục automation...\n")
                return True
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            remaining = timeout - elapsed
            if remaining > 0:
                print(f"⏳ Vẫn đang chờ... (còn {remaining}s)")
        
        elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        self.logger.log_step(
            step="WAIT_MANUAL_LOGIN",
            result="FAILED",
            time_ms=elapsed_time,
            error="Hết thời gian chờ đăng nhập thủ công"
        )
        
        print("\n❌ Hết thời gian chờ đăng nhập. Vui lòng thử lại.\n")
        return False

