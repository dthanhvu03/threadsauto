#!/usr/bin/env python3
"""
Job Management CLI Tool - Công cụ quản lý jobs dễ dàng.

Usage:
    python scripts/jobs_cli.py <command> [options]

Commands:
    list        - Liệt kê jobs với filter
    search      - Tìm kiếm jobs theo content/keyword
    stats       - Thống kê jobs
    export      - Export jobs ra CSV/JSON
    import      - Import jobs từ template file (JSON)
    backup      - Backup jobs
    restore     - Restore jobs từ backup
    clean       - Cleanup jobs (expired, completed, etc.)
    bulk        - Bulk operations (delete, update status, etc.)
    template    - Tạo job template
    validate    - Validate jobs và báo cáo issues
"""

import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Setup path using common utility
from scripts.common import setup_path, get_logger, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()

from services.scheduler import Scheduler, JobStatus, JobPriority
from services.scheduler.models import Platform


class JobsCLI:
    """CLI tool để quản lý jobs."""
    
    def __init__(self, jobs_dir: Optional[Path] = None):
        """Initialize CLI tool."""
        self.jobs_dir = jobs_dir or Path("./jobs")
        self.logger = get_logger("jobs_cli")
        self.scheduler = Scheduler(storage_dir=self.jobs_dir, logger=self.logger)
    
    def list_jobs(
        self,
        account_id: Optional[str] = None,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        priority: Optional[str] = None,
        limit: Optional[int] = None,
        output_format: str = "table",
        reload: bool = True
    ) -> None:
        """
        Liệt kê jobs với filter.
        
        Args:
            account_id: Filter by account ID
            status: Filter by status
            platform: Filter by platform
            priority: Filter by priority
            limit: Limit số lượng
            output_format: Output format (table, json, csv, simple)
            reload: Nếu True, reload jobs từ storage trước khi list (đảm bảo realtime update)
        """
        # QUAN TRỌNG: Reload jobs từ storage trước khi list để đảm bảo realtime update
        # Điều này đảm bảo CLI luôn hiển thị jobs mới nhất từ file JSON
        if reload:
            try:
                self.scheduler.reload_jobs(force=False)  # Không force để tránh race condition
            except Exception as reload_error:
                # Log nhưng không fail - vẫn có thể list jobs từ memory
                print(f"[JobsCLI] WARNING: Failed to reload jobs: {str(reload_error)}")
        
        jobs = self.scheduler.list_jobs(account_id=account_id)
        
        # Filter by status
        if status:
            status_enum = JobStatus[status.upper()]
            jobs = [j for j in jobs if j.status == status_enum]
        
        # Filter by platform
        if platform:
            platform_enum = Platform[platform.upper()]
            jobs = [j for j in jobs if getattr(j, 'platform', Platform.THREADS) == platform_enum]
        
        # Filter by priority
        if priority:
            priority_enum = JobPriority[priority.upper()]
            jobs = [j for j in jobs if j.priority == priority_enum]
        
        # Limit
        if limit:
            jobs = jobs[:limit]
        
        # Display
        if output_format == "table":
            self._display_table(jobs)
        elif output_format == "json":
            self._display_json(jobs)
        elif output_format == "csv":
            self._display_csv(jobs)
        else:
            self._display_simple(jobs)
    
    def search_jobs(self, keyword: str, field: str = "content") -> None:
        """Tìm kiếm jobs theo keyword."""
        all_jobs = self.scheduler.list_jobs()
        
        keyword_lower = keyword.lower()
        results = []
        
        for job in all_jobs:
            if field == "content":
                if keyword_lower in job.content.lower():
                    results.append(job)
            elif field == "account_id":
                if keyword_lower in job.account_id.lower():
                    results.append(job)
            elif field == "job_id":
                if keyword_lower in job.job_id.lower():
                    results.append(job)
            elif field == "all":
                if (keyword_lower in job.content.lower() or
                    keyword_lower in job.account_id.lower() or
                    keyword_lower in job.job_id.lower()):
                    results.append(job)
        
        print(f"\n🔍 Tìm thấy {len(results)} jobs với keyword '{keyword}':")
        print_header("")
        self._display_table(results)
    
    def stats(self) -> None:
        """Thống kê jobs."""
        all_jobs = self.scheduler.list_jobs()
        
        stats = {
            'total': len(all_jobs),
            'by_status': defaultdict(int),
            'by_priority': defaultdict(int),
            'by_platform': defaultdict(int),
            'by_account': defaultdict(int),
            'ready': 0,
            'expired': 0,
            'today': 0,
            'this_week': 0,
            'this_month': 0
        }
        
        now = datetime.now()
        today = now.date()
        week_start = today - timedelta(days=now.weekday())
        month_start = today.replace(day=1)
        
        for job in all_jobs:
            stats['by_status'][job.status.value] += 1
            stats['by_priority'][job.priority.value] += 1
            platform = getattr(job, 'platform', Platform.THREADS)
            stats['by_platform'][platform.value] += 1
            stats['by_account'][job.account_id] += 1
            
            if job.is_ready():
                stats['ready'] += 1
            
            if job.is_expired():
                stats['expired'] += 1
            
            job_date = job.scheduled_time.date()
            if job_date == today:
                stats['today'] += 1
            if job_date >= week_start:
                stats['this_week'] += 1
            if job_date >= month_start:
                stats['this_month'] += 1
        
        # Display stats
        print_header("📊 THỐNG KÊ JOBS")
        print(f"Tổng số jobs: {stats['total']}")
        print(f"\n📈 Theo trạng thái:")
        for status, count in sorted(stats['by_status'].items()):
            print(f"  {status:15s}: {count:4d}")
        
        print(f"\n⭐ Theo priority:")
        for priority, count in sorted(stats['by_priority'].items()):
            priority_name = {1: "LOW", 2: "NORMAL", 3: "HIGH", 4: "URGENT"}.get(priority, "UNKNOWN")
            print(f"  {priority_name:15s}: {count:4d}")
        
        print(f"\n🌐 Theo platform:")
        for platform, count in sorted(stats['by_platform'].items()):
            print(f"  {platform:15s}: {count:4d}")
        
        print(f"\n👤 Theo account:")
        for account, count in sorted(stats['by_account'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {account:30s}: {count:4d}")
        
        print(f"\n⏰ Theo thời gian:")
        print(f"  Ready ngay:        {stats['ready']:4d}")
        print(f"  Expired:           {stats['expired']:4d}")
        print(f"  Hôm nay:           {stats['today']:4d}")
        print(f"  Tuần này:          {stats['this_week']:4d}")
        print(f"  Tháng này:         {stats['this_month']:4d}")
    
    def export_jobs(
        self,
        output_file: str,
        output_format: str = "json",
        account_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> None:
        """Export jobs ra file."""
        jobs = self.scheduler.list_jobs(account_id=account_id)
        
        if status:
            status_enum = JobStatus[status.upper()]
            jobs = [j for j in jobs if j.status == status_enum]
        
        if output_format == "json":
            jobs_data = [job.to_dict() for job in jobs]
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Đã export {len(jobs)} jobs ra {output_file}")
        
        elif output_format == "csv":
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if not jobs:
                    return
                
                fieldnames = [
                    'job_id', 'account_id', 'content', 'scheduled_time',
                    'status', 'priority', 'platform', 'created_at',
                    'started_at', 'completed_at', 'thread_id', 'error',
                    'retry_count', 'max_retries', 'status_message'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for job in jobs:
                    job_dict = job.to_dict()
                    row = {}
                    for field in fieldnames:
                        value = job_dict.get(field)
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        elif hasattr(value, 'value'):
                            value = value.value
                        row[field] = value
                    writer.writerow(row)
            
            print(f"✅ Đã export {len(jobs)} jobs ra {output_file}")
    
    def backup_jobs(self, backup_dir: Optional[Path] = None) -> str:
        """Backup jobs."""
        backup_dir = backup_dir or Path("./backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"jobs_backup_{timestamp}.json"
        
        all_jobs = self.scheduler.list_jobs()
        jobs_data = [job.to_dict() for job in all_jobs]
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'total_jobs': len(jobs_data),
            'jobs': jobs_data
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Đã backup {len(jobs_data)} jobs ra {backup_file}")
        return str(backup_file)
    
    def restore_jobs(self, backup_file: str, dry_run: bool = False) -> None:
        """Restore jobs từ backup."""
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        jobs_data = backup_data.get('jobs', [])
        print(f"📦 Backup date: {backup_data.get('backup_date', 'Unknown')}")
        print(f"📦 Total jobs: {len(jobs_data)}")
        
        if dry_run:
            print("\n🔍 DRY RUN - Sẽ import các jobs sau:")
            for job_data in jobs_data[:10]:
                print(f"  - {job_data.get('job_id', 'unknown')}: {job_data.get('content', '')[:50]}")
            if len(jobs_data) > 10:
                print(f"  ... và {len(jobs_data) - 10} jobs khác")
            return
        
        # Import jobs
        imported = 0
        skipped = 0
        
        for job_data in jobs_data:
            try:
                # Convert từ dict sang ScheduledJob
                from services.scheduler.models import ScheduledJob
                job = ScheduledJob.from_dict(job_data)
                
                # Check duplicate
                duplicate = self.scheduler.job_manager._check_duplicate_content(
                    job.account_id,
                    job.content,
                    job.platform
                )
                
                if duplicate:
                    skipped += 1
                    continue
                
                # Add job
                self.scheduler.jobs[job.job_id] = job
                imported += 1
            except Exception as e:
                print(f"⚠️  Lỗi khi import job {job_data.get('job_id', 'unknown')}: {e}")
                skipped += 1
        
        # Save
        self.scheduler._save_jobs()
        
        print(f"\n✅ Đã restore {imported} jobs")
        if skipped > 0:
            print(f"⚠️  Đã skip {skipped} jobs (duplicate hoặc lỗi)")
    
    def clean_jobs(
        self,
        expired: bool = False,
        completed: bool = False,
        failed: bool = False,
        older_than_days: Optional[int] = None,
        dry_run: bool = False
    ) -> None:
        """Cleanup jobs."""
        all_jobs = self.scheduler.list_jobs()
        to_remove = []
        
        now = datetime.now()
        cutoff_date = now - timedelta(days=older_than_days) if older_than_days else None
        
        for job in all_jobs:
            should_remove = False
            
            if expired and job.is_expired():
                should_remove = True
            
            if completed and job.status == JobStatus.COMPLETED:
                should_remove = True
            
            if failed and job.status == JobStatus.FAILED:
                should_remove = True
            
            if cutoff_date and job.created_at and job.created_at < cutoff_date:
                should_remove = True
            
            if should_remove:
                to_remove.append(job)
        
        if dry_run:
            print(f"\n🔍 DRY RUN - Sẽ xóa {len(to_remove)} jobs:")
            for job in to_remove[:10]:
                print(f"  - {job.job_id}: {job.status.value} - {job.content[:50]}")
            if len(to_remove) > 10:
                print(f"  ... và {len(to_remove) - 10} jobs khác")
            return
        
        # Remove jobs
        for job in to_remove:
            self.scheduler.remove_job(job.job_id)
        
        print(f"✅ Đã xóa {len(to_remove)} jobs")
    
    def bulk_operation(
        self,
        operation: str,
        filter_status: Optional[str] = None,
        filter_account: Optional[str] = None,
        new_status: Optional[str] = None,
        dry_run: bool = False
    ) -> None:
        """Bulk operations."""
        jobs = self.scheduler.list_jobs(account_id=filter_account)
        
        if filter_status:
            status_enum = JobStatus[filter_status.upper()]
            jobs = [j for j in jobs if j.status == status_enum]
        
        if operation == "delete":
            if dry_run:
                print(f"🔍 DRY RUN - Sẽ xóa {len(jobs)} jobs")
            else:
                for job in jobs:
                    self.scheduler.remove_job(job.job_id)
                print(f"✅ Đã xóa {len(jobs)} jobs")
        
        elif operation == "update_status" and new_status:
            status_enum = JobStatus[new_status.upper()]
            if dry_run:
                print(f"🔍 DRY RUN - Sẽ update {len(jobs)} jobs thành {new_status}")
            else:
                for job in jobs:
                    job.status = status_enum
                self.scheduler._save_jobs()
                print(f"✅ Đã update {len(jobs)} jobs thành {new_status}")
    
    def create_template(self, output_file: str = "job_template.json") -> None:
        """Tạo job template."""
        template = {
            "account_id": "account_01",
            "content": "Nội dung bài post",
            "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "priority": "NORMAL",
            "platform": "THREADS",
            "max_retries": 3
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Đã tạo template tại {output_file}")
    
    def import_from_template(self, template_file: str, dry_run: bool = False) -> None:
        """Import jobs từ template file (JSON array)."""
        with open(template_file, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        # Support both single object and array
        if isinstance(templates, dict):
            templates = [templates]
        
        if dry_run:
            print(f"\n🔍 DRY RUN - Sẽ import {len(templates)} jobs:")
            for i, template in enumerate(templates[:10], 1):
                print(f"  {i}. {template.get('account_id', 'unknown')}: {template.get('content', '')[:50]}")
            if len(templates) > 10:
                print(f"  ... và {len(templates) - 10} jobs khác")
            return
        
        imported = 0
        failed = 0
        
        for template in templates:
            try:
                # Parse scheduled_time
                scheduled_time_str = template.get('scheduled_time')
                if isinstance(scheduled_time_str, str):
                    scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                else:
                    scheduled_time = datetime.now() + timedelta(hours=1)
                
                # Parse priority
                priority_str = template.get('priority', 'NORMAL')
                if isinstance(priority_str, str):
                    priority = JobPriority[priority_str.upper()]
                else:
                    priority = JobPriority(priority_str)
                
                # Parse platform
                platform_str = template.get('platform', 'THREADS')
                if isinstance(platform_str, str):
                    platform = Platform[platform_str.upper()]
                else:
                    platform = Platform(platform_str)
                
                # Add job
                self.scheduler.add_job(
                    account_id=template.get('account_id'),
                    content=template.get('content'),
                    scheduled_time=scheduled_time,
                    priority=priority,
                    platform=platform,
                    max_retries=template.get('max_retries', 3)
                )
                imported += 1
            except Exception as e:
                print(f"⚠️  Lỗi khi import job: {e}")
                failed += 1
        
        print(f"\n✅ Đã import {imported} jobs")
        if failed > 0:
            print(f"⚠️  Đã fail {failed} jobs")
    
    def validate_jobs(self) -> Dict[str, Any]:
        """Validate tất cả jobs và báo cáo issues."""
        all_jobs = self.scheduler.list_jobs()
        
        issues = {
            'invalid_content': [],
            'invalid_time': [],
            'expired': [],
            'stuck': [],
            'duplicates': []
        }
        
        content_map = defaultdict(list)
        
        for job in all_jobs:
            # Check content
            if not job.content or len(job.content.strip()) == 0:
                issues['invalid_content'].append(job.job_id)
            
            if len(job.content) > 500:
                issues['invalid_content'].append(job.job_id)
            
            # Check scheduled_time
            now = datetime.now()
            one_year_ago = now - timedelta(days=365)
            one_year_later = now + timedelta(days=365)
            
            if job.scheduled_time < one_year_ago or job.scheduled_time > one_year_later:
                issues['invalid_time'].append(job.job_id)
            
            # Check expired
            if job.is_expired():
                issues['expired'].append(job.job_id)
            
            # Check stuck
            if job.status == JobStatus.RUNNING:
                if job.is_stuck(max_running_minutes=30):
                    issues['stuck'].append(job.job_id)
            
            # Track duplicates
            normalized = job.content.strip().lower()
            content_map[normalized].append(job.job_id)
        
        # Find duplicates
        for content, job_ids in content_map.items():
            if len(job_ids) > 1:
                issues['duplicates'].append({
                    'content_preview': content[:50],
                    'job_ids': job_ids,
                    'count': len(job_ids)
                })
        
        # Display report
        print_header("🔍 VALIDATION REPORT")
        
        total_issues = sum(len(v) if isinstance(v, list) else 1 for v in issues.values())
        
        if total_issues == 0:
            print("✅ Tất cả jobs đều hợp lệ!")
            return issues
        
        print(f"⚠️  Tìm thấy {total_issues} issues:\n")
        
        if issues['invalid_content']:
            print(f"❌ Invalid content: {len(issues['invalid_content'])} jobs")
            for job_id in issues['invalid_content'][:5]:
                print(f"   - {job_id}")
            if len(issues['invalid_content']) > 5:
                print(f"   ... và {len(issues['invalid_content']) - 5} jobs khác")
            print()
        
        if issues['invalid_time']:
            print(f"❌ Invalid scheduled_time: {len(issues['invalid_time'])} jobs")
            for job_id in issues['invalid_time'][:5]:
                print(f"   - {job_id}")
            if len(issues['invalid_time']) > 5:
                print(f"   ... và {len(issues['invalid_time']) - 5} jobs khác")
            print()
        
        if issues['expired']:
            print(f"⏰ Expired: {len(issues['expired'])} jobs")
            print()
        
        if issues['stuck']:
            print(f"🔄 Stuck (RUNNING > 30 phút): {len(issues['stuck'])} jobs")
            for job_id in issues['stuck'][:5]:
                print(f"   - {job_id}")
            if len(issues['stuck']) > 5:
                print(f"   ... và {len(issues['stuck']) - 5} jobs khác")
            print()
        
        if issues['duplicates']:
            print(f"⚠️  Duplicate content: {len(issues['duplicates'])} nhóm")
            for dup in issues['duplicates'][:5]:
                print(f"   - '{dup['content_preview']}': {dup['count']} jobs")
                print(f"     Job IDs: {', '.join(dup['job_ids'][:3])}")
                if len(dup['job_ids']) > 3:
                    print(f"     ... và {len(dup['job_ids']) - 3} jobs khác")
            if len(issues['duplicates']) > 5:
                print(f"   ... và {len(issues['duplicates']) - 5} nhóm khác")
            print()
        
        return issues
    
    def _display_table(self, jobs: List) -> None:
        """Display jobs dạng table."""
        if not jobs:
            print("📋 Không có jobs nào.")
            return
        
        print(f"\n📋 Danh sách {len(jobs)} jobs:")
        # Use print_header for separator line
        separator = "=" * 120
        print(separator)
        print(f"{'ID':<12} {'Account':<15} {'Status':<12} {'Priority':<8} {'Scheduled':<20} {'Content':<40}")
        print("-" * 120)
        
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
            
            priority_name = {1: "LOW", 2: "NORMAL", 3: "HIGH", 4: "URGENT"}.get(job.priority.value, "UNKNOWN")
            
            content_preview = job.content[:37] + "..." if len(job.content) > 40 else job.content
            scheduled_str = job.scheduled_time.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"{job.job_id[:12]:<12} {job.account_id:<15} {status_emoji} {job.status.value:<10} "
                  f"{priority_name:<8} {scheduled_str:<20} {content_preview:<40}")
    
    def _display_json(self, jobs: List) -> None:
        """Display jobs dạng JSON."""
        jobs_data = [job.to_dict() for job in jobs]
        print(json.dumps(jobs_data, indent=2, ensure_ascii=False, default=str))
    
    def _display_csv(self, jobs: List) -> None:
        """Display jobs dạng CSV."""
        if not jobs:
            return
        
        import io
        output = io.StringIO()
        fieldnames = ['job_id', 'account_id', 'content', 'scheduled_time', 'status', 'priority']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for job in jobs:
            job_dict = job.to_dict()
            row = {k: job_dict.get(k) for k in fieldnames}
            writer.writerow(row)
        
        print(output.getvalue())
    
    def _display_simple(self, jobs: List) -> None:
        """Display jobs dạng simple."""
        for job in jobs:
            print(f"{job.job_id}: {job.status.value} - {job.content[:50]}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Job Management CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--jobs-dir',
        type=Path,
        default=Path("./jobs"),
        help="Thư mục chứa jobs (default: ./jobs)"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='Liệt kê jobs')
    list_parser.add_argument('--account', help='Filter by account_id')
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--platform', help='Filter by platform')
    list_parser.add_argument('--priority', help='Filter by priority')
    list_parser.add_argument('--limit', type=int, help='Limit số lượng')
    list_parser.add_argument('--format', choices=['table', 'json', 'csv', 'simple'], default='table', dest='output_format')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Tìm kiếm jobs')
    search_parser.add_argument('keyword', help='Keyword để tìm')
    search_parser.add_argument('--field', choices=['content', 'account_id', 'job_id', 'all'], default='all')
    
    # Stats command
    subparsers.add_parser('stats', help='Thống kê jobs')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export jobs')
    export_parser.add_argument('output', help='Output file')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', dest='output_format')
    export_parser.add_argument('--account', help='Filter by account_id')
    export_parser.add_argument('--status', help='Filter by status')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup jobs')
    backup_parser.add_argument('--dir', type=Path, help='Backup directory')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore jobs từ backup')
    restore_parser.add_argument('backup_file', help='Backup file path')
    restore_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Cleanup jobs')
    clean_parser.add_argument('--expired', action='store_true', help='Xóa expired jobs')
    clean_parser.add_argument('--completed', action='store_true', help='Xóa completed jobs')
    clean_parser.add_argument('--failed', action='store_true', help='Xóa failed jobs')
    clean_parser.add_argument('--older-than-days', type=int, help='Xóa jobs cũ hơn N ngày')
    clean_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    # Bulk command
    bulk_parser = subparsers.add_parser('bulk', help='Bulk operations')
    bulk_parser.add_argument('operation', choices=['delete', 'update_status'], help='Operation')
    bulk_parser.add_argument('--filter-status', help='Filter by status')
    bulk_parser.add_argument('--filter-account', help='Filter by account')
    bulk_parser.add_argument('--new-status', help='New status (for update_status)')
    bulk_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    # Template command
    template_parser = subparsers.add_parser('template', help='Tạo job template')
    template_parser.add_argument('--output', default='job_template.json', help='Output file')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import jobs từ template file')
    import_parser.add_argument('template_file', help='Template file path (JSON)')
    import_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate jobs và báo cáo issues')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = JobsCLI(jobs_dir=args.jobs_dir)
    
    try:
        if args.command == 'list':
            cli.list_jobs(
                account_id=args.account,
                status=args.status,
                platform=args.platform,
                priority=args.priority,
                limit=args.limit,
                output_format=getattr(args, 'output_format', 'table')
            )
        elif args.command == 'search':
            cli.search_jobs(args.keyword, field=args.field)
        elif args.command == 'stats':
            cli.stats()
        elif args.command == 'export':
            cli.export_jobs(
                output_file=args.output,
                output_format=getattr(args, 'output_format', 'json'),
                account_id=args.account,
                status=args.status
            )
        elif args.command == 'backup':
            cli.backup_jobs(backup_dir=args.dir)
        elif args.command == 'restore':
            cli.restore_jobs(args.backup_file, dry_run=args.dry_run)
        elif args.command == 'clean':
            cli.clean_jobs(
                expired=args.expired,
                completed=args.completed,
                failed=args.failed,
                older_than_days=args.older_than_days,
                dry_run=args.dry_run
            )
        elif args.command == 'bulk':
            cli.bulk_operation(
                operation=args.operation,
                filter_status=args.filter_status,
                filter_account=args.filter_account,
                new_status=args.new_status,
                dry_run=args.dry_run
            )
        elif args.command == 'template':
            cli.create_template(output_file=args.output)
        elif args.command == 'import':
            cli.import_from_template(args.template_file, dry_run=args.dry_run)
        elif args.command == 'validate':
            cli.validate_jobs()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

