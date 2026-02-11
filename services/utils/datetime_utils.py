"""
Module: services/utils/datetime_utils.py

Datetime utility functions for timezone normalization.

TIMEZONE STRATEGY (simple):
- All user input (Excel, forms) is in Vietnam time (UTC+7)
- All datetimes stored in DB are UTC
- All API responses send ISO UTC strings
- Frontend converts UTC → VN for display

Functions:
- vn_to_utc(dt): Convert VN naive datetime → UTC aware datetime
- ensure_utc(dt): Ensure any datetime is UTC (aware or naive)
- utc_to_vn(dt): Convert UTC datetime → VN datetime for display
- get_utc_now(): Get current UTC time
- get_vn_now(): Get current VN time
"""

from datetime import datetime, timezone, timedelta

# Vietnam timezone constant (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))


def vn_to_utc(dt: datetime) -> datetime:
    """
    Convert a Vietnam time (UTC+7) datetime to UTC.

    - Naive datetime: assumed to be VN time, converts to UTC
    - Aware datetime with VN tz: converts to UTC
    - Already UTC: returns as-is

    This is the PRIMARY function for handling user input (Excel, forms).

    Args:
        dt: Datetime object (naive = assumed VN time)

    Returns:
        Timezone-aware UTC datetime

    Example:
        >>> vn_to_utc(datetime(2026, 2, 10, 10, 15, 0))
        datetime(2026, 2, 10, 3, 15, 0, tzinfo=timezone.utc)
    """
    if dt is None:
        raise ValueError("datetime cannot be None")

    if dt.tzinfo is not None and dt.tzinfo == timezone.utc:
        return dt

    if dt.tzinfo is not None:
        # Has timezone info, just convert to UTC
        return dt.astimezone(timezone.utc)

    # Naive datetime → treat as VN time
    return dt.replace(tzinfo=VIETNAM_TZ).astimezone(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is UTC-aware.

    - Naive datetime: assumed to be UTC (for DB values)
    - Aware datetime: converts to UTC

    This is for datetimes that are ALREADY in UTC (e.g., from DB).
    For user input, use vn_to_utc() instead.

    Args:
        dt: Datetime object

    Returns:
        Timezone-aware UTC datetime
    """
    if dt is None:
        raise ValueError("datetime cannot be None")

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def utc_to_vn(dt: datetime) -> datetime:
    """
    Convert UTC datetime to Vietnam timezone (UTC+7) for display.

    Args:
        dt: UTC datetime (naive or aware)

    Returns:
        Timezone-aware VN datetime
    """
    if dt is None:
        raise ValueError("datetime cannot be None")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(VIETNAM_TZ)


def format_vn(dt: datetime) -> str:
    """
    Format datetime as VN display string: dd/MM/yyyy HH:mm:ss

    Args:
        dt: Datetime (any timezone, will be converted to VN)

    Returns:
        Formatted string
    """
    if dt is None:
        return ""

    vn_dt = utc_to_vn(dt)
    return vn_dt.strftime("%d/%m/%Y %H:%M:%S")


def get_utc_now() -> datetime:
    """Get current time in UTC."""
    return datetime.now(timezone.utc)


def get_vn_now() -> datetime:
    """Get current time in Vietnam timezone."""
    return datetime.now(VIETNAM_TZ)


# Backward compatibility aliases
normalize_to_utc = vn_to_utc
get_vietnam_now = get_vn_now
