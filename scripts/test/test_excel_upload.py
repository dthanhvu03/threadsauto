#!/usr/bin/env python3
"""
Test script để test Excel upload flow.

Simulate Excel upload và verify jobs được save đúng.
"""

import sys
from pathlib import Path
from datetime import datetime
import time

# Setup path using common utility
from scripts.common import setup_path, get_logger, print_header, print_section

# Add project root to path (must be after importing common)
setup_path()

from services.scheduler import Scheduler, JobPriority
from services.scheduler.models import JobStatus, Platform
from services.scheduler.storage import JobStorage


def test_add_job_flow():
    """Test add_job flow và verify job được save."""
    print_header("TEST: Excel Upload → Add Job → Save Flow")
    
    # Create a test scheduler
    print("\n1. Creating test scheduler...")
    test_scheduler = Scheduler()
    print(f"   ✅ Created scheduler: {id(test_scheduler)}")
    print(f"   Jobs in scheduler memory: {len(test_scheduler.jobs)}")
    
    # Simulate adding a job (like Excel upload)
    print("\n2. Simulating Excel upload - adding job...")
    test_content = f"Test job from Excel upload - {datetime.now().strftime('%H:%M:%S')}"
    test_scheduled_time = datetime.now()
    
    try:
        job_id = test_scheduler.add_job(
            account_id="account_01",
            content=test_content,
            scheduled_time=test_scheduled_time,
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        print(f"   ✅ Job added: {job_id}")
    except Exception as e:
        print(f"   ❌ Failed to add job: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify job in memory
    print("\n3. Verifying job in memory...")
    if job_id in test_scheduler.jobs:
        print(f"   ✅ Job found in scheduler.jobs")
        job = test_scheduler.jobs[job_id]
        print(f"   Job status: {job.status}")
        print(f"   Job account_id: {job.account_id}")
    else:
        print(f"   ❌ Job NOT found in scheduler.jobs")
        print(f"   Available job IDs: {list(test_scheduler.jobs.keys())[:5]}")
        return False
    
    # Check jobs count
    print(f"\n4. Jobs count in scheduler: {len(test_scheduler.jobs)}")
    
    # Wait a bit for save to complete
    print("\n5. Waiting 1 second for save to complete...")
    time.sleep(1)
    
    # Verify job in storage
    print("\n6. Verifying job in storage...")
    logger = get_logger("test")
    storage = JobStorage(Path("./jobs"), logger)
    stored_jobs = storage.load_jobs()
    
    if job_id in stored_jobs:
        print(f"   ✅ Job found in storage")
        stored_job = stored_jobs[job_id]
        print(f"   Stored job status: {stored_job.status}")
        print(f"   Stored job account_id: {stored_job.account_id}")
    else:
        print(f"   ❌ Job NOT found in storage")
        print(f"   Available job IDs in storage: {list(stored_jobs.keys())[:5]}")
        print(f"   Total jobs in storage: {len(stored_jobs)}")
        return False
    
    # Check file
    print("\n7. Checking job files...")
    job_files = list(Path("./jobs").glob("jobs_*.json"))
    print(f"   Found {len(job_files)} job files")
    
    job_found_in_file = False
    for job_file in job_files:
        import json
        with open(job_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            jobs_in_file = data.get('jobs', [])
            for job_data in jobs_in_file:
                if job_data.get('job_id') == job_id:
                    print(f"   ✅ Job found in: {job_file.name}")
                    print(f"      Status: {job_data.get('status')}")
                    print(f"      Account: {job_data.get('account_id')}")
                    job_found_in_file = True
                    break
            if job_found_in_file:
                break
    
    if not job_found_in_file:
        print(f"   ❌ Job NOT found in any file")
        return False
    
    print_header("✅ TEST PASSED: Job successfully added and saved!")
    return True


if __name__ == "__main__":
    success = test_add_job_flow()
    sys.exit(0 if success else 1)

