"""
Module: threads/types.py

Type definitions và constants cho Threads automation.
"""

# Standard library
from typing import Optional
from enum import Enum


class UIState(Enum):
    """Enum trạng thái UI."""
    UNKNOWN = "unknown"
    LOADING = "loading"
    DISABLED = "disabled"
    SUCCESS = "success"
    ERROR = "error"
    SHADOW_FAIL = "shadow_fail"


# Constants
POST_URL_PATTERN = "/post/"
XPATH_PREFIX = "xpath="
TEXT_CONTENT_EXPRESSION = "el => el.textContent || el.innerText || ''"


class PostResult:
    """Kết quả của thao tác đăng bài."""
    
    def __init__(
        self,
        success: bool,
        thread_id: Optional[str] = None,
        state: UIState = UIState.UNKNOWN,
        error: Optional[str] = None,
        shadow_fail: bool = False
    ):
        self.success = success
        self.thread_id = thread_id
        self.state = state
        self.error = error
        self.shadow_fail = shadow_fail

