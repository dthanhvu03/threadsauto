"""
Browser automation module for Threads.

Handles browser lifecycle, profile management, and session persistence.
"""

from browser.manager import BrowserManager
from browser.login_guard import LoginGuard

__all__ = ["BrowserManager", "LoginGuard"]

