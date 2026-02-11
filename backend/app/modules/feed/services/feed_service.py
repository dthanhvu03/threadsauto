"""
Feed service.

Business logic layer for feed extraction and interaction features.
"""

# Standard library
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
import httpx

# Local
from backend.app.modules.feed.services.qrtools_client import QrtoolsClient
from backend.app.modules.feed.repositories.feed_repository import FeedRepository
from backend.app.modules.feed.schemas import FeedFilters, FeedItem, FeedItemResponse, FeedResponse
from services.logger import StructuredLogger


class FeedService:
    """Service for feed extraction and interaction features."""
    
    def __init__(
        self,
        qrtools_client: Optional[QrtoolsClient] = None,
        feed_repository: Optional[FeedRepository] = None
    ):
        """
        Initialize feed service.
        
        Args:
            qrtools_client: QrtoolsClient instance. If None, creates new instance.
            feed_repository: FeedRepository instance. If None, creates new instance.
        """
        self.qrtools_client = qrtools_client or QrtoolsClient()
        self.feed_repository = feed_repository or FeedRepository()
        self.logger = StructuredLogger(name="feed_service")
    
    def _normalize_media_type(self, media_type: Any) -> Optional[int]:
        """
        Normalize media_type from string to integer.
        
        Args:
            media_type: Media type value (can be int, str, or None)
        
        Returns:
            Integer media type (1=image, 2=video) or None
        """
        if media_type is None:
            return None
        
        # If already an integer, return as-is
        if isinstance(media_type, int):
            return media_type
        
        # If string, convert to integer
        if isinstance(media_type, str):
            media_type_lower = media_type.lower().strip()
            
            # Mapping: string values to integers
            media_type_map = {
                'image': 1,
                'carousel_image': 1,
                'carousel': 1,
                'photo': 1,
                'video': 2,
                '1': 1,
                '2': 2
            }
            
            if media_type_lower in media_type_map:
                return media_type_map[media_type_lower]
            
            # Try to parse as integer string
            try:
                return int(media_type_lower)
            except ValueError:
                # Unknown value, return None
                return None
        
        # Unknown type, return None
        return None
    
    def _normalize_feed_item_data(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize feed item data from QrtoolsClient response.
        
        Args:
            item_data: Raw feed item data from QrtoolsClient
        
        Returns:
            Normalized feed item data ready for FeedItem creation
        """
        normalized = item_data.copy()
        
        # Normalize media_type
        if 'media_type' in normalized:
            normalized['media_type'] = self._normalize_media_type(normalized['media_type'])
        
        return normalized
    
    async def get_feed(
        self,
        filters: Optional[FeedFilters] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> FeedResponse:
        """
        Get feed items với filters.
        
        Args:
            filters: Feed filters
            account_id: Account ID for browser context
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            FeedResponse with feed items
        """
        # #region agent log
        import json
        log_data = {"location": "feed_service.py:get_feed", "message": "Service received account_id", "data": {"account_id": account_id}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}
        with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
        # #endregion
        try:
            # Qrtools will handle browser context creation
            # Convert filters to dict, excluding None values
            filter_dict = {}
            if filters:
                filter_dict = filters.dict(exclude_none=True)
            
            # Call Qrtools API
            # #region agent log
            log_data3 = {"location": "feed_service.py:get_feed", "message": "Before calling Qrtools API", "data": {"account_id": account_id, "filter_dict": filter_dict}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data3) + "\n")
            # #endregion
            response = await self.qrtools_client.get_feed(
                filters=filter_dict,
                account_id=account_id,
                profile_path=profile_path
            )
            # #region agent log
            log_data4 = {"location": "feed_service.py:get_feed", "message": "After calling Qrtools API", "data": {"account_id": account_id, "response_keys": list(response.keys()) if isinstance(response, dict) else "not_dict"}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data4) + "\n")
            # #endregion
            
            # Transform response
            if response.get("success"):
                feed_items = [FeedItem(**self._normalize_feed_item_data(item)) for item in response.get("data", [])]
                
                # AUTO-SAVE: Lưu vào database ngay sau khi fetch thành công
                if account_id and feed_items:
                    try:
                        saved_count = self.feed_repository.save_feed_items(
                            account_id=account_id,
                            feed_items=feed_items
                        )
                        self.logger.log_step(
                            step="FEED_SERVICE_AUTO_SAVE",
                            result="SUCCESS",
                            account_id=account_id,
                            items_saved=saved_count,
                            total_items=len(feed_items)
                        )
                    except Exception as e:
                        # Log error nhưng không fail request
                        self.logger.log_step(
                            step="FEED_SERVICE_AUTO_SAVE",
                            result="FAILED",
                            error=str(e),
                            account_id=account_id,
                            total_items=len(feed_items)
                        )
                
                # Convert FeedItem to FeedItemResponse (exclude URLs)
                feed_items_response = [FeedItemResponse.from_feed_item(item) for item in feed_items]
                
                return FeedResponse(
                    success=True,
                    data=feed_items_response,
                    meta=response.get("meta", {}),
                    timestamp=response.get("timestamp", datetime.utcnow().isoformat())
                )
            else:
                raise Exception(f"Qrtools API returned error: {response.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_FEED",
                result="FAILED",
                error=str(e),
                account_id=account_id
            )
            raise
    
    async def get_feed_post(
        self,
        post_id: str,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> FeedItem:
        """
        Get một post cụ thể theo ID.
        
        Args:
            post_id: Post ID
            account_id: Account ID for browser context
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            FeedItem
        """
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.get_feed_post(
                post_id=post_id,
                account_id=account_id,
                profile_path=profile_path
            )
            
            if response.get("success"):
                return FeedItem(**self._normalize_feed_item_data(response.get("data", {})))
            else:
                raise Exception(f"Qrtools API returned error: {response.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_FEED_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def get_user_posts(
        self,
        username: str,
        filters: Optional[FeedFilters] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> FeedResponse:
        """
        Get posts từ user profile.
        
        Args:
            username: Username (with or without @)
            filters: Feed filters
            account_id: Account ID for browser context
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            FeedResponse with user posts
        """
        try:
            # Qrtools will handle browser context creation
            filter_dict = {}
            if filters:
                filter_dict = filters.dict(exclude_none=True)
            
            response = await self.qrtools_client.get_user_posts(
                username=username,
                filters=filter_dict,
                account_id=account_id,
                profile_path=profile_path
            )
            
            if response.get("success"):
                feed_items = [FeedItem(**self._normalize_feed_item_data(item)) for item in response.get("data", [])]
                # Convert FeedItem to FeedItemResponse (exclude URLs)
                feed_items_response = [FeedItemResponse.from_feed_item(item) for item in feed_items]
                return FeedResponse(
                    success=True,
                    data=feed_items_response,
                    meta=response.get("meta", {}),
                    timestamp=response.get("timestamp", datetime.utcnow().isoformat())
                )
            else:
                raise Exception(f"Qrtools API returned error: {response.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_USER_POSTS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username
            )
            raise
    
    async def refresh_feed(
        self,
        filters: Optional[FeedFilters] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> FeedResponse:
        """
        Force refresh feed (bypass cache).
        
        Args:
            filters: Feed filters
            account_id: Account ID for browser context
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            FeedResponse with refreshed feed items
        """
        try:
            # Qrtools will handle browser context creation
            filter_dict = {}
            if filters:
                filter_dict = filters.dict(exclude_none=True)
            
            response = await self.qrtools_client.refresh_feed(
                filters=filter_dict,
                account_id=account_id,
                profile_path=profile_path
            )
            
            if response.get("success"):
                feed_items = [FeedItem(**self._normalize_feed_item_data(item)) for item in response.get("data", [])]
                # Convert FeedItem to FeedItemResponse (exclude URLs)
                feed_items_response = [FeedItemResponse.from_feed_item(item) for item in feed_items]
                return FeedResponse(
                    success=True,
                    data=feed_items_response,
                    meta=response.get("meta", {}),
                    timestamp=response.get("timestamp", datetime.utcnow().isoformat())
                )
            else:
                raise Exception(f"Qrtools API returned error: {response.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_REFRESH_FEED",
                result="FAILED",
                error=str(e),
                account_id=account_id
            )
            raise
    
    async def clear_cache(
        self,
        username: Optional[str] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clear cache.
        
        Args:
            username: Optional username to clear cache for
            account_id: Account ID for session isolation (optional)
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            Clear cache response
        """
        try:
            response = await self.qrtools_client.clear_cache(
                username=username,
                account_id=account_id,
                profile_path=profile_path
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_CLEAR_CACHE",
                result="FAILED",
                error=str(e),
                username=username
            )
            raise
    
    async def get_stats(
        self,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get feed statistics.
        
        Args:
            account_id: Account ID for session isolation (optional)
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            Stats response
        """
        try:
            # CRITICAL LOG: This method should NOT be called when loading saved feed
            import traceback
            stack_trace = ''.join(traceback.format_stack()[-10:])
            self.logger.log_step(
                step="FEED_SERVICE_GET_STATS",
                result="IN_PROGRESS",
                account_id=account_id,
                profile_path=profile_path,
                note="Calling Qrtools /stats API - THIS WILL OPEN BROWSER",
                stack_trace=stack_trace,
                warning="This should NOT be called when loading saved feed!"
            )
            print(f"[CRITICAL] FEED_SERVICE_GET_STATS CALLED - THIS WILL OPEN BROWSER")
            print(f"[CRITICAL] account_id={account_id}, profile_path={profile_path}")
            print(f"[CRITICAL] Stack trace:\n{stack_trace}")
            response = await self.qrtools_client.get_stats(
                account_id=account_id,
                profile_path=profile_path
            )
            # Log response structure for debugging
            self.logger.log_step(
                step="FEED_SERVICE_GET_STATS",
                result="SUCCESS",
                account_id=account_id,
                profile_path=profile_path,
                response_keys=list(response.keys()) if isinstance(response, dict) else "not_dict",
                cache_enabled=response.get("cache", {}).get("enabled") if isinstance(response, dict) else None,
                note="Received stats response from Qrtools"
            )
            return response
        except (httpx.ConnectError, ConnectionError) as e:
            # Connection error - Qrtools service not available
            error_msg = "Cannot connect to Qrtools API. Please make sure Qrtools service is running on http://localhost:3000"
            self.logger.log_step(
                step="FEED_SERVICE_GET_STATS",
                result="FAILED",
                error=error_msg,
                account_id=account_id,
                profile_path=profile_path,
                original_error=str(e)
            )
            # Return a default stats response instead of raising error
            return {
                "success": True,
                "cache": {
                    "enabled": False,
                    "hasData": False,
                    "age": None
                },
                "server": {
                    "qrtools_available": False,
                    "qrtools_error": error_msg
                },
                "note": "Qrtools API is not available. This is a fallback response."
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Qrtools API doesn't have /stats endpoint - return default response
                self.logger.log_step(
                    step="FEED_SERVICE_GET_STATS",
                    result="INFO",
                    note="Qrtools API endpoint /stats not found. Returning default stats.",
                    account_id=account_id,
                    profile_path=profile_path,
                    status_code=404
                )
                return {
                    "success": True,
                    "cache": {
                        "enabled": True,
                        "hasData": False,
                        "age": None
                    },
                    "server": {
                        "qrtools_available": True,
                        "qrtools_endpoint_note": "Qrtools API /stats endpoint not available"
                    },
                    "note": "Stats endpoint not available in Qrtools API. This is a fallback response."
                }
            else:
                # For other HTTP errors (500, etc.), return fallback response instead of raising
                error_msg = f"Qrtools API error: {e.response.status_code} - {str(e)}"
                self.logger.log_step(
                    step="FEED_SERVICE_GET_STATS",
                    result="FAILED",
                    error=error_msg,
                    account_id=account_id,
                    profile_path=profile_path,
                    status_code=e.response.status_code
                )
                # Return fallback response instead of raising to prevent frontend crash
                return {
                    "success": True,
                    "cache": {
                        "enabled": False,
                        "hasData": False,
                        "age": None
                    },
                    "server": {
                        "qrtools_available": True,
                        "qrtools_error": error_msg,
                        "qrtools_status_code": e.response.status_code
                    },
                    "note": f"Qrtools API returned error {e.response.status_code}. This is a fallback response."
                }
        except httpx.TimeoutException as e:
            # Timeout error
            error_msg = "Qrtools API request timed out. The service may be slow or unavailable."
            self.logger.log_step(
                step="FEED_SERVICE_GET_STATS",
                result="FAILED",
                error=error_msg,
                account_id=account_id,
                profile_path=profile_path,
                original_error=str(e)
            )
            # Return default response instead of raising error
            return {
                "success": True,
                "cache": {
                    "enabled": False,
                    "hasData": False,
                    "age": None
                },
                "server": {
                    "qrtools_available": False,
                    "qrtools_error": error_msg
                },
                "note": "Qrtools API request timed out. This is a fallback response."
            }
        except Exception as e:
            # Catch all other exceptions and return default response
            error_msg = f"Failed to get stats from Qrtools API: {str(e)}"
            self.logger.log_step(
                step="FEED_SERVICE_GET_STATS",
                result="FAILED",
                error=error_msg,
                account_id=account_id,
                profile_path=profile_path,
                original_error=str(e)
            )
            # Return default response instead of raising error to prevent frontend crash
            return {
                "success": True,
                "cache": {
                    "enabled": False,
                    "hasData": False,
                    "age": None
                },
                "server": {
                    "qrtools_available": False,
                    "qrtools_error": error_msg
                },
                "note": "Failed to get stats from Qrtools API. This is a fallback response."
            }
    
    async def get_config(
        self,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Qrtools configuration.
        
        Args:
            account_id: Account ID (optional, for logging)
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            Config response
        """
        try:
            response = await self.qrtools_client.get_config(
                account_id=account_id,
                profile_path=profile_path
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_CONFIG",
                result="FAILED",
                error=str(e)
            )
            raise
    
    async def get_health(
        self,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get health check.
        
        Args:
            account_id: Account ID (optional, for logging)
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            Health check response
        """
        try:
            response = await self.qrtools_client.get_health(
                account_id=account_id,
                profile_path=profile_path
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_HEALTH",
                result="FAILED",
                error=str(e)
            )
            raise
    
    async def login(
        self,
        username: str,
        password: str,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Login to Threads.
        
        Args:
            username: Threads username
            password: Threads password
            account_id: Optional account ID for session storage
            profile_path: Browser profile path (client-side, optional)
        
        Returns:
            Login response
            
        Session will be saved to:
        - profile_threads/{accountId}/threads_session.json (if account_id provided)
        - output/threads_session.json (if no account_id)
        """
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.login(
                username=username,
                password=password,
                account_id=account_id,
                profile_path=profile_path
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_LOGIN",
                result="FAILED",
                error=str(e),
                username=username,
                account_id=account_id
            )
            raise
    
    # Post Interactions
    async def like_post(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Like a post."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.like_post(post_id, account_id, profile_path=profile_path, **kwargs)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_LIKE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def unlike_post(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Unlike a post."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.unlike_post(post_id, account_id, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_UNLIKE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def comment_on_post(
        self,
        post_id: str,
        comment: str,
        account_id: str,
        profile_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Comment on a post."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.comment_on_post(
                post_id,
                comment,
                account_id,
                profile_path=profile_path,
                **kwargs
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_COMMENT_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def repost_post(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Repost a post."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.repost_post(post_id, account_id, profile_path=profile_path, **kwargs)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_REPOST_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def quote_post(
        self,
        post_id: str,
        quote: str,
        account_id: str,
        profile_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Quote a post with comment."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.quote_post(
                post_id,
                quote,
                account_id,
                profile_path=profile_path,
                **kwargs
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_QUOTE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def unrepost_post(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Unrepost a post."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.unrepost_post(post_id, account_id, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_UNREPOST_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def get_post_interactions(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get post interaction status."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.get_post_interactions(post_id, account_id, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_POST_INTERACTIONS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def get_repost_status(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get repost status."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.get_repost_status(
                post_id=post_id,
                account_id=account_id,
                profile_path=profile_path,
                **kwargs
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_REPOST_STATUS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    async def share_post(
        self,
        post_id: str,
        account_id: str,
        platform: str = 'copy',
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Share a post."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.share_post(post_id, account_id, platform, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_SHARE_POST",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                post_id=post_id
            )
            raise
    
    # User Interactions
    async def follow_user(
        self,
        username: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Follow a user."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.follow_user(username, account_id, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_FOLLOW_USER",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username
            )
            raise
    
    async def unfollow_user(
        self,
        username: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Unfollow a user."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.unfollow_user(username, account_id, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_UNFOLLOW_USER",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username
            )
            raise
    
    async def get_user_follow_status(
        self,
        username: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user follow status."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.get_user_follow_status(username, account_id, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_USER_FOLLOW_STATUS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username
            )
            raise
    
    # Feed Browsing
    async def browse_and_comment(
        self,
        config: Dict[str, Any],
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Browse feed and auto comment."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.browse_and_comment(config, account_id, profile_path=profile_path)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_BROWSE_AND_COMMENT",
                result="FAILED",
                error=str(e),
                account_id=account_id
            )
            raise
    
    async def select_user_and_comment(
        self,
        config: Dict[str, Any],
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select user from feed and comment on their posts.
        
        NOTE: This method only forwards the request to qrtools service.
        Browser context creation happens ONLY in qrtools service (API), not in this backend.
        This prevents browser from being launched twice.
        """
        try:
            # Log before forwarding to confirm no browser context creation here
            self.logger.log_step(
                step="FEED_SERVICE_SELECT_USER_AND_COMMENT",
                result="IN_PROGRESS",
                account_id=account_id,
                profile_path=profile_path,
                config_keys=list(config.keys()) if isinstance(config, dict) else "not_dict",
                note="Forwarding to qrtools service - NO browser context creation here. Browser will be launched only in qrtools service."
            )
            
            # Forward to qrtools service - browser context creation happens there only
            # Do NOT create browser context here to avoid launching browser twice
            response = await self.qrtools_client.select_user_and_comment(config, account_id, profile_path=profile_path)
            
            # Log successful forwarding
            self.logger.log_step(
                step="FEED_SERVICE_SELECT_USER_AND_COMMENT",
                result="SUCCESS",
                account_id=account_id,
                profile_path=profile_path,
                response_keys=list(response.keys()) if isinstance(response, dict) else "not_dict",
                note="Successfully forwarded request to qrtools service"
            )
            
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_SELECT_USER_AND_COMMENT",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                profile_path=profile_path,
                error_type=type(e).__name__,
                note="Failed to forward request to qrtools service"
            )
            raise
    
    async def list_profiles(
        self,
        base_directory: str
    ) -> Dict[str, Any]:
        """List all profiles in base directory."""
        try:
            response = await self.qrtools_client.list_profiles(base_directory=base_directory)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_LIST_PROFILES",
                result="FAILED",
                error=str(e),
                base_directory=base_directory
            )
            raise
    
    async def get_profile(
        self,
        profile_id: str,
        base_directory: str
    ) -> Dict[str, Any]:
        """Get profile info by ID."""
        try:
            response = await self.qrtools_client.get_profile(profile_id=profile_id, base_directory=base_directory)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_PROFILE",
                result="FAILED",
                error=str(e),
                profile_id=profile_id,
                base_directory=base_directory
            )
            raise
    
    async def bulk_login(
        self,
        request: Optional[Dict],
        base_directory: str
    ) -> Dict[str, Any]:
        """Login multiple accounts."""
        try:
            response = await self.qrtools_client.bulk_login(request=request, base_directory=base_directory)
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_BULK_LOGIN",
                result="FAILED",
                error=str(e),
                base_directory=base_directory
            )
            raise
    
    async def comment_user_posts(
        self,
        username: str,
        account_id: str,
        config: Dict[str, Any],
        profile_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Comment on posts from a user."""
        try:
            # Qrtools will handle browser context creation
            response = await self.qrtools_client.comment_user_posts(
                username=username,
                account_id=account_id,
                config=config,
                profile_path=profile_path
            )
            return response
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_COMMENT_USER_POSTS",
                result="FAILED",
                error=str(e),
                account_id=account_id,
                username=username
            )
            raise
    
    def get_saved_feed(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[FeedFilters] = None
    ) -> FeedResponse:
        """
        Get saved feed items from database.
        
        NOTE: This method ONLY reads from database. It does NOT call Qrtools API or open browser.
        
        Args:
            account_id: Account ID filter
            limit: Limit number of results
            offset: Offset for pagination
            filters: Optional FeedFilters for advanced filtering
        
        Returns:
            FeedResponse with saved feed items
        """
        try:
            # Log that we're starting to get saved feed (database only, no browser)
            import traceback
            stack_trace = ''.join(traceback.format_stack()[-10:])
            self.logger.log_step(
                step="FEED_SERVICE_GET_SAVED_FEED",
                result="IN_PROGRESS",
                account_id=account_id,
                limit=limit,
                offset=offset,
                filters=filters.dict(exclude_none=True) if filters else None,
                note="Reading from database only - NO Qrtools API call, NO browser",
                stack_trace=stack_trace
            )
            print(f"[INFO] FEED_SERVICE_GET_SAVED_FEED CALLED - Database only, NO browser")
            print(f"[INFO] account_id={account_id}, filters={filters.dict(exclude_none=True) if filters else None}, stack_trace:\n{stack_trace}")
            
            # Get feed items from repository (database only)
            feed_items = self.feed_repository.get_feed_items(
                account_id=account_id,
                limit=limit,
                offset=offset,
                order_by="fetched_at DESC",
                filters=filters
            )
            
            # Get total count and filtered_total from repository result
            # feed_items is a FeedItemsList wrapper with _total_count and _filtered_total attributes
            total_count = feed_items._total_count if hasattr(feed_items, '_total_count') else len(feed_items)
            filtered_total = feed_items._filtered_total if hasattr(feed_items, '_filtered_total') else total_count
            
            self.logger.log_step(
                step="FEED_SERVICE_GET_SAVED_FEED",
                result="SUCCESS",
                account_id=account_id,
                items_count=len(feed_items),
                total_count=total_count,
                filtered_total=filtered_total,
                limit=limit,
                offset=offset,
                note="Successfully read from database - NO browser was opened"
            )
            
            # Convert FeedItem to FeedItemResponse (exclude URLs)
            feed_items_response = [FeedItemResponse.from_feed_item(item) for item in feed_items]
            
            return FeedResponse(
                success=True,
                data=feed_items_response,
                meta={
                    "source": "database",
                    "total": total_count,
                    "filtered_total": filtered_total,
                    "count": len(feed_items),
                    "limit": limit or 100,
                    "offset": offset or 0,
                    "has_more": (offset or 0) + len(feed_items) < filtered_total if limit else False
                },
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_SAVED_FEED",
                result="FAILED",
                error=str(e),
                account_id=account_id
            )
            raise
    
    def get_post_history(
        self,
        post_id: str,
        account_id: Optional[str] = None
    ) -> List[FeedItem]:
        """
        Get history of a post (all fetched_at timestamps).
        
        Args:
            post_id: Post ID
            account_id: Optional account ID filter
        
        Returns:
            List of FeedItem objects with different fetched_at timestamps
        """
        try:
            history = self.feed_repository.get_feed_item_history(
                post_id=post_id,
                account_id=account_id
            )
            
            self.logger.log_step(
                step="FEED_SERVICE_GET_POST_HISTORY",
                result="SUCCESS",
                post_id=post_id,
                account_id=account_id,
                history_count=len(history)
            )
            
            return history
        except Exception as e:
            self.logger.log_step(
                step="FEED_SERVICE_GET_POST_HISTORY",
                result="FAILED",
                error=str(e),
                post_id=post_id,
                account_id=account_id
            )
            raise