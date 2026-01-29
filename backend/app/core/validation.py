"""
Module: backend/app/core/validation.py

Input validation functions cho API endpoints.
Validate và sanitize user inputs để tránh injection attacks.
"""

# Standard library
import re
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

# Local
from utils.sanitize import sanitize_user_input


def validate_job_input(job_data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate job input data.
    
    Args:
        job_data: Job data dictionary
        is_update: If True, fields are optional (only validate provided fields)
    
    Returns:
        (is_valid, error_message)
    """
    # Validate content (required for create, optional for update)
    if "content" in job_data:
        content = job_data.get("content", "")
        if not content or not isinstance(content, str):
            return False, "Content must be a non-empty string"
        
        if len(content) > 500:
            return False, "Content must be 1-500 characters (Threads limit)"
        
        # Check for dangerous characters/patterns
        dangerous_patterns = [
            r'<script', r'javascript:', r'onerror=', r'onload=',
            r'<iframe', r'<object', r'<embed', r'eval\(', r'exec\('
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, "Content contains potentially dangerous content"
    elif not is_update:
        # Content is required for create
        return False, "Content is required"
    
    # Validate account_id (required for create, optional for update)
    if "account_id" in job_data:
        account_id = job_data.get("account_id", "")
        if account_id:  # Allow empty for update (can be null)
            if not isinstance(account_id, str):
                return False, "account_id must be a string"
            is_valid, error_msg = validate_account_id(account_id)
            if not is_valid:
                return False, error_msg
    elif not is_update:
        # Account ID is required for create
        return False, "account_id is required"
    
    # Validate scheduled_time (required for create, optional for update)
    if "scheduled_time" in job_data:
        scheduled_time = job_data.get("scheduled_time", "")
        if not scheduled_time or not isinstance(scheduled_time, str):
            return False, "scheduled_time must be a non-empty string"
        
        is_valid, error_msg = validate_scheduled_time(scheduled_time)
        if not is_valid:
            return False, error_msg
    elif not is_update:
        # Scheduled time is required for create
        return False, "scheduled_time is required"
    
    # Validate priority (optional)
    if "priority" in job_data:
        priority = job_data.get("priority")
        if priority and not isinstance(priority, str):
            return False, "priority must be a string"
    
    # Validate platform (optional)
    if "platform" in job_data:
        platform = job_data.get("platform")
        if platform and not isinstance(platform, str):
            return False, "platform must be a string"
    
    return True, None


def validate_account_id(account_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate account_id format and existence.
    
    Args:
        account_id: Account ID string
    
    Returns:
        (is_valid, error_message)
    """
    if not account_id or not isinstance(account_id, str):
        return False, "account_id must be a non-empty string"
    
    if len(account_id) > 100:
        return False, "account_id must be 100 characters or less"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', account_id):
        return False, "account_id format invalid (alphanumeric, underscore, dash only)"
    
    return True, None


def validate_scheduled_time(scheduled_time: str) -> Tuple[bool, Optional[str]]:
    """
    Validate scheduled_time format.
    
    Args:
        scheduled_time: ISO 8601 datetime string
    
    Returns:
        (is_valid, error_message)
    """
    if not scheduled_time or not isinstance(scheduled_time, str):
        return False, "scheduled_time must be a non-empty string"
    
    try:
        # Try to parse ISO format
        dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        
        # Check if scheduled_time is not too far in the past (more than 1 year)
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        if (now - dt).total_seconds() > 365 * 24 * 3600:
            return False, "scheduled_time cannot be more than 1 year in the past"
        
        # Check if scheduled_time is not too far in the future (more than 1 year)
        if (dt - now).total_seconds() > 365 * 24 * 3600:
            return False, "scheduled_time cannot be more than 1 year in the future"
        
        return True, None
    except (ValueError, AttributeError) as e:
        return False, f"Invalid scheduled_time format (expected ISO 8601): {str(e)}"


def validate_content(content: str, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """
    Validate content string.
    
    Args:
        content: Content string
        max_length: Maximum allowed length
    
    Returns:
        (is_valid, error_message)
    """
    if not content or not isinstance(content, str):
        return False, "Content must be a non-empty string"
    
    if len(content) > max_length:
        return False, f"Content must be 1-{max_length} characters"
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'<script', r'javascript:', r'onerror=', r'onload=',
        r'<iframe', r'<object', r'<embed', r'eval\(', r'exec\('
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False, "Content contains potentially dangerous content"
    
    return True, None


def sanitize_job_input(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize job input data.
    
    Args:
        job_data: Job data dictionary
    
    Returns:
        Sanitized job data dictionary
    """
    sanitized = job_data.copy()
    
    # Sanitize content
    if "content" in sanitized and isinstance(sanitized["content"], str):
        sanitized["content"] = sanitize_user_input(sanitized["content"], input_type="text")
    
    # Sanitize account_id
    if "account_id" in sanitized and isinstance(sanitized["account_id"], str):
        sanitized["account_id"] = sanitize_user_input(sanitized["account_id"], input_type="account_id")
    
    # Sanitize link_aff if present
    if "link_aff" in sanitized and isinstance(sanitized["link_aff"], str):
        sanitized["link_aff"] = sanitize_user_input(sanitized["link_aff"], input_type="url")
    
    return sanitized
