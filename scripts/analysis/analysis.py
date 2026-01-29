#!/usr/bin/env python3
"""
Unified Analysis Script for Threads Automation Tool
Combines all analysis scripts into one with menu
"""

import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

# Setup path using common utility
from scripts.common import setup_path, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()


def show_menu():
    """Show analysis menu."""
    print()
    print("=" * 60)
    print("ANALYSIS SCRIPTS MENU")
    print("=" * 60)
    print()
    print("1. Analyze Jobs")
    print("2. Analyze Next Button Logs")
    print()
    print("0. Exit")
    print()
    choice = input("Chọn option (0-2): ").strip()
    return choice


# ============================================================================
# ANALYZE JOBS
# ============================================================================

def analyze_jobs(jobs_dir: Path) -> Dict[str, Any]:
    """Phân tích jobs và trả về statistics."""
    stats = {
        'total_files': 0,
        'total_jobs': 0,
        'jobs_by_status': defaultdict(int),
        'jobs_by_date': defaultdict(int),
        'oldest_job': None,
        'newest_job': None,
        'total_size_mb': 0.0,
        'completed_jobs': [],
        'failed_jobs': [],
        'scheduled_jobs': [],
        'duplicate_content': []
    }
    
    job_files = sorted(jobs_dir.glob("jobs_*.json"))
    stats['total_files'] = len(job_files)
    
    all_jobs = []
    content_map = defaultdict(list)  # content -> [job_ids]
    
    for job_file in job_files:
        try:
            file_size = job_file.stat().st_size
            stats['total_size_mb'] += file_size / (1024 * 1024)
            
            with open(job_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs = data.get('jobs', [])
                stats['total_jobs'] += len(jobs)
                
                # Extract date từ filename
                date_str = job_file.stem.replace("jobs_", "")
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    stats['jobs_by_date'][date_str] = len(jobs)
                except ValueError:
                    pass
                
                for job in jobs:
                    all_jobs.append(job)
                    status = job.get('status', 'unknown')
                    stats['jobs_by_status'][status] += 1
                    
                    # Track content để tìm duplicate
                    content = job.get('content', '').strip()
                    if content:
                        content_map[content].append({
                            'job_id': job.get('job_id'),
                            'status': status,
                            'date': date_str
                        })
                    
                    # Track completed jobs
                    if status == 'completed':
                        completed_at = job.get('completed_at')
                        if completed_at:
                            try:
                                completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                                stats['completed_jobs'].append({
                                    'job_id': job.get('job_id'),
                                    'completed_at': completed_at,
                                    'date': completed_dt.strftime('%Y-%m-%d'),
                                    'file': date_str
                                })
                            except:
                                pass
                    
                    # Track oldest/newest
                    created_at = job.get('created_at')
                    if created_at:
                        try:
                            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            if stats['oldest_job'] is None or created_dt < stats['oldest_job']:
                                stats['oldest_job'] = created_dt
                            if stats['newest_job'] is None or created_dt > stats['newest_job']:
                                stats['newest_job'] = created_dt
                        except:
                            pass
        
        except Exception as e:
            print(f"⚠️  Lỗi đọc file {job_file.name}: {str(e)}")
    
    # Tìm duplicate content
    for content, job_list in content_map.items():
        if len(job_list) > 1:
            stats['duplicate_content'].append({
                'content_preview': content[:50] + "..." if len(content) > 50 else content,
                'count': len(job_list),
                'jobs': job_list
            })
    
    # Sort completed jobs by date
    stats['completed_jobs'].sort(key=lambda x: x.get('completed_at', ''))
    
    return stats


def suggest_actions(stats: Dict[str, Any], archive_days: int = 30) -> List[Dict[str, Any]]:
    """Đề xuất các hành động xử lý jobs."""
    suggestions = []
    now = datetime.now()
    
    # 1. Archive old completed jobs
    old_completed = [
        j for j in stats['completed_jobs']
        if j.get('completed_at')
    ]
    if old_completed:
        try:
            oldest_completed = datetime.fromisoformat(old_completed[0]['completed_at'].replace('Z', '+00:00'))
            days_old = (now - oldest_completed).days
            if days_old > archive_days:
                suggestions.append({
                    'action': 'archive_old_completed',
                    'priority': 'high',
                    'description': f'Archive {len(old_completed)} completed jobs cũ hơn {archive_days} ngày',
                    'count': len(old_completed),
                    'days_old': days_old
                })
        except:
            pass
    
    # 2. Remove duplicate content
    if stats['duplicate_content']:
        total_duplicates = sum(d['count'] - 1 for d in stats['duplicate_content'])
        suggestions.append({
            'action': 'remove_duplicates',
            'priority': 'medium',
            'description': f'Xóa {total_duplicates} jobs duplicate content',
            'count': total_duplicates,
            'duplicate_groups': len(stats['duplicate_content'])
        })
    
    # 3. Merge small files
    small_files = [
        (date, count) for date, count in stats['jobs_by_date'].items()
        if count < 10
    ]
    if len(small_files) > 3:
        suggestions.append({
            'action': 'merge_small_files',
            'priority': 'low',
            'description': f'Merge {len(small_files)} files nhỏ (< 10 jobs)',
            'count': len(small_files)
        })
    
    # 4. Cleanup empty files
    empty_files = [
        date for date, count in stats['jobs_by_date'].items()
        if count == 0
    ]
    if empty_files:
        suggestions.append({
            'action': 'cleanup_empty_files',
            'priority': 'high',
            'description': f'Xóa {len(empty_files)} files rỗng',
            'count': len(empty_files)
        })
    
    # 5. Optimize storage (nếu quá lớn)
    if stats['total_size_mb'] > 10:
        suggestions.append({
            'action': 'optimize_storage',
            'priority': 'medium',
            'description': f'Storage hiện tại: {stats["total_size_mb"]:.2f} MB - nên archive jobs cũ',
            'size_mb': stats['total_size_mb']
        })
    
    return suggestions


def print_jobs_report(stats: Dict[str, Any], suggestions: List[Dict[str, Any]]):
    """In báo cáo phân tích jobs."""
    print_header("📊 PHÂN TÍCH JOBS", width=60)
    print()
    
    print("📁 Tổng quan:")
    print(f"   - Tổng số files: {stats['total_files']}")
    print(f"   - Tổng số jobs: {stats['total_jobs']}")
    print(f"   - Tổng dung lượng: {stats['total_size_mb']:.2f} MB")
    print()
    
    print("📊 Jobs theo status:")
    for status, count in sorted(stats['jobs_by_status'].items()):
        percentage = (count / stats['total_jobs'] * 100) if stats['total_jobs'] > 0 else 0
        print(f"   - {status:15s}: {count:5d} ({percentage:5.1f}%)")
    print()
    
    if stats['oldest_job'] and stats['newest_job']:
        print("📅 Thời gian:")
        print(f"   - Job cũ nhất: {stats['oldest_job'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   - Job mới nhất: {stats['newest_job'].strftime('%Y-%m-%d %H:%M:%S')}")
        days_span = (stats['newest_job'] - stats['oldest_job']).days
        print(f"   - Khoảng thời gian: {days_span} ngày")
        print()
    
    if stats['duplicate_content']:
        print(f"⚠️  Duplicate content: {len(stats['duplicate_content'])} nhóm")
        for dup in stats['duplicate_content'][:5]:  # Show first 5
            print(f"   - '{dup['content_preview']}': {dup['count']} jobs")
        if len(stats['duplicate_content']) > 5:
            print(f"   ... và {len(stats['duplicate_content']) - 5} nhóm khác")
        print()
    
    print_header("💡 ĐỀ XUẤT HÀNH ĐỘNG", width=60)
    print()
    
    if not suggestions:
        print("✅ Không có hành động nào cần thiết. Jobs đang được quản lý tốt!")
        return
    
    for i, suggestion in enumerate(suggestions, 1):
        priority_icon = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }.get(suggestion['priority'], '⚪')
        
        print(f"{i}. {priority_icon} {suggestion['description']}")
        if 'count' in suggestion:
            print(f"   → Sẽ xử lý: {suggestion['count']} items")
        if 'days_old' in suggestion:
            print(f"   → Jobs cũ: {suggestion['days_old']} ngày")
        if 'size_mb' in suggestion:
            print(f"   → Dung lượng: {suggestion['size_mb']:.2f} MB")
        print()
    
    print_header("📝 HƯỚNG DẪN", width=60)
    print()
    print("1. Archive old completed jobs:")
    print("   python scripts/utility/archive_old_jobs.py --days 30")
    print()
    print("2. Remove duplicate content:")
    print("   python scripts/utility/remove_duplicate_jobs.py --jobs-dir jobs/")
    print()
    print("3. Merge small files:")
    print("   python scripts/utility/sync_jobs_from_logs.py")
    print()
    print("4. Cleanup empty files:")
    print("   python scripts/utility/cleanup_old_logs.py")


def run_analyze_jobs(jobs_dir: str = "jobs/", archive_days: int = 30):
    """Run analyze jobs."""
    jobs_path = Path(jobs_dir)
    if not jobs_path.exists():
        print(f"❌ Thư mục không tồn tại: {jobs_path}")
        return
    
    print("🔄 Đang phân tích jobs...")
    print()
    
    stats = analyze_jobs(jobs_path)
    suggestions = suggest_actions(stats, archive_days)
    
    print_jobs_report(stats, suggestions)


# ============================================================================
# ANALYZE NEXT BUTTON LOGS
# ============================================================================

def analyze_next_button_logs(log_file_path: str = None):
    """Phân tích log để xem nút 'Tiếp' hoạt động."""
    
    if log_file_path is None:
        # Tìm log file mới nhất
        log_dir = Path("logs")
        log_files = list(log_dir.glob("facebook_composer_*.log"))
        if not log_files:
            print("❌ Không tìm thấy log file facebook_composer_*.log")
            return
        
        log_file_path = max(log_files, key=lambda p: p.stat().st_mtime)
        print(f"📄 Đang phân tích: {log_file_path}")
    else:
        log_file_path = Path(log_file_path)
    
    if not log_file_path.exists():
        print(f"❌ File không tồn tại: {log_file_path}")
        return
    
    print_header("PHÂN TÍCH LOG NÚT 'TIẾP'")
    
    # Đọc log file
    with open(log_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Tìm các log liên quan đến nút "Tiếp"
    next_button_logs = []
    for line in lines:
        if "CLICK_NEXT_BUTTON" in line or "FIND_NEXT_BUTTON" in line:
            next_button_logs.append(line.strip())
    
    if not next_button_logs:
        print("\n❌ Không tìm thấy log nào về nút 'Tiếp'")
        return
    
    print(f"\n📊 Tìm thấy {len(next_button_logs)} log entries về nút 'Tiếp'\n")
    
    # Phân tích từng session (mỗi lần post)
    sessions = []
    current_session = []
    
    for log_line in next_button_logs:
        if "CLICK_NEXT_BUTTON.*IN_PROGRESS" in log_line or "Looking for 'Tiếp'" in log_line:
            if current_session:
                sessions.append(current_session)
            current_session = [log_line]
        else:
            if current_session:
                current_session.append(log_line)
    
    if current_session:
        sessions.append(current_session)
    
    print(f"📋 Tìm thấy {len(sessions)} session(s) (lần thử click nút 'Tiếp')\n")
    
    # Phân tích từng session
    for i, session in enumerate(sessions, 1):
        print_header(f"SESSION {i}")
        
        # Tìm method được dùng
        method = None
        button_name = None
        result = None
        
        for log_line in session:
            # Extract thông tin từ log
            if "METHOD=getByRole" in log_line:
                method = "getByRole (Playwright best practice)"
            elif "METHOD=javascript_click" in log_line:
                method = "JavaScript click"
            elif "METHOD=playwright_click_with_offset" in log_line:
                method = "Playwright click with offset"
            elif "METHOD=direct_click" in log_line:
                method = "Direct click"
            
            if "BUTTON_NAME=" in log_line:
                match = re.search(r"BUTTON_NAME=([^\s]+)", log_line)
                if match:
                    button_name = match.group(1)
            
            if "RESULT=SUCCESS" in log_line and "CLICK_NEXT_BUTTON" in log_line:
                result = "SUCCESS"
            elif "RESULT=FAILED" in log_line or "RESULT=WARNING" in log_line:
                if result != "SUCCESS":
                    result = "FAILED"
        
        # In summary
        print(f"\n📌 Summary:")
        if method:
            print(f"   Method: {method}")
        if button_name:
            print(f"   Button Name: {button_name}")
        if result:
            print(f"   Result: {result}")
        
        # In chi tiết từng bước
        print(f"\n📝 Chi tiết các bước:")
        for log_line in session:
            # Extract timestamp
            timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", log_line)
            timestamp = timestamp_match.group(1) if timestamp_match else ""
            
            # Extract step
            step_match = re.search(r"STEP=([^\s]+)", log_line)
            step = step_match.group(1) if step_match else ""
            
            # Extract result
            result_match = re.search(r"RESULT=([^\s]+)", log_line)
            result_val = result_match.group(1) if result_match else ""
            
            # Extract note
            note_match = re.search(r"NOTE=([^\|]+)", log_line)
            note = note_match.group(1).strip() if note_match else ""
            
            # Extract error nếu có
            error_match = re.search(r"ERROR=([^\|]+)", log_line)
            error = error_match.group(1).strip() if error_match else ""
            
            # Extract selector/button_name
            selector_match = re.search(r"SELECTOR=([^\s]+)", log_line)
            selector = selector_match.group(1) if selector_match else ""
            
            button_name_match = re.search(r"BUTTON_NAME=([^\s]+)", log_line)
            button_name_val = button_name_match.group(1) if button_name_match else ""
            
            # Format output
            status_icon = "✅" if result_val == "SUCCESS" else "❌" if result_val == "FAILED" else "⚠️" if result_val == "WARNING" else "🔄"
            
            print(f"\n   {status_icon} [{timestamp}] {step} - {result_val}")
            if note:
                print(f"      Note: {note}")
            if selector:
                print(f"      Selector: {selector[:80]}...")
            if button_name_val:
                print(f"      Button Name: {button_name_val}")
            if error:
                print(f"      Error: {error[:100]}...")
    
    # Thống kê tổng hợp
    print_header("THỐNG KÊ TỔNG HỢP")
    print()
    
    success_count = sum(1 for s in sessions if any("RESULT=SUCCESS" in line and "CLICK_NEXT_BUTTON" in line for line in s))
    failed_count = len(sessions) - success_count
    
    print(f"✅ Thành công: {success_count}/{len(sessions)} session(s)")
    print(f"❌ Thất bại: {failed_count}/{len(sessions)} session(s)")
    
    # Phân tích method được dùng
    methods_used = defaultdict(int)
    for session in sessions:
        for log_line in session:
            if "METHOD=getByRole" in log_line:
                methods_used["getByRole"] += 1
                break
            elif "METHOD=javascript_click" in log_line:
                methods_used["JavaScript click"] += 1
                break
            elif "METHOD=playwright_click_with_offset" in log_line:
                methods_used["Playwright click with offset"] += 1
                break
            elif "METHOD=direct_click" in log_line:
                methods_used["Direct click"] += 1
                break
    
    if methods_used:
        print(f"\n📊 Methods được sử dụng:")
        for method, count in methods_used.items():
            print(f"   - {method}: {count} lần")
    
    print()


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified Analysis Script")
    parser.add_argument('--analyze-jobs', action='store_true', help='Analyze jobs')
    parser.add_argument('--jobs-dir', type=str, default='jobs/', help='Jobs directory')
    parser.add_argument('--archive-days', type=int, default=30, help='Archive days threshold')
    parser.add_argument('--analyze-logs', type=str, nargs='?', const=None, help='Analyze next button logs (optional log file path)')
    
    args = parser.parse_args()
    
    # If command provided, run directly
    if args.analyze_jobs:
        run_analyze_jobs(args.jobs_dir, args.archive_days)
        return
    
    if args.analyze_logs is not None:
        analyze_next_button_logs(args.analyze_logs)
        return
    
    # Otherwise show menu
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            jobs_dir = input("Enter jobs directory (default: jobs/): ").strip() or "jobs/"
            archive_days = input("Enter archive days threshold (default: 30): ").strip()
            archive_days = int(archive_days) if archive_days.isdigit() else 30
            run_analyze_jobs(jobs_dir, archive_days)
        elif choice == "2":
            log_file = input("Enter log file path (press Enter for latest): ").strip() or None
            analyze_next_button_logs(log_file)
        else:
            print("❌ Invalid option. Please choose 0-2.")
        
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
