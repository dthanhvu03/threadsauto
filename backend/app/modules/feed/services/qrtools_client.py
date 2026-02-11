"""
Qrtools API client.

HTTP client để gọi Qrtools microservice với TẤT CẢ endpoints.
"""

# Standard library
import os
import uuid
from typing import Optional, Dict, List, Any
import httpx

# Local
from services.logger import StructuredLogger


class QrtoolsClient:
    """Client để gọi Qrtools API."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        """
        Initialize Qrtools client.
        
        Args:
            base_url: Base URL for Qrtools API. Defaults to env var or localhost:3000.
            timeout: Request timeout in seconds. Defaults to config or 120.0.
        
        Raises:
            ValueError: If base_url points to backend itself (self-loop prevention)
        """
        self.base_url = base_url or os.getenv("QRTOOLS_API_URL", "http://localhost:3000/api")
        self.logger = StructuredLogger(name="qrtools_client")
        
        # Prevent self-loop: check if base_url points to backend itself
        backend_port = os.getenv("PORT", "8000")
        backend_host = os.getenv("HOST", "localhost")
        backend_urls = [
            f"http://{backend_host}:{backend_port}/api",
            f"http://{backend_host}:{backend_port}",
            f"http://127.0.0.1:{backend_port}/api",
            f"http://127.0.0.1:{backend_port}",
            f"http://localhost:{backend_port}/api",
            f"http://localhost:{backend_port}",
        ]
        
        # Normalize URLs for comparison (remove trailing slashes, lowercase)
        normalized_base_url = self.base_url.rstrip('/').lower()
        normalized_backend_urls = [url.rstrip('/').lower() for url in backend_urls]
        
        if normalized_base_url in normalized_backend_urls:
            error_msg = (
                f"QRTOOLS_API_URL cannot point to backend itself ({self.base_url}). "
                f"This will cause self-loop and browser to launch twice. "
                f"Set QRTOOLS_API_URL to qrtools service URL (default: http://localhost:3000/api)"
            )
            self.logger.log_step(
                step="QRTOOLS_CLIENT_INIT",
                result="ERROR",
                error=error_msg,
                qrtools_url=self.base_url,
                backend_port=backend_port,
                backend_host=backend_host,
                note="Self-loop prevention: QRTOOLS_API_URL points to backend itself"
            )
            raise ValueError(error_msg)
        
        # Get timeout from config if available
        if timeout is None:
            try:
                from config.config_loader import get_config_from_env
                config = get_config_from_env()
                if hasattr(config, 'api') and config.api and hasattr(config.api, 'timeout'):
                    timeout = config.api.timeout.feed_extraction / 1000.0  # Convert ms to seconds
                else:
                    timeout = 120.0
            except:
                timeout = 120.0
        
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Log successful initialization
        self.logger.log_step(
            step="QRTOOLS_CLIENT_INIT",
            result="SUCCESS",
            qrtools_url=self.base_url,
            timeout=timeout,
            note="Qrtools client initialized - browser context creation happens in qrtools service only"
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def _prepare_params(self, account_id: Optional[str] = None, profile_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Prepare query parameters with account_id and profile_path.
        
        According to Qrtools API v1.1.0+:
        - Account ID can be passed via query params (highest priority)
        - Profile path can be passed via query params (highest priority)
        - Also supported via body or headers (lower priority)
        """
        params = {k: v for k, v in kwargs.items() if v is not None}
        if account_id:
            params['account_id'] = account_id
        if profile_path:
            params['profile_path'] = profile_path
        return params
    
    def _prepare_headers(self, account_id: Optional[str] = None, profile_path: Optional[str] = None, **kwargs) -> Dict[str, str]:
        """
        Prepare HTTP headers with account_id and profile_path.
        
        According to Qrtools API v1.1.0+:
        - Account ID can be passed via headers (X-Account-ID or account-id)
        - Profile path can be passed via headers (X-Profile-Path or profile-path)
        - This is lower priority than query params or body
        """
        headers = {k: v for k, v in kwargs.items() if v is not None}
        if account_id:
            # Support both header formats as per Qrtools API docs
            headers['X-Account-ID'] = account_id
            headers['account-id'] = account_id
        if profile_path:
            # Support both header formats as per Qrtools API docs
            headers['X-Profile-Path'] = profile_path
            headers['profile-path'] = profile_path
        return headers
    
    # Feed Extraction Endpoints
    async def get_feed(self, filters: Optional[Dict] = None, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Get feed items với filters.
        
        Args:
            filters: Feed filters
            account_id: Account ID for browser context
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path, **(filters or {}))
        # #region agent log
        import json
        log_data = {"location": "qrtools_client.py:get_feed", "message": "QrtoolsClient get_feed called", "data": {"account_id": account_id, "profile_path": profile_path, "params_account_id": params.get("account_id")}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}
        with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
        # #endregion
        try:
            # #region agent log
            import json
            log_data2 = {"location": "qrtools_client.py:get_feed", "message": "Making HTTP request to Qrtools API", "data": {"url": f"{self.base_url}/feed", "params": params, "account_id_in_params": params.get("account_id"), "profile_path_in_params": params.get("profile_path")}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data2) + "\n")
            # #endregion
            # Prepare headers with account_id and profile_path (lower priority than query params)
            headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
            response = await self.client.get(f"{self.base_url}/feed", params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            # #region agent log
            log_data3 = {"location": "qrtools_client.py:get_feed", "message": "Received response from Qrtools API", "data": {"status_code": response.status_code, "result_keys": list(result.keys()) if isinstance(result, dict) else "not_dict"}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data3) + "\n")
            # #endregion
            return result
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_FEED",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    async def get_feed_post(self, post_id: str, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Get một post cụ thể theo ID.
        
        Args:
            post_id: Post ID
            account_id: Account ID for browser context
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.get(f"{self.base_url}/feed/{post_id}", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_FEED_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def get_user_posts(self, username: str, filters: Optional[Dict] = None, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Get posts từ user profile.
        
        Args:
            username: Username
            filters: Feed filters
            account_id: Account ID for browser context
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path, **(filters or {}))
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            # Remove @ prefix if present
            username_clean = username.lstrip('@')
            response = await self.client.get(f"{self.base_url}/user/{username_clean}/posts", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_USER_POSTS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username,
                profile_path=profile_path
            )
            raise
    
    async def refresh_feed(self, filters: Optional[Dict] = None, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Force refresh feed (bypass cache).
        
        Account ID and Profile Path can be passed via:
        - Query params (highest priority)
        - Request body
        - Headers (X-Account-ID, X-Profile-Path)
        """
        data = filters or {}
        if account_id:
            data['account_id'] = account_id  # Also in body for POST requests
        if profile_path:
            data['profile_path'] = profile_path  # Also in body for POST requests
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/feed/refresh", json=data, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_REFRESH_FEED",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    # Cache Management
    async def clear_cache(self, username: Optional[str] = None, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Clear cache.
        
        Args:
            username: Username to clear cache for (optional)
            account_id: Account ID for session isolation (optional)
            profile_path: Browser profile path (client-side, optional)
        """
        params = {}
        if username:
            params['username'] = username.lstrip('@')
        params = self._prepare_params(account_id=account_id, profile_path=profile_path, **params)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.delete(f"{self.base_url}/cache", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_CLEAR_CACHE",
                result="FAILED",
                error=str(e),
                username=username,
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    # Stats & Config
    async def get_health(self, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Get health check.
        
        Args:
            account_id: Account ID (optional, for logging)
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.get(f"{self.base_url}/health", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_HEALTH",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    async def get_stats(self, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Get feed statistics.
        
        Args:
            account_id: Account ID for session isolation (optional)
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            # CRITICAL LOG: This will open browser - should NOT be called when loading saved feed
            import traceback
            stack_trace = ''.join(traceback.format_stack()[-10:])
            self.logger.log_step(
                step="QRTOOLS_GET_STATS",
                result="IN_PROGRESS",
                account_id=account_id,
                profile_path=profile_path,
                url=f"{self.base_url}/stats",
                params=params,
                note="Making request to Qrtools /stats API - THIS WILL OPEN BROWSER",
                stack_trace=stack_trace,
                warning="This should NOT be called when loading saved feed!"
            )
            print(f"[CRITICAL] QRTOOLS_CLIENT_GET_STATS CALLED - THIS WILL OPEN BROWSER")
            print(f"[CRITICAL] account_id={account_id}, profile_path={profile_path}")
            print(f"[CRITICAL] Stack trace:\n{stack_trace}")
            response = await self.client.get(f"{self.base_url}/stats", params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            # Log response structure for debugging
            self.logger.log_step(
                step="QRTOOLS_GET_STATS",
                result="SUCCESS",
                account_id=account_id,
                profile_path=profile_path,
                status_code=response.status_code,
                response_keys=list(result.keys()) if isinstance(result, dict) else "not_dict",
                cache_enabled=result.get("cache", {}).get("enabled") if isinstance(result, dict) else None,
                note="Received response from Qrtools /stats API"
            )
            return result
        except httpx.ConnectError as e:
            # Connection error - Qrtools service not available
            self.logger.log_step(
                step="QRTOOLS_GET_STATS",
                result="FAILED",
                error=f"Cannot connect to Qrtools API: {str(e)}",
                account_id=account_id,
                profile_path=profile_path
            )
            # Raise a specific exception that feed_service can catch
            raise ConnectionError(f"Cannot connect to Qrtools API at {self.base_url}: {str(e)}") from e
        except httpx.HTTPStatusError as e:
            # HTTP error (404, 500, etc.)
            self.logger.log_step(
                step="QRTOOLS_GET_STATS",
                result="FAILED",
                error=f"Qrtools API error: {e.response.status_code} - {str(e)}",
                account_id=account_id,
                profile_path=profile_path,
                status_code=e.response.status_code
            )
            # Re-raise as HTTPStatusError so feed_service can handle 404 specifically
            raise
        except httpx.HTTPError as e:
            # Other HTTP errors (timeout, etc.)
            self.logger.log_step(
                step="QRTOOLS_GET_STATS",
                result="FAILED",
                error=f"HTTP error: {str(e)}",
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    async def get_config(self, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Get Qrtools configuration.
        
        Args:
            account_id: Account ID (optional, for logging)
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.get(f"{self.base_url}/config", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_CONFIG",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    # Post Interactions
    async def like_post(self, post_id: str, account_id: str, profile_path: Optional[str] = None, **kwargs) -> Dict:
        """
        Like a post.
        
        Args:
            post_id: Post ID
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
            **kwargs: Additional options (username, shortcode, postUrl)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path, **kwargs)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/post/{post_id}/like", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_LIKE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def unlike_post(self, post_id: str, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Unlike a post.
        
        Args:
            post_id: Post ID
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.delete(f"{self.base_url}/post/{post_id}/like", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_UNLIKE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def comment_on_post(self, post_id: str, comment: str, account_id: str, profile_path: Optional[str] = None, **kwargs) -> Dict:
        """
        Comment on a post.
        
        Account ID and Profile Path can be passed via:
        - Query params (highest priority)
        - Request body
        - Headers (X-Account-ID, X-Profile-Path)
        """
        data = {'comment': comment, **kwargs}
        if account_id:
            data['account_id'] = account_id  # Also in body for POST requests
        if profile_path:
            data['profile_path'] = profile_path  # Also in body for POST requests
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/post/{post_id}/comment", json=data, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_COMMENT_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def repost_post(self, post_id: str, account_id: str, profile_path: Optional[str] = None, **kwargs) -> Dict:
        """
        Repost a post.
        
        Args:
            post_id: Post ID
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
            **kwargs: Additional options (username, shortcode, postUrl)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path, **kwargs)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/post/{post_id}/repost", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_REPOST_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def quote_post(self, post_id: str, quote: str, account_id: str, profile_path: Optional[str] = None, **kwargs) -> Dict:
        """
        Quote a post with comment.
        
        Account ID and Profile Path can be passed via:
        - Query params (highest priority)
        - Request body
        - Headers (X-Account-ID, X-Profile-Path)
        """
        data = {'quote': quote, **kwargs}
        if account_id:
            data['account_id'] = account_id  # Also in body for POST requests
        if profile_path:
            data['profile_path'] = profile_path  # Also in body for POST requests
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/post/{post_id}/quote", json=data, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_QUOTE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def unrepost_post(self, post_id: str, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Unrepost a post.
        
        Args:
            post_id: Post ID
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.delete(f"{self.base_url}/post/{post_id}/repost", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_UNREPOST_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def get_post_interactions(self, post_id: str, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Get post interaction status.
        
        Args:
            post_id: Post ID
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.get(f"{self.base_url}/post/{post_id}/interactions", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_POST_INTERACTIONS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def get_repost_status(self, post_id: str, account_id: str, profile_path: Optional[str] = None, **kwargs) -> Dict:
        """
        Get repost status.
        
        Args:
            post_id: Post ID
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
            **kwargs: Additional options (username, shortcode, postUrl)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path, **kwargs)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.get(f"{self.base_url}/post/{post_id}/repost-status", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_REPOST_STATUS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    async def share_post(self, post_id: str, account_id: str, platform: str = 'copy', profile_path: Optional[str] = None) -> Dict:
        """
        Share a post.
        
        Args:
            post_id: Post ID
            account_id: Account ID
            platform: Platform for share (default: 'copy')
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path, platform=platform)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/post/{post_id}/share", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_SHARE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id,
                profile_path=profile_path
            )
            raise
    
    # User Interactions
    async def follow_user(self, username: str, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Follow a user.
        
        Args:
            username: Username
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        username_clean = username.lstrip('@')
        try:
            response = await self.client.post(f"{self.base_url}/user/{username_clean}/follow", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_FOLLOW_USER",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username,
                profile_path=profile_path
            )
            raise
    
    async def unfollow_user(self, username: str, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Unfollow a user.
        
        Args:
            username: Username
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        username_clean = username.lstrip('@')
        try:
            response = await self.client.delete(f"{self.base_url}/user/{username_clean}/follow", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_UNFOLLOW_USER",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username,
                profile_path=profile_path
            )
            raise
    
    async def get_user_follow_status(self, username: str, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Get user follow status.
        
        Args:
            username: Username
            account_id: Account ID
            profile_path: Browser profile path (client-side, optional)
        """
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        username_clean = username.lstrip('@')
        try:
            response = await self.client.get(f"{self.base_url}/user/{username_clean}/follow-status", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_USER_FOLLOW_STATUS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username,
                profile_path=profile_path
            )
            raise
    
    # Feed Browsing
    async def browse_and_comment(self, config: Dict, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Browse feed and auto comment.
        
        Account ID and Profile Path can be passed via:
        - Query params (highest priority)
        - Request body
        - Headers (X-Account-ID, X-Profile-Path)
        """
        data = {**config}
        if account_id:
            data['account_id'] = account_id  # Also in body for POST requests
        if profile_path:
            data['profile_path'] = profile_path  # Also in body for POST requests
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/feed/browse-and-comment", json=data, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_BROWSE_AND_COMMENT",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    async def select_user_and_comment(self, config: Dict, account_id: str, profile_path: Optional[str] = None) -> Dict:
        """
        Select user from feed and comment on their posts.
        
        Account ID and Profile Path can be passed via:
        - Query params (highest priority)
        - Request body
        - Headers (X-Account-ID, X-Profile-Path)
        
        NOTE: Browser context creation happens ONLY in qrtools service, not in this backend.
        This method only forwards the request to qrtools service.
        """
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        
        data = {**config}
        if account_id:
            data['account_id'] = account_id  # Also in body for POST requests
        if profile_path:
            data['profile_path'] = profile_path  # Also in body for POST requests
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        
        # Add request ID to headers for tracking across services
        headers['X-Request-ID'] = request_id
        
        # Log request details before calling qrtools service
        qrtools_url = f"{self.base_url}/feed/select-user-and-comment"
        self.logger.log_step(
            step="QRTOOLS_SELECT_USER_AND_COMMENT_REQUEST",
            result="IN_PROGRESS",
            request_id=request_id,
            account_id=account_id,
            profile_path=profile_path,
            qrtools_url=qrtools_url,
            params_keys=list(params.keys()),
            headers_keys=list(headers.keys()),
            config_keys=list(config.keys()),
            note="Forwarding request to qrtools service - browser context creation happens there only"
        )
        
        try:
            response = await self.client.post(qrtools_url, json=data, params=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Log successful response
            self.logger.log_step(
                step="QRTOOLS_SELECT_USER_AND_COMMENT",
                result="SUCCESS",
                request_id=request_id,
                account_id=account_id,
                profile_path=profile_path,
                status_code=response.status_code,
                response_keys=list(result.keys()) if isinstance(result, dict) else "not_dict",
                note="Successfully received response from qrtools service"
            )
            
            return result
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_SELECT_USER_AND_COMMENT",
                result="FAILED",
                request_id=request_id,
                error=str(e),
                account_id=account_id,
                profile_path=profile_path,
                qrtools_url=qrtools_url,
                note="Failed to call qrtools service"
            )
            raise
    
    # Authentication
    async def login(self, username: str, password: str, account_id: Optional[str] = None, profile_path: Optional[str] = None) -> Dict:
        """
        Login to Threads.
        
        Account ID and Profile Path can be passed via:
        - Query params (highest priority)
        - Request body
        - Headers (X-Account-ID, X-Profile-Path)
        
        Session will be saved to:
        - profile_threads/{accountId}/threads_session.json (if account_id provided)
        - output/threads_session.json (if no account_id)
        """
        data = {'username': username, 'password': password}
        if account_id:
            data['account_id'] = account_id  # Also in body for POST requests
        if profile_path:
            data['profile_path'] = profile_path  # Also in body for POST requests
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        try:
            response = await self.client.post(f"{self.base_url}/login", json=data, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_LOGIN",
                result="FAILED",
                error=str(e),
                username=username,
                account_id=account_id,
                profile_path=profile_path
            )
            raise
    
    async def bulk_login(self, request: Optional[Dict], base_directory: str) -> Dict:
        """
        Login multiple accounts.
        
        Args:
            request: Bulk login request with accounts and options
            base_directory: Base directory path on client machine
        """
        data = request or {}
        if base_directory:
            data['base_directory'] = base_directory
        params = {}
        if base_directory:
            params['base_directory'] = base_directory
        headers = {}
        if base_directory:
            headers['X-Base-Directory'] = base_directory
        try:
            response = await self.client.post(f"{self.base_url}/login/bulk", json=data, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_BULK_LOGIN",
                result="FAILED",
                error=str(e),
                base_directory=base_directory
            )
            raise
    
    # Profile Management
    async def list_profiles(self, base_directory: str) -> Dict:
        """
        List all profiles in base directory.
        
        Args:
            base_directory: Base directory path on client machine
        """
        params = {'base_directory': base_directory}
        headers = {'X-Base-Directory': base_directory}
        try:
            response = await self.client.get(f"{self.base_url}/profiles", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_LIST_PROFILES",
                result="FAILED",
                error=str(e),
                base_directory=base_directory
            )
            raise
    
    async def get_profile(self, profile_id: str, base_directory: str) -> Dict:
        """
        Get profile info by ID.
        
        Args:
            profile_id: Profile ID
            base_directory: Base directory path on client machine
        """
        params = {'base_directory': base_directory}
        headers = {'X-Base-Directory': base_directory}
        try:
            response = await self.client.get(f"{self.base_url}/profiles/{profile_id}", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_GET_PROFILE",
                result="FAILED",
                error=str(e),
                profile_id=profile_id,
                base_directory=base_directory
            )
            raise
    
    async def comment_user_posts(
        self,
        username: str,
        account_id: str,
        config: Dict[str, Any],
        profile_path: Optional[str] = None
    ) -> Dict:
        """
        Comment on posts from a user.
        
        Args:
            username: Username
            account_id: Account ID
            config: Comment posts configuration
            profile_path: Browser profile path (client-side, optional)
        """
        data = {**config}
        if account_id:
            data['account_id'] = account_id
        if profile_path:
            data['profile_path'] = profile_path
        params = self._prepare_params(account_id=account_id, profile_path=profile_path)
        headers = self._prepare_headers(account_id=account_id, profile_path=profile_path)
        username_clean = username.lstrip('@')
        try:
            response = await self.client.post(
                f"{self.base_url}/user/{username_clean}/comment-posts",
                json=data,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.log_step(
                step="QRTOOLS_COMMENT_USER_POSTS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username,
                profile_path=profile_path
            )
            raise