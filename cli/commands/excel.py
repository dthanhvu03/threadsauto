"""
Module: cli/commands/excel.py

Excel handling commands.
"""

import asyncio
import random
from typing import List, Dict, Any

from browser.manager import BrowserManager
from browser.login_guard import LoginGuard
from threads.composer import ThreadComposer
from config import Config, RunMode
from services.scheduler import Scheduler, JobPriority
from content.excel_loader import ExcelLoader, ExcelLoadError


def handle_create_template(template_path: str) -> None:
    """
    Xử lý lệnh tạo Excel template.
    
    Args:
        template_path: Đường dẫn file template
    """
    try:
        ExcelLoader.create_template(template_path)
        print(f"✅ Đã tạo template Excel tại: {template_path}")
        print("\n📋 Format file Excel:")
        print("\n   🔹 Cột bắt buộc:")
        print("      - content: Nội dung thread chính (tối đa 500 ký tự tổng)")
        print("\n   🔹 Cột tùy chọn:")
        print("      - scheduled_time: Thời gian lên lịch (format: YYYY-MM-DD HH:MM:SS)")
        print("        * Để trống = đăng ngay lập tức")
        print("        * Có giá trị = lên lịch đăng vào thời gian đó")
        print("      - priority: Độ ưu tiên (LOW, NORMAL, HIGH, URGENT)")
        print("        * Mặc định: NORMAL (nếu để trống)")
        print("        * Chỉ áp dụng khi có scheduled_time")
        print("      - link_aff: Link affiliate (sẽ được append vào cuối content)")
        print("        * Để trống nếu không có")
        print("      - cta: Call-to-action text (sẽ được append vào cuối content)")
        print("        * Ví dụ: 'Follow mình để xem thêm nha ✨'")
        print("        * Để trống nếu không có")
        print("      - note: Ghi chú (chỉ để tham khảo, KHÔNG được đăng)")
        print("        * Để trống nếu không có")
        print("\n   💡 Lưu ý:")
        print("      - Content cuối cùng = content + link_aff + cta (tối đa 500 ký tự)")
        print("      - Các bài có scheduled_time sẽ được thêm vào scheduler")
        print("      - Các bài không có scheduled_time sẽ đăng ngay (với delay 10-20s giữa các bài)")
        print("      - Chạy scheduler: python main.py --scheduler --account <account_id>")
    except Exception as e:
        print(f"❌ Lỗi tạo template: {str(e)}")


async def handle_excel_posts(
    excel_path: str,
    account_id: str,
    config: Config
) -> None:
    """
    Xử lý lệnh đăng bài từ Excel file.
    
    Args:
        excel_path: Đường dẫn file Excel
        account_id: ID tài khoản
        config: Config instance
    """
    try:
        loader = ExcelLoader()
        posts = loader.load_from_file(excel_path)
        
        print(f"\n📊 Đã load {len(posts)} bài từ Excel file: {excel_path}\n")
        
        # Phân loại: có scheduled_time → thêm vào scheduler, không có → đăng ngay
        scheduled_posts = [p for p in posts if "scheduled_time" in p]
        immediate_posts = [p for p in posts if "scheduled_time" not in p]
        
        if scheduled_posts:
            await _handle_scheduled_posts(scheduled_posts, account_id)
        
        if immediate_posts:
            await _handle_immediate_posts(immediate_posts, account_id, config)
        
        if not scheduled_posts and not immediate_posts:
            print("⚠️  Không có bài nào để xử lý")
            
    except ExcelLoadError as e:
        print(f"❌ Lỗi load Excel: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}")
        import traceback
        traceback.print_exc()


async def _handle_scheduled_posts(
    posts: List[Dict[str, Any]],
    account_id: str
) -> None:
    """Xử lý các bài được lên lịch."""
    print(f"📅 Có {len(posts)} bài sẽ được lên lịch:")
    scheduler = Scheduler()
    from services.scheduler.models import Platform
    
    priority_map = {
        "LOW": JobPriority.LOW,
        "NORMAL": JobPriority.NORMAL,
        "HIGH": JobPriority.HIGH,
        "URGENT": JobPriority.URGENT
    }
    
    platform_map = {
        "THREADS": Platform.THREADS,
        "FACEBOOK": Platform.FACEBOOK
    }
    
    for i, post in enumerate(posts, 1):
        try:
            priority = priority_map.get(
                post.get("priority", "NORMAL"),
                JobPriority.NORMAL
            )
            # Parse platform với backward compatible: default THREADS
            platform_str = post.get("platform", "THREADS")
            if platform_str:
                platform_str = platform_str.upper()
            else:
                platform_str = "THREADS"
            platform = platform_map.get(platform_str, Platform.THREADS)
            
            job_id = scheduler.add_job(
                account_id=account_id,
                content=post["content"],
                scheduled_time=post["scheduled_time"],
                priority=priority,
                platform=platform
            )
            added_job = scheduler.jobs.get(job_id)
            platform_display = platform_str if platform_str else "THREADS"
            print(f"   {i}. ✅ Đã lên lịch: {post['scheduled_time'].strftime('%Y-%m-%d %H:%M:%S')} "
                  f"(Priority: {post.get('priority', 'NORMAL')}, Platform: {platform_display})")
            if added_job and added_job.status_message:
                print(f"      Trạng thái: {added_job.status_message}")
        except Exception as e:
            print(f"   {i}. ❌ Lỗi lên lịch: {str(e)}")
    
    print(f"\n💡 Chạy scheduler bằng lệnh:")
    print(f"   python main.py --scheduler --account {account_id}")


async def _handle_immediate_posts(
    posts: List[Dict[str, Any]],
    account_id: str,
    config: Config
) -> None:
    """Xử lý các bài đăng ngay."""
    print(f"\n🚀 Có {len(posts)} bài sẽ được đăng ngay:\n")
    
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
            
            # Đăng từng bài
            composer = ThreadComposer(browser.page, config=config)
            success_count = 0
            fail_count = 0
            
            for i, post in enumerate(posts, 1):
                print(f"[{i}/{len(posts)}] Đang đăng: {post['content'][:50]}...")
                
                try:
                    result = await composer.post_thread(post["content"])
                    
                    if result.success:
                        success_count += 1
                        print(f"   ✅ Thành công! Thread ID: {result.thread_id}")
                    else:
                        fail_count += 1
                        print(f"   ❌ Thất bại: {result.error}")
                        if result.shadow_fail:
                            print("   ⚠️  Shadow fail: đã click nhưng không đăng")
                    
                    # Delay giữa các bài (anti-detection)
                    if i < len(posts):
                        delay = random.uniform(10.0, 20.0)
                        print(f"   ⏳ Chờ {delay:.1f}s trước bài tiếp theo...")
                        await asyncio.sleep(delay)
                        
                except KeyboardInterrupt:
                    print("\n\n⏹️  Đã hủy bởi user.")
                    break
                except Exception as e:
                    fail_count += 1
                    print(f"   ❌ Lỗi không mong đợi: {str(e)}")
            
            print(f"\n📊 Kết quả:")
            print(f"   ✅ Thành công: {success_count}/{len(posts)}")
            print(f"   ❌ Thất bại: {fail_count}/{len(posts)}")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Đã hủy bởi user.")
    except Exception as e:
        print(f"\n❌ Lỗi không mong đợi: {str(e)}")
        import traceback
        traceback.print_exc()

