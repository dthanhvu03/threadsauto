#!/usr/bin/env python3
"""
Test migration với sample data để verify trước khi migrate full.

Usage:
    python scripts/test_migration_sample.py
"""

import sys
from pathlib import Path
from datetime import datetime
import random

# Setup path using common utility
from scripts.common import setup_path, get_logger, print_header, print_section

# Add parent to path (must be after importing common)
setup_path()

from services.scheduler.storage.json_storage import JobStorage
from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.scheduler.models import ScheduledJob, JobStatus


def test_migration_sample():
    """Test migration với sample data."""
    print_header("🧪 Testing Migration với Sample Data", width=60)
    
    logger = get_logger("test_migration_sample")
    
    # Initialize storages
    print("\n📁 Initializing storages...")
    json_storage = JobStorage(Path("./jobs"), logger)
    mysql_storage = MySQLJobStorage(
        host="localhost",
        port=3306,
        user="threads_user",
        password="threads_password",
        database="threads_analytics",
        logger=logger
    )
    print("✅ Storages initialized")
    
    # Load all jobs from JSON
    print("\n📊 Loading jobs from JSON...")
    all_json_jobs = json_storage.load_jobs()
    total_jobs = len(all_json_jobs)
    print(f"✅ Loaded {total_jobs} jobs from JSON")
    
    if total_jobs == 0:
        print("⚠️  No jobs found in JSON files")
        return False
    
    # Select sample (first 10 jobs)
    sample_size = min(10, total_jobs)
    sample_jobs = dict(list(all_json_jobs.items())[:sample_size])
    print(f"\n📦 Selected {sample_size} sample jobs for testing")
    
    # Show sample job IDs
    print("\n📋 Sample Job IDs:")
    for i, job_id in enumerate(sample_jobs.keys(), 1):
        job = sample_jobs[job_id]
        print(f"   {i}. {job_id[:8]}... - {job.status.value} - Account: {job.account_id}")
    
    # Get current MySQL count
    print("\n🗄️  Checking MySQL database...")
    mysql_jobs_before = mysql_storage.load_jobs()
    mysql_count_before = len(mysql_jobs_before)
    print(f"   MySQL jobs before: {mysql_count_before}")
    
    # Save sample to MySQL
    print(f"\n💾 Saving {sample_size} sample jobs to MySQL...")
    try:
        mysql_storage.save_jobs(sample_jobs)
        print("✅ Sample jobs saved successfully")
    except Exception as e:
        print(f"❌ Failed to save sample jobs: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify migration
    print("\n🔍 Verifying migration...")
    mysql_jobs_after = mysql_storage.load_jobs()
    mysql_count_after = len(mysql_jobs_after)
    
    print(f"   JSON sample jobs: {sample_size}")
    print(f"   MySQL jobs before: {mysql_count_before}")
    print(f"   MySQL jobs after: {mysql_count_after}")
    print(f"   Expected MySQL count: {mysql_count_before + sample_size}")
    
    # Verify each sample job
    print("\n✅ Verifying sample jobs...")
    verified = 0
    failed = 0
    
    for job_id, original_job in sample_jobs.items():
        try:
            mysql_job = mysql_storage.get_job_by_id(job_id)
            
            if mysql_job is None:
                print(f"   ❌ Job {job_id[:8]}... not found in MySQL")
                failed += 1
                continue
            
            # Verify key fields
            # For datetime comparison, normalize to ignore microseconds if difference < 1 second
            scheduled_time_match = original_job.scheduled_time == mysql_job.scheduled_time
            if not scheduled_time_match:
                # Check if difference is just microseconds (acceptable)
                diff_seconds = abs((original_job.scheduled_time - mysql_job.scheduled_time).total_seconds())
                if diff_seconds < 1.0:
                    # Microsecond precision difference (acceptable)
                    scheduled_time_match = True
            
            checks = [
                ("job_id", original_job.job_id == mysql_job.job_id),
                ("account_id", original_job.account_id == mysql_job.account_id),
                ("content", original_job.content == mysql_job.content),
                ("status", original_job.status == mysql_job.status),
                ("scheduled_time", scheduled_time_match),
            ]
            
            all_match = all(check[1] for check in checks)
            
            if all_match:
                verified += 1
            else:
                print(f"   ⚠️  Job {job_id[:8]}... has mismatches:")
                for field, match in checks:
                    if not match:
                        print(f"      - {field}: mismatch")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Error verifying job {job_id[:8]}...: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print_header("", width=60)
    print(f"Sample jobs tested: {sample_size}")
    print(f"✅ Verified: {verified}")
    print(f"❌ Failed: {failed}")
    print(f"MySQL count before: {mysql_count_before}")
    print(f"MySQL count after: {mysql_count_after}")
    
    if verified == sample_size:
        print("\n✅ All sample jobs migrated correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} jobs had issues")
        return False


if __name__ == "__main__":
    success = test_migration_sample()
    sys.exit(0 if success else 1)
