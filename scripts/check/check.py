#!/usr/bin/env python3
"""
Unified Check Script for Threads Automation Tool
Combines all check scripts into one with menu
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Setup path using common utility
from scripts.common import (
    setup_path,
    get_logger,
    get_mysql_config,
    get_mysql_connection,
    get_account_storage,
    get_account_username,
    print_header,
    print_section
)

# Add parent directory to path (must be after importing common)
setup_path()

# Mock streamlit for scripts that need it
sys.modules['streamlit'] = type(sys)('streamlit')

from services.scheduler import Scheduler, JobStatus
from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.analytics.storage import MetricsStorage
from datetime import datetime

# Import get_active_scheduler with fallback
try:
    from ui.utils import get_active_scheduler
except ImportError:
    _active_scheduler = None
    def get_active_scheduler():
        return _active_scheduler


def show_menu():
    """Show check menu."""
    print()
    print("=" * 60)
    print("CHECK SCRIPTS MENU")
    print("=" * 60)
    print()
    print("1. Check Job Status")
    print("2. Check Scheduler Status")
    print("3. Check Scheduler Live")
    print("4. Check Scheduler Workflow")
    print("5. Check Jobs Simple")
    print("6. Check Thread ID in DB")
    print("7. Check Thread ID in DB (Direct)")
    print("8. Verify Browser Profile Account")
    print()
    print("0. Exit")
    print()
    choice = input("Chọn option (0-8): ").strip()
    return choice


# ============================================================================
# CHECK JOB STATUS
# ============================================================================

def check_job_status(fix: bool = False):
    """Kiểm tra trạng thái jobs."""
    logger = get_logger("check_jobs")
    scheduler = Scheduler(storage_dir=Path("./jobs"), logger=logger)
    
    all_jobs = scheduler.list_jobs()
    
    print_header("📊 KIỂM TRA TRẠNG THÁI JOBS")
    print()
    
    # Phân loại jobs
    by_status = {}
    for job in all_jobs:
        status = job.status.value
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(job)
    
    print("📈 Jobs theo trạng thái:")
    for status, jobs in sorted(by_status.items()):
        print(f"  {status:15s}: {len(jobs):3d} jobs")
    print()
    
    # Kiểm tra jobs đã đến thời gian nhưng chưa chạy
    now = datetime.now()
    ready_but_not_running = []
    
    for job in all_jobs:
        if job.status in [JobStatus.SCHEDULED, JobStatus.PENDING]:
            if now >= job.scheduled_time:
                ready_but_not_running.append(job)
    
    if ready_but_not_running:
        print(f"⚠️  Tìm thấy {len(ready_but_not_running)} jobs đã đến thời gian nhưng chưa chạy:")
        for job in ready_but_not_running[:10]:
            time_passed = (now - job.scheduled_time).total_seconds() / 60
            print(f"  - {job.job_id[:8]}... scheduled: {job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} "
                  f"(đã qua {int(time_passed)} phút)")
        if len(ready_but_not_running) > 10:
            print(f"  ... và {len(ready_but_not_running) - 10} jobs khác")
        print()
        
        if fix:
            print("🔧 Đang fix...")
            print("   → Jobs này cần được scheduler chạy. Kiểm tra:")
            print("     1. Scheduler có đang chạy không?")
            print("     2. Có lỗi trong logs không?")
            print("     3. Jobs có bị stuck không?")
        else:
            print("💡 Để fix, chạy: python scripts/check/check.py --job-status --fix")
    
    # Kiểm tra jobs completed nhưng thiếu completed_at
    completed_without_timestamp = []
    for job in all_jobs:
        if job.status == JobStatus.COMPLETED:
            if not job.completed_at:
                completed_without_timestamp.append(job)
    
    if completed_without_timestamp:
        print(f"⚠️  Tìm thấy {len(completed_without_timestamp)} jobs COMPLETED nhưng thiếu completed_at:")
        for job in completed_without_timestamp[:5]:
            print(f"  - {job.job_id[:8]}... thread_id: {job.thread_id or 'N/A'}")
        print()
        
        if fix:
            print("🔧 Đang fix...")
            fixed = 0
            for job in completed_without_timestamp:
                if job.started_at:
                    job.completed_at = job.started_at
                    fixed += 1
                elif job.created_at:
                    job.completed_at = job.created_at
                    fixed += 1
            
            if fixed > 0:
                scheduler._save_jobs()
                print(f"   ✅ Đã fix {fixed} jobs (set completed_at từ started_at/created_at)")
    
    # Kiểm tra jobs running quá lâu (có thể bị stuck)
    running_too_long = []
    for job in all_jobs:
        if job.status == JobStatus.RUNNING:
            if job.started_at:
                running_duration = (now - job.started_at).total_seconds() / 60
                if running_duration > 30:  # > 30 phút
                    running_too_long.append((job, running_duration))
    
    if running_too_long:
        print(f"⚠️  Tìm thấy {len(running_too_long)} jobs RUNNING quá lâu (có thể bị stuck):")
        for job, duration in running_too_long[:5]:
            print(f"  - {job.job_id[:8]}... đã chạy {int(duration)} phút")
        print()
        
        if fix:
            print("🔧 Đang recover stuck jobs...")
            scheduler.recovery.recover_stuck_jobs(scheduler.jobs, scheduler._save_jobs)
            print("   ✅ Đã recover stuck jobs")
    
    print()
    print_header("✅ Kiểm tra hoàn tất")


# ============================================================================
# CHECK SCHEDULER STATUS
# ============================================================================

def check_scheduler_status():
    """Kiểm tra trạng thái scheduler."""
    print_header("🔍 KIỂM TRA TRẠNG THÁI SCHEDULER")
    print()
    
    # === 1. Check active scheduler ===
    print_section("📋 1. ACTIVE SCHEDULER")
    active_scheduler = get_active_scheduler()
    if active_scheduler:
        print(f"✅ Active scheduler tồn tại")
        print(f"   - Instance ID: {id(active_scheduler)}")
        print(f"   - Running: {active_scheduler.running}")
        print(f"   - Jobs count: {len(active_scheduler.jobs)}")
        
        if hasattr(active_scheduler, '_task'):
            task = active_scheduler._task
            if task:
                print(f"   - Task: {task}")
                print(f"   - Task done: {task.done()}")
                if task.done():
                    try:
                        result = task.result()
                        print(f"   - Task result: {result}")
                    except Exception as e:
                        print(f"   - Task exception: {e}")
                else:
                    print(f"   - Task đang chạy")
            else:
                print(f"   - Task: None (chưa được tạo)")
        else:
            print(f"   - Task: Không có attribute _task")
    else:
        print("❌ KHÔNG CÓ active scheduler!")
        print("   → Scheduler chưa được start từ UI")
    print()
    
    # === 2. Tạo scheduler mới để test ===
    print_section("📋 2. TẠO SCHEDULER MỚI (TEST)")
    try:
        logger = get_logger("test")
        test_scheduler = Scheduler(storage_dir=Path("./jobs"), logger=logger)
        print(f"✅ Scheduler mới tạo thành công")
        print(f"   - Running: {test_scheduler.running}")
        print(f"   - Jobs count: {len(test_scheduler.jobs)}")
        
        # Test get_ready_jobs
        ready_jobs = test_scheduler.get_ready_jobs()
        print(f"   - Ready jobs: {len(ready_jobs)}")
        
        if ready_jobs:
            print("   Jobs sẵn sàng:")
            for job in ready_jobs[:3]:
                print(f"     - {job.job_id[:8]}... | {job.scheduled_time}")
    except Exception as e:
        print(f"❌ Lỗi tạo scheduler: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # === 3. Khuyến nghị ===
    print_header("💡 KHUYẾN NGHỊ")
    
    if not active_scheduler:
        print("❌ SCHEDULER CHƯA ĐƯỢC START!")
        print()
        print("CÁCH KHẮC PHỤC:")
        print("1. Mở UI (Streamlit app)")
        print("2. Vào tab '⏰ Lịch trình'")
        print("3. Click nút '▶️ Bắt đầu' để start scheduler")
        print("4. Kiểm tra lại trạng thái")
    elif not active_scheduler.running:
        print("⚠️  SCHEDULER TỒN TẠI NHƯNG KHÔNG ĐANG CHẠY!")
        print()
        print("CÁCH KHẮC PHỤC:")
        print("1. Restart scheduler từ UI")
        print("2. Hoặc stop và start lại")
    else:
        print("✅ Scheduler đang chạy bình thường")
        if ready_jobs:
            print(f"   → Có {len(ready_jobs)} jobs sẵn sàng chạy")
        else:
            print("   → Không có jobs sẵn sàng (có thể chưa đến giờ)")
    print()


# ============================================================================
# CHECK SCHEDULER LIVE
# ============================================================================

def check_scheduler_live():
    """Kiểm tra scheduler đang chạy."""
    print_header("🔍 KIỂM TRA SCHEDULER ĐANG CHẠY")
    print()
    
    now = datetime.now()
    print(f"⏰ Thời gian hiện tại: {now}")
    print()
    
    # Check active scheduler
    active_scheduler = get_active_scheduler()
    if not active_scheduler:
        print("❌ KHÔNG CÓ active scheduler!")
        print("   → Scheduler chưa được start từ UI")
        return
    
    print(f"✅ Active scheduler tồn tại")
    print(f"   - Running: {active_scheduler.running}")
    print(f"   - Jobs count: {len(active_scheduler.jobs)}")
    print()
    
    if not active_scheduler.running:
        print("❌ Scheduler không đang chạy!")
        return
    
    # Check ready jobs
    print_section("📋 KIỂM TRA READY JOBS")
    try:
        ready_jobs = active_scheduler.get_ready_jobs()
        print(f"Ready jobs: {len(ready_jobs)}")
        
        if ready_jobs:
            print("   Jobs sẵn sàng:")
            for job in ready_jobs[:5]:
                scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"   - {job.job_id[:8]}... | {scheduled_str} | Priority: {job.priority.value}")
        else:
            print("   ⚠️  Không có jobs sẵn sàng")
            
            # Debug: Check scheduled jobs
            scheduled = [j for j in active_scheduler.jobs.values() if j.status == JobStatus.SCHEDULED]
            print(f"   Scheduled jobs: {len(scheduled)}")
            
            if scheduled:
                print("   Jobs scheduled (chưa ready):")
                for job in scheduled[:5]:
                    scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                    time_until = (job.scheduled_time - now).total_seconds()
                    is_ready = job.is_ready()
                    print(f"   - {job.job_id[:8]}... | {scheduled_str} | Time until: {int(time_until)}s | Ready: {is_ready}")
    except Exception as e:
        print(f"❌ Lỗi get_ready_jobs: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Check running jobs
    print_section("📋 KIỂM TRA RUNNING JOBS")
    try:
        running_jobs = [j for j in active_scheduler.jobs.values() if j.status == JobStatus.RUNNING]
        print(f"Running jobs: {len(running_jobs)}")
        if running_jobs:
            for job in running_jobs:
                print(f"   - {job.job_id[:8]}... | Started: {job.started_at}")
    except Exception as e:
        print(f"❌ Lỗi check running: {e}")
    print()
    
    # Check task
    print_section("📋 KIỂM TRA SCHEDULER TASK")
    if hasattr(active_scheduler, '_task'):
        task = active_scheduler._task
        if task:
            print(f"Task: {task}")
            print(f"Task done: {task.done()}")
            if task.done():
                try:
                    result = task.result()
                    print(f"Task result: {result}")
                except Exception as e:
                    print(f"❌ Task exception: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("✅ Task đang chạy")
        else:
            print("❌ Task is None")
    else:
        print("❌ Không có attribute _task")
    print()


# ============================================================================
# CHECK SCHEDULER WORKFLOW
# ============================================================================

def check_scheduler_workflow():
    """Kiểm tra workflow scheduler."""
    print_header("🔍 KIỂM TRA SCHEDULER WORKFLOW")
    print()
    
    # === 1. Check Active Scheduler ===
    print("📋 1. KIỂM TRA ACTIVE SCHEDULER")
    print("-" * 80)
    active_scheduler = get_active_scheduler()
    if active_scheduler:
        print(f"✅ Active scheduler tồn tại")
        print(f"   - Running: {active_scheduler.running}")
        print(f"   - Jobs count: {len(active_scheduler.jobs)}")
        print(f"   - Instance ID: {id(active_scheduler)}")
    else:
        print("❌ KHÔNG CÓ active scheduler!")
        print("   → Scheduler chưa được start hoặc đã bị dừng")
        print()
        return
    
    print()
    
    # === 2. Check Jobs Status ===
    print_section("📋 2. KIỂM TRA JOBS")
    now = datetime.now()
    print(f"⏰ Thời gian hiện tại: {now}")
    print()
    
    all_jobs = list(active_scheduler.jobs.values())
    print(f"📊 Tổng số jobs: {len(all_jobs)}")
    print()
    
    # Phân loại theo status
    by_status = {}
    for job in all_jobs:
        status = job.status.value if hasattr(job.status, 'value') else str(job.status)
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(job)
    
    print("📈 Jobs theo trạng thái:")
    for status, jobs in sorted(by_status.items()):
        print(f"   {status:15s}: {len(jobs):3d} jobs")
    print()
    
    # === 3. Check Ready Jobs ===
    print_section("📋 3. KIỂM TRA READY JOBS")
    try:
        ready_jobs = active_scheduler.get_ready_jobs()
        print(f"✅ Ready jobs: {len(ready_jobs)}")
        if ready_jobs:
            print("   Jobs sẵn sàng chạy:")
            for job in ready_jobs[:5]:
                scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(job.scheduled_time, 'strftime') else str(job.scheduled_time)
                time_until = (job.scheduled_time - now).total_seconds()
                print(f"   - {job.job_id[:8]}... | {scheduled_str} | Priority: {job.priority.value if hasattr(job.priority, 'value') else job.priority} | Time until: {int(time_until)}s")
        else:
            print("   ⚠️  Không có jobs sẵn sàng")
    except Exception as e:
        print(f"❌ Lỗi khi lấy ready jobs: {str(e)}")
        import traceback
        traceback.print_exc()
    print()
    
    # === 4. Check Scheduled Jobs ===
    print_section("📋 4. KIỂM TRA SCHEDULED JOBS (CHƯA ĐẾN GIỜ)")
    scheduled_jobs = [j for j in all_jobs if j.status == JobStatus.SCHEDULED]
    if scheduled_jobs:
        print(f"📅 Scheduled jobs: {len(scheduled_jobs)}")
        print("   Jobs đang chờ:")
        for job in scheduled_jobs[:10]:
            scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(job.scheduled_time, 'strftime') else str(job.scheduled_time)
            time_until = (job.scheduled_time - now).total_seconds()
            is_ready = job.is_ready() if hasattr(job, 'is_ready') else False
            status_msg = "✅ READY" if is_ready else f"⏳ Chờ {int(time_until)}s"
            print(f"   - {job.job_id[:8]}... | {scheduled_str} | {status_msg}")
    else:
        print("   📭 Không có scheduled jobs")
    print()
    
    # === 5. Check Overdue Jobs ===
    print_section("📋 5. KIỂM TRA JOBS ĐÃ QUÁ GIỜ NHƯNG CHƯA CHẠY")
    overdue_jobs = []
    for job in all_jobs:
        if job.status in [JobStatus.SCHEDULED, JobStatus.PENDING]:
            if now >= job.scheduled_time:
                is_expired = job.is_expired() if hasattr(job, 'is_expired') else False
                if not is_expired:
                    overdue_jobs.append(job)
    
    if overdue_jobs:
        print(f"⚠️  CÓ {len(overdue_jobs)} JOBS ĐÃ QUÁ GIỜ NHƯNG CHƯA CHẠY!")
        print("   Đây là vấn đề - jobs đã đến giờ nhưng scheduler không chạy:")
        for job in overdue_jobs[:10]:
            scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(job.scheduled_time, 'strftime') else str(job.scheduled_time)
            overdue_seconds = (now - job.scheduled_time).total_seconds()
            is_ready = job.is_ready() if hasattr(job, 'is_ready') else False
            print(f"   - {job.job_id[:8]}... | {scheduled_str} | Quá {int(overdue_seconds)}s | Ready: {is_ready}")
        print()
        print("   🔍 NGUYÊN NHÂN CÓ THỂ:")
        print("      1. Scheduler không đang chạy (running = False)")
        print("      2. Có job đang RUNNING (scheduler chỉ chạy 1 job tại một thời điểm)")
        print("      3. is_ready() trả về False (có thể do expired hoặc status không đúng)")
        print("      4. get_ready_jobs() không tìm thấy jobs (có thể do filter logic)")
    else:
        print("✅ Không có jobs nào đã quá giờ")
    print()
    
    # === 6. Check Running Jobs ===
    print_section("📋 6. KIỂM TRA RUNNING JOBS")
    running_jobs = [j for j in all_jobs if j.status == JobStatus.RUNNING]
    if running_jobs:
        print(f"🔄 Running jobs: {len(running_jobs)}")
        print("   Jobs đang chạy (scheduler sẽ không chạy job mới khi có job đang RUNNING):")
        for job in running_jobs:
            started_str = job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at and hasattr(job.started_at, 'strftime') else str(job.started_at) if job.started_at else "N/A"
            running_duration = (now - job.started_at).total_seconds() if job.started_at else 0
            is_stuck = job.is_stuck() if hasattr(job, 'is_stuck') else False
            stuck_msg = "⚠️ STUCK" if is_stuck else "✅ OK"
            print(f"   - {job.job_id[:8]}... | Started: {started_str} | Duration: {int(running_duration)}s | {stuck_msg}")
    else:
        print("✅ Không có jobs đang chạy")
    print()
    
    # === 7. Recommendations ===
    print_header("💡 KHUYẾN NGHỊ")
    
    if not active_scheduler.running:
        print("❌ SCHEDULER KHÔNG ĐANG CHẠY!")
        print("   → Cần start scheduler từ UI hoặc CLI")
    elif overdue_jobs:
        print("⚠️  CÓ JOBS ĐÃ QUÁ GIỜ NHƯNG CHƯA CHẠY")
        print("   → Kiểm tra:")
        print("      - Scheduler loop có đang chạy không?")
        print("      - get_ready_jobs() có trả về jobs không?")
        print("      - Có job đang RUNNING không?")
        print("      - is_ready() có trả về True không?")
    elif running_jobs:
        print("ℹ️  CÓ JOBS ĐANG CHẠY")
        print("   → Scheduler sẽ chờ job hiện tại hoàn thành trước khi chạy job mới")
    else:
        print("✅ Scheduler đang hoạt động bình thường")
        if scheduled_jobs:
            next_job = min(scheduled_jobs, key=lambda j: j.scheduled_time)
            time_until = (next_job.scheduled_time - now).total_seconds()
            print(f"   → Job tiếp theo sẽ chạy sau {int(time_until)} giây")
    
    print()


# ============================================================================
# CHECK JOBS SIMPLE
# ============================================================================

def check_jobs_simple():
    """Kiểm tra jobs từ file JSON."""
    print_header("🔍 KIỂM TRA JOBS TỪ FILE JSON")
    print()
    
    jobs_dir = Path("./jobs")
    if not jobs_dir.exists():
        print(f"❌ Thư mục jobs không tồn tại: {jobs_dir}")
        return
    
    now = datetime.now()
    print(f"⏰ Thời gian hiện tại: {now}")
    print()
    
    # Load scheduled jobs
    scheduled_file = jobs_dir / f"jobs_{now.strftime('%Y-%m-%d')}_scheduled.json"
    if scheduled_file.exists():
        print(f"📄 File: {scheduled_file.name}")
        import json
        with open(scheduled_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            jobs = data.get('jobs', [])
            print(f"   Tổng số jobs: {len(jobs)}")
            print()
            
            # Check ready jobs
            ready_jobs = []
            overdue_jobs = []
            
            for job in jobs:
                try:
                    scheduled_str = job.get('scheduled_time', '')
                    if scheduled_str:
                        # Parse datetime
                        if 'T' in scheduled_str:
                            scheduled_time = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
                        else:
                            scheduled_time = datetime.fromisoformat(scheduled_str)
                        
                        status = job.get('status', '')
                        job_id = job.get('job_id', 'unknown')[:8]
                        
                        if status == 'scheduled':
                            if now >= scheduled_time:
                                overdue_jobs.append((job_id, scheduled_time, job))
                                if not job.get('error'):  # Not failed
                                    ready_jobs.append((job_id, scheduled_time, job))
                except Exception as e:
                    # Skip jobs with invalid datetime
                    continue
            
            print(f"📊 Phân tích:")
            print(f"   - Jobs đã quá giờ: {len(overdue_jobs)}")
            print(f"   - Jobs sẵn sàng chạy: {len(ready_jobs)}")
            print()
            
            if overdue_jobs:
                print("⚠️  JOBS ĐÃ QUÁ GIỜ NHƯNG CHƯA CHẠY:")
                for job_id, scheduled_time, job in overdue_jobs[:10]:
                    overdue_seconds = (now - scheduled_time).total_seconds()
                    status_msg = job.get('status_message', 'N/A')
                    print(f"   - {job_id}... | {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} | Quá {int(overdue_seconds)}s | {status_msg}")
                print()
            
            if ready_jobs:
                print("✅ JOBS SẴN SÀNG CHẠY:")
                for job_id, scheduled_time, job in ready_jobs[:10]:
                    print(f"   - {job_id}... | {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} | Priority: {job.get('priority', 'N/A')}")
                print()
            
            # Check running jobs
            running_file = jobs_dir / f"jobs_{now.strftime('%Y-%m-%d')}_running.json"
            if running_file.exists():
                with open(running_file, 'r', encoding='utf-8') as f:
                    running_data = json.load(f)
                    running_jobs = running_data.get('jobs', [])
                    if running_jobs:
                        print(f"🔄 JOBS ĐANG CHẠY: {len(running_jobs)}")
                        print("   → Scheduler sẽ không chạy job mới khi có job đang RUNNING")
                        for job in running_jobs:
                            job_id = job.get('job_id', 'unknown')[:8]
                            started_at = job.get('started_at', 'N/A')
                            print(f"   - {job_id}... | Started: {started_at}")
                        print()
    else:
        print(f"❌ File không tồn tại: {scheduled_file}")
    
    print_header("💡 KHUYẾN NGHỊ")
    print("1. Kiểm tra scheduler có đang chạy không (từ UI)")
    print("2. Kiểm tra logs để xem scheduler loop có đang chạy không")
    print("3. Kiểm tra xem có job đang RUNNING không (blocking)")
    print("4. Kiểm tra get_ready_jobs() có trả về jobs không")
    print()


# ============================================================================
# CHECK THREAD ID IN DB
# ============================================================================

def check_thread_id_in_db(thread_id: str, account_id: str = None):
    """Kiểm tra thread_id có trong database không."""
    try:
        mysql_config = get_mysql_config()
        
        print_header("🔍 CHECK THREAD_ID IN DATABASE")
        print(f"Thread ID: {thread_id}")
        if account_id:
            print(f"Account ID: {account_id}")
        
        # Use MySQLJobStorage
        job_storage = MySQLJobStorage(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            database=mysql_config.database
        )
        
        # Get all completed jobs and filter by thread_id
        print(f"\n📋 Checking jobs table...")
        
        jobs_found = []
        if account_id:
            # Get jobs for this account
            jobs_list = job_storage.get_jobs_by_account(account_id=account_id, status=JobStatus.COMPLETED)
            for job in jobs_list:
                if job.thread_id == thread_id:
                    jobs_found.append({
                        'job_id': job.job_id,
                        'account_id': job.account_id,
                        'thread_id': job.thread_id,
                        'status': job.status.value,
                        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                        'content': job.content
                    })
        else:
            # Get all completed jobs and filter
            all_jobs = job_storage.load_jobs()
            for job in all_jobs.values():
                if job.status == JobStatus.COMPLETED and job.thread_id == thread_id:
                    jobs_found.append({
                        'job_id': job.job_id,
                        'account_id': job.account_id,
                        'thread_id': job.thread_id,
                        'status': job.status.value,
                        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                        'content': job.content
                    })
        
        if jobs_found:
            print(f"\n✅ Found {len(jobs_found)} job(s) with this thread_id:\n")
            for idx, job in enumerate(jobs_found, 1):
                print(f"{idx}. Job ID: {job['job_id']}")
                print(f"   Account ID: {job['account_id']}")
                print(f"   Thread ID: {job['thread_id']}")
                print(f"   Status: {job['status']}")
                print(f"   Completed at: {job['completed_at']}")
                content = job['content']
                if content:
                    print(f"   Content: {content[:60]}...")
                print()
        else:
            print(f"\n❌ No jobs found with thread_id = '{thread_id}'")
            if account_id:
                print(f"   AND account_id = '{account_id}'")
        
        # Check thread_metrics
        print("=" * 80)
        print("📊 CHECK IN thread_metrics TABLE")
        print("=" * 80)
        
        metrics_storage = MetricsStorage(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            database=mysql_config.database
        )
        
        latest_metrics = metrics_storage.get_latest_metrics(thread_id)
        
        if latest_metrics:
            print(f"\n✅ Found metrics for this thread_id:\n")
            print(f"   Account: {latest_metrics.get('account_id')}")
            print(f"   Views: {latest_metrics.get('views', 'N/A')}")
            print(f"   Likes: {latest_metrics.get('likes', 0)}")
            print(f"   Replies: {latest_metrics.get('replies', 0)}")
            print(f"   Reposts: {latest_metrics.get('reposts', 0)}")
            print(f"   Shares: {latest_metrics.get('shares', 0)}")
            print(f"   Fetched at: {latest_metrics.get('fetched_at')}")
        else:
            print(f"\n⚠️  No metrics found for this thread_id")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"Thread ID: {thread_id}")
        print(f"Jobs found: {len(jobs_found)}")
        print(f"Metrics found: {'Yes' if latest_metrics else 'No'}")
        
        if jobs_found:
            accounts = set(j['account_id'] for j in jobs_found)
            print(f"\n✅ Thread ID exists in database!")
            print(f"   - Belongs to account(s): {', '.join(accounts)}")
        else:
            print(f"\n❌ Thread ID NOT found in database!")
            print(f"   This thread_id may have been:")
            print(f"   1. Extracted incorrectly (from feed instead of URL)")
            print(f"   2. Not saved after post completion")
            print(f"   3. Belongs to a different account")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# CHECK THREAD ID IN DB DIRECT
# ============================================================================

def check_thread_id_direct(account_id: str, thread_id: str = None):
    """Check thread_id trực tiếp trong MySQL."""
    try:
        print_header("🔍 CHECK THREAD_ID IN DATABASE (DIRECT SQL QUERY)")
        print(f"Account ID: {account_id}")
        if thread_id:
            print(f"Thread ID to check: {thread_id}")
        
        # Connect to MySQL using common utility
        conn = get_mysql_connection()
        
        import pymysql
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Query 1: Check trong jobs table
                print(f"\n📋 Query 1: Check trong jobs table")
                if thread_id:
                    query = """
                        SELECT 
                            job_id, account_id, thread_id, content, 
                            status, completed_at, created_at
                        FROM jobs
                        WHERE account_id = %s AND thread_id = %s
                        ORDER BY completed_at DESC
                    """
                    cursor.execute(query, (account_id, thread_id))
                    print(f"   SQL: SELECT * FROM jobs WHERE account_id = '{account_id}' AND thread_id = '{thread_id}'")
                else:
                    query = """
                        SELECT 
                            job_id, account_id, thread_id, content, 
                            status, completed_at, created_at
                        FROM jobs
                        WHERE account_id = %s AND status = 'completed' AND thread_id IS NOT NULL
                        ORDER BY completed_at DESC
                        LIMIT 10
                    """
                    cursor.execute(query, (account_id,))
                    print(f"   SQL: SELECT * FROM jobs WHERE account_id = '{account_id}' AND status = 'completed' AND thread_id IS NOT NULL")
                
                jobs = cursor.fetchall()
                
                if jobs:
                    print(f"   ✅ Found {len(jobs)} job(s):\n")
                    for idx, job in enumerate(jobs, 1):
                        print(f"   {idx}. Job ID: {job['job_id']}")
                        print(f"      Thread ID: {job['thread_id']}")
                        print(f"      Status: {job['status']}")
                        print(f"      Completed at: {job['completed_at']}")
                        content = job.get('content', '')
                        if content:
                            print(f"      Content: {content[:60]}...")
                        print()
                else:
                    print(f"   ❌ No jobs found!")
                    if thread_id:
                        print(f"      Thread ID '{thread_id}' NOT in database for account '{account_id}'")
                    else:
                        print(f"      No completed jobs with thread_id for account '{account_id}'")
                
                # Query 2: Check trong jobs_with_metrics view
                print(f"\n📋 Query 2: Check trong jobs_with_metrics view")
                if thread_id:
                    query = """
                        SELECT *
                        FROM jobs_with_metrics
                        WHERE account_id = %s AND thread_id = %s
                        ORDER BY latest_likes DESC
                    """
                    cursor.execute(query, (account_id, thread_id))
                    print(f"   SQL: SELECT * FROM jobs_with_metrics WHERE account_id = '{account_id}' AND thread_id = '{thread_id}'")
                else:
                    query = """
                        SELECT *
                        FROM jobs_with_metrics
                        WHERE account_id = %s
                        ORDER BY latest_likes DESC
                        LIMIT 10
                    """
                    cursor.execute(query, (account_id,))
                    print(f"   SQL: SELECT * FROM jobs_with_metrics WHERE account_id = '{account_id}' LIMIT 10")
                
                view_results = cursor.fetchall()
                
                if view_results:
                    print(f"   ✅ Found {len(view_results)} record(s) in view:\n")
                    for idx, row in enumerate(view_results, 1):
                        print(f"   {idx}. Thread ID: {row['thread_id']}")
                        print(f"      Account ID: {row['account_id']}")
                        print(f"      Latest Likes: {row.get('latest_likes', 'N/A')}")
                        print(f"      Latest Views: {row.get('latest_views', 'N/A')}")
                        print()
                else:
                    print(f"   ❌ No records found in view!")
                    if thread_id:
                        print(f"      Thread ID '{thread_id}' NOT in jobs_with_metrics view for account '{account_id}'")
                    else:
                        print(f"      No records in jobs_with_metrics view for account '{account_id}'")
                
                # Summary
                print("=" * 80)
                print("📊 SUMMARY")
                print("=" * 80)
                print(f"Account ID: {account_id}")
                if thread_id:
                    print(f"Thread ID: {thread_id}")
                    print(f"In jobs table: {'✅ YES' if jobs else '❌ NO'}")
                    print(f"In jobs_with_metrics view: {'✅ YES' if view_results else '❌ NO'}")
                    
                    if not jobs and not view_results:
                        print(f"\n❌ Thread ID '{thread_id}' NOT FOUND in database!")
                        print(f"   This thread_id does NOT exist in database.")
                        print(f"   Script should NOT say it's from database!")
                else:
                    print(f"Jobs in table: {len(jobs)}")
                    print(f"Records in view: {len(view_results)}")
                    
                    if not jobs:
                        print(f"\n⚠️  No completed jobs with thread_id in database for account '{account_id}'")
                        print(f"   Script should NOT return any thread_id!")
                
        finally:
            conn.close()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# VERIFY BROWSER PROFILE ACCOUNT
# ============================================================================

async def verify_browser_profile_account(account_id: str):
    """Verify browser profile đang login đúng account."""
    print_header("🔍 VERIFY BROWSER PROFILE ACCOUNT")
    print(f"Account ID: {account_id}")
    
    try:
        # 1. Check profile path
        profile_path = Path(f"./profiles/{account_id}")
        print(f"\n📋 Step 1: Check profile path")
        print(f"   Profile path: {profile_path}")
        if profile_path.exists():
            print(f"   ✅ Profile path exists")
        else:
            print(f"   ⚠️  Profile path does not exist")
            print(f"   💡 Solution: Login first using this profile")
            return
        
        # 2. Get username từ metadata
        print(f"\n📋 Step 2: Get username from account metadata")
        from config.storage_config_loader import get_storage_config_from_env
        from services.storage.accounts_storage import AccountStorage
        
        storage_config = get_storage_config_from_env()
        mysql_config = storage_config.mysql
        
        account_storage = AccountStorage(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            database=mysql_config.database
        )
        
        account = account_storage.get_account(account_id)
        if not account:
            print(f"   ❌ Account '{account_id}' not found in database!")
            return
        
        import json
        metadata = account.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        expected_username = metadata.get('username') or metadata.get('threads_username')
        
        if expected_username:
            print(f"   ✅ Expected username from metadata: {expected_username}")
        else:
            print(f"   ⚠️  No username in metadata")
            print(f"   💡 Will extract from browser profile")
        
        # 3. Open browser và check username
        print(f"\n📋 Step 3: Open browser and check logged-in account")
        print(f"   Opening browser with profile: {profile_path}")
        
        from browser.manager import BrowserManager
        browser_manager = BrowserManager(account_id=account_id)
        await browser_manager.start()
        
        try:
            page = browser_manager.page
            
            # Navigate to Threads home
            print(f"   Navigating to Threads...")
            await page.goto("https://www.threads.com/", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            # Check URL - nếu redirect về profile, extract username
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            # Try to find username in URL
            import re
            url_match = re.search(r'@([^/]+)', current_url)
            if url_match:
                actual_username = url_match.group(1)
                print(f"   ✅ Found username in URL: {actual_username}")
                
                if expected_username:
                    if actual_username == expected_username:
                        print(f"\n   ✅ VERIFICATION PASSED!")
                        print(f"      Expected: {expected_username}")
                        print(f"      Actual: {actual_username}")
                        print(f"      Browser profile is logged into correct account!")
                    else:
                        print(f"\n   ❌ VERIFICATION FAILED!")
                        print(f"      Expected: {expected_username} (from metadata)")
                        print(f"      Actual: {actual_username} (from browser profile)")
                        print(f"      Browser profile is logged into WRONG account!")
                        print(f"   💡 Solutions:")
                        print(f"      1. Logout from current account in browser")
                        print(f"      2. Login into correct account: {expected_username}")
                        print(f"      3. Or update account metadata with correct username: {actual_username}")
                else:
                    print(f"\n   ⚠️  No expected username in metadata")
                    print(f"      Found username in browser: {actual_username}")
                    print(f"   💡 Consider saving this username to account metadata")
            else:
                print(f"   ⚠️  Could not extract username from URL")
                print(f"      URL: {current_url}")
                
                # Try to navigate to profile page
                print(f"   Attempting to navigate to profile page...")
                try:
                    # Look for profile link
                    profile_links = await page.query_selector_all("a[href*='/@']")
                    if profile_links:
                        first_link = profile_links[0]
                        href = await first_link.get_attribute("href")
                        if href:
                            print(f"   Found profile link: {href}")
                            username_match = re.search(r'@([^/]+)', href)
                            if username_match:
                                actual_username = username_match.group(1)
                                print(f"   ✅ Extracted username: {actual_username}")
                                
                                if expected_username:
                                    if actual_username == expected_username:
                                        print(f"\n   ✅ VERIFICATION PASSED!")
                                    else:
                                        print(f"\n   ❌ VERIFICATION FAILED!")
                                        print(f"      Expected: {expected_username}")
                                        print(f"      Actual: {actual_username}")
                except Exception as e:
                    print(f"   ⚠️  Error checking profile: {e}")
            
        finally:
            await browser_manager.close()
            print(f"\n   ✅ Browser closed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified Check Script")
    parser.add_argument('--job-status', action='store_true', help='Check job status')
    parser.add_argument('--scheduler-status', action='store_true', help='Check scheduler status')
    parser.add_argument('--scheduler-live', action='store_true', help='Check scheduler live')
    parser.add_argument('--scheduler-workflow', action='store_true', help='Check scheduler workflow')
    parser.add_argument('--jobs-simple', action='store_true', help='Check jobs simple')
    parser.add_argument('--thread-id', type=str, help='Check thread ID in DB')
    parser.add_argument('--thread-id-direct', type=str, nargs='+', help='Check thread ID direct (account_id [thread_id])')
    parser.add_argument('--verify-profile', type=str, help='Verify browser profile account (account_id)')
    parser.add_argument('--fix', action='store_true', help='Auto fix issues (for --job-status)')
    
    args = parser.parse_args()
    
    # If command provided, run directly
    if args.job_status:
        check_job_status(fix=args.fix)
        return
    
    if args.scheduler_status:
        check_scheduler_status()
        return
    
    if args.scheduler_live:
        check_scheduler_live()
        return
    
    if args.scheduler_workflow:
        check_scheduler_workflow()
        return
    
    if args.jobs_simple:
        check_jobs_simple()
        return
    
    if args.thread_id:
        account_id = sys.argv[sys.argv.index('--thread-id') + 1] if '--thread-id' in sys.argv and len(sys.argv) > sys.argv.index('--thread-id') + 2 else None
        check_thread_id_in_db(args.thread_id, account_id)
        return
    
    if args.thread_id_direct:
        account_id = args.thread_id_direct[0]
        thread_id = args.thread_id_direct[1] if len(args.thread_id_direct) > 1 else None
        check_thread_id_direct(account_id, thread_id)
        return
    
    if args.verify_profile:
        asyncio.run(verify_browser_profile_account(args.verify_profile))
        return
    
    # Otherwise show menu
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            check_job_status()
        elif choice == "2":
            check_scheduler_status()
        elif choice == "3":
            check_scheduler_live()
        elif choice == "4":
            check_scheduler_workflow()
        elif choice == "5":
            check_jobs_simple()
        elif choice == "6":
            thread_id = input("Enter thread ID: ").strip()
            account_id = input("Enter account ID (optional): ").strip() or None
            check_thread_id_in_db(thread_id, account_id)
        elif choice == "7":
            account_id = input("Enter account ID: ").strip()
            thread_id = input("Enter thread ID (optional): ").strip() or None
            check_thread_id_direct(account_id, thread_id)
        elif choice == "8":
            account_id = input("Enter account ID: ").strip()
            asyncio.run(verify_browser_profile_account(account_id))
        else:
            print("❌ Invalid option. Please choose 0-8.")
        
        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
