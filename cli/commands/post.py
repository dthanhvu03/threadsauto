"""
Module: cli/commands/post.py

Posting commands.
"""

from browser.manager import BrowserManager
from browser.login_guard import LoginGuard
from threads.composer import ThreadComposer
from config import Config


async def handle_post_thread(
    account_id: str,
    content: str,
    config: Config
) -> None:
    """
    Xử lý lệnh đăng thread ngay lập tức.
    
    Args:
        account_id: ID tài khoản
        content: Nội dung thread
        config: Config instance
    """
    try:
        async with BrowserManager(
            account_id=account_id,
            config=config
        ) as browser:
            # Điều hướng đến Threads
            await browser.navigate("https://www.threads.com/?hl=vi")
            
            # Kiểm tra trạng thái đăng nhập
            login_guard = LoginGuard(browser.page, config=config)
            is_logged_in = await login_guard.check_login_state()
            
            if not is_logged_in:
                # Tự động click nút Instagram login trước
                print("\n🔍 Phát hiện chưa đăng nhập. Đang tự động mở form đăng nhập...")
                instagram_clicked = await login_guard.click_instagram_login()
                
                if instagram_clicked:
                    print("✅ Đã mở form đăng nhập Instagram")
                else:
                    print("⚠️  Không tìm thấy nút Instagram login, vui lòng đăng nhập thủ công")
                
                # Chờ đăng nhập thủ công
                login_success = await login_guard.wait_for_manual_login(timeout=300)
                if not login_success:
                    print("❌ Đăng nhập thất bại. Thoát.")
                    return
            
            # Đăng thread
            composer = ThreadComposer(browser.page, config=config)
            result = await composer.post_thread(content)
            
            if result.success:
                print(f"✅ Đăng thread thành công! Thread ID: {result.thread_id}")
            else:
                print(f"❌ Không thể đăng thread: {result.error}")
                if result.shadow_fail:
                    print("⚠️  Phát hiện shadow fail: đã click nhưng không đăng")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Đã hủy bởi user.")
    except Exception as e:
        print(f"\n❌ Lỗi không mong đợi: {str(e)}")
        print(f"   Loại lỗi: {type(e).__name__}")
        import traceback
        print("\n📋 Chi tiết lỗi:")
        traceback.print_exc()

