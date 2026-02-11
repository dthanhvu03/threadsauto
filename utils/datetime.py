"""
Datetime formatting utilities for Vietnam timezone (UTC+7).

Simple approach:
- Input: UTC datetime from DB/model
- Output: VN-formatted string for display

Uses services.utils.datetime_utils as the single source of truth.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from services.utils.datetime_utils import VIETNAM_TZ


def to_vietnam_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert any datetime to Vietnam timezone (UTC+7).

    - Naive datetime: assumed UTC, converts to VN
    - Aware datetime: converts to VN

    Args:
        dt: Datetime object or None

    Returns:
        VN timezone datetime or None
    """
    if dt is None:
        return None

    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(VIETNAM_TZ)
    except (AttributeError, ValueError, TypeError):
        return None


def format_datetime_vn(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime to VN: dd/MM/yyyy HH:mm:ss

    Args:
        dt: Datetime (assumed UTC if naive)

    Returns:
        Formatted string or None
    """
    vn_dt = to_vietnam_timezone(dt)
    if vn_dt is None:
        return None

    try:
        return vn_dt.strftime("%d/%m/%Y %H:%M:%S")
    except (AttributeError, ValueError):
        return None


def format_date_vn(dt: Optional[datetime]) -> Optional[str]:
    """Format date to VN: dd/MM/yyyy"""
    vn_dt = to_vietnam_timezone(dt)
    if vn_dt is None:
        return None

    try:
        return vn_dt.strftime("%d/%m/%Y")
    except (AttributeError, ValueError):
        return None


def format_time_vn(dt: Optional[datetime]) -> Optional[str]:
    """Format time to VN: HH:mm:ss"""
    vn_dt = to_vietnam_timezone(dt)
    if vn_dt is None:
        return None

    try:
        return vn_dt.strftime("%H:%M:%S")
    except (AttributeError, ValueError):
        return None
