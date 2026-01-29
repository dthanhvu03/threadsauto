"""
Module: cli/parser.py

Argument parser setup cho CLI commands.
"""

import argparse
from typing import Any


def create_parser() -> argparse.ArgumentParser:
    """
    Tạo và cấu hình argument parser.
    
    Returns:
        ArgumentParser đã được cấu hình
    """
    parser = argparse.ArgumentParser(description="Threads Automation Tool")
    
    # Core arguments
    parser.add_argument(
        "--account",
        type=str,
        required=False,
        help="ID tài khoản (ví dụ: account_01)"
    )
    parser.add_argument(
        "--content",
        type=str,
        help="Nội dung thread cần đăng (bắt buộc nếu không dùng --scheduler)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="SAFE",
        choices=["SAFE", "FAST"],
        help="Chế độ chạy (mặc định: SAFE)"
    )
    
    # Scheduling arguments
    parser.add_argument(
        "--schedule",
        type=str,
        help="Thời gian lên lịch (format: YYYY-MM-DD HH:MM:SS, ví dụ: 2024-12-17 10:00:00)"
    )
    parser.add_argument(
        "--priority",
        type=str,
        default="NORMAL",
        choices=["LOW", "NORMAL", "HIGH", "URGENT"],
        help="Độ ưu tiên cho scheduled job (mặc định: NORMAL)"
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Chạy scheduler để xử lý các jobs đã lên lịch"
    )
    
    # Job management arguments
    parser.add_argument(
        "--list-jobs",
        action="store_true",
        help="Liệt kê các jobs đã lên lịch"
    )
    parser.add_argument(
        "--remove-job",
        type=str,
        help="Xóa job theo job_id"
    )
    parser.add_argument(
        "--reset-jobs",
        action="store_true",
        help="Reset tất cả jobs (xóa tất cả jobs đã lên lịch)"
    )
    parser.add_argument(
        "--reset-status",
        type=str,
        choices=["running", "failed", "expired"],
        help="Reset status của các jobs có status cụ thể về SCHEDULED"
    )
    parser.add_argument(
        "--delete-job-file",
        type=str,
        help="Xóa file job theo ngày (format: YYYY-MM-DD, ví dụ: 2025-12-17)"
    )
    parser.add_argument(
        "--reset-job-file",
        type=str,
        help="Reset file job về trạng thái mới - reset tất cả jobs trong file về SCHEDULED (format: YYYY-MM-DD)"
    )
    
    # Excel arguments
    parser.add_argument(
        "--excel",
        type=str,
        help="Đường dẫn đến file Excel chứa nội dung cần đăng"
    )
    parser.add_argument(
        "--create-template",
        type=str,
        help="Tạo file Excel template mẫu tại đường dẫn chỉ định"
    )
    
    return parser

