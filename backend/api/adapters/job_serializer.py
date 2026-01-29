"""
Job serialization helpers for UI APIs.

Tách logic chuyển đổi `ScheduledJob` → dict khỏi `JobsAPI`
để giảm trách nhiệm của lớp API và dễ tái sử dụng.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from services.scheduler.models import Platform
from utils.sanitize import sanitize_error
from utils.datetime import format_datetime_vn


def _dt_to_str(value: Any) -> Optional[str]:
    """
    Convert datetime to ISO string (legacy, kept for backward compatibility).
    For new code, use _dt_to_str_vn instead.
    """
    if not value:
        return None
    try:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)
    except Exception:
        return str(value) if value else None


def _dt_to_str_vn(value: Any) -> Optional[str]:
    """
    Convert datetime to Vietnam timezone formatted string (dd/MM/yyyy HH:mm:ss).
    """
    if not value:
        return None
    try:
        if hasattr(value, "isoformat") or isinstance(value, datetime):
            return format_datetime_vn(value)
        return str(value)
    except Exception:
        return str(value) if value else None


def _enum_to_value(value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        return value.value if hasattr(value, "value") else str(value)
    except Exception:
        return str(value)


def _calculate_running_duration(job: Any, started_at: Any) -> Optional[Dict[str, Any]]:
    try:
        status = getattr(job, "status", None)
        if status and getattr(status, "value", None) == "running" and started_at:
            duration = datetime.now() - started_at
            return {
                "total_seconds": int(duration.total_seconds()),
                "minutes": int(duration.total_seconds() / 60),
                "formatted": f"{int(duration.total_seconds() / 60)}m {int(duration.total_seconds() % 60)}s",
            }
    except (AttributeError, TypeError, ValueError):
        pass
    return None


def serialize_job(job: Any) -> Dict[str, Any]:
    """
    Convert ScheduledJob-like object to dict for UI.

    Args:
        job: ScheduledJob object (hoặc object có fields tương tự)

    Returns:
        Dict representation với full content và preview.
    """
    started_at = getattr(job, "started_at", None)
    running_duration = _calculate_running_duration(job, started_at)

    # Safely get job fields
    job_id = getattr(job, "job_id", "N/A")
    account_id = getattr(job, "account_id", "N/A")
    content = getattr(job, "content", "")
    scheduled_time = getattr(job, "scheduled_time", None)
    status = getattr(job, "status", None)
    status_message = getattr(job, "status_message", None)
    thread_id = getattr(job, "thread_id", None)
    error = getattr(job, "error", None)
    priority = getattr(job, "priority", None)
    platform = getattr(job, "platform", Platform.THREADS)
    retry_count = getattr(job, "retry_count", 0)
    created_at = getattr(job, "created_at", None)
    completed_at = getattr(job, "completed_at", None)

    # Format content safely - trả về content thực tế cho UI
    # CHỈ sanitize trong logs, KHÔNG sanitize trong API responses
    if content and isinstance(content, str) and len(content) > 0:
        content_preview = content[:100] + "..." if len(content) > 100 else content
        content_full = content
    else:
        content_preview = ''
        content_full = ''

    # Sanitize error nếu có (error messages vẫn cần sanitize)
    sanitized_error = sanitize_error(error) if error else None

    # Format datetime fields using Vietnam timezone
    scheduled_time_str = _dt_to_str_vn(scheduled_time)
    created_at_str = _dt_to_str_vn(created_at)
    started_at_str = _dt_to_str_vn(started_at)
    completed_at_str = _dt_to_str_vn(completed_at)

    status_value = _enum_to_value(status)
    priority_value = _enum_to_value(priority)
    platform_value = _enum_to_value(platform) or Platform.THREADS.value

    return {
        "job_id": job_id,
        "account_id": account_id,
        "content": content_preview,
        "content_full": content_full,
        "scheduled_time": scheduled_time_str,
        "status": status_value,
        "status_message": status_message,
        "thread_id": thread_id,
        "error": sanitized_error,
        "priority": priority_value,
        "platform": platform_value,
        "retry_count": retry_count,
        "created_at": created_at_str,
        "started_at": started_at_str,
        "completed_at": completed_at_str,
        "running_duration": running_duration,
    }
