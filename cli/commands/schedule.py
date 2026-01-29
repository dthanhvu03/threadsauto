"""
Module: cli/commands/schedule.py

Scheduling commands.
"""

from datetime import datetime, timedelta

from services.scheduler import Scheduler, JobPriority
from services.exceptions import (
    SchedulerError,
    InvalidScheduleTimeError,
    StorageError
)


def handle_schedule_job(
    account_id: str,
    content: str,
    schedule_str: str,
    priority_str: str
) -> None:
    """
    Xử lý lệnh lên lịch đăng bài.
    
    Args:
        account_id: ID tài khoản
        content: Nội dung thread
        schedule_str: Thời gian lên lịch (format: YYYY-MM-DD HH:MM:SS)
        priority_str: Độ ưu tiên (LOW, NORMAL, HIGH, URGENT)
    """
    if not content:
        print("❌ Cần --content khi lên lịch đăng bài.")
        return
    
    try:
        scheduled_time = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M:%S")
        
        # Validate scheduled_time không quá xa trong quá khứ
        now = datetime.now()
        if scheduled_time < now - timedelta(days=365):
            print(f"❌ Thời gian lên lịch ({scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}) quá xa trong quá khứ (> 1 năm)")
            print(f"   Hiện tại: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        # Validate scheduled_time không quá xa trong tương lai
        if scheduled_time > now + timedelta(days=365):
            print(f"❌ Thời gian lên lịch ({scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}) quá xa trong tương lai (> 1 năm)")
            print(f"   Hiện tại: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        # Cảnh báo nếu scheduled_time trong quá khứ gần (< 1 năm nhưng đã qua)
        if scheduled_time < now:
            print(f"⚠️  Cảnh báo: Thời gian lên lịch ({scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}) đã qua")
            print(f"   Hiện tại: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            response = input("   Bạn có muốn tiếp tục? (y/n): ")
            if response.lower() != 'y':
                print("❌ Đã hủy.")
                return
    except ValueError as e:
        print(f"❌ Format thời gian không đúng: {str(e)}")
        print("   Sử dụng format: YYYY-MM-DD HH:MM:SS")
        print(f"   Ví dụ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return
    
    priority_map = {
        "LOW": JobPriority.LOW,
        "NORMAL": JobPriority.NORMAL,
        "HIGH": JobPriority.HIGH,
        "URGENT": JobPriority.URGENT
    }
    priority = priority_map.get(priority_str, JobPriority.NORMAL)
    
    try:
        scheduler = Scheduler()
        job_id = scheduler.add_job(
            account_id=account_id,
            content=content,
            scheduled_time=scheduled_time,
            priority=priority
        )
        
        print(f"✅ Đã lên lịch đăng bài!")
        print(f"   Job ID: {job_id}")
        print(f"   Thời gian: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Độ ưu tiên: {priority_str}")
        print(f"\n💡 Chạy scheduler bằng lệnh:")
        print(f"   python main.py --scheduler --account {account_id}")
    except InvalidScheduleTimeError as e:
        print(f"❌ Lỗi thời gian lên lịch: {str(e)}")
    except ValueError as e:
        print(f"❌ Lỗi validation: {str(e)}")
    except StorageError as e:
        print(f"❌ Lỗi lưu job: {str(e)}")
        print("   Kiểm tra quyền ghi thư mục jobs/")
    except SchedulerError as e:
        print(f"❌ Lỗi scheduler: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}")
        print(f"   Loại lỗi: {type(e).__name__}")


async def handle_scheduler(account_id: str, post_thread_callback) -> None:
    """
    Xử lý lệnh chạy scheduler.
    
    Args:
        account_id: ID tài khoản
        post_thread_callback: Callback function để đăng bài
    """
    import asyncio
    
    scheduler = Scheduler()
    
    print("🚀 Bắt đầu scheduler...")
    print("📋 Đang load jobs...")
    
    jobs = scheduler.list_jobs(account_id=account_id, status=None)
    print(f"📊 Tổng số jobs: {len(jobs)}")
    
    if not jobs:
        print("⚠️  Không có jobs nào để chạy. Thoát.")
        return
    
    print("\n⏰ Scheduler đang chạy. Nhấn Ctrl+C để dừng.\n")
    
    try:
        # start() không phải async, chỉ tạo task và return
        scheduler.start(post_thread_callback)
        # Chạy vô hạn cho đến khi bị interrupt
        while scheduler.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Đang dừng scheduler...")
        await scheduler.stop()
        print("✅ Scheduler đã dừng.")

