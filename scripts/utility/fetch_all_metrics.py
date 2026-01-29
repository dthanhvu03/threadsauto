#!/usr/bin/env python3
"""
Script để fetch metrics cho toàn bộ threads của một account.

⚠️ CRITICAL REQUIREMENTS:
1. Verify username từ account metadata trước khi fetch
2. Fetch metrics cho tất cả threads chưa có metrics hoặc cần update
3. Skip threads đã có recent metrics (trong 1 giờ)

Usage:
    python scripts/utility/fetch_all_metrics.py <account_id> [--force] [--limit N]
    python scripts/utility/fetch_all_metrics.py 02                    # Fetch tất cả
    python scripts/utility/fetch_all_metrics.py 02 --force            # Force fetch (skip recent check)
    python scripts/utility/fetch_all_metrics.py 02 --limit 10         # Chỉ fetch 10 threads đầu tiên
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from datetime import datetime as dt

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.common import (
    setup_path,
    get_mysql_config,
    get_account_storage,
    get_account_username,
    print_header,
    print_section
)

setup_path()

from services.analytics.service import MetricsService
from services.analytics.storage import MetricsStorage
from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.scheduler.models import JobStatus


def verify_username(account_id: str) -> Optional[str]:
    """
    Verify và lấy username từ account metadata.
    
    Returns:
        Username nếu tìm thấy, None nếu không có
    """
    try:
        # Use common utility function
        username = get_account_username(account_id)
        
        if username:
            print(f"✅ Username từ metadata: @{username}")
            return username
        else:
            print(f"⚠️  WARNING: Username không có trong metadata!")
            print(f"   Script sẽ extract username từ page (có thể sai nếu browser login account khác)")
            print(f"   💡 Fix: python scripts/utility/fix_account_username.py {account_id} your_username")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi khi lấy username: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_threads_to_fetch(account_id: str, force: bool = False) -> List[str]:
    """
    Lấy danh sách thread_ids cần fetch.
    
    Args:
        account_id: Account ID
        force: Nếu True, fetch cả những threads đã có recent metrics
    
    Returns:
        List of thread_ids
    """
    # Get MySQL config
    mysql_config = get_mysql_config()
    
    # Get jobs storage
    job_storage = MySQLJobStorage(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database
    )
    
    # Get metrics storage
    metrics_storage = MetricsStorage(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database
    )
    
    # Get completed jobs với thread_id
    try:
        print(f"   Đang kết nối database...")
        jobs = job_storage.get_jobs_by_status(JobStatus.COMPLETED)
        jobs_with_thread = [
            job for job in jobs 
            if job.thread_id and job.account_id == account_id
        ]
        
        print(f"   ✅ Tìm thấy {len(jobs_with_thread)} completed jobs với thread_id")
        
        # Filter threads cần fetch
        threads_to_fetch = []
        threads_skipped = []
        
        # Sort by completed_at DESC (mới nhất trước)
        # Để fetch threads mới nhất trước
        jobs_with_thread_sorted = sorted(
            jobs_with_thread,
            key=lambda j: j.completed_at or datetime.min,
            reverse=True
        )
        
        for job in jobs_with_thread_sorted:
            thread_id = job.thread_id
            
            if force:
                # Force fetch: fetch tất cả
                threads_to_fetch.append(thread_id)
            else:
                # Check recent metrics (trong 24 giờ - tăng từ 1 giờ)
                # Tránh fetch duplicate quá nhiều
                if metrics_storage.has_recent_metrics(thread_id, hours=24):
                    threads_skipped.append(thread_id)
                else:
                    threads_to_fetch.append(thread_id)
        
        print(f"📊 Phân tích:")
        print(f"   ✅ Cần fetch: {len(threads_to_fetch)} threads (sắp xếp: mới nhất trước)")
        print(f"   ⏭️  Skip (có recent metrics trong 24h): {len(threads_skipped)} threads")
        
        return threads_to_fetch
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy threads: {e}")
        import traceback
        traceback.print_exc()
        return []


async def fetch_all_metrics(
    account_id: str,
    thread_ids: List[str],
    username: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, any]:
    """
    Fetch metrics cho tất cả threads.
    
    Args:
        account_id: Account ID
        thread_ids: List of thread IDs
        username: Username (optional)
        limit: Limit số threads (optional)
    
    Returns:
        Dict với summary
    """
    if limit:
        thread_ids = thread_ids[:limit]
        print(f"⚠️  Giới hạn: chỉ fetch {limit} threads đầu tiên")
    
    if not thread_ids:
        print("⚠️  Không có threads nào cần fetch")
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
    
    print(f"\n🚀 Bắt đầu fetch metrics cho {len(thread_ids)} threads...")
    print_header("")
    
    # Create MetricsService
    service = MetricsService()
    
    # Fetch metrics
    # Note: MetricsService sẽ tự tạo browser nếu không có page
    # Browser sẽ được tạo với đúng account_id và profile path
    results = await service.fetch_multiple_metrics(
        thread_ids=thread_ids,
        account_id=account_id,
        username=username,
        page=None  # Let service create browser with correct account_id
    )
    
    # Summary
    success_count = sum(1 for r in results if r.get("success"))
    failed_count = sum(1 for r in results if not r.get("success") and not r.get("skipped"))
    skipped_count = sum(1 for r in results if r.get("skipped"))
    cached_count = sum(1 for r in results if r.get("cached"))
    
    print_header("")
    print(f"📊 KẾT QUẢ FETCH METRICS")
    print_header("")
    print(f"   ✅ Thành công: {success_count} threads")
    print(f"   ⏭️  Bỏ qua (username khác): {skipped_count} threads")
    print(f"   ❌ Thất bại: {failed_count} threads")
    print(f"   💾 Cached (đã có recent): {cached_count} threads")
    print(f"   📊 Tổng cộng: {len(results)} threads")
    
    # Show skipped threads (username mismatch)
    if skipped_count > 0:
        print(f"\n⏭️  Threads bị bỏ qua (username khác):")
        for result in results:
            if result.get("skipped"):
                thread_id = result.get("thread_id", "N/A")
                error = result.get("error", "Unknown")
                print(f"   - {thread_id}: {error[:80]}")
    
    # Show failed threads (real errors)
    if failed_count > 0:
        print(f"\n❌ Threads thất bại:")
        for result in results:
            if not result.get("success") and not result.get("skipped"):
                thread_id = result.get("thread_id", "N/A")
                error = result.get("error", "Unknown error")
                print(f"   - {thread_id}: {error[:100]}")
    
    return {
        "total": len(results),
        "success": success_count,
        "failed": failed_count,
        "cached": cached_count,
        "results": results
    }


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/utility/fetch_all_metrics.py <account_id> [--force] [--limit N] [--yes]")
        print("")
        print("Examples:")
        print("  python scripts/utility/fetch_all_metrics.py 02")
        print("  python scripts/utility/fetch_all_metrics.py 02 --yes          # Tự động tiếp tục (không hỏi)")
        print("  python scripts/utility/fetch_all_metrics.py 02 --force")
        print("  python scripts/utility/fetch_all_metrics.py 02 --limit 10")
        sys.exit(1)
    
    account_id = sys.argv[1]
    force = "--force" in sys.argv or "-f" in sys.argv
    auto_yes = "--yes" in sys.argv or "-y" in sys.argv
    limit = None
    
    # Parse limit
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[idx + 1])
            except ValueError:
                print(f"⚠️  Invalid limit value: {sys.argv[idx + 1]}")
                sys.exit(1)
    
    print_header("")
    print(f"🔄 FETCH METRICS CHO TOÀN BỘ THREADS")
    print_header("")
    print(f"📋 Account ID: {account_id}")
    print(f"📋 Force mode: {'Có' if force else 'Không'} (skip recent check)")
    if limit:
        print(f"📋 Limit: {limit} threads")
    print_header("")
    
    # Step 1: Verify username
    print("📋 Step 1: Verify username từ account metadata...")
    username = verify_username(account_id)
    
    if not username:
        response = input("\n⚠️  Username không có trong metadata. Tiếp tục? (y/n): ")
        if response.lower() != 'y':
            print("❌ Đã hủy. Vui lòng set username trước:")
            print(f"   python scripts/utility/fix_account_username.py {account_id} your_username")
            sys.exit(1)
    
    print_header("")
    
    # Step 2: Get threads to fetch
    print("📋 Step 2: Lấy danh sách threads cần fetch...")
    thread_ids = get_threads_to_fetch(account_id, force=force)
    
    if not thread_ids:
        print("✅ Không có threads nào cần fetch!")
        sys.exit(0)
    
    print_header("")
    
    # Step 3: Confirm
    print(f"⚠️  SẮP FETCH METRICS CHO {len(thread_ids)} THREADS")
    if limit:
        print(f"⚠️  (Giới hạn: {limit} threads)")
    print(f"")
    print(f"⏱️  Ước tính thời gian: ~{len(thread_ids) * 7} giây ({len(thread_ids) * 7 / 60:.1f} phút)")
    print(f"")
    
    if not auto_yes:
        try:
            response = input("Tiếp tục? (y/n): ")
            if response.lower() != 'y':
                print("❌ Đã hủy")
                sys.exit(0)
        except EOFError:
            # No interactive terminal - auto continue
            print("⚠️  Không có interactive terminal, tự động tiếp tục...")
    else:
        print("✅ Tự động tiếp tục (--yes flag)")
    
    print_header("")
    
    # Step 4: Fetch metrics
    print("📋 Step 3: Fetch metrics...")
    print_header("")
    
    # Run async
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        summary = loop.run_until_complete(
            fetch_all_metrics(
                account_id=account_id,
                thread_ids=thread_ids,
                username=username,
                limit=limit
            )
        )
        
        print_header("")
        print("✅ HOÀN THÀNH!")
        print_header("")
        
        # Final summary
        if summary["success"] > 0:
            print(f"✅ Đã fetch thành công {summary['success']} threads")
        if summary["failed"] > 0:
            print(f"❌ {summary['failed']} threads thất bại (xem chi tiết ở trên)")
        if summary["cached"] > 0:
            print(f"⏭️  {summary['cached']} threads đã có recent metrics (skipped)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
