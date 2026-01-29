"""
Module: services/utils/datetime_utils.py

Datetime utility functions for timezone normalization.
Ensures consistent timezone-aware datetime handling across the codebase.

TIMEZONE STRATEGY:
- Tất cả datetime từ user input (Excel, form) được coi là giờ Việt Nam (UTC+7)
- Tất cả datetime được lưu trong database là UTC (best practice)
- Tất cả datetime được hiển thị cho user là giờ Việt Nam (UTC+7)
- normalize_to_utc() giả định naive datetime là UTC+7 và convert về UTC

Ví dụ:
- Excel có scheduled_time: "2026-01-27 11:39:00" (giờ VN)
- normalize_to_utc() convert thành: "2026-01-27 04:39:00 UTC"
- Lưu trong database: "2026-01-27 04:39:00 UTC"
- Hiển thị cho user: "27/01/2026 11:39:00" (giờ VN)
"""

from datetime import datetime, timezone, timedelta

# Vietnam timezone constant (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))


def normalize_to_utc(dt: datetime) -> datetime:
    """
    Normalize datetime to UTC timezone-aware datetime.
    
    Converts both timezone-naive and timezone-aware datetimes to UTC.
    - If datetime is timezone-naive: assumes it's in local timezone and converts to UTC
    - If datetime is timezone-aware: converts to UTC
    
    Args:
        dt: Datetime object (naive or aware)
    
    Returns:
        Timezone-aware datetime with UTC timezone
    
    Example:
        >>> from datetime import datetime, timezone, timedelta
        >>> naive = datetime(2024, 1, 1, 12, 0, 0)
        >>> utc_dt = normalize_to_utc(naive)
        >>> assert utc_dt.tzinfo == timezone.utc
        
        >>> aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=7)))
        >>> utc_dt = normalize_to_utc(aware)
        >>> assert utc_dt.tzinfo == timezone.utc
    """
    if dt is None:
        raise ValueError("datetime cannot be None")
    
    # If already UTC-aware, return as-is
    if dt.tzinfo == timezone.utc:
        return dt
    
    # If timezone-aware but not UTC, convert to UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
    
    # If timezone-naive, assume local timezone (UTC+7 for Vietnam) and convert to UTC
    # This is safer than assuming UTC directly, as it preserves the intended time
    # For Excel uploads, scheduled_time is typically in local time (UTC+7)
    dt_with_tz = dt.replace(tzinfo=VIETNAM_TZ)
    return dt_with_tz.astimezone(timezone.utc)


def get_vietnam_now() -> datetime:
    """
    Get current time in Vietnam timezone (UTC+7).
    
    Returns:
        Timezone-aware datetime with Vietnam timezone (UTC+7)
    """
    return datetime.now(VIETNAM_TZ)


def get_utc_now() -> datetime:
    """
    Get current time in UTC.
    
    Returns:
        Timezone-aware datetime with UTC timezone
    """
    return datetime.now(timezone.utc)
