#!/usr/bin/env python3
"""
Test script cho MySQLJobStorage.

Usage:
    python scripts/test_mysql_storage.py
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid

# Setup path using common utility
from scripts.common import setup_path, get_logger, print_header, print_section

# Add parent to path (must be after importing common)
setup_path()

from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.scheduler.models import (
    ScheduledJob,
    JobStatus,
    JobPriority,
    Platform
)


def test_mysql_storage():
    """Test MySQLJobStorage implementation."""
    print_header("🧪 Testing MySQLJobStorage...", width=60)
    
    # Initialize storage
    try:
        logger = get_logger("test_mysql_storage")
        storage = MySQLJobStorage(
            host='localhost',
            port=3306,
            user='threads_user',
            password='threads_password',
            database='threads_analytics',
            logger=logger
        )
        print("✅ MySQLJobStorage initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # Test 1: Load empty database
    print("\n📋 Test 1: Load jobs from empty database")
    try:
        jobs = storage.load_jobs()
        print(f"✅ Loaded {len(jobs)} jobs (expected: 0)")
    except Exception as e:
        print(f"❌ Failed to load jobs: {e}")
        return False
    
    # Test 2: Create and save job
    print("\n📋 Test 2: Create and save job")
    try:
        test_job = ScheduledJob(
            job_id=str(uuid.uuid4()),
            account_id="test_account",
            content="Test content for MySQL storage",
            scheduled_time=datetime.now(),
            priority=JobPriority.NORMAL,
            status=JobStatus.SCHEDULED,
            platform=Platform.THREADS,
            max_retries=3,
            retry_count=0
        )
        
        jobs_dict = {test_job.job_id: test_job}
        storage.save_jobs(jobs_dict)
        print(f"✅ Saved job: {test_job.job_id}")
    except Exception as e:
        print(f"❌ Failed to save job: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Load and verify
    print("\n📋 Test 3: Load and verify saved job")
    try:
        loaded_jobs = storage.load_jobs()
        if test_job.job_id in loaded_jobs:
            loaded_job = loaded_jobs[test_job.job_id]
            print(f"✅ Job loaded: {loaded_job.job_id}")
            print(f"   Content: {loaded_job.content}")
            print(f"   Status: {loaded_job.status.value}")
        else:
            print(f"❌ Job not found in loaded jobs")
            return False
    except Exception as e:
        print(f"❌ Failed to load job: {e}")
        return False
    
    # Test 4: Get by ID
    print("\n📋 Test 4: Get job by ID")
    try:
        job = storage.get_job_by_id(test_job.job_id)
        if job and job.job_id == test_job.job_id:
            print(f"✅ get_job_by_id works: {job.job_id}")
        else:
            print(f"❌ get_job_by_id failed")
            return False
    except Exception as e:
        print(f"❌ Failed to get job by ID: {e}")
        return False
    
    # Test 5: Get by status
    print("\n📋 Test 5: Get jobs by status")
    try:
        scheduled_jobs = storage.get_jobs_by_status(JobStatus.SCHEDULED)
        print(f"✅ get_jobs_by_status works: {len(scheduled_jobs)} scheduled jobs")
    except Exception as e:
        print(f"❌ Failed to get jobs by status: {e}")
        return False
    
    # Test 6: Get by account
    print("\n📋 Test 6: Get jobs by account")
    try:
        account_jobs = storage.get_jobs_by_account("test_account")
        print(f"✅ get_jobs_by_account works: {len(account_jobs)} jobs for test_account")
    except Exception as e:
        print(f"❌ Failed to get jobs by account: {e}")
        return False
    
    # Test 7: Update job status
    print("\n📋 Test 7: Update job status")
    try:
        test_job.status = JobStatus.COMPLETED
        test_job.completed_at = datetime.now()
        test_job.thread_id = "test_thread_123"
        
        storage.save_jobs({test_job.job_id: test_job})
        
        # Verify update
        updated_job = storage.get_job_by_id(test_job.job_id)
        if updated_job and updated_job.status == JobStatus.COMPLETED:
            print(f"✅ Job status updated: {updated_job.status.value}")
            print(f"   Thread ID: {updated_job.thread_id}")
        else:
            print(f"❌ Job status not updated correctly")
            return False
    except Exception as e:
        print(f"❌ Failed to update job: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup: Delete test job
    print("\n🧹 Cleanup: Removing test job")
    try:
        # Note: We'll need to add delete method or just leave it for now
        # For now, we'll just leave the test job in the database
        print("   (Test job left in database for manual inspection)")
    except Exception as e:
        print(f"   Warning: Cleanup failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    return True


if __name__ == "__main__":
    success = test_mysql_storage()
    sys.exit(0 if success else 1)
