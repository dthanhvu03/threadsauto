"""
Browser context provider for Qrtools.

Manages browser contexts và provides them to Qrtools when needed.
"""

# Standard library
from typing import Optional, Dict
import asyncio

# Local
from browser.manager import BrowserManager
from browser.login_guard import LoginGuard
from services.logger import StructuredLogger


class BrowserContextProvider:
    """Provider để manage và provide browser contexts cho Qrtools."""
    
    def __init__(self):
        """Initialize browser context provider."""
        self.contexts: Dict[str, BrowserManager] = {}
        self.logger = StructuredLogger(name="browser_context_provider")
        self._locks: Dict[str, asyncio.Lock] = {}  # Lock per key to prevent race conditions
    
    def _get_key(self, account_id: str, profile_path: Optional[str] = None) -> str:
        """
        Generate composite key from account_id and profile_path.
        
        Args:
            account_id: Account ID
            profile_path: Browser profile path (optional)
        
        Returns:
            Composite key string
        """
        if profile_path:
            # Normalize profile_path for consistency
            from browser.manager import normalize_profile_path
            normalized_path = normalize_profile_path(profile_path)
            return f"{account_id}:{normalized_path}"
        return f"{account_id}:default"
    
    async def get_or_create_context(self, account_id: str, profile_path: Optional[str] = None) -> BrowserManager:
        """
        Get existing context hoặc tạo mới.
        
        Thread-safe: Sử dụng lock để tránh race condition khi nhiều request
        đồng thời cố gắng tạo context cho cùng account_id.
        
        Args:
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            BrowserManager instance
        """
        # Generate composite key
        key = self._get_key(account_id, profile_path)
        
        # Fast path: Check if context already exists (no lock needed for read)
        if key in self.contexts:
            self.logger.log_step(
                step="BROWSER_CONTEXT_REUSE",
                result="SUCCESS",
                account_id=account_id,
                profile_path=profile_path,
                key=key,
                note=f"Reusing existing browser context for account {account_id}"
            )
            return self.contexts[key]
        
        # Get or create lock for this key
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        
        # Acquire lock to serialize context creation
        async with self._locks[key]:
            # Double-check after acquiring lock (another request may have created it)
            if key in self.contexts:
                self.logger.log_step(
                    step="BROWSER_CONTEXT_REUSE",
                    result="SUCCESS",
                    account_id=account_id,
                    profile_path=profile_path,
                    key=key,
                    note=f"Reusing existing browser context (created by concurrent request)"
                )
                return self.contexts[key]
            
            # Log current contexts for debugging
            self.logger.log_step(
                step="BROWSER_CONTEXT_GET",
                result="INFO",
                account_id=account_id,
                profile_path=profile_path,
                key=key,
                existing_contexts=list(self.contexts.keys())
            )
            # #region agent log
            import json
            log_data = {"location": "browser_context_provider.py:get_or_create_context", "message": "get_or_create_context called", "data": {"account_id": account_id, "profile_path": profile_path, "key": key, "existing_contexts": list(self.contexts.keys())}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
            # #endregion
            
            # Create new context (we have the lock, so this is safe)
            self.logger.log_step(
                step="BROWSER_CONTEXT_CREATE",
                result="IN_PROGRESS",
                account_id=account_id,
                profile_path=profile_path,
                note=f"Creating new browser context for account {account_id}"
            )
            
            browser_manager = BrowserManager(account_id=account_id, profile_path=profile_path)
            # #region agent log
            import json
            log_data2 = {"location": "browser_context_provider.py:get_or_create_context", "message": "Before browser_manager.start()", "data": {"account_id": account_id, "browser_manager_account_id": browser_manager.account_id, "profile_path": str(browser_manager.profile_path)}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C"}
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data2) + "\n")
            # #endregion
            await browser_manager.start()
            # #region agent log
            log_data3 = {"location": "browser_context_provider.py:get_or_create_context", "message": "After browser_manager.start()", "data": {"account_id": account_id, "browser_manager_account_id": browser_manager.account_id}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C"}
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data3) + "\n")
            # #endregion
            
            # Navigate to Threads
            await browser_manager.navigate("https://www.threads.com/?hl=vi")
            
            # Check login state
            login_guard = LoginGuard(browser_manager.page)
            is_logged_in = await login_guard.check_login_state()
            
            if not is_logged_in:
                self.logger.log_step(
                    step="BROWSER_CONTEXT_LOGIN",
                    result="WAITING",
                    account_id=account_id,
                    note="Waiting for manual login"
                )
                # Wait for manual login
                await login_guard.wait_for_manual_login(timeout=300)
            
            # Store context with composite key
            self.contexts[key] = browser_manager
            
            self.logger.log_step(
                step="BROWSER_CONTEXT_CREATE",
                result="SUCCESS",
                account_id=account_id,
                profile_path=profile_path,
                key=key,
                note=f"Browser context created and ready for account {account_id}"
            )
            
            return self.contexts[key]
    
    async def release_context(self, account_id: str, profile_path: Optional[str] = None):
        """
        Release context khi không cần nữa.
        
        Args:
            account_id: Account ID
            profile_path: Browser profile path (optional)
        """
        key = self._get_key(account_id, profile_path)
        
        if key in self.contexts:
            self.logger.log_step(
                step="BROWSER_CONTEXT_RELEASE",
                result="IN_PROGRESS",
                account_id=account_id,
                profile_path=profile_path,
                key=key
            )
            
            await self.contexts[key].close()
            del self.contexts[key]
            
            # Clean up lock if no longer needed
            if key in self._locks:
                del self._locks[key]
            
            self.logger.log_step(
                step="BROWSER_CONTEXT_RELEASE",
                result="SUCCESS",
                account_id=account_id,
                profile_path=profile_path,
                key=key
            )
    
    def has_context(self, account_id: str, profile_path: Optional[str] = None) -> bool:
        """
        Check if context exists for account.
        
        Args:
            account_id: Account ID
            profile_path: Browser profile path (optional)
        
        Returns:
            True if context exists
        """
        key = self._get_key(account_id, profile_path)
        return key in self.contexts
    
    async def cleanup_all(self):
        """Cleanup all contexts."""
        keys = list(self.contexts.keys())
        for key in keys:
            # Extract account_id from key (format: "account_id:profile_path" or "account_id:default")
            if ':' in key:
                account_id = key.split(':', 1)[0]
                profile_path = key.split(':', 1)[1] if key.split(':', 1)[1] != 'default' else None
            else:
                account_id = key
                profile_path = None
            await self.release_context(account_id, profile_path=profile_path)
