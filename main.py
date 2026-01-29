"""
Điểm vào chính cho Threads Automation Tool.

Ví dụ sử dụng:
    # Đăng bài ngay lập tức
    python main.py --account account_01 --content "Xin chào Threads!"
    
    # Lên lịch đăng bài
    python main.py --account account_01 --content "Xin chào Threads!" --schedule "2024-12-17 10:00:00"
    
    # Chạy scheduler
    python main.py --scheduler --account account_01
"""

# Standard library
import asyncio
from typing import Optional, Callable

# Local
from browser.manager import BrowserManager
from browser.login_guard import LoginGuard
from threads.composer import ThreadComposer
from config import Config, RunMode
from cli.parser import create_parser
from cli.commands import (
    handle_create_template,
    handle_excel_posts,
    handle_list_jobs,
    handle_remove_job,
    handle_reset_jobs,
    handle_reset_status,
    handle_delete_job_file,
    handle_reset_job_file,
    handle_post_thread,
    handle_schedule_job,
    handle_scheduler,
)


async def post_thread_callback(
    account_id: str,
    content: str,
    status_updater: Optional[Callable[[str], None]] = None,
    link_aff: Optional[str] = None
):
    """
    Callback function để đăng bài (dùng cho scheduler).
    
    Args:
        account_id: ID tài khoản
        content: Nội dung thread
        status_updater: Optional callback để update status message real-time
        link_aff: Optional link affiliate để đăng trong comment
    
    Returns:
        PostResult
    """
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
        
        # Điều hướng đến Threads
        await browser.navigate("https://www.threads.com/?hl=vi")
        
        # Kiểm tra trạng thái đăng nhập
        login_guard = LoginGuard(browser.page, config=config, logger=ws_logger)
        is_logged_in = await login_guard.check_login_state()
        
        if not is_logged_in:
            if status_updater:
                status_updater("🔐 Đang mở form đăng nhập...")
            
            # Tự động click nút Instagram login trước
            instagram_clicked = await login_guard.click_instagram_login()
            if instagram_clicked:
                print("✅ Đã mở form đăng nhập Instagram")
            else:
                print("⚠️  Không tìm thấy nút Instagram login, vui lòng đăng nhập thủ công")
            
            if status_updater:
                status_updater("⏳ Đang chờ đăng nhập thủ công...")
            
            # Chờ đăng nhập thủ công
            login_success = await login_guard.wait_for_manual_login(timeout=300)
            if not login_success:
                print("❌ Đăng nhập thất bại. Thoát.")
                return None
        
        if status_updater:
            status_updater("✍️ Đang chuẩn bị đăng bài...")
        
        # Đăng thread (composer sẽ tự update status_message trong quá trình thực thi)
        # Pass WebSocketLogger để broadcast realtime logs
        composer = ThreadComposer(
            browser.page,
            config=config,
            logger=ws_logger,
            status_updater=status_updater
        )
        result = await composer.post_thread(content, link_aff=link_aff)
        
        return result


async def main():
    """Hàm chính - entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Khởi tạo config
    config = Config(mode=RunMode.SAFE if args.mode == "SAFE" else RunMode.FAST)
    
    # Route commands đến các handlers
    if args.create_template:
        handle_create_template(args.create_template)
        return
    
    # Validate account (bắt buộc cho các lệnh khác)
    if not args.account:
        parser.error("--account là bắt buộc (trừ khi dùng --create-template)")
    
    # Excel commands
    if args.excel:
        await handle_excel_posts(args.excel, args.account, config)
        return
    
    # Job management commands
    if args.list_jobs:
        handle_list_jobs(args.account)
        return
    
    if args.remove_job:
        handle_remove_job(args.remove_job)
        return
    
    if args.reset_jobs:
        handle_reset_jobs(args.account)
        return
    
    if args.reset_status:
        handle_reset_status(args.reset_status, args.account)
        return
    
    if args.delete_job_file:
        handle_delete_job_file(args.delete_job_file)
        return
    
    if args.reset_job_file:
        handle_reset_job_file(args.reset_job_file)
        return
    
    # Scheduler command
    if args.scheduler:
        await handle_scheduler(args.account, post_thread_callback)
        return
    
    # Schedule job command
    if args.schedule:
        handle_schedule_job(args.account, args.content, args.schedule, args.priority)
        return
    
    # Post thread command (default)
    if not args.content:
        print("❌ Cần --content để đăng bài hoặc --schedule để lên lịch.")
        return
    
    await handle_post_thread(args.account, args.content, config)


if __name__ == "__main__":
    asyncio.run(main())
