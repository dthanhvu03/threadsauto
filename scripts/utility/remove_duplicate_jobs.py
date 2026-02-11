#!/usr/bin/env python3
"""
Script xóa jobs duplicate content (giữ lại job đầu tiên, xóa các job sau).

Usage:
    python scripts/remove_duplicate_jobs.py [--jobs-dir jobs/] [--dry-run]
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict

# Setup path using common utility
from scripts.common import setup_path, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()


def normalize_content(content: str) -> str:
    """
    Normalize content để so sánh.
    
    Note: Uses shared utility function from utils.content
    """
    from utils.content import normalize_content as normalize_content_util
    return normalize_content_util(content)


def find_duplicates(jobs_dir: Path) -> Dict[str, List[Dict]]:
    """Tìm duplicate content jobs."""
    content_map = defaultdict(list)  # normalized_content -> [jobs]
    
    job_files = sorted(jobs_dir.glob("jobs_*.json"))
    
    for job_file in job_files:
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs = data.get('jobs', [])
                
                for job in jobs:
                    content = normalize_content(job.get('content', ''))
                    if content:
                        content_map[content].append({
                            'job': job,
                            'file': job_file,
                            'date': job_file.stem.replace("jobs_", "")
                        })
        except Exception as e:
            print(f"⚠️  Lỗi đọc file {job_file.name}: {str(e)}")
    
    # Tìm duplicates (content có > 1 job)
    duplicates = {
        content: jobs_list
        for content, jobs_list in content_map.items()
        if len(jobs_list) > 1
    }
    
    return duplicates


def remove_duplicates(jobs_dir: Path, dry_run: bool = False) -> int:
    """
    Xóa duplicate jobs (giữ lại job đầu tiên theo thời gian).
    
    Returns:
        Số lượng jobs đã xóa
    """
    duplicates = find_duplicates(jobs_dir)
    
    if not duplicates:
        print("✅ Không có duplicate content nào.")
        return 0
    
    print(f"🔍 Tìm thấy {len(duplicates)} nhóm duplicate content:")
    for content, jobs_list in list(duplicates.items())[:5]:
        print(f"   - '{content[:50]}...': {len(jobs_list)} jobs")
    if len(duplicates) > 5:
        print(f"   ... và {len(duplicates) - 5} nhóm khác")
    print()
    
    # Nhóm jobs theo file để update
    files_to_update: Dict[Path, List[Dict]] = defaultdict(list)
    jobs_to_remove: Set[str] = set()
    removed_count = 0
    
    for content, jobs_list in duplicates.items():
        # Sort theo created_at (giữ job cũ nhất)
        jobs_list.sort(key=lambda x: x['job'].get('created_at', ''))
        
        # Giữ job đầu tiên, đánh dấu các job sau để xóa
        for i, job_info in enumerate(jobs_list):
            if i == 0:
                # Giữ lại job đầu tiên
                continue
            
            job = job_info['job']
            job_id = job.get('job_id')
            job_file = job_info['file']
            
            jobs_to_remove.add(job_id)
            files_to_update[job_file].append(job_id)
            removed_count += 1
    
    if dry_run:
        print(f"🔍 DRY RUN: Sẽ xóa {removed_count} duplicate jobs")
        for job_file, job_ids in files_to_update.items():
            print(f"   - {job_file.name}: {len(job_ids)} jobs")
        return 0
    
    # Update files
    print(f"🗑️  Đang xóa {removed_count} duplicate jobs...")
    
    for job_file, job_ids_to_remove in files_to_update.items():
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_count = len(data.get('jobs', []))
            data['jobs'] = [
                job for job in data.get('jobs', [])
                if job.get('job_id') not in job_ids_to_remove
            ]
            removed_from_file = original_count - len(data['jobs'])
            
            if removed_from_file > 0:
                # Atomic write
                temp_file = job_file.with_suffix('.json.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                temp_file.replace(job_file)
                
                print(f"   ✅ {job_file.name}: Xóa {removed_from_file} jobs")
        
        except Exception as e:
            print(f"   ❌ Lỗi update file {job_file.name}: {str(e)}")
    
    print()
    print(f"✅ Hoàn thành! Đã xóa {removed_count} duplicate jobs.")
    
    return removed_count


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Xóa jobs duplicate content"
    )
    parser.add_argument(
        "--jobs-dir",
        type=str,
        default="jobs/",
        help="Thư mục chứa jobs (mặc định: jobs/)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ hiển thị sẽ xóa gì, không thực sự xóa"
    )
    
    args = parser.parse_args()
    
    jobs_dir = Path(args.jobs_dir)
    if not jobs_dir.exists():
        print(f"❌ Thư mục không tồn tại: {jobs_dir}")
        return
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - Không thực sự xóa jobs")
        print()
    
    remove_duplicates(jobs_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

