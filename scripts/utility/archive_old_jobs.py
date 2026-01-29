#!/usr/bin/env python3
"""
Script archive jobs cũ (completed > X ngày) vào thư mục archive.

Usage:
    python scripts/archive_old_jobs.py [--jobs-dir jobs/] [--archive-dir archive/] [--days 30] [--dry-run]
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Setup path using common utility
from scripts.common import setup_path, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()


def archive_old_jobs(
    jobs_dir: Path,
    archive_dir: Path,
    days: int = 30,
    dry_run: bool = False
) -> int:
    """
    Archive jobs completed cũ hơn X ngày.
    
    Returns:
        Số lượng jobs đã archive
    """
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    cutoff_date = datetime.now() - timedelta(days=days)
    print(f"📅 Archive jobs completed trước: {cutoff_date.strftime('%Y-%m-%d')}")
    print()
    
    job_files = sorted(jobs_dir.glob("jobs_*.json"))
    archived_count = 0
    files_updated = 0
    
    for job_file in job_files:
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            jobs = data.get('jobs', [])
            jobs_to_archive = []
            jobs_to_keep = []
            
            for job in jobs:
                status = job.get('status', '')
                completed_at = job.get('completed_at')
                
                # Chỉ archive completed jobs cũ
                if status == 'completed' and completed_at:
                    try:
                        completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        if completed_dt < cutoff_date:
                            jobs_to_archive.append(job)
                            archived_count += 1
                        else:
                            jobs_to_keep.append(job)
                    except:
                        # Nếu không parse được date, giữ lại
                        jobs_to_keep.append(job)
                else:
                    # Giữ lại jobs chưa completed
                    jobs_to_keep.append(job)
            
            if jobs_to_archive:
                # Lưu vào archive file
                archive_file = archive_dir / job_file.name
                
                if archive_file.exists():
                    # Merge với archive file hiện có
                    with open(archive_file, 'r', encoding='utf-8') as f:
                        archive_data = json.load(f)
                    archive_data['jobs'].extend(jobs_to_archive)
                else:
                    archive_data = {
                        'jobs': jobs_to_archive,
                        'archived_at': datetime.now().isoformat(),
                        'archived_from': job_file.name,
                        'cutoff_date': cutoff_date.isoformat()
                    }
                
                if not dry_run:
                    with open(archive_file, 'w', encoding='utf-8') as f:
                        json.dump(archive_data, f, indent=2, ensure_ascii=False)
                
                print(f"   📦 {job_file.name}: Archive {len(jobs_to_archive)} jobs → {archive_file.name}")
                
                # Update file gốc (chỉ giữ jobs còn lại)
                if not dry_run:
                    data['jobs'] = jobs_to_keep
                    data['updated_at'] = datetime.now().isoformat()
                    
                    # Atomic write
                    temp_file = job_file.with_suffix('.json.tmp')
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    temp_file.replace(job_file)
                    
                    files_updated += 1
        
        except Exception as e:
            print(f"   ❌ Lỗi xử lý file {job_file.name}: {str(e)}")
    
    print()
    if dry_run:
        print(f"🔍 DRY RUN: Sẽ archive {archived_count} jobs")
    else:
        print(f"✅ Hoàn thành! Đã archive {archived_count} jobs vào {archive_dir}")
        print(f"   → Updated {files_updated} files")
    
    return archived_count


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Archive jobs completed cũ"
    )
    parser.add_argument(
        "--jobs-dir",
        type=str,
        default="jobs/",
        help="Thư mục chứa jobs (mặc định: jobs/)"
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        default="jobs/archive/",
        help="Thư mục archive (mặc định: jobs/archive/)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Số ngày để coi là 'cũ' (mặc định: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ hiển thị sẽ archive gì, không thực sự archive"
    )
    
    args = parser.parse_args()
    
    jobs_dir = Path(args.jobs_dir)
    if not jobs_dir.exists():
        print(f"❌ Thư mục không tồn tại: {jobs_dir}")
        return
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - Không thực sự archive jobs")
        print()
    
    archive_old_jobs(
        jobs_dir=jobs_dir,
        archive_dir=Path(args.archive_dir),
        days=args.days,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

