#!/usr/bin/env python3
"""
Script cleanup logs cũ để giảm dung lượng.

Usage:
    python scripts/utility/cleanup_old_logs.py [--days 30] [--dry-run] [--min-size 10M]
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
import argparse


def print_header(text: str, width: int = 80):
    """Print formatted header."""
    print("=" * width)
    if text:
        print(text)
        print("=" * width)
    else:
        print("=" * width)


def print_section(text: str, width: int = 80):
    """Print formatted section."""
    if text:
        print(text)
    print("-" * width)


def parse_size(size_str: str) -> int:
    """
    Parse size string (e.g., '10M', '1G', '500K') thành bytes.
    
    Args:
        size_str: Size string với suffix (M, G, K)
    
    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    
    if size_str.endswith('K'):
        return int(size_str[:-1]) * 1024
    elif size_str.endswith('M'):
        return int(size_str[:-1]) * 1024 * 1024
    elif size_str.endswith('G'):
        return int(size_str[:-1]) * 1024 * 1024 * 1024
    else:
        # Assume bytes
        return int(size_str)


def format_size(size_bytes: int) -> str:
    """Format size in bytes thành human-readable string."""
    for unit in ['B', 'K', 'M', 'G']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}T"


def get_log_files(logs_dir: Path) -> List[Tuple[Path, int, datetime]]:
    """
    Get all log files với size và modification time.
    
    Returns:
        List of (path, size_bytes, mtime) tuples
    """
    log_files = []
    
    for log_file in logs_dir.glob("*.log"):
        try:
            stat = log_file.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime)
            log_files.append((log_file, size, mtime))
        except Exception as e:
            print(f"⚠️  Error reading {log_file.name}: {str(e)}")
    
    return log_files


def cleanup_old_logs(
    logs_dir: Path,
    days: int = 30,
    min_size: int = 0,
    dry_run: bool = False
) -> dict:
    """
    Cleanup logs cũ hơn X ngày hoặc lớn hơn min_size.
    
    Args:
        logs_dir: Thư mục chứa logs
        days: Số ngày để giữ lại (default: 30)
        min_size: Minimum size in bytes để cleanup (default: 0 = cleanup all)
        dry_run: Chỉ hiển thị, không xóa thực sự
    
    Returns:
        Dict với stats: {'deleted': count, 'freed': bytes, 'total_size': bytes}
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    print_section(f"📋 Cleanup logs cũ hơn {days} ngày (before {cutoff_date.strftime('%Y-%m-%d')})")
    if min_size > 0:
        print(f"   Và logs lớn hơn {format_size(min_size)}")
    print()
    
    log_files = get_log_files(logs_dir)
    
    if not log_files:
        print("📋 Không có log files nào.")
        return {'deleted': 0, 'freed': 0, 'total_size': 0}
    
    # Calculate total size
    total_size = sum(size for _, size, _ in log_files)
    print(f"📊 Tổng số log files: {len(log_files)}")
    print(f"📊 Tổng dung lượng: {format_size(total_size)}")
    print()
    
    # Find files to delete
    files_to_delete = []
    
    for log_file, size, mtime in log_files:
        should_delete = False
        reason = []
        
        # Check age
        if mtime < cutoff_date:
            should_delete = True
            reason.append(f"cũ ({mtime.strftime('%Y-%m-%d')})")
        
        # Check size
        if min_size > 0 and size > min_size:
            should_delete = True
            reason.append(f"lớn ({format_size(size)})")
        
        if should_delete:
            files_to_delete.append((log_file, size, reason))
    
    if not files_to_delete:
        print("✅ Không có logs nào cần cleanup.")
        return {'deleted': 0, 'freed': 0, 'total_size': total_size}
    
    # Show files to delete
    print(f"🗑️  Tìm thấy {len(files_to_delete)} files để xóa:")
    freed_bytes = 0
    
    for log_file, size, reasons in sorted(files_to_delete, key=lambda x: x[1], reverse=True):
        freed_bytes += size
        print(f"   - {log_file.name} ({format_size(size)}) - {', '.join(reasons)}")
    
    print()
    print(f"📊 Sẽ giải phóng: {format_size(freed_bytes)}")
    print()
    
    if dry_run:
        print("🔍 DRY RUN: Không thực sự xóa files.")
        return {'deleted': 0, 'freed': freed_bytes, 'total_size': total_size}
    
    # Delete files
    deleted_count = 0
    for log_file, size, _ in files_to_delete:
        try:
            log_file.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"❌ Lỗi xóa {log_file.name}: {str(e)}")
    
    print(f"✅ Đã xóa {deleted_count}/{len(files_to_delete)} files")
    print(f"📊 Đã giải phóng: {format_size(freed_bytes)}")
    
    return {
        'deleted': deleted_count,
        'freed': freed_bytes,
        'total_size': total_size - freed_bytes
    }


def show_log_stats(logs_dir: Path):
    """Hiển thị thống kê về logs."""
    print_header("📊 LOG STATISTICS")
    
    log_files = get_log_files(logs_dir)
    
    if not log_files:
        print("📋 Không có log files nào.")
        return
    
    # Sort by size
    log_files.sort(key=lambda x: x[1], reverse=True)
    
    total_size = sum(size for _, size, _ in log_files)
    total_count = len(log_files)
    
    print(f"Tổng số files: {total_count}")
    print(f"Tổng dung lượng: {format_size(total_size)}")
    print()
    
    # Group by prefix (e.g., scheduler_, jobs_api_, etc.)
    by_prefix = {}
    for log_file, size, _ in log_files:
        # Extract prefix (e.g., 'scheduler' from 'scheduler_20260120.log')
        parts = log_file.stem.split('_')
        if len(parts) >= 2:
            prefix = '_'.join(parts[:-1])  # All parts except date
        else:
            prefix = log_file.stem
        
        if prefix not in by_prefix:
            by_prefix[prefix] = {'count': 0, 'size': 0, 'files': []}
        
        by_prefix[prefix]['count'] += 1
        by_prefix[prefix]['size'] += size
        by_prefix[prefix]['files'].append((log_file, size))
    
    # Show top prefixes by size
    print("📋 Top log types by size:")
    sorted_prefixes = sorted(by_prefix.items(), key=lambda x: x[1]['size'], reverse=True)
    
    for prefix, data in sorted_prefixes[:10]:
        print(f"   {prefix:30s} - {data['count']:3d} files - {format_size(data['size']):>10s}")
    
    print()
    
    # Show largest files
    print("📋 Top 10 largest log files:")
    for log_file, size, mtime in log_files[:10]:
        age_days = (datetime.now() - mtime).days
        print(f"   {log_file.name:50s} - {format_size(size):>10s} - {age_days:3d} days old")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Cleanup old log files"
    )
    parser.add_argument(
        "--logs-dir",
        type=str,
        default="./logs",
        help="Thư mục chứa logs (mặc định: ./logs)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Số ngày để giữ lại logs (mặc định: 30)"
    )
    parser.add_argument(
        "--min-size",
        type=str,
        default="0",
        help="Minimum size để cleanup (e.g., '10M', '1G') - cleanup all if 0 (mặc định: 0)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ hiển thị sẽ xóa gì, không thực sự xóa"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Chỉ hiển thị thống kê, không cleanup"
    )
    
    args = parser.parse_args()
    
    logs_dir = Path(args.logs_dir)
    if not logs_dir.exists():
        print(f"❌ Thư mục không tồn tại: {logs_dir}")
        return
    
    # Show stats
    show_log_stats(logs_dir)
    
    if args.stats_only:
        return
    
    print()
    
    # Parse min_size
    min_size = parse_size(args.min_size) if args.min_size else 0
    
    if args.dry_run:
        print_header("🔍 DRY RUN MODE - Không thực sự xóa logs")
        print()
    
    # Cleanup
    cleanup_old_logs(
        logs_dir=logs_dir,
        days=args.days,
        min_size=min_size,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
