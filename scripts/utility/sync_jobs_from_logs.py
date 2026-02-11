#!/usr/bin/env python3
"""
Script sync jobs status từ logs vào jobs file.

Tìm jobs đã chạy thành công trong logs nhưng chưa được update trong jobs file,
và update status thành COMPLETED với completed_at và thread_id.

Usage:
    python scripts/sync_jobs_from_logs.py [--dry-run] [--log-file logs/scheduler_20251225.log]
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

# Setup path using common utility
from scripts.common import setup_path, get_logger, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()

from services.scheduler import Scheduler, JobStatus


def parse_logs_for_completed_jobs(log_file: Path) -> Dict[str, Dict]:
    """
    Parse logs để tìm jobs đã completed.
    
    Returns:
        Dict mapping job_id -> {thread_id, completed_time, ...}
    """
    completed_jobs = {}
    
    if not log_file.exists():
        print(f"⚠️  Log file không tồn tại: {log_file}")
        return completed_jobs
    
    print(f"📖 Đang đọc logs từ: {log_file}")
    
    # Patterns để tìm completed jobs từ log format thực tế
    # Format: STEP=RUN_JOB RESULT=SUCCESS JOB_ID=xxx THREAD_ID=xxx
    # Hoặc: STEP=POST_THREAD RESULT=SUCCESS THREAD_ID=xxx
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"   Đọc {len(lines)} dòng logs...")
        
        for i, line in enumerate(lines):
            # Pattern 1: RUN_JOB SUCCESS với JOB_ID và THREAD_ID
            # Format: STEP=RUN_JOB RESULT=SUCCESS JOB_ID=xxx THREAD_ID=xxx
            if 'STEP=RUN_JOB' in line and 'RESULT=SUCCESS' in line:
                job_id_match = re.search(r'JOB_ID=([a-f0-9-]+)', line, re.IGNORECASE)
                thread_id_match = re.search(r'THREAD_ID=([A-Za-z0-9_-]+)', line, re.IGNORECASE)
                
                if job_id_match:
                    job_id = job_id_match.group(1)
                    thread_id = thread_id_match.group(1) if thread_id_match else None
                    
                    # Extract timestamp từ đầu log line
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        try:
                            date_str, time_str = timestamp_match.groups()
                            completed_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError):
                            completed_time = datetime.now()
                    else:
                        completed_time = datetime.now()
                    
                    if job_id not in completed_jobs:
                        completed_jobs[job_id] = {
                            'thread_id': thread_id,
                            'completed_time': completed_time,
                            'log_line': i + 1
                        }
                    else:
                        # Update nếu có thêm thông tin
                        if thread_id and not completed_jobs[job_id].get('thread_id'):
                            completed_jobs[job_id]['thread_id'] = thread_id
                        if completed_time > completed_jobs[job_id]['completed_time']:
                            completed_jobs[job_id]['completed_time'] = completed_time
            
            # Pattern 2: POST_THREAD SUCCESS với THREAD_ID (tìm job_id từ context)
            elif 'STEP=POST_THREAD' in line and 'RESULT=SUCCESS' in line:
                thread_id_match = re.search(r'THREAD_ID=([A-Za-z0-9_-]+)', line, re.IGNORECASE)
                if thread_id_match:
                    thread_id = thread_id_match.group(1)
                    # Tìm job_id từ các dòng trước đó (trong vòng 10 dòng)
                    job_id = None
                    for j in range(max(0, i-10), i):
                        job_id_match = re.search(r'JOB_ID=([a-f0-9-]+)', lines[j], re.IGNORECASE)
                        if job_id_match:
                            job_id = job_id_match.group(1)
                            break
                    
                    if job_id:
                        # Extract timestamp
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', line)
                        if timestamp_match:
                            try:
                                date_str, time_str = timestamp_match.groups()
                                completed_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                            except (ValueError, TypeError):
                                completed_time = datetime.now()
                        else:
                            completed_time = datetime.now()
                        
                        if job_id not in completed_jobs:
                            completed_jobs[job_id] = {
                                'thread_id': thread_id,
                                'completed_time': completed_time,
                                'log_line': i + 1
                            }
                        else:
                            # Update nếu có thêm thông tin
                            if thread_id and not completed_jobs[job_id].get('thread_id'):
                                completed_jobs[job_id]['thread_id'] = thread_id
                            if completed_time > completed_jobs[job_id]['completed_time']:
                                completed_jobs[job_id]['completed_time'] = completed_time
        
        print(f"   ✅ Tìm thấy {len(completed_jobs)} jobs đã completed trong logs")
        
    except Exception as e:
        print(f"❌ Lỗi đọc log file: {e}")
        return completed_jobs
    
    return completed_jobs


def sync_jobs_from_logs(
    scheduler: Scheduler,
    completed_jobs_from_logs: Dict[str, Dict],
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Sync jobs status từ logs vào scheduler.
    
    Returns:
        Dict với stats: {updated, skipped, errors}
    """
    stats = {
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    print_section("🔄 Đang sync jobs...")
    
    for job_id, log_info in completed_jobs_from_logs.items():
        job = scheduler.jobs.get(job_id)
        
        if not job:
            print(f"⚠️  Job {job_id[:8]}... không tìm thấy trong scheduler (có thể đã bị xóa)")
            stats['skipped'] += 1
            continue
        
        # Check nếu job đã completed rồi
        if job.status == JobStatus.COMPLETED:
            print(f"✅ Job {job_id[:8]}... đã COMPLETED rồi, skip")
            stats['skipped'] += 1
            continue
        
        # Update job
        if dry_run:
            print(f"🔍 [DRY RUN] Sẽ update job {job_id[:8]}...")
            print(f"   - Status: {job.status.value} → COMPLETED")
            print(f"   - Thread ID: {log_info.get('thread_id', 'N/A')}")
            print(f"   - Completed at: {log_info.get('completed_time', 'N/A')}")
            stats['updated'] += 1
        else:
            try:
                # Update job status
                job.status = JobStatus.COMPLETED
                job.completed_at = log_info.get('completed_time', datetime.now())
                job.thread_id = log_info.get('thread_id')
                job.status_message = f"Hoàn thành thành công - Thread ID: {job.thread_id or 'N/A'}"
                
                print(f"✅ Đã update job {job_id[:8]}... → COMPLETED")
                print(f"   - Thread ID: {job.thread_id or 'N/A'}")
                print(f"   - Completed at: {job.completed_at}")
                
                stats['updated'] += 1
            except Exception as e:
                print(f"❌ Lỗi update job {job_id[:8]}...: {e}")
                stats['errors'] += 1
    
    if not dry_run and stats['updated'] > 0:
        print("\n💾 Đang save jobs...")
        try:
            scheduler._save_jobs()
            print(f"✅ Đã save {stats['updated']} jobs")
        except Exception as e:
            print(f"❌ Lỗi save jobs: {e}")
            stats['errors'] += 1
    
    return stats


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sync jobs status từ logs vào jobs file"
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        default=Path("./logs/scheduler_20251225.log"),
        help='Log file để parse (default: logs/scheduler_20251225.log)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (chỉ xem, không update)'
    )
    parser.add_argument(
        '--jobs-dir',
        type=Path,
        default=Path("./jobs"),
        help='Thư mục chứa jobs (default: ./jobs)'
    )
    
    args = parser.parse_args()
    
    print_header("🔄 SYNC JOBS TỪ LOGS")
    print()
    
    # Parse logs
    completed_jobs_from_logs = parse_logs_for_completed_jobs(args.log_file)
    
    if not completed_jobs_from_logs:
        print("\n⚠️  Không tìm thấy jobs completed trong logs")
        print("   Có thể:")
        print("   - Log file không đúng")
        print("   - Jobs chưa được chạy")
        print("   - Pattern matching không match")
        return
    
    print(f"\n📊 Tìm thấy {len(completed_jobs_from_logs)} jobs đã completed trong logs:")
    for job_id, info in list(completed_jobs_from_logs.items())[:5]:
        print(f"   - {job_id[:8]}... thread_id: {info.get('thread_id', 'N/A')}")
    if len(completed_jobs_from_logs) > 5:
        print(f"   ... và {len(completed_jobs_from_logs) - 5} jobs khác")
    
    # Load scheduler
    print(f"\n📂 Đang load jobs từ {args.jobs_dir}...")
        logger = get_logger("sync_jobs")
        scheduler = Scheduler(storage_dir=args.jobs_dir, logger=logger)
    
    all_jobs = scheduler.list_jobs()
    print(f"   ✅ Đã load {len(all_jobs)} jobs")
    
    # Sync
    stats = sync_jobs_from_logs(scheduler, completed_jobs_from_logs, dry_run=args.dry_run)
    
    # Summary
    print_header("📊 TỔNG KẾT")
    print(f"✅ Updated: {stats['updated']}")
    print(f"⏭️  Skipped: {stats['skipped']}")
    print(f"❌ Errors: {stats['errors']}")
    
    if args.dry_run:
        print("\n💡 Để thực sự update, chạy lại không có --dry-run:")
        print(f"   python3 scripts/sync_jobs_from_logs.py --log-file {args.log_file}")
    else:
        print("\n✅ Sync hoàn tất!")


if __name__ == "__main__":
    main()

