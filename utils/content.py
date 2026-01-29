"""
Content utilities.

Shared functions for content processing and normalization.
"""

from typing import Optional


def normalize_content(content: Optional[str]) -> str:
    """
    Normalize content để so sánh duplicate.
    
    Standardize across all modules:
    - Lowercase
    - Strip whitespace
    - Remove extra spaces
    
    Args:
        content: Content string (can be None)
    
    Returns:
        Normalized content string (empty string nếu None hoặc empty)
    
    Examples:
        >>> normalize_content("  Hello   World  ")
        'hello world'
        >>> normalize_content(None)
        ''
        >>> normalize_content("")
        ''
    """
    if not content:
        return ""
    
    # Lowercase, strip whitespace, remove extra spaces
    normalized = content.lower().strip()
    normalized = ' '.join(normalized.split())
    
    return normalized


def calculate_content_hash(content: Optional[str]) -> str:
    """
    Calculate hash for content (after normalization).
    
    Args:
        content: Content string
    
    Returns:
        SHA256 hash hex string
    """
    import hashlib
    
    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
