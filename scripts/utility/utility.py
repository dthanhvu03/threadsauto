#!/usr/bin/env python3
"""
Unified Utility Script for Threads Automation Tool
Combines all utility scripts into one with menu
"""

import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Setup path using common utility
from scripts.common import setup_path, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()

# Import functions directly from original scripts
from scripts.utility.view_metrics import view_account_metrics, view_thread_metrics
from scripts.utility.fetch_all_metrics import verify_username, get_threads_to_fetch, fetch_all_metrics
from scripts.utility.check_browser_profile import check_browser_profile
from scripts.utility.cleanup_old_logs import cleanup_old_logs, show_log_stats, parse_size
from scripts.utility.init_default_data import init_default_config, init_default_selectors
from scripts.utility.fix_account_username import list_accounts, check_account, set_username
from scripts.utility.sync_jobs_from_logs import parse_logs_for_completed_jobs, sync_jobs_from_logs
from scripts.utility.find_next_button import find_next_button
from scripts.utility.archive_old_jobs import archive_old_jobs
from scripts.utility.validate_job_json import validate_with_schema
from scripts.utility.remove_duplicate_jobs import remove_duplicates
from scripts.utility.kill_port_8000 import find_processes_on_port, kill_process, main as kill_port_main


def show_menu():
    """Show utility menu."""
    print()
    print("=" * 60)
    print("UTILITY SCRIPTS MENU")
    print("=" * 60)
    print()
    print("1. View Metrics")
    print("2. Fetch All Metrics")
    print("3. Check Browser Profile")
    print("4. Cleanup Old Logs")
    print("5. Init Default Data")
    print("6. Fix Account Username")
    print("7. Sync Jobs From Logs")
    print("8. Find Next Button")
    print("9. Archive Old Jobs")
    print("10. Validate Job JSON")
    print("11. Remove Duplicate Jobs")
    print("12. Kill Port 8000")
    print()
    print("0. Exit")
    print()
    choice = input("Chọn option (0-12): ").strip()
    return choice


# ============================================================================
# WRAPPER FUNCTIONS - Call imported functions directly
# ============================================================================

def run_view_metrics(account_id: str = None, thread_id: str = None):
    """Run view_metrics."""
    try:
        if thread_id:
            view_thread_metrics(thread_id, account_id)
        else:
            if not account_id:
                account_id = input("Enter account_id: ").strip()
                if not account_id:
                    print("❌ Account ID required")
                    return False
            view_account_metrics(account_id)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_fetch_all_metrics(account_id: str = None, force: bool = False, limit: int = None):
    """Run fetch_all_metrics."""
    try:
        if not account_id:
            account_id = input("Enter account_id: ").strip()
            if not account_id:
                print("❌ Account ID required")
                return False
        
        print_header("")
        print(f"🔄 FETCH METRICS CHO TOÀN BỘ THREADS")
        print_header("")
        print(f"📋 Account ID: {account_id}")
        print(f"📋 Force mode: {'Có' if force else 'Không'}")
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
                print(f"   python scripts/utility/utility.py --fix-username {account_id} your_username")
                return False
        
        print_header("")
        
        # Step 2: Get threads to fetch
        print("📋 Step 2: Lấy danh sách threads cần fetch...")
        thread_ids = get_threads_to_fetch(account_id, force=force)
        
        if not thread_ids:
            print("✅ Không có threads nào cần fetch!")
            return True
        
        print_header("")
        
        # Step 3: Confirm
        print(f"⚠️  SẮP FETCH METRICS CHO {len(thread_ids)} THREADS")
        if limit:
            print(f"⚠️  (Giới hạn: {limit} threads)")
        print(f"")
        print(f"⏱️  Ước tính thời gian: ~{len(thread_ids) * 7} giây ({len(thread_ids) * 7 / 60:.1f} phút)")
        print(f"")
        
        response = input("Tiếp tục? (y/n): ")
        if response.lower() != 'y':
            print("❌ Đã hủy")
            return False
        
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
            
            if summary["success"] > 0:
                print(f"✅ Đã fetch thành công {summary['success']} threads")
            if summary["failed"] > 0:
                print(f"❌ {summary['failed']} threads thất bại")
            if summary.get("cached", 0) > 0:
                print(f"⏭️  {summary['cached']} threads đã có recent metrics (skipped)")
            
            return True
        except KeyboardInterrupt:
            print("\n\n⚠️  Đã dừng bởi user (Ctrl+C)")
            return False
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            loop.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_check_browser_profile(account_id: str = None):
    """Run check_browser_profile."""
    try:
        if not account_id:
            account_id = input("Enter account_id: ").strip()
            if not account_id:
                print("❌ Account ID required")
                return False
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_browser_profile(account_id))
            return True
        except KeyboardInterrupt:
            print("\n\n⚠️  Đã dừng bởi user (Ctrl+C)")
            return False
        finally:
            loop.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_cleanup_old_logs(days: int = None, dry_run: bool = False, min_size: str = None):
    """Run cleanup_old_logs."""
    try:
        logs_dir = Path("./logs")
        if not logs_dir.exists():
            print(f"❌ Thư mục không tồn tại: {logs_dir}")
            return False
        
        if days is None:
            days = 30
        
        min_size_bytes = parse_size(min_size) if min_size else 0
        
        # Show stats
        show_log_stats(logs_dir)
        print()
        
        if dry_run:
            print_header("🔍 DRY RUN MODE - Không thực sự xóa logs")
            print()
        
        # Cleanup
        cleanup_old_logs(
            logs_dir=logs_dir,
            days=days,
            min_size=min_size_bytes,
            dry_run=dry_run
        )
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_init_default_data(mysql_password: str = None):
    """Run init_default_data."""
    try:
        if not mysql_password:
            mysql_password = input("Enter MySQL password: ").strip()
            if not mysql_password:
                print("❌ MySQL password required")
                return False
        
        print("🔄 Initialize Default Data: Config & Selectors")
        print_header("", width=60)
        
        success_config = init_default_config(mysql_password)
        success_selectors = init_default_selectors(mysql_password)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Summary")
        print_header("", width=60)
        print(f"Config: {'✅ Success' if success_config else '❌ Failed'}")
        print(f"Selectors: {'✅ Success' if success_selectors else '❌ Failed'}")
        
        if success_config and success_selectors:
            print("\n✅ All default data initialized successfully!")
            return True
        else:
            print("\n⚠️  Some operations failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_fix_account_username(account_id: str = None, username: str = None):
    """Run fix_account_username."""
    try:
        if not account_id:
            # List all accounts
            list_accounts()
        elif not username:
            # Check one account
            check_account(account_id)
        else:
            # Set username
            if username.startswith('@'):
                username = username[1:]
            set_username(account_id, username)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_sync_jobs_from_logs(dry_run: bool = False, log_file: str = None):
    """Run sync_jobs_from_logs."""
    try:
        from services.scheduler import Scheduler, JobStatus
        from scripts.common import get_logger
        
        if not log_file:
            log_file = "./logs/scheduler_20251225.log"
        
        log_file_path = Path(log_file)
        
        print_header("🔄 SYNC JOBS TỪ LOGS")
        print()
        
        # Parse logs
        completed_jobs_from_logs = parse_logs_for_completed_jobs(log_file_path)
        
        if not completed_jobs_from_logs:
            print("\n⚠️  Không tìm thấy jobs completed trong logs")
            return False
        
        print(f"\n📊 Tìm thấy {len(completed_jobs_from_logs)} jobs đã completed trong logs:")
        for job_id, info in list(completed_jobs_from_logs.items())[:5]:
            print(f"   - {job_id[:8]}... thread_id: {info.get('thread_id', 'N/A')}")
        if len(completed_jobs_from_logs) > 5:
            print(f"   ... và {len(completed_jobs_from_logs) - 5} jobs khác")
        
        # Load scheduler
        jobs_dir = Path("./jobs")
        print(f"\n📂 Đang load jobs từ {jobs_dir}...")
        logger = get_logger("sync_jobs")
        scheduler = Scheduler(storage_dir=jobs_dir, logger=logger)
        
        all_jobs = scheduler.list_jobs()
        print(f"   ✅ Đã load {len(all_jobs)} jobs")
        
        # Sync
        stats = sync_jobs_from_logs(scheduler, completed_jobs_from_logs, dry_run=dry_run)
        
        # Summary
        print_header("📊 TỔNG KẾT")
        print(f"✅ Updated: {stats['updated']}")
        print(f"⏭️  Skipped: {stats['skipped']}")
        print(f"❌ Errors: {stats['errors']}")
        
        if dry_run:
            print("\n💡 Để thực sự update, chạy lại không có --dry-run")
        else:
            print("\n✅ Sync hoàn tất!")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_find_next_button():
    """Run find_next_button."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(find_next_button())
            return True
        except KeyboardInterrupt:
            print("\n\n⚠️  Đã dừng bởi user (Ctrl+C)")
            return False
        finally:
            loop.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_archive_old_jobs(days: int = None, dry_run: bool = False):
    """Run archive_old_jobs."""
    try:
        jobs_dir = Path("./jobs")
        archive_dir = Path("./jobs/archive")
        
        if not jobs_dir.exists():
            print(f"❌ Thư mục không tồn tại: {jobs_dir}")
            return False
        
        if days is None:
            days = 30
        
        if dry_run:
            print("🔍 DRY RUN MODE - Không thực sự archive jobs")
            print()
        
        archive_old_jobs(
            jobs_dir=jobs_dir,
            archive_dir=archive_dir,
            days=days,
            dry_run=dry_run
        )
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_validate_job_json(json_file: str = None, schema: str = None):
    """Run validate_job_json."""
    try:
        import json
        
        if not json_file:
            json_file = input("Enter JSON file path: ").strip()
            if not json_file:
                print("❌ JSON file required")
                return False
        
        json_file_path = Path(json_file)
        if not json_file_path.exists():
            print(f"❌ JSON file không tồn tại: {json_file_path}")
            return False
        
        if not schema:
            schema = Path(__file__).parent.parent / 'schemas' / 'job_schema.json'
        else:
            schema = Path(schema)
        
        if not schema.exists():
            print(f"❌ Schema file không tồn tại: {schema}")
            return False
        
        # Load schema
        with open(schema, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # Load JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Validate
        if isinstance(json_data, list):
            # Batch validation
            print(f"📋 Validating {len(json_data)} jobs...")
            all_valid = True
            for i, job in enumerate(json_data):
                is_valid, errors = validate_with_schema(job, schema_data)
                if not is_valid:
                    all_valid = False
                    print(f"\n❌ Job {i+1} có lỗi:")
                    for error in errors:
                        print(f"   - {error}")
                else:
                    print(f"✅ Job {i+1} hợp lệ")
            
            if all_valid:
                print(f"\n✅ Tất cả {len(json_data)} jobs đều hợp lệ!")
                return True
            else:
                return False
        else:
            # Single job validation
            is_valid, errors = validate_with_schema(json_data, schema_data)
            
            if is_valid:
                print("✅ JSON file hợp lệ!")
                return True
            else:
                print("❌ JSON file có lỗi:")
                for error in errors:
                    print(f"   - {error}")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_remove_duplicate_jobs(dry_run: bool = False):
    """Run remove_duplicate_jobs."""
    try:
        jobs_dir = Path("./jobs")
        
        if not jobs_dir.exists():
            print(f"❌ Thư mục không tồn tại: {jobs_dir}")
            return False
        
        if dry_run:
            print("🔍 DRY RUN MODE - Không thực sự xóa jobs")
            print()
        
        remove_duplicates(jobs_dir, dry_run=dry_run)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified Utility Script")
    parser.add_argument('--view-metrics', type=str, nargs='?', const='', help='View metrics (account_id)')
    parser.add_argument('--thread-id', type=str, help='Thread ID for view metrics')
    parser.add_argument('--fetch-metrics', type=str, nargs='?', const='', help='Fetch all metrics (account_id)')
    parser.add_argument('--force', action='store_true', help='Force fetch metrics')
    parser.add_argument('--limit', type=int, help='Limit for fetch metrics')
    parser.add_argument('--check-profile', type=str, nargs='?', const='', help='Check browser profile (account_id)')
    parser.add_argument('--cleanup-logs', action='store_true', help='Cleanup old logs')
    parser.add_argument('--days', type=int, help='Days for cleanup logs')
    parser.add_argument('--min-size', type=str, help='Min size for cleanup logs')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--init-data', action='store_true', help='Init default data')
    parser.add_argument('--mysql-password', type=str, help='MySQL password')
    parser.add_argument('--fix-username', type=str, nargs='?', const='', help='Fix account username (account_id)')
    parser.add_argument('--username', type=str, help='Username for fix account')
    parser.add_argument('--sync-jobs', action='store_true', help='Sync jobs from logs')
    parser.add_argument('--log-file', type=str, help='Log file for sync jobs')
    parser.add_argument('--find-button', action='store_true', help='Find next button')
    parser.add_argument('--archive-jobs', action='store_true', help='Archive old jobs')
    parser.add_argument('--validate-json', type=str, help='Validate job JSON (file path)')
    parser.add_argument('--schema', type=str, help='Schema file for validate')
    parser.add_argument('--remove-duplicates', action='store_true', help='Remove duplicate jobs')
    parser.add_argument('--kill-port', action='store_true', help='Kill port 8000')
    
    args = parser.parse_args()
    
    # If command provided, run directly
    if args.view_metrics is not None:
        run_view_metrics(args.view_metrics or None, args.thread_id)
        return
    
    if args.fetch_metrics is not None:
        run_fetch_all_metrics(args.fetch_metrics or None, args.force, args.limit)
        return
    
    if args.check_profile is not None:
        run_check_browser_profile(args.check_profile or None)
        return
    
    if args.cleanup_logs:
        run_cleanup_old_logs(args.days, args.dry_run, args.min_size)
        return
    
    if args.init_data:
        run_init_default_data(args.mysql_password)
        return
    
    if args.fix_username is not None:
        run_fix_account_username(args.fix_username or None, args.username)
        return
    
    if args.sync_jobs:
        run_sync_jobs_from_logs(args.dry_run, args.log_file)
        return
    
    if args.find_button:
        run_find_next_button()
        return
    
    if args.archive_jobs:
        run_archive_old_jobs(args.days, args.dry_run)
        return
    
    if args.validate_json:
        run_validate_job_json(args.validate_json, args.schema)
        return
    
    if args.remove_duplicates:
        run_remove_duplicate_jobs(args.dry_run)
        return
    
    if args.kill_port:
        kill_port_main()
        return
    
    # Otherwise show menu
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            account_id = input("Enter account_id (optional, press Enter to list all): ").strip() or None
            thread_id = input("Enter thread_id (optional): ").strip() or None
            run_view_metrics(account_id, thread_id)
        elif choice == "2":
            account_id = input("Enter account_id: ").strip()
            force = input("Force fetch? (y/n): ").strip().lower() == 'y'
            limit = input("Limit (optional): ").strip()
            limit = int(limit) if limit.isdigit() else None
            run_fetch_all_metrics(account_id, force, limit)
        elif choice == "3":
            account_id = input("Enter account_id: ").strip()
            run_check_browser_profile(account_id)
        elif choice == "4":
            days = input("Days (default 30): ").strip()
            days = int(days) if days.isdigit() else 30
            dry_run = input("Dry run? (y/n): ").strip().lower() == 'y'
            min_size = input("Min size (optional, e.g. 10M): ").strip() or None
            run_cleanup_old_logs(days, dry_run, min_size)
        elif choice == "5":
            mysql_password = input("Enter MySQL password: ").strip()
            run_init_default_data(mysql_password)
        elif choice == "6":
            account_id = input("Enter account_id (or press Enter to list all): ").strip() or None
            username = input("Enter username (optional): ").strip() or None
            run_fix_account_username(account_id, username)
        elif choice == "7":
            dry_run = input("Dry run? (y/n): ").strip().lower() == 'y'
            log_file = input("Log file (optional): ").strip() or None
            run_sync_jobs_from_logs(dry_run, log_file)
        elif choice == "8":
            run_find_next_button()
        elif choice == "9":
            days = input("Days (default 30): ").strip()
            days = int(days) if days.isdigit() else 30
            dry_run = input("Dry run? (y/n): ").strip().lower() == 'y'
            run_archive_old_jobs(days, dry_run)
        elif choice == "10":
            json_file = input("Enter JSON file path: ").strip()
            schema = input("Schema file (optional): ").strip() or None
            run_validate_job_json(json_file, schema)
        elif choice == "11":
            dry_run = input("Dry run? (y/n): ").strip().lower() == 'y'
            run_remove_duplicate_jobs(dry_run)
        elif choice == "12":
            kill_port_main()
        else:
            print("❌ Invalid option. Please choose 0-12.")
        
        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
