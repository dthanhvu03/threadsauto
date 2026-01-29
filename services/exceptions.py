"""
Module: services/exceptions.py

Custom exceptions cho Threads automation.
"""


class ThreadsAutomationError(Exception):
    """Base exception cho Threads automation."""
    ...


class SchedulerError(ThreadsAutomationError):
    """Exception liên quan đến scheduler."""
    ...


class JobNotFoundError(SchedulerError):
    """Job không tồn tại."""
    ...


class InvalidScheduleTimeError(SchedulerError):
    """Thời gian lên lịch không hợp lệ."""
    ...


class JobExpiredError(SchedulerError):
    """Job đã hết hạn."""
    ...


class StorageError(SchedulerError):
    """Lỗi khi lưu/load jobs."""
    ...


class BrowserError(ThreadsAutomationError):
    """Exception liên quan đến browser."""
    ...


class LoginError(BrowserError):
    """Lỗi đăng nhập."""
    ...


class PostError(ThreadsAutomationError):
    """Exception liên quan đến đăng bài."""
    ...


class ContentValidationError(PostError):
    """Lỗi validation content."""
    ...


class SelectorNotFoundError(PostError):
    """Không tìm thấy selector."""
    ...


class UIStateError(PostError):
    """Lỗi liên quan đến UI state."""
    ...

