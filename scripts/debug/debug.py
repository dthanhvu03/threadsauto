#!/usr/bin/env python3
"""
Unified Debug Script for Threads Automation Tool
Combines all debug scripts into one with menu
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

# Setup path using common utility
from scripts.common import setup_path, get_logger, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()

# Mock streamlit để import được
sys.modules['streamlit'] = type(sys)('streamlit')


def show_menu():
    """Show debug menu."""
    print()
    print("=" * 60)
    print("DEBUG SCRIPTS MENU")
    print("=" * 60)
    print()
    print("1. Debug Scheduler Detailed")
    print("2. Debug Excel Upload Flow")
    print("3. Debug Save Flow")
    print()
    print("0. Exit")
    print()
    choice = input("Chọn option (0-3): ").strip()
    return choice


# ============================================================================
# DEBUG SCHEDULER DETAILED
# ============================================================================

def debug_scheduler_detailed():
    """Debug chi tiết scheduler."""
    print_header("🔍 DEBUG SCHEDULER CHI TIẾT")
    print()
    
    try:
        from services.scheduler import Scheduler, JobStatus
        from services.scheduler.models import ScheduledJob
        from services.scheduler.storage import JobStorage
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    now = datetime.now()
    print(f"⏰ Thời gian hiện tại: {now}")
    print()
    
    # === 1. Load jobs từ storage ===
    print_section("📋 1. LOAD JOBS TỪ STORAGE")
    try:
        logger = get_logger("debug")
        storage = JobStorage(Path("./jobs"), logger)
        all_jobs_dict = storage.load_jobs()
        print(f"✅ Loaded {len(all_jobs_dict)} jobs từ storage")
        
        # Phân loại
        scheduled = [j for j in all_jobs_dict.values() if j.status == JobStatus.SCHEDULED]
        running = [j for j in all_jobs_dict.values() if j.status == JobStatus.RUNNING]
        completed = [j for j in all_jobs_dict.values() if j.status == JobStatus.COMPLETED]
        failed = [j for j in all_jobs_dict.values() if j.status == JobStatus.FAILED]
        
        print(f"   - Scheduled: {len(scheduled)}")
        print(f"   - Running: {len(running)}")
        print(f"   - Completed: {len(completed)}")
        print(f"   - Failed: {len(failed)}")
        print()
    except Exception as e:
        print(f"❌ Lỗi load jobs: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # === 2. Tạo scheduler instance ===
    print_section("📋 2. TẠO SCHEDULER INSTANCE")
    try:
        logger = get_logger("debug")
        scheduler = Scheduler(storage_dir=Path("./jobs"), logger=logger)
        print(f"✅ Scheduler created")
        print(f"   - Running: {scheduler.running}")
        print(f"   - Jobs in memory: {len(scheduler.jobs)}")
        print()
    except Exception as e:
        print(f"❌ Lỗi tạo scheduler: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # === 3. Kiểm tra ready jobs ===
    print_section("📋 3. KIỂM TRA READY JOBS")
    try:
        ready_jobs = scheduler.get_ready_jobs()
        print(f"✅ get_ready_jobs() trả về: {len(ready_jobs)} jobs")
        
        if ready_jobs:
            print("   Jobs sẵn sàng:")
            for job in ready_jobs[:5]:
                scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"   - {job.job_id[:8]}... | {scheduled_str} | Priority: {job.priority.value}")
        else:
            print("   ⚠️  Không có jobs sẵn sàng")
            
            # Debug: Kiểm tra từng job
            print()
            print("   🔍 Debug từng scheduled job:")
            scheduled_jobs = [j for j in scheduler.jobs.values() if j.status == JobStatus.SCHEDULED]
            for job in scheduled_jobs[:10]:
                scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                time_until = (job.scheduled_time - now).total_seconds()
                is_ready = job.is_ready()
                is_expired = job.is_expired()
                
                print(f"   - {job.job_id[:8]}... | {scheduled_str}")
                print(f"     Time until: {int(time_until)}s | Ready: {is_ready} | Expired: {is_expired}")
                print(f"     Status: {job.status.value} | Status message: {job.status_message}")
        print()
    except Exception as e:
        print(f"❌ Lỗi get_ready_jobs: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # === 4. Kiểm tra running jobs ===
    print_section("📋 4. KIỂM TRA RUNNING JOBS")
    try:
        running_jobs = [j for j in scheduler.jobs.values() if j.status == JobStatus.RUNNING]
        print(f"Running jobs: {len(running_jobs)}")
        if running_jobs:
            print("   ⚠️  CÓ JOBS ĐANG CHẠY - Scheduler sẽ không chạy job mới!")
            for job in running_jobs:
                started_str = job.started_at.strftime('%Y-%m-%d %H:%M:%S') if job.started_at else "N/A"
                duration = (now - job.started_at).total_seconds() if job.started_at else 0
                is_stuck = job.is_stuck()
                print(f"   - {job.job_id[:8]}... | Started: {started_str} | Duration: {int(duration)}s | Stuck: {is_stuck}")
        else:
            print("   ✅ Không có jobs đang chạy")
        print()
    except Exception as e:
        print(f"❌ Lỗi check running jobs: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # === 5. Kiểm tra jobs đã quá giờ ===
    print_section("📋 5. KIỂM TRA JOBS ĐÃ QUÁ GIỜ")
    try:
        overdue_jobs = []
        for job in scheduler.jobs.values():
            if job.status in [JobStatus.SCHEDULED, JobStatus.PENDING]:
                if now >= job.scheduled_time:
                    is_expired = job.is_expired()
                    is_ready = job.is_ready()
                    if not is_expired:
                        overdue_jobs.append((job, is_ready))
        
        if overdue_jobs:
            print(f"⚠️  CÓ {len(overdue_jobs)} JOBS ĐÃ QUÁ GIỜ:")
            for job, is_ready in overdue_jobs[:10]:
                scheduled_str = job.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                overdue_seconds = (now - job.scheduled_time).total_seconds()
                print(f"   - {job.job_id[:8]}... | {scheduled_str} | Quá {int(overdue_seconds)}s")
                print(f"     Ready: {is_ready} | Expired: {job.is_expired()} | Status: {job.status.value}")
                print(f"     Status message: {job.status_message}")
        else:
            print("   ✅ Không có jobs đã quá giờ")
        print()
    except Exception as e:
        print(f"❌ Lỗi check overdue jobs: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # === 6. Kiểm tra scheduler running flag ===
    print_section("📋 6. KIỂM TRA SCHEDULER RUNNING FLAG")
    print(f"Scheduler running: {scheduler.running}")
    if not scheduler.running:
        print("   ❌ SCHEDULER KHÔNG ĐANG CHẠY!")
        print("   → Cần start scheduler từ UI")
    else:
        print("   ✅ Scheduler đang chạy")
    print()
    
    # === 7. Kiểm tra callback factory ===
    print_section("📋 7. KIỂM TRA CALLBACK FACTORY")
    try:
        from ui.utils import get_platform_callback
        from services.scheduler.models import Platform
        
        threads_callback = get_platform_callback(Platform.THREADS)
        print(f"✅ Threads callback: {threads_callback}")
        print(f"   Function: {threads_callback.__name__}")
        
        # Check signature
        import inspect
        sig = inspect.signature(threads_callback)
        print(f"   Signature: {sig}")
        params = list(sig.parameters.keys())
        print(f"   Parameters: {params}")
        
        if len(params) < 3:
            print("   ⚠️  Callback chỉ có 2 parameters, cần 3 (account_id, content, status_updater)")
        else:
            print("   ✅ Callback có đủ 3 parameters")
    except Exception as e:
        print(f"❌ Lỗi check callback: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # === 8. Tóm tắt và khuyến nghị ===
    print_header("💡 TÓM TẮT VÀ KHUYẾN NGHỊ")
    
    issues = []
    
    if not scheduler.running:
        issues.append("❌ Scheduler không đang chạy - cần start từ UI")
    
    if running_jobs:
        issues.append(f"⚠️  Có {len(running_jobs)} jobs đang RUNNING - blocking jobs mới")
    
    if overdue_jobs and not ready_jobs:
        issues.append(f"⚠️  Có {len(overdue_jobs)} jobs đã quá giờ nhưng không ready - kiểm tra is_ready()")
    
    if not ready_jobs and scheduled:
        issues.append("⚠️  Có scheduled jobs nhưng không có ready jobs - kiểm tra scheduled_time")
    
    if issues:
        print("VẤN ĐỀ PHÁT HIỆN:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ Không phát hiện vấn đề rõ ràng")
        print("   → Kiểm tra logs để xem scheduler loop có đang chạy không")
    
    print()


# ============================================================================
# DEBUG EXCEL UPLOAD FLOW
# ============================================================================

def debug_excel_upload_flow():
    """Debug flow từ Excel upload đến save jobs."""
    
    print_header("Excel Upload → Save Jobs Flow")
    print()
    
    try:
        from services.scheduler.storage import JobStorage
        from services.scheduler.models import ScheduledJob, JobStatus
        from ui.api.jobs_api import JobsAPI
        from ui.api.accounts_api import AccountsAPI
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # === STEP 1: Check JobsAPI initialization ===
    print_section("📋 STEP 1: JobsAPI Initialization")
    try:
        jobs_api = JobsAPI()
        print(f"✅ JobsAPI created")
        print(f"   - Scheduler instance: {id(jobs_api.scheduler)}")
        
        # Check active scheduler
        try:
            from ui.utils import get_active_scheduler
            active_scheduler = get_active_scheduler()
            if active_scheduler:
                print(f"   - Active scheduler: {id(active_scheduler)}, running: {active_scheduler.running}")
            else:
                print(f"   - Active scheduler: None")
        except Exception as e:
            print(f"   ⚠️  Could not get active scheduler: {str(e)}")
        
        print()
    except Exception as e:
        print(f"❌ Error creating JobsAPI: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 2: Simulate add_job (như Excel upload) ===
    print_section("📋 STEP 2: Simulate add_job (Excel upload)")
    
    test_job = {
        "account_id": "account_01",
        "content": "Test job từ Excel upload - Debug flow",
        "scheduled_time": datetime.now().isoformat(),
        "priority": "NORMAL",
        "platform": "THREADS"
    }
    
    print(f"Test job data:")
    print(f"   - account_id: {test_job['account_id']}")
    print(f"   - content: {test_job['content'][:50]}...")
    print(f"   - scheduled_time: {test_job['scheduled_time']}")
    print(f"   - priority: {test_job['priority']}")
    print(f"   - platform: {test_job['platform']}")
    print()
    
    try:
        # Check target scheduler trước khi add
        from ui.utils import get_active_scheduler
        active_scheduler = get_active_scheduler()
        target_scheduler = active_scheduler if active_scheduler else jobs_api.scheduler
        print(f"Target scheduler:")
        print(f"   - Instance: {id(target_scheduler)}")
        print(f"   - Is active: {target_scheduler == active_scheduler if active_scheduler else False}")
        print(f"   - Jobs in memory: {len(target_scheduler.jobs)}")
        print()
        
        # Add job
        print("Adding job...")
        job_id = jobs_api.add_job(
            account_id=test_job["account_id"],
            content=test_job["content"],
            scheduled_time=test_job["scheduled_time"],
            priority=test_job["priority"],
            platform=test_job["platform"]
        )
        print(f"✅ Job added successfully")
        print(f"   - Job ID: {job_id}")
        print()
        
        # Check job trong memory
        if job_id in target_scheduler.jobs:
            job = target_scheduler.jobs[job_id]
            print(f"Job in memory:")
            print(f"   - job_id: {job.job_id}")
            print(f"   - status: {job.status.value}")
            print(f"   - scheduled_time: {job.scheduled_time}")
            print(f"   - account_id: {job.account_id}")
            print()
        else:
            print(f"⚠️  Job {job_id} not found in memory!")
            print()
        
    except Exception as e:
        print(f"❌ Error adding job: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 3: Check storage files ===
    print_section("📋 STEP 3: Check Storage Files")
    
    logger = get_logger("debug")
    storage = JobStorage(
        storage_dir=Path("./jobs"),
        logger=logger
    )
    
    # List all job files
    job_files = storage._get_all_job_files()
    print(f"Job files found: {len(job_files)}")
    for f in sorted(job_files, reverse=True)[:5]:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"   - {f.name} (modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    print()
    
    # Check if job is in storage
    print("Loading jobs from storage...")
    try:
        stored_jobs = storage.load_jobs()
        print(f"✅ Loaded {len(stored_jobs)} jobs from storage")
        
        if job_id in stored_jobs:
            stored_job = stored_jobs[job_id]
            print(f"✅ Job found in storage:")
            print(f"   - job_id: {stored_job.job_id}")
            print(f"   - status: {stored_job.status.value}")
            print(f"   - scheduled_time: {stored_job.scheduled_time}")
            print(f"   - account_id: {stored_job.account_id}")
            
            # Check which file it should be in
            if stored_job.completed_at:
                date_key = stored_job.completed_at.strftime("%Y-%m-%d")
                status_key = "completed"
            elif stored_job.status == JobStatus.RUNNING:
                date_key = stored_job.scheduled_time.strftime("%Y-%m-%d")
                status_key = "running"
            else:
                date_key = stored_job.scheduled_time.strftime("%Y-%m-%d")
                status_key = stored_job.status.value
            
            expected_file = f"jobs_{date_key}_{status_key}.json"
            print(f"   - Expected file: {expected_file}")
            
            # Check if file exists
            expected_path = Path("./jobs") / expected_file
            if expected_path.exists():
                print(f"   ✅ File exists: {expected_file}")
                # Check if job is in file
                with open(expected_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    job_ids_in_file = [j.get('job_id') for j in file_data.get('jobs', [])]
                    if job_id in job_ids_in_file:
                        print(f"   ✅ Job found in file")
                    else:
                        print(f"   ⚠️  Job NOT found in file (but file exists)")
                        print(f"   - Jobs in file: {len(file_data.get('jobs', []))}")
            else:
                print(f"   ⚠️  File does NOT exist: {expected_file}")
        else:
            print(f"⚠️  Job {job_id} NOT found in storage!")
            print(f"   - This means job was not saved to file")
            print()
            print("Checking all jobs in storage:")
            for sid, sjob in list(stored_jobs.items())[:5]:
                print(f"   - {sid[:8]}... | {sjob.status.value} | {sjob.account_id}")
        
        print()
    except Exception as e:
        print(f"❌ Error loading jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 4: Check recent files ===
    print_section("📋 STEP 4: Check Recent Files")
    
    # Find most recently modified file
    if job_files:
        latest_file = max(job_files, key=lambda f: f.stat().st_mtime)
        mtime = datetime.fromtimestamp(latest_file.stat().st_mtime)
        print(f"Most recent file: {latest_file.name}")
        print(f"   - Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   - Age: {(datetime.now() - mtime).total_seconds():.2f} seconds ago")
        
        # Check if job is in latest file
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                job_ids_in_file = [j.get('job_id') for j in file_data.get('jobs', [])]
                if job_id in job_ids_in_file:
                    print(f"   ✅ Job found in latest file")
                else:
                    print(f"   ⚠️  Job NOT in latest file")
                    print(f"   - Jobs in file: {len(file_data.get('jobs', []))}")
        except Exception as e:
            print(f"   ❌ Error reading file: {str(e)}")
    
    print()
    
    # === STEP 5: Summary ===
    print_header("📊 SUMMARY")
    print()
    print(f"Job ID: {job_id}")
    print(f"Status: {'✅ SAVED' if job_id in stored_jobs else '❌ NOT SAVED'}")
    print()


# ============================================================================
# DEBUG SAVE FLOW
# ============================================================================

def debug_save_flow():
    """Debug flow từ add_job đến save jobs (không cần streamlit)."""
    
    print_header("Add Job → Save Jobs Flow")
    print()
    
    try:
        from services.scheduler import Scheduler
        from services.scheduler.storage import JobStorage
        from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # === STEP 1: Create scheduler ===
    print_section("📋 STEP 1: Create Scheduler")
    try:
        scheduler = Scheduler()
        print(f"✅ Scheduler created")
        print(f"   - Instance: {id(scheduler)}")
        print(f"   - Jobs in memory: {len(scheduler.jobs)}")
        print()
    except Exception as e:
        print(f"❌ Error creating scheduler: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 2: Add job (simulate Excel upload) ===
    print_section("📋 STEP 2: Add Job (Simulate Excel Upload)")
    
    test_content = "Test job từ Excel upload - Debug flow " + datetime.now().strftime("%H:%M:%S")
    scheduled_time = datetime.now()
    
    print(f"Test job:")
    print(f"   - account_id: account_01")
    print(f"   - content: {test_content[:50]}...")
    print(f"   - scheduled_time: {scheduled_time.isoformat()}")
    print(f"   - priority: NORMAL")
    print(f"   - platform: THREADS")
    print()
    
    try:
        print("Calling scheduler.add_job()...")
        job_id = scheduler.add_job(
            account_id="account_01",
            content=test_content,
            scheduled_time=scheduled_time,
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        print(f"✅ Job added successfully")
        print(f"   - Job ID: {job_id}")
        print()
        
        # Check job trong memory
        if job_id in scheduler.jobs:
            job = scheduler.jobs[job_id]
            print(f"Job in memory:")
            print(f"   - job_id: {job.job_id}")
            print(f"   - status: {job.status.value}")
            print(f"   - scheduled_time: {job.scheduled_time}")
            print(f"   - account_id: {job.account_id}")
            print(f"   - content: {job.content[:50]}...")
            print()
        else:
            print(f"❌ Job {job_id} NOT found in memory!")
            return
        
    except Exception as e:
        print(f"❌ Error adding job: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 3: Check storage (before save) ===
    print_section("📋 STEP 3: Check Storage (Before Manual Save)")
    
    storage = scheduler.storage
    
    # List all job files
    job_files = storage._get_all_job_files()
    print(f"Job files found: {len(job_files)}")
    for f in sorted(job_files, reverse=True)[:5]:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"   - {f.name} (modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    print()
    
    # Load jobs from storage
    print("Loading jobs from storage...")
    try:
        stored_jobs_before = storage.load_jobs()
        print(f"✅ Loaded {len(stored_jobs_before)} jobs from storage")
        
        if job_id in stored_jobs_before:
            print(f"✅ Job already in storage (saved by add_job callback)")
        else:
            print(f"⚠️  Job NOT in storage yet (save_callback may not have been called)")
        
        print()
    except Exception as e:
        print(f"❌ Error loading jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 4: Manual save (to verify) ===
    print_section("📋 STEP 4: Manual Save (Verify)")
    
    try:
        print("Calling scheduler._save_jobs()...")
        scheduler._save_jobs()
        print(f"✅ Save completed")
        print()
    except Exception as e:
        print(f"❌ Error saving jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 5: Check storage (after save) ===
    print_section("📋 STEP 5: Check Storage (After Save)")
    
    # Reload jobs from storage
    print("Reloading jobs from storage...")
    try:
        stored_jobs_after = storage.load_jobs()
        print(f"✅ Loaded {len(stored_jobs_after)} jobs from storage")
        
        if job_id in stored_jobs_after:
            stored_job = stored_jobs_after[job_id]
            print(f"✅ Job found in storage:")
            print(f"   - job_id: {stored_job.job_id}")
            print(f"   - status: {stored_job.status.value}")
            print(f"   - scheduled_time: {stored_job.scheduled_time}")
            print(f"   - account_id: {stored_job.account_id}")
            
            # Determine expected file
            if stored_job.completed_at:
                date_key = stored_job.completed_at.strftime("%Y-%m-%d")
                status_key = "completed"
            elif stored_job.status == JobStatus.RUNNING:
                date_key = stored_job.scheduled_time.strftime("%Y-%m-%d")
                status_key = "running"
            else:
                date_key = stored_job.scheduled_time.strftime("%Y-%m-%d")
                status_key = stored_job.status.value
            
            expected_file = f"jobs_{date_key}_{status_key}.json"
            print(f"   - Expected file: {expected_file}")
            
            # Check if file exists
            expected_path = Path("./jobs") / expected_file
            if expected_path.exists():
                print(f"   ✅ File exists: {expected_file}")
                
                # Check file modification time
                mtime = datetime.fromtimestamp(expected_path.stat().st_mtime)
                print(f"   - File modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                age_seconds = (datetime.now() - mtime).total_seconds()
                print(f"   - Age: {age_seconds:.2f} seconds ago")
                
                # Check if job is in file
                with open(expected_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    job_ids_in_file = [j.get('job_id') for j in file_data.get('jobs', [])]
                    if job_id in job_ids_in_file:
                        print(f"   ✅ Job found in file")
                        print(f"   - Total jobs in file: {len(file_data.get('jobs', []))}")
                    else:
                        print(f"   ⚠️  Job NOT found in file (but file exists)")
                        print(f"   - Jobs in file: {len(file_data.get('jobs', []))}")
                        print(f"   - Job IDs in file: {[j[:8] + '...' for j in job_ids_in_file[:5]]}")
            else:
                print(f"   ⚠️  File does NOT exist: {expected_file}")
                print(f"   - This means job was not saved correctly")
        else:
            print(f"❌ Job {job_id} NOT found in storage!")
            print(f"   - This means save failed")
        
        print()
    except Exception as e:
        print(f"❌ Error loading jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # === STEP 6: Check all recent files ===
    print_section("📋 STEP 6: Check All Recent Files")
    
    # Find most recently modified files
    if job_files:
        recent_files = sorted(job_files, key=lambda f: f.stat().st_mtime, reverse=True)[:3]
        print(f"Most recent files:")
        for f in recent_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            age_seconds = (datetime.now() - mtime).total_seconds()
            print(f"   - {f.name}")
            print(f"     Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')} ({age_seconds:.2f}s ago)")
            
            # Check if job is in this file
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    file_data = json.load(file)
                    job_ids_in_file = [j.get('job_id') for j in file_data.get('jobs', [])]
                    if job_id in job_ids_in_file:
                        print(f"     ✅ Job found in this file")
                    else:
                        print(f"     - Jobs in file: {len(file_data.get('jobs', []))}")
            except Exception as e:
                print(f"     ⚠️  Error reading file: {str(e)}")
    
    print()
    
    # === STEP 7: Summary ===
    print_header("📊 SUMMARY")
    print()
    print(f"Job ID: {job_id}")
    print(f"Job in memory: {'✅ YES' if job_id in scheduler.jobs else '❌ NO'}")
    print(f"Job in storage: {'✅ YES' if job_id in stored_jobs_after else '❌ NO'}")
    print()
    
    if job_id in stored_jobs_after:
        stored_job = stored_jobs_after[job_id]
        if stored_job.completed_at:
            date_key = stored_job.completed_at.strftime("%Y-%m-%d")
            status_key = "completed"
        elif stored_job.status == JobStatus.RUNNING:
            date_key = stored_job.scheduled_time.strftime("%Y-%m-%d")
            status_key = "running"
        else:
            date_key = stored_job.scheduled_time.strftime("%Y-%m-%d")
            status_key = stored_job.status.value
        
        expected_file = f"jobs_{date_key}_{status_key}.json"
        expected_path = Path("./jobs") / expected_file
        
        if expected_path.exists():
            print(f"✅ Job is in correct file: {expected_file}")
            print(f"✅ Flow completed successfully!")
        else:
            print(f"⚠️  Expected file does not exist: {expected_file}")
            print(f"⚠️  Job may be in wrong file or not saved")
    else:
        print("❌ Job was NOT saved to storage")
        print("   - Check if save_callback was called in add_job")
        print("   - Check if storage.save_jobs() was called")
        print("   - Check logs for errors")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified Debug Script")
    parser.add_argument('--scheduler', action='store_true', help='Debug scheduler detailed')
    parser.add_argument('--excel-upload', action='store_true', help='Debug Excel upload flow')
    parser.add_argument('--save-flow', action='store_true', help='Debug save flow')
    
    args = parser.parse_args()
    
    # If command provided, run directly
    if args.scheduler:
        debug_scheduler_detailed()
        return
    
    if args.excel_upload:
        debug_excel_upload_flow()
        return
    
    if args.save_flow:
        debug_save_flow()
        return
    
    # Otherwise show menu
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            debug_scheduler_detailed()
        elif choice == "2":
            debug_excel_upload_flow()
        elif choice == "3":
            debug_save_flow()
        else:
            print("❌ Invalid option. Please choose 0-3.")
        
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
