"""
Feed controller.

Request/response handling layer.
Transforms service responses to API responses.
"""

# Standard library
from typing import Dict, Optional
from fastapi.responses import StreamingResponse
import httpx

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import NotFoundError, ValidationError, InternalError
from backend.app.modules.feed.services.feed_service import FeedService
from backend.app.modules.feed.schemas import (
    FeedFilters,
    PostInteractionRequest,
    BrowseCommentConfig,
    SelectUserCommentConfig,
    BulkLoginRequest,
    UserCommentPostsConfig
)


class FeedController:
    """
    Controller for feed endpoints.
    
    Handles:
    - Request validation (using schemas)
    - Calling service layer
    - Transforming service response to API response
    - HTTP status codes
    """
    
    def __init__(self, service: Optional[FeedService] = None):
        """
        Initialize feed controller.
        
        Args:
            service: FeedService instance. If None, creates new instance.
        """
        self.service = service or FeedService()
    
    async def get_feed(
        self,
        filters: Optional[FeedFilters] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get feed items với filters."""
        # #region agent log
        import json
        log_data = {"location": "controllers.py:get_feed", "message": "Controller received account_id", "data": {"account_id": account_id, "profile_path": profile_path}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}
        with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
        # #endregion
        try:
            result = await self.service.get_feed(filters=filters, account_id=account_id, profile_path=profile_path)
            return success_response(data=result.dict())
        except Exception as e:
            raise InternalError(f"Failed to get feed: {str(e)}")
    
    async def get_feed_post(
        self,
        post_id: str,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get một post cụ thể theo ID."""
        try:
            result = await self.service.get_feed_post(post_id=post_id, account_id=account_id, profile_path=profile_path)
            return success_response(data=result.dict())
        except Exception as e:
            raise NotFoundError(f"Post not found: {str(e)}")
    
    async def get_user_posts(
        self,
        username: str,
        filters: Optional[FeedFilters] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get posts từ user profile."""
        try:
            result = await self.service.get_user_posts(
                username=username,
                filters=filters,
                account_id=account_id,
                profile_path=profile_path
            )
            return success_response(data=result.dict())
        except Exception as e:
            raise InternalError(f"Failed to get user posts: {str(e)}")
    
    async def refresh_feed(
        self,
        filters: Optional[FeedFilters] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Force refresh feed (bypass cache)."""
        try:
            result = await self.service.refresh_feed(filters=filters, account_id=account_id, profile_path=profile_path)
            return success_response(data=result.dict())
        except Exception as e:
            raise InternalError(f"Failed to refresh feed: {str(e)}")
    
    async def clear_cache(
        self,
        username: Optional[str] = None,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Clear cache."""
        try:
            result = await self.service.clear_cache(username=username, account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to clear cache: {str(e)}")
    
    async def get_stats(
        self,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get feed statistics."""
        try:
            result = await self.service.get_stats(account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to get stats: {str(e)}")
    
    async def get_config(
        self,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get Qrtools configuration."""
        try:
            result = await self.service.get_config(account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to get config: {str(e)}")
    
    async def get_health(
        self,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get health check."""
        try:
            result = await self.service.get_health(account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to get health: {str(e)}")
    
    async def get_repost_status(
        self,
        post_id: str,
        account_id: str,
        request: Optional[PostInteractionRequest] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get repost status."""
        try:
            kwargs = {}
            if request:
                kwargs = request.dict(exclude_none=True)
            result = await self.service.get_repost_status(
                post_id=post_id,
                account_id=account_id,
                profile_path=profile_path,
                **kwargs
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to get repost status: {str(e)}")
    
    async def login(
        self,
        username: str,
        password: str,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """
        Login to Threads.
        
        Args:
            username: Username or email
            password: Password
            account_id: Optional account ID for session storage
            profile_path: Browser profile path (client-side, optional)
        """
        try:
            result = await self.service.login(
                username=username,
                password=password,
                account_id=account_id,
                profile_path=profile_path
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to login: {str(e)}")
    
    # Post Interactions
    async def like_post(
        self,
        post_id: str,
        account_id: str,
        request: Optional[PostInteractionRequest] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Like a post."""
        try:
            kwargs = {}
            if request:
                kwargs = request.dict(exclude_none=True)
            result = await self.service.like_post(
                post_id=post_id,
                account_id=account_id,
                profile_path=profile_path,
                **kwargs
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to like post: {str(e)}")
    
    async def unlike_post(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Unlike a post."""
        try:
            result = await self.service.unlike_post(post_id=post_id, account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to unlike post: {str(e)}")
    
    async def comment_on_post(
        self,
        post_id: str,
        account_id: str,
        request: PostInteractionRequest,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Comment on a post."""
        try:
            if not request.comment:
                raise ValidationError("Comment text is required")
            kwargs = request.dict(exclude_none=True, exclude={'comment'})
            result = await self.service.comment_on_post(
                post_id=post_id,
                comment=request.comment,
                account_id=account_id,
                profile_path=profile_path,
                **kwargs
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to comment on post: {str(e)}")
    
    async def repost_post(
        self,
        post_id: str,
        account_id: str,
        request: Optional[PostInteractionRequest] = None,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Repost a post."""
        try:
            kwargs = {}
            if request:
                kwargs = request.dict(exclude_none=True)
            result = await self.service.repost_post(
                post_id=post_id,
                account_id=account_id,
                profile_path=profile_path,
                **kwargs
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to repost: {str(e)}")
    
    async def quote_post(
        self,
        post_id: str,
        account_id: str,
        request: PostInteractionRequest,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Quote a post with comment."""
        try:
            if not request.quote:
                raise ValidationError("Quote text is required")
            kwargs = request.dict(exclude_none=True, exclude={'quote'})
            result = await self.service.quote_post(
                post_id=post_id,
                quote=request.quote,
                account_id=account_id,
                profile_path=profile_path,
                **kwargs
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to quote post: {str(e)}")
    
    async def unrepost_post(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Unrepost a post."""
        try:
            result = await self.service.unrepost_post(post_id=post_id, account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to unrepost: {str(e)}")
    
    async def get_post_interactions(
        self,
        post_id: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get post interaction status."""
        try:
            result = await self.service.get_post_interactions(
                post_id=post_id,
                account_id=account_id,
                profile_path=profile_path
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to get post interactions: {str(e)}")
    
    async def share_post(
        self,
        post_id: str,
        account_id: str,
        platform: str = 'copy',
        profile_path: Optional[str] = None
    ) -> Dict:
        """Share a post."""
        try:
            result = await self.service.share_post(
                post_id=post_id,
                account_id=account_id,
                platform=platform,
                profile_path=profile_path
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to share post: {str(e)}")
    
    # User Interactions
    async def follow_user(
        self,
        username: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Follow a user."""
        try:
            result = await self.service.follow_user(username=username, account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to follow user: {str(e)}")
    
    async def unfollow_user(
        self,
        username: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Unfollow a user."""
        try:
            result = await self.service.unfollow_user(username=username, account_id=account_id, profile_path=profile_path)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to unfollow user: {str(e)}")
    
    async def get_user_follow_status(
        self,
        username: str,
        account_id: str,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Get user follow status."""
        try:
            result = await self.service.get_user_follow_status(
                username=username,
                account_id=account_id,
                profile_path=profile_path
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to get user follow status: {str(e)}")
    
    # Feed Browsing
    async def browse_and_comment(
        self,
        account_id: str,
        config: BrowseCommentConfig,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Browse feed and auto comment."""
        try:
            config_dict = config.dict(exclude_none=True)
            # Convert filter_criteria to dict if present
            if 'filter_criteria' in config_dict and config_dict['filter_criteria']:
                filter_criteria = config_dict['filter_criteria']
                # Check if it's a Pydantic model (has .dict() method) or already a dict
                if hasattr(filter_criteria, 'dict'):
                    config_dict['filter_criteria'] = filter_criteria.dict(exclude_none=True)
                # If already a dict, keep it as-is
            result = await self.service.browse_and_comment(
                config=config_dict,
                account_id=account_id,
                profile_path=profile_path
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to browse and comment: {str(e)}")
    
    async def select_user_and_comment(
        self,
        account_id: str,
        config: SelectUserCommentConfig,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Select user from feed and comment on their posts."""
        try:
            config_dict = config.dict(exclude_none=True)
            # Convert filter_criteria to dict if present
            if 'filter_criteria' in config_dict and config_dict['filter_criteria']:
                filter_criteria = config_dict['filter_criteria']
                # Check if it's a Pydantic model (has .dict() method) or already a dict
                if hasattr(filter_criteria, 'dict'):
                    config_dict['filter_criteria'] = filter_criteria.dict(exclude_none=True)
                # If already a dict, keep it as-is
            result = await self.service.select_user_and_comment(
                config=config_dict,
                account_id=account_id,
                profile_path=profile_path
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to select user and comment: {str(e)}")
    
    async def list_profiles(
        self,
        base_directory: str
    ) -> Dict:
        """List all profiles in base directory."""
        try:
            result = await self.service.list_profiles(base_directory=base_directory)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to list profiles: {str(e)}")
    
    async def get_profile(
        self,
        profile_id: str,
        base_directory: str
    ) -> Dict:
        """Get profile info by ID."""
        try:
            result = await self.service.get_profile(profile_id=profile_id, base_directory=base_directory)
            return success_response(data=result)
        except Exception as e:
            raise NotFoundError(f"Profile not found: {str(e)}")
    
    async def bulk_login(
        self,
        request: Optional[Dict],
        base_directory: str
    ) -> Dict:
        """Login multiple accounts."""
        try:
            result = await self.service.bulk_login(request=request, base_directory=base_directory)
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to bulk login: {str(e)}")
    
    async def comment_user_posts(
        self,
        username: str,
        account_id: str,
        config: Dict,
        profile_path: Optional[str] = None
    ) -> Dict:
        """Comment on posts from a user."""
        try:
            result = await self.service.comment_user_posts(
                username=username,
                account_id=account_id,
                config=config,
                profile_path=profile_path
            )
            return success_response(data=result)
        except Exception as e:
            raise InternalError(f"Failed to comment on user posts: {str(e)}")
    
    async def get_saved_feed(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional["FeedFilters"] = None
    ) -> Dict:
        """Get saved feed items from database."""
        try:
            # Run in thread pool to avoid blocking event loop
            # Add timeout to prevent hanging
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Set timeout to 25 seconds (less than frontend timeout of 30s)
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.service.get_saved_feed(
                        account_id=account_id,
                        limit=limit,
                        offset=offset,
                        filters=filters
                    )
                ),
                timeout=25.0
            )
            # FeedResponse already has success, data, meta, timestamp
            # Extract meta and pass to success_response for top-level meta
            result_dict = result.dict()
            return success_response(
                data=result_dict.get("data", []),
                meta=result_dict.get("meta", {})
            )
        except asyncio.TimeoutError:
            raise InternalError("Database query timeout. Please check database connection and query performance.")
        except Exception as e:
            raise InternalError(f"Failed to get saved feed: {str(e)}")
    
    def get_post_history(
        self,
        post_id: str,
        account_id: Optional[str] = None
    ) -> Dict:
        """Get history of a post (all fetched_at timestamps)."""
        try:
            history = self.service.get_post_history(
                post_id=post_id,
                account_id=account_id
            )
            # Convert FeedItem objects to dicts
            history_dicts = [item.dict() for item in history]
            return success_response(data=history_dicts)
        except Exception as e:
            raise NotFoundError(f"Post history not found: {str(e)}")
    
    async def proxy_media(
        self,
        url: str,
        account_id: Optional[str] = None
    ) -> StreamingResponse:
        """
        Proxy media from external URL (e.g., Threads CDN) to bypass CORS.
        
        Fetches media from the provided URL and serves it with proper CORS headers.
        """
        from urllib.parse import urlparse, unquote
        
        try:
            # Decode URL if it's encoded
            url = unquote(url)
            
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError(f"Invalid media URL: {url}")
            
            # Only allow HTTPS URLs for security
            if parsed.scheme != 'https':
                raise ValidationError("Only HTTPS URLs are allowed")
            
            print(f"[FeedController] proxy_media: Fetching media from {url}")
            
            # Fetch media with timeout
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                print(f"[FeedController] proxy_media: Successfully fetched media, status={response.status_code}, content-type={response.headers.get('content-type')}")
                
                # Determine content type from response headers or URL
                content_type = response.headers.get('content-type', 'image/jpeg')
                
                # If content-type is not set, try to detect from URL
                if 'image' not in content_type and 'video' not in content_type:
                    if url.lower().endswith(('.jpg', '.jpeg')) or '.jpg' in url.lower():
                        content_type = 'image/jpeg'
                    elif url.lower().endswith('.png') or '.png' in url.lower():
                        content_type = 'image/png'
                    elif url.lower().endswith('.gif') or '.gif' in url.lower():
                        content_type = 'image/gif'
                    elif url.lower().endswith('.webp') or '.webp' in url.lower():
                        content_type = 'image/webp'
                    elif url.lower().endswith(('.mp4', '.mov')) or '.mp4' in url.lower():
                        content_type = 'video/mp4'
                    elif url.lower().endswith('.webm') or '.webm' in url.lower():
                        content_type = 'video/webm'
                    else:
                        content_type = 'image/jpeg'  # Default fallback
                
                # Create streaming response with CORS headers
                return StreamingResponse(
                    iter([response.content]),
                    media_type=content_type,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET',
                        'Access-Control-Allow-Headers': '*',
                        'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                    }
                )
        except httpx.HTTPStatusError as e:
            print(f"[FeedController] proxy_media: HTTP error {e.response.status_code} for {url}")
            raise NotFoundError(f"Failed to fetch media: HTTP {e.response.status_code}")
        except httpx.TimeoutException:
            print(f"[FeedController] proxy_media: Timeout fetching {url}")
            raise InternalError("Media fetch timeout")
        except ValidationError:
            raise
        except Exception as e:
            print(f"[FeedController] proxy_media: Error fetching {url}: {str(e)}")
            raise InternalError(f"Failed to proxy media: {str(e)}")
    
    async def serve_media(
        self,
        post_id: str,
        index: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> StreamingResponse:
        """
        Serve media file for a post.
        
        Looks up media URL from database, downloads if needed, and serves.
        Supports optional width/height for thumbnail generation.
        """
        from backend.app.modules.feed.services.media_service import MediaService
        
        media_service = MediaService()
        try:
            return await media_service.serve_media(
                post_id=post_id,
                index=index,
                width=width,
                height=height
            )
        finally:
            await media_service.close()
    
    async def serve_avatar(
        self,
        user_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> StreamingResponse:
        """
        Serve avatar file for a user.
        
        Looks up avatar URL from database, downloads if needed, and serves.
        Supports optional width/height for thumbnail generation.
        """
        from backend.app.modules.feed.services.media_service import MediaService
        
        media_service = MediaService()
        try:
            return await media_service.serve_avatar(
                user_id=user_id,
                width=width,
                height=height
            )
        finally:
            await media_service.close()