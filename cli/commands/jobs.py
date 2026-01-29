"""
Module: cli/commands/jobs.py

Job management commands.
"""

import json
from datetime import datetime
from pathlib import Path

from services.scheduler import Scheduler, JobStatus
from services.exceptions import (
    SchedulerError,
    JobNotFoundError,
    StorageError
)


def handle_list_jobs(account_id: str) -> None:
    """
    Xử lý lệnh liệt kê jobs.
    
    Args:
        account_id: ID tài khoản
    """
    scheduler = Scheduler()
    
    # QUAN TRỌNG: Reload jobs từ storage trước khi list để đảm bảo realtime update
    # Điều này đảm bảo CLI luôn hiển thị jobs mới nhất từ file JSON
    try:
        scheduler.reload_jobs(force=False)  # Không force để tránh race condition
    except Exception as reload_error:
        # Log nhưng không fail - vẫn có thể list jobs từ memory
        print(f"⚠️  Warning: Failed to reload jobs: {str(reload_error)}")
    
    jobs = scheduler.list_jobs(account_id=account_id)
    
    if not jobs:
        print("📋 Không có jobs nào được lên lịch.")
        return
    
    print(f"\n📋 Danh sách jobs cho account: {account_id}")
    print("-" * 80)
    for job in jobs:
        status_emoji = {
            "pending": "⏳",
            "scheduled": "📅",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫",
            "expired": "⏰"
        }.get(job.status.value, "❓")
        
        priority_emoji = {
            1: "🔵",
            2: "🟢",
            3: "🟡",
            4: "🔴"
        }.get(job.priority.value, "⚪")
        
        print(f"{status_emoji} {priority_emoji} Job ID: {job.job_id}")
        print(f"   Content: {job.content[:50]}{'...' if len(job.content) > 50 else ''}")
        print(f"   Scheduled: {job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Status: {job.status.value}")
        if job.status_message:
            print(f"   Trạng thái: {job.status_message}")
        if job.thread_id:
            print(f"   Thread ID: {job.thread_id}")
        if job.error:
            print(f"   Error: {job.error}")
        if job.retry_count > 0:
            print(f"   Retry: {job.retry_count}/{job.max_retries}")
        print()


def handle_remove_job(job_id: str) -> None:
    """
    Xử lý lệnh xóa job.
    
    Args:
        job_id: ID của job cần xóa
    """
    try:
        scheduler = Scheduler()
        scheduler.remove_job(job_id)
        print(f"✅ Đã xóa job: {job_id}")
    except JobNotFoundError as e:
        print(f"❌ {str(e)}")
    except StorageError as e:
        print(f"❌ Lỗi lưu sau khi xóa: {str(e)}")
    except SchedulerError as e:
        print(f"❌ Lỗi scheduler: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}")
        print(f"   Loại lỗi: {type(e).__name__}")


def handle_reset_jobs(account_id: str = None) -> None:
    """
    Xử lý lệnh reset tất cả jobs.
    
    Args:
        account_id: ID tài khoản (optional)
    """
    try:
        scheduler = Scheduler()
        jobs = scheduler.list_jobs(account_id=account_id)
        
        if not jobs:
            print("📋 Không có jobs nào để xóa.")
            return
        
        print(f"⚠️  Bạn sắp xóa {len(jobs)} job(s).")
        confirm = input("Nhập 'yes' để xác nhận: ")
        
        if confirm.lower() != 'yes':
            print("❌ Đã hủy. Không có job nào bị xóa.")
            return
        
        deleted_count = 0
        for job in jobs:
            try:
                scheduler.remove_job(job.job_id)
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Không thể xóa job {job.job_id}: {str(e)}")
        
        print(f"✅ Đã xóa {deleted_count}/{len(jobs)} job(s).")
    except StorageError as e:
        print(f"❌ Lỗi lưu: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}")
        print(f"   Loại lỗi: {type(e).__name__}")


def handle_reset_status(status: str, account_id: str = None) -> None:
    """
    Xử lý lệnh reset status của jobs.
    
    Args:
        status: Status cần reset (running, failed, expired)
        account_id: ID tài khoản (optional)
    """
    try:
        scheduler = Scheduler()
        jobs = scheduler.list_jobs(account_id=account_id)
        
        # Filter jobs theo status
        target_status_map = {
            "running": JobStatus.RUNNING,
            "failed": JobStatus.FAILED,
            "expired": JobStatus.EXPIRED
        }
        target_status = target_status_map[status]
        
        filtered_jobs = [j for j in jobs if j.status == target_status]
        
        if not filtered_jobs:
            print(f"📋 Không có jobs nào có status '{status}'.")
            return
        
        print(f"⚠️  Bạn sắp reset {len(filtered_jobs)} job(s) từ '{status}' về 'SCHEDULED'.")
        confirm = input("Nhập 'yes' để xác nhận: ")
        
        if confirm.lower() != 'yes':
            print("❌ Đã hủy. Không có job nào bị reset.")
            return
        
        reset_count = 0
        for job in filtered_jobs:
            try:
                job.status = JobStatus.SCHEDULED
                job.status_message = f"Đã reset từ {status} - sẽ chạy vào {job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
                job.error = None
                job.retry_count = 0
                reset_count += 1
            except Exception as e:
                print(f"⚠️  Không thể reset job {job.job_id}: {str(e)}")
        
        # Lưu lại
        scheduler.storage.save_jobs(scheduler.jobs)
        
        print(f"✅ Đã reset {reset_count}/{len(filtered_jobs)} job(s).")
    except StorageError as e:
        print(f"❌ Lỗi lưu: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}")
        print(f"   Loại lỗi: {type(e).__name__}")


def _get_job_file_path(storage_dir: Path, date: datetime) -> Path:
    """
    Helper function để lấy đường dẫn file job cho một ngày.
    
    Args:
        storage_dir: Thư mục lưu jobs
        date: Ngày để lấy file path
    
    Returns:
        Path đến file job: jobs/jobs_YYYY-MM-DD.json
    """
    date_str = date.strftime("%Y-%m-%d")
    return storage_dir / f"jobs_{date_str}.json"


def handle_delete_job_file(date_str: str) -> None:
    """
    Xử lý lệnh xóa file job theo ngày.
    
    Args:
        date_str: Ngày dạng YYYY-MM-DD
    """
    try:
        # Validate date format
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Format ngày không hợp lệ. Sử dụng: YYYY-MM-DD (ví dụ: 2025-12-17)")
            return
        
        scheduler = Scheduler()
        job_file_path = _get_job_file_path(scheduler.storage_dir, date_obj)
        
        if not job_file_path.exists():
            print(f"❌ File không tồn tại: {job_file_path}")
            return
        
        # Đếm số jobs trong file
        try:
            with open(job_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs_count = len(data.get('jobs', []))
        except Exception:
            jobs_count = 0
        
        print(f"⚠️  Bạn sắp xóa file: {job_file_path.name}")
        if jobs_count > 0:
            print(f"   File này chứa {jobs_count} job(s).")
        print(f"   Ngày: {date_str}")
        confirm = input("Nhập 'yes' để xác nhận: ")
        
        if confirm.lower() != 'yes':
            print("❌ Đã hủy. File không bị xóa.")
            return
        
        # Xóa file
        job_file_path.unlink()
        
        # Reload jobs để cập nhật trong memory
        scheduler.jobs = scheduler.storage.load_jobs()
        
        print(f"✅ Đã xóa file: {job_file_path.name}")
        if jobs_count > 0:
            print(f"   Đã xóa {jobs_count} job(s) trong file.")
    except PermissionError as e:
        print(f"❌ Không có quyền xóa file: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}")
        print(f"   Loại lỗi: {type(e).__name__}")


def handle_reset_job_file(date_str: str) -> None:
    """
    Xử lý lệnh reset file job về trạng thái mới.
    
    Args:
        date_str: Ngày dạng YYYY-MM-DD
    """
    try:
        # Validate date format
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Format ngày không hợp lệ. Sử dụng: YYYY-MM-DD (ví dụ: 2025-12-17)")
            return
        
        scheduler = Scheduler()
        job_file_path = _get_job_file_path(scheduler.storage_dir, date_obj)
        
        if not job_file_path.exists():
            print(f"❌ File không tồn tại: {job_file_path}")
            return
        
        # Load jobs từ file
        try:
            with open(job_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs_data = data.get('jobs', [])
        except Exception as e:
            print(f"❌ Không thể đọc file: {str(e)}")
            return
        
        if not jobs_data:
            print(f"📋 File rỗng, không có job nào để reset.")
            return
        
        # Đếm jobs sẽ bị reset
        reset_count = 0
        for job_data in jobs_data:
            status = job_data.get('status', '')
            # Chỉ reset các jobs không phải COMPLETED
            if status not in ['completed', 'cancelled']:
                reset_count += 1
        
        if reset_count == 0:
            print(f"📋 Không có job nào cần reset (tất cả đã completed hoặc cancelled).")
            return
        
        print(f"⚠️  Bạn sắp reset {reset_count} job(s) trong file: {job_file_path.name}")
        print(f"   Tất cả jobs sẽ được reset về SCHEDULED (trừ COMPLETED và CANCELLED).")
        print(f"   Ngày: {date_str}")
        confirm = input("Nhập 'yes' để xác nhận: ")
        
        if confirm.lower() != 'yes':
            print("❌ Đã hủy. File không bị thay đổi.")
            return
        
        # Reset jobs
        updated_count = 0
        for job_data in jobs_data:
            status = job_data.get('status', '')
            # Chỉ reset các jobs không phải COMPLETED hoặc CANCELLED
            if status not in ['completed', 'cancelled']:
                job_data['status'] = 'scheduled'
                job_data['error'] = None
                job_data['retry_count'] = 0
                if 'status_message' in job_data:
                    scheduled_time_str = job_data.get('scheduled_time', '')
                    try:
                        scheduled_time = datetime.fromisoformat(scheduled_time_str) if scheduled_time_str else datetime.now()
                        job_data['status_message'] = f"Đã reset - sẽ chạy vào {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    except Exception:
                        job_data['status_message'] = "Đã reset - sẵn sàng chạy"
                updated_count += 1
        
        # Lưu lại file
        data['jobs'] = jobs_data
        with open(job_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Reload jobs để cập nhật trong memory
        scheduler.jobs = scheduler.storage.load_jobs()
        
        print(f"✅ Đã reset {updated_count} job(s) trong file: {job_file_path.name}")
    except PermissionError as e:
        print(f"❌ Không có quyền ghi file: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}")
        print(f"   Loại lỗi: {type(e).__name__}")

