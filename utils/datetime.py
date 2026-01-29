"""
Datetime formatting utilities for Vietnam timezone (UTC+7).

All datetime values are converted from UTC to Vietnam timezone (Asia/Ho_Chi_Minh)
and formatted according to Vietnamese date format standards.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


# Vietnam timezone offset: UTC+7
VN_TIMEZONE_OFFSET = timedelta(hours=7)


def to_vietnam_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert a datetime from UTC to Vietnam timezone (UTC+7).
    
    Args:
        dt: Datetime object (assumed to be in UTC) or None
    
    Returns:
        Datetime in Vietnam timezone or None if input is None
    
    Example:
        >>> utc_dt = datetime(2026, 1, 26, 7, 30, 45, tzinfo=timezone.utc)
        >>> vn_dt = to_vietnam_timezone(utc_dt)
        >>> vn_dt.hour  # Should be 14 (7 + 7)
    """
    if dt is None:
        return None
    
    try:
        # If datetime is naive (no timezone), assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to Vietnam timezone (UTC+7)
        vn_tz = timezone(VN_TIMEZONE_OFFSET)
        vn_dt = dt.astimezone(vn_tz)
        
        return vn_dt
    except (AttributeError, ValueError, TypeError) as e:
        # Log error but don't crash
        print(f"Error converting to Vietnam timezone: {e}")
        return None


def format_datetime_vn(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime to Vietnam format: dd/MM/yyyy HH:mm:ss
    
    Args:
        dt: Datetime object (assumed to be in UTC) or None
    
    Returns:
        Formatted datetime string in format "dd/MM/yyyy HH:mm:ss" or None if input is None
    
    Example:
        >>> utc_dt = datetime(2026, 1, 26, 7, 30, 45, tzinfo=timezone.utc)
        >>> format_datetime_vn(utc_dt)
        '26/01/2026 14:30:45'
    """
    vn_dt = to_vietnam_timezone(dt)
    if vn_dt is None:
        return None
    
    try:
        # Format: dd/MM/yyyy HH:mm:ss
        day = str(vn_dt.day).zfill(2)
        month = str(vn_dt.month).zfill(2)
        year = str(vn_dt.year)
        hours = str(vn_dt.hour).zfill(2)
        minutes = str(vn_dt.minute).zfill(2)
        seconds = str(vn_dt.second).zfill(2)
        
        return f"{day}/{month}/{year} {hours}:{minutes}:{seconds}"
    except (AttributeError, ValueError) as e:
        print(f"Error formatting datetime: {e}")
        return None


def format_date_vn(dt: Optional[datetime]) -> Optional[str]:
    """
    Format date to Vietnam format: dd/MM/yyyy
    
    Args:
        dt: Datetime object (assumed to be in UTC) or None
    
    Returns:
        Formatted date string in format "dd/MM/yyyy" or None if input is None
    
    Example:
        >>> utc_dt = datetime(2026, 1, 26, 7, 30, 45, tzinfo=timezone.utc)
        >>> format_date_vn(utc_dt)
        '26/01/2026'
    """
    vn_dt = to_vietnam_timezone(dt)
    if vn_dt is None:
        return None
    
    try:
        # Format: dd/MM/yyyy
        day = str(vn_dt.day).zfill(2)
        month = str(vn_dt.month).zfill(2)
        year = str(vn_dt.year)
        
        return f"{day}/{month}/{year}"
    except (AttributeError, ValueError) as e:
        print(f"Error formatting date: {e}")
        return None


def format_time_vn(dt: Optional[datetime]) -> Optional[str]:
    """
    Format time to Vietnam format: HH:mm:ss
    
    Args:
        dt: Datetime object (assumed to be in UTC) or None
    
    Returns:
        Formatted time string in format "HH:mm:ss" or None if input is None
    
    Example:
        >>> utc_dt = datetime(2026, 1, 26, 7, 30, 45, tzinfo=timezone.utc)
        >>> format_time_vn(utc_dt)
        '14:30:45'
    """
    vn_dt = to_vietnam_timezone(dt)
    if vn_dt is None:
        return None
    
    try:
        # Format: HH:mm:ss
        hours = str(vn_dt.hour).zfill(2)
        minutes = str(vn_dt.minute).zfill(2)
        seconds = str(vn_dt.second).zfill(2)
        
        return f"{hours}:{minutes}:{seconds}"
    except (AttributeError, ValueError) as e:
        print(f"Error formatting time: {e}")
        return None
