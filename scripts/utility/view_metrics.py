#!/usr/bin/env python3
"""
Script để xem metrics (views, likes, replies, reposts, shares) từ database.

Usage:
    python scripts/utility/view_metrics.py [account_id] [--thread_id THREAD_ID]
    python scripts/utility/view_metrics.py account_01                    # Xem tất cả metrics của account
    python scripts/utility/view_metrics.py account_01 --thread_id 123   # Xem metrics của thread cụ thể
"""

import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.common import (
    setup_path,
    get_mysql_config,
    print_header,
    print_section
)

setup_path()

from services.analytics.storage import MetricsStorage
from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.scheduler.models import JobStatus
from typing import List, Dict, Optional
from datetime import datetime


def format_number(num: Optional[int]) -> str:
    """Format number với K/M suffix."""
    if num is None:
        return "N/A"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def view_account_metrics(account_id: str, limit: int = 50, only_with_metrics: bool = False):
    """Xem tất cả metrics của một account.
    
    Args:
        account_id: Account ID
        limit: Giới hạn số threads hiển thị (default: 50)
        only_with_metrics: Chỉ hiển thị threads đã có metrics (default: False)
    """
    print_header("")
    print(f"📊 METRICS CHO ACCOUNT: {account_id}")
    print_header("")
    
    # Get MySQL config
    mysql_config = get_mysql_config()
    
    # Get jobs với thread_id
    job_storage = MySQLJobStorage(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database
    )
    
    # Get completed jobs với thread_id
    try:
        jobs = job_storage.get_jobs_by_status(JobStatus.COMPLETED)
        # Filter jobs by account_id and thread_id
        jobs_with_thread = [
            job for job in jobs 
            if job.thread_id and job.account_id == account_id
        ]
        
        if not jobs_with_thread:
            print(f"⚠️  Không tìm thấy completed jobs với thread_id cho account '{account_id}'")
            return
        
        print(f"📋 Tìm thấy {len(jobs_with_thread)} completed jobs với thread_id\n")
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy jobs: {e}")
        return
    
    # Get metrics storage
    storage = MetricsStorage(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database
    )
    
    # Get metrics cho mỗi thread
    # Sử dụng get_account_metrics_history để lấy metrics trực tiếp từ DB (nhanh hơn)
    # Sau đó group by thread_id và lấy latest cho mỗi thread
    table_data = []
    count_with_metrics = 0
    count_without_metrics = 0
    
    # Get all metrics history for account (last 24h)
    metrics_history = storage.get_account_metrics_history(account_id)
    
    # Create dict: thread_id -> latest metrics
    latest_metrics_dict = {}
    for metrics in metrics_history:
        thread_id = metrics.get("thread_id")
        if thread_id:
            # Keep latest metrics for each thread
            if thread_id not in latest_metrics_dict:
                latest_metrics_dict[thread_id] = metrics
            else:
                # Compare fetched_at to keep latest
                current_fetched = metrics.get("fetched_at")
                existing_fetched = latest_metrics_dict[thread_id].get("fetched_at")
                if current_fetched and existing_fetched and current_fetched > existing_fetched:
                    latest_metrics_dict[thread_id] = metrics
    
    # Sort jobs by completed_at DESC (newest first)
    jobs_with_thread_sorted = sorted(
        jobs_with_thread,
        key=lambda j: j.completed_at if j.completed_at else datetime.min,
        reverse=True
    )
    
    for job in jobs_with_thread_sorted[:limit]:  # Limit số lượng
        thread_id = job.thread_id
        if not thread_id:
            continue
        
        metrics = latest_metrics_dict.get(thread_id)
        
        # Get content from job
        content = job.content if hasattr(job, 'content') else ""
        content_preview = content[:60] + "..." if len(content) > 60 else content
        content_preview = content_preview.replace('\n', ' ').replace('\r', ' ')
        
        if metrics:
            count_with_metrics += 1
            table_data.append({
                "Thread ID": thread_id[:20] + "..." if len(thread_id) > 20 else thread_id,
                "Content": content_preview,
                "Views": format_number(metrics.get("views")),
                "Likes": format_number(metrics.get("likes", 0)),
                "Replies": format_number(metrics.get("replies", 0)),
                "Reposts": format_number(metrics.get("reposts", 0)),
                "Shares": format_number(metrics.get("shares", 0)),
                "Fetched At": metrics.get("fetched_at").strftime("%Y-%m-%d %H:%M") if metrics.get("fetched_at") else "N/A"
            })
        else:
            count_without_metrics += 1
            if not only_with_metrics:  # Chỉ thêm nếu không filter
                table_data.append({
                    "Thread ID": thread_id[:20] + "..." if len(thread_id) > 20 else thread_id,
                    "Content": content_preview,
                    "Views": "❌ Chưa fetch",
                    "Likes": "❌ Chưa fetch",
                    "Replies": "❌ Chưa fetch",
                    "Reposts": "❌ Chưa fetch",
                    "Shares": "❌ Chưa fetch",
                    "Fetched At": "N/A"
                })
    
    if table_data:
        # Print table manually
        headers = list(table_data[0].keys())
        col_widths = {h: max(len(str(h)), max(len(str(row[h])) for row in table_data)) for h in headers}
        
        # Print header
        header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
        print(header_line)
        print("-" * len(header_line))
        
        # Print rows
        for row in table_data:
            row_line = " | ".join(str(row[h]).ljust(col_widths[h]) for h in headers)
            print(row_line)
        
        print(f"\n📊 Tổng cộng: {len(table_data)} threads hiển thị")
        if count_with_metrics > 0:
            print(f"   ✅ Có metrics: {count_with_metrics} threads")
        if count_without_metrics > 0:
            print(f"   ❌ Chưa fetch: {count_without_metrics} threads")
        if len(jobs_with_thread) > limit:
            print(f"   ⚠️  Đang hiển thị {limit}/{len(jobs_with_thread)} threads (dùng --limit để xem thêm)")
    else:
        print("⚠️  Không có metrics nào được tìm thấy")


def view_thread_metrics(thread_id: str, account_id: Optional[str] = None):
    """Xem metrics của một thread cụ thể."""
    print_header("")
    print(f"📊 METRICS CHO THREAD: {thread_id}")
    print_header("")
    
    # Get MySQL config
    mysql_config = get_mysql_config()
    
    # Get job storage để lấy content
    job_storage = MySQLJobStorage(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database
    )
    
    # Find job với thread_id này
    job = None
    if account_id:
        jobs = job_storage.get_jobs_by_account(account_id, JobStatus.COMPLETED)
        for j in jobs:
            if j.thread_id == thread_id:
                job = j
                break
    else:
        # Find in all completed jobs
        all_jobs = job_storage.get_jobs_by_status(JobStatus.COMPLETED)
        for j in all_jobs:
            if j.thread_id == thread_id:
                job = j
                account_id = j.account_id
                break
    
    # Get metrics storage
    storage = MetricsStorage(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database
    )
    
    # Get latest metrics
    metrics = storage.get_latest_metrics(thread_id)
    
    # Display content nếu có
    if job:
        print(f"📝 CONTENT:")
        print(f"   {job.content}")
        print_header("")
        print(f"📋 Thread ID: {thread_id}")
        print(f"📋 Account ID: {account_id or job.account_id}")
    else:
        print(f"📋 Thread ID: {thread_id}")
        print(f"📋 Account ID: {account_id or 'N/A'}")
        print(f"⚠️  Không tìm thấy job content trong database")
    
    if not metrics:
        print(f"\n❌ Không tìm thấy metrics cho thread_id: {thread_id}")
        print(f"💡 Có thể chưa fetch metrics. Chạy fetch metrics trước.")
        return
    
    print(f"")
    print(f"📊 METRICS:")
    print(f"   👁️  Views:    {format_number(metrics.get('views')):>10} ({metrics.get('views') or 0:,} total)")
    print(f"   ❤️  Likes:    {format_number(metrics.get('likes', 0)):>10} ({metrics.get('likes', 0):,} total)")
    print(f"   💬 Replies:  {format_number(metrics.get('replies', 0)):>10} ({metrics.get('replies', 0):,} total)")
    print(f"   🔄 Reposts:   {format_number(metrics.get('reposts', 0)):>10} ({metrics.get('reposts', 0):,} total)")
    print(f"   📤 Shares:    {format_number(metrics.get('shares', 0)):>10} ({metrics.get('shares', 0):,} total)")
    print(f"")
    print(f"⏰ Fetched At: {metrics.get('fetched_at')}")
    
    # Get metrics history nếu có
    history = storage.get_thread_metrics_history(thread_id)
    if history and len(history) > 5:
        history = history[:5]  # Limit to 5 most recent
    if history and len(history) > 1:
        print(f"\n📈 LỊCH SỬ METRICS (5 lần gần nhất):")
        history_data = []
        for h in history:
            history_data.append({
                "Fetched At": h.get("fetched_at").strftime("%Y-%m-%d %H:%M") if h.get("fetched_at") else "N/A",
                "Views": format_number(h.get("views")),
                "Likes": format_number(h.get("likes", 0)),
                "Replies": format_number(h.get("replies", 0)),
                "Reposts": format_number(h.get("reposts", 0)),
                "Shares": format_number(h.get("shares", 0))
            })
        # Print history table manually
        if history_data:
            headers = list(history_data[0].keys())
            col_widths = {h: max(len(str(h)), max(len(str(row[h])) for row in history_data)) for h in headers}
            
            # Print header
            header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
            print(header_line)
            print("-" * len(header_line))
            
            # Print rows
            for row in history_data:
                row_line = " | ".join(str(row[h]).ljust(col_widths[h]) for h in headers)
                print(row_line)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/utility/view_metrics.py <account_id>")
        print("  python scripts/utility/view_metrics.py <account_id> --thread_id <thread_id>")
        print("  python scripts/utility/view_metrics.py <account_id> --only-metrics [--limit N]")
        sys.exit(1)
    
    account_id = sys.argv[1]
    thread_id = None
    only_with_metrics = "--only-metrics" in sys.argv or "--only" in sys.argv
    limit = 50
    
    # Parse arguments
    if "--thread_id" in sys.argv:
        idx = sys.argv.index("--thread_id")
        if idx + 1 < len(sys.argv):
            thread_id = sys.argv[idx + 1]
    
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[idx + 1])
            except ValueError:
                print(f"⚠️  Invalid limit value: {sys.argv[idx + 1]}, using default 50")
    
    if thread_id:
        view_thread_metrics(thread_id, account_id)
    else:
        view_account_metrics(account_id, limit=limit, only_with_metrics=only_with_metrics)


if __name__ == "__main__":
    main()
