"""
Module: utils/sanitize.py

Utility functions để sanitize dữ liệu nhạy cảm trước khi log hoặc gửi qua WebSocket.
"""

# Standard library
import re
import hashlib
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse, urlunparse


# Default list of sensitive keys
DEFAULT_SENSITIVE_KEYS = [
    'password', 'passwd', 'pwd',
    'token', 'access_token', 'refresh_token', 'auth_token',
    'secret', 'api_key', 'api_secret', 'private_key',
    'auth', 'authorization', 'credential', 'credentials',
    'content', 'text', 'message', 'body', 'data',
    'link_aff', 'affiliate_link', 'aff_link',
    'profile_path', 'user_data_dir', 'file_path', 'path',
    'traceback', 'stack_trace', 'error_traceback'
]


def sanitize_error(error: Union[str, Exception]) -> str:
    """
    Sanitize error message, loại bỏ file paths và internal structure.
    
    Args:
        error: Error string hoặc Exception object
    
    Returns:
        Sanitized error message
    """
    if isinstance(error, Exception):
        error_str = str(error)
        error_type = type(error).__name__
    else:
        error_str = str(error)
        error_type = None
    
    # Loại bỏ file paths (absolute paths)
    # Pattern: /path/to/file hoặc C:\path\to\file
    error_str = re.sub(r'[A-Za-z]:\\[^\s]+|/[^\s]+\.(py|js|ts|json|yaml|yml)', '[FILE_PATH]', error_str)
    
    # Loại bỏ line numbers trong file paths
    error_str = re.sub(r'line \d+', '[LINE]', error_str)
    
    # Loại bỏ internal structure details
    error_str = re.sub(r'<[^>]+>', '[OBJECT]', error_str)
    
    # Nếu có error type, thêm vào đầu
    if error_type:
        return f"{error_type}: {error_str}"
    
    return error_str


def mask_url(url: str) -> str:
    """
    Mask URL, giữ domain nhưng ẩn query params và path nếu nhạy cảm.
    
    Args:
        url: URL string
    
    Returns:
        Masked URL
    """
    try:
        parsed = urlparse(url)
        # Giữ scheme và netloc (domain)
        # Mask path và query
        masked_path = '/[REDACTED]' if parsed.path else ''
        masked_query = '?[REDACTED]' if parsed.query else ''
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            masked_path,
            parsed.params,
            masked_query,
            ''  # fragment
        ))
    except Exception:
        # Nếu parse fail, return masked version
        return '[REDACTED_URL]'


def sanitize_value(key: str, value: Any) -> Any:
    """
    Sanitize một giá trị dựa trên key.
    
    Args:
        key: Key name
        value: Value to sanitize
    
    Returns:
        Sanitized value
    """
    key_lower = key.lower()
    
    # Password, token, secret fields
    if any(sensitive in key_lower for sensitive in ['password', 'token', 'secret', 'api_key', 'auth', 'credential']):
        return '[REDACTED]'
    
    # Content fields - hash thay vì redact hoàn toàn để vẫn có thể track duplicates
    if any(content_key in key_lower for content_key in ['content', 'text', 'message', 'body']):
        if isinstance(value, str) and len(value) > 0:
            # Hash content để vẫn có thể track nhưng không expose nội dung
            content_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]
            return f'[HASH:{content_hash}]'
        return '[REDACTED]'
    
    # URL fields
    if any(url_key in key_lower for url_key in ['link_aff', 'affiliate_link', 'aff_link', 'url']):
        if isinstance(value, str):
            return mask_url(value)
        return '[REDACTED]'
    
    # Path fields
    if any(path_key in key_lower for path_key in ['profile_path', 'user_data_dir', 'file_path', 'path']):
        if isinstance(value, str):
            # Mask path, chỉ giữ tên file cuối cùng nếu có
            parts = value.replace('\\', '/').split('/')
            if parts:
                return f'[PATH:.../{parts[-1]}]'
            return '[REDACTED_PATH]'
        return '[REDACTED]'
    
    # Error fields
    if key_lower in ['error', 'error_message']:
        return sanitize_error(value)
    
    # Stack trace fields
    if key_lower in ['traceback', 'stack_trace', 'error_traceback']:
        if isinstance(value, str):
            # Chỉ giữ error type và message, loại bỏ stack trace
            lines = value.split('\n')
            if lines:
                return sanitize_error(lines[0])
            return '[REDACTED]'
        return '[REDACTED]'
    
    # Return original value nếu không phải sensitive
    return value


def sanitize_data(
    data: Dict[str, Any],
    sensitive_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Sanitize dictionary data, loại bỏ hoặc mask các fields nhạy cảm.
    
    Args:
        data: Dictionary data to sanitize
        sensitive_keys: Optional list of additional sensitive keys
    
    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data
    
    sensitive_keys_list = (sensitive_keys or []) + DEFAULT_SENSITIVE_KEYS
    
    sanitized = {}
    for key, value in data.items():
        # Check if key is sensitive
        key_lower = key.lower()
        is_sensitive = any(
            sensitive_key.lower() in key_lower
            for sensitive_key in sensitive_keys_list
        )
        
        if is_sensitive:
            sanitized[key] = sanitize_value(key, value)
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_data(value, sensitive_keys)
        elif isinstance(value, list):
            # Sanitize list items
            sanitized[key] = [
                sanitize_data(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Keep non-sensitive values as-is
            sanitized[key] = value
    
    return sanitized


def sanitize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize kwargs dictionary.
    
    Args:
        kwargs: Keyword arguments to sanitize
    
    Returns:
        Sanitized kwargs
    """
    return sanitize_data(kwargs)


def sanitize_status_message(message: str) -> str:
    """
    Sanitize status message, loại bỏ thread_id, file paths, error details.
    
    Args:
        message: Status message string
    
    Returns:
        Sanitized status message
    """
    if not message or not isinstance(message, str):
        return message
    
    # Loại bỏ thread_id patterns (ví dụ: "Thread ID: DTkSzQkkr8f")
    message = re.sub(r'Thread ID[:\s]+[A-Za-z0-9_-]+', 'Thread ID: [REDACTED]', message)
    
    # Loại bỏ file paths
    message = re.sub(r'[A-Za-z]:\\[^\s]+|/[^\s]+\.(py|js|ts|json|yaml|yml)', '[FILE_PATH]', message)
    
    # Sanitize error messages nếu có
    if 'error' in message.lower() or 'failed' in message.lower():
        message = sanitize_error(message)
    
    return message


def sanitize_user_input(input_str: str, input_type: str = "text") -> str:
    """
    Sanitize user input based on type.
    
    Args:
        input_str: Input string to sanitize
        input_type: Type of input (text, account_id, url, etc.)
    
    Returns:
        Sanitized string
    """
    if not input_str or not isinstance(input_str, str):
        return ""
    
    # Remove HTML/script tags
    input_str = re.sub(r'<[^>]+>', '', input_str)
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'javascript:', r'onerror=', r'onload=', r'eval\(', r'exec\(',
        r'<script', r'<iframe', r'<object', r'<embed'
    ]
    for pattern in dangerous_patterns:
        input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE)
    
    # Type-specific sanitization
    if input_type == "account_id":
        # Only allow alphanumeric, underscore, dash
        input_str = re.sub(r'[^a-zA-Z0-9_-]', '', input_str)
    elif input_type == "url":
        # Basic URL validation - remove dangerous protocols
        input_str = re.sub(r'^(javascript|data|vbscript):', '', input_str, flags=re.IGNORECASE)
    
    return input_str.strip()
