"""
Feed routes.

FastAPI routes for feed endpoints.
Thin layer that calls controller.
"""

# Standard library
from typing import Optional, Dict
from fastapi import APIRouter, Query, Body, Path, Request, Header
from fastapi.responses import StreamingResponse

# Local
from backend.app.modules.feed.controllers import FeedController
from backend.app.modules.feed.schemas import (
    FeedFilters,
    PostInteractionRequest,
    BrowseCommentConfig,
    SelectUserCommentConfig
)

router = APIRouter()
controller = FeedController()


def resolve_profile_path(
    profile_path: Optional[str] = None,
    profile_dir: Optional[str] = None,  # Alias for profile_path
    profile_id: Optional[str] = None,
    base_directory: Optional[str] = None,
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory")
) -> Optional[str]:
    """
    Resolve profile path with priority:
    1. profile_path (query param)
    2. profile_dir (query param, alias for profile_path)
    3. profile_id + base_directory (query params)
    4. X-Profile-Path (header)
    5. X-Profile-Id + X-Base-Directory (headers)
    
    Returns: Full resolved absolute path or None
    """
    import os
    from pathlib import Path
    from browser.manager import normalize_profile_path
    
    resolved_path = None
    
    # Priority 1: profile_path query param
    if profile_path:
        resolved_path = profile_path
    # Priority 2: profile_dir query param (alias)
    elif profile_dir:
        resolved_path = profile_dir
    # Priority 3: profile_id + base_directory query params
    elif profile_id and base_directory:
        # Resolve to full path: {base_directory}/{profile_id}
        resolved = os.path.join(base_directory, profile_id)
        resolved_path = os.path.normpath(resolved)
    # Priority 4: X-Profile-Path header
    elif x_profile_path:
        resolved_path = x_profile_path
    # Priority 5: X-Profile-Id + X-Base-Directory headers
    elif x_profile_id and x_base_directory:
        resolved = os.path.join(x_base_directory, x_profile_id)
        resolved_path = os.path.normpath(resolved)
    
    # Normalize path: convert relative to absolute, Windows to Linux format
    if resolved_path:
        return normalize_profile_path(resolved_path)
    
    return None


def extract_account_id(
    account_id: Optional[str] = None,  # Query param
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID"),
    account_id_header: Optional[str] = Header(None, alias="account-id"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    request: Optional[Request] = None
) -> Optional[str]:
    """
    Extract account_id with priority (matching API documentation):
    1. Query parameter (highest priority)
    2. X-Account-ID header
    3. account-id header
    4. JWT token (if CONFIG.api.accountId.parseJWT = true)
    5. Custom headers (from CONFIG.api.accountId.customHeaders)
    
    Args:
        account_id: Account ID from query parameter
        x_account_id: Account ID from X-Account-ID header
        account_id_header: Account ID from account-id header
        authorization: Authorization header (for JWT token)
        request: FastAPI Request object (for accessing all headers)
    
    Returns:
        Extracted account ID or None
    """
    import os
    from config.config import Config
    
    # Try to get config (may not be available in all contexts)
    try:
        from config.config_loader import get_config_from_env
        config = get_config_from_env()
        api_config = config.api if hasattr(config, 'api') else None
    except:
        api_config = None
    
    # Priority 1: Query parameter
    if account_id:
        if api_config and api_config.account_id and api_config.account_id.log_extraction:
            import json
            log_data = {
                "location": "routes.py:extract_account_id",
                "message": "Account ID extracted from query parameter",
                "data": {"account_id": account_id, "source": "query_param"},
                "timestamp": __import__("time").time() * 1000
            }
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        return account_id
    
    # Priority 2: X-Account-ID header
    if x_account_id:
        if api_config and api_config.account_id and api_config.account_id.log_extraction:
            import json
            log_data = {
                "location": "routes.py:extract_account_id",
                "message": "Account ID extracted from X-Account-ID header",
                "data": {"account_id": x_account_id, "source": "X-Account-ID"},
                "timestamp": __import__("time").time() * 1000
            }
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        return x_account_id
    
    # Priority 3: account-id header
    if account_id_header:
        if api_config and api_config.account_id and api_config.account_id.log_extraction:
            import json
            log_data = {
                "location": "routes.py:extract_account_id",
                "message": "Account ID extracted from account-id header",
                "data": {"account_id": account_id_header, "source": "account-id"},
                "timestamp": __import__("time").time() * 1000
            }
            with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_data) + "\n")
        return account_id_header
    
    # Priority 4: JWT token parsing (if enabled)
    if api_config and api_config.account_id and api_config.account_id.parse_jwt:
        if authorization:
            try:
                # Extract JWT token from "Bearer <token>" format
                if authorization.startswith("Bearer "):
                    token = authorization[7:]
                else:
                    token = authorization
                
                # Decode JWT token
                try:
                    import jwt
                    jwt_secret = api_config.account_id.jwt_secret or os.getenv("JWT_SECRET", "")
                    if jwt_secret:
                        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
                        extracted_id = payload.get("account_id") or payload.get("sub") or payload.get("user_id")
                        if extracted_id:
                            if api_config.account_id.log_extraction:
                                import json
                                log_data = {
                                    "location": "routes.py:extract_account_id",
                                    "message": "Account ID extracted from JWT token",
                                    "data": {"account_id": extracted_id, "source": "JWT"},
                                    "timestamp": __import__("time").time() * 1000
                                }
                                with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                                    f.write(json.dumps(log_data) + "\n")
                            return str(extracted_id)
                except ImportError:
                    # PyJWT not installed
                    pass
                except jwt.InvalidTokenError:
                    # Invalid JWT token, continue to next priority
                    pass
            except Exception:
                # JWT parsing failed, continue to next priority
                pass
    
    # Priority 5: Custom headers (if configured)
    if api_config and api_config.account_id and api_config.account_id.custom_headers and request:
        for header_name in api_config.account_id.custom_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                if api_config.account_id.log_extraction:
                    import json
                    log_data = {
                        "location": "routes.py:extract_account_id",
                        "message": f"Account ID extracted from custom header {header_name}",
                        "data": {"account_id": header_value, "source": f"custom_header:{header_name}"},
                        "timestamp": __import__("time").time() * 1000
                    }
                    with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
                        f.write(json.dumps(log_data) + "\n")
                return header_value
    
    return None


# Backward compatibility alias
def extract_profile_path(
    profile_path: Optional[str] = None,
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path")
) -> Optional[str]:
    """Backward compatibility wrapper for resolve_profile_path."""
    return resolve_profile_path(profile_path=profile_path, x_profile_path=x_profile_path)


# Feed Extraction Endpoints
@router.get("")
async def get_feed(
    request: Request,
    account_id: Optional[str] = Query(None, description="Account ID for browser context"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    authorization: Optional[str] = Header(None, alias="Authorization", description="Authorization header for JWT token"),
    min_likes: Optional[int] = Query(None, description="Minimum like count"),
    max_likes: Optional[int] = Query(None, description="Maximum like count"),
    min_replies: Optional[int] = Query(None, description="Minimum reply count"),
    min_reposts: Optional[int] = Query(None, description="Minimum repost count"),
    min_shares: Optional[int] = Query(None, description="Minimum share count"),
    max_shares: Optional[int] = Query(None, description="Maximum share count"),
    has_media: Optional[bool] = Query(None, description="Only posts with media"),
    username: Optional[str] = Query(None, description="Filter by username"),
    text_contains: Optional[str] = Query(None, description="Filter posts containing text"),
    after_timestamp: Optional[int] = Query(None, description="Posts after timestamp"),
    before_timestamp: Optional[int] = Query(None, description="Posts before timestamp"),
    limit: Optional[int] = Query(None, description="Limit number of items"),
    refresh: Optional[bool] = Query(False, description="Force refresh cache")
):
    """Get feed items với filters."""
    # #region agent log
    import json
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header,
        authorization=authorization,
        request=request
    )
    log_data = {"location": "routes.py:get_feed", "message": "Route received account_id", "data": {"account_id": final_account_id, "profile_path": final_profile_path}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}
    with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
        f.write(json.dumps(log_data) + "\n")
    # #endregion
    filters = FeedFilters(
        min_likes=min_likes,
        max_likes=max_likes,
        min_replies=min_replies,
        min_reposts=min_reposts,
        min_shares=min_shares,
        max_shares=max_shares,
        has_media=has_media,
        username=username,
        text_contains=text_contains,
        after_timestamp=after_timestamp,
        before_timestamp=before_timestamp,
        limit=limit,
        refresh=refresh
    )
    return await controller.get_feed(filters=filters, account_id=final_account_id, profile_path=final_profile_path)


# Media Endpoints (MUST be defined BEFORE /{post_id} route to avoid route conflict)
@router.get("/media/{post_id}/{index}")
async def serve_media(
    post_id: str = Path(..., description="Post ID"),
    index: int = Path(..., description="Media index (0-based)"),
    w: Optional[int] = Query(None, description="Width in pixels (for thumbnails)"),
    h: Optional[int] = Query(None, description="Height in pixels (for thumbnails)")
):
    """
    Serve media file for a post.
    
    Downloads media from Instagram CDN if not cached, then serves from filesystem.
    Supports optional width/height parameters for thumbnail generation.
    """
    return await controller.serve_media(post_id=post_id, index=index, width=w, height=h)

@router.get("/avatar/{user_id}")
async def serve_avatar(
    user_id: str = Path(..., description="User ID"),
    w: Optional[int] = Query(None, description="Width in pixels (for thumbnails)"),
    h: Optional[int] = Query(None, description="Height in pixels (for thumbnails)")
):
    """
    Serve avatar file for a user.
    
    Downloads avatar from Instagram CDN if not cached, then serves from filesystem.
    Supports optional width/height parameters for thumbnail generation.
    """
    return await controller.serve_avatar(user_id=user_id, width=w, height=h)

# Media Proxy Endpoint (Legacy - kept for backward compatibility)
@router.get("/media/proxy")
async def proxy_media(
    url: str = Query(..., description="Media URL to proxy"),
    account_id: Optional[str] = Query(None, description="Account ID for logging")
):
    """
    Proxy media from external URLs (e.g., Threads CDN) to bypass CORS.
    
    Fetches media from the provided URL and serves it with proper CORS headers
    to allow embedding in the frontend.
    
    NOTE: This is a legacy endpoint. Use /media/{post_id}/{index} instead.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[FeedRoutes] proxy_media called with url={url[:100]}..., account_id={account_id}")
    print(f"[FeedRoutes] proxy_media called with url={url[:100]}..., account_id={account_id}")
    return await controller.proxy_media(url=url, account_id=account_id)


# Saved Feed Endpoints (MUST be defined BEFORE /{post_id} route to avoid route conflict)
@router.get("/saved")
async def get_saved_feed(
    account_id: Optional[str] = Query(None, description="Account ID filter"),
    limit: Optional[int] = Query(100, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    min_likes: Optional[int] = Query(None, description="Minimum like count"),
    max_likes: Optional[int] = Query(None, description="Maximum like count"),
    min_replies: Optional[int] = Query(None, description="Minimum reply count"),
    min_reposts: Optional[int] = Query(None, description="Minimum repost count"),
    min_shares: Optional[int] = Query(None, description="Minimum share count"),
    max_shares: Optional[int] = Query(None, description="Maximum share count"),
    has_media: Optional[bool] = Query(None, description="Only posts with media"),
    username: Optional[str] = Query(None, description="Filter by username (exact match)"),
    text_contains: Optional[str] = Query(None, description="Filter posts containing text"),
    after_timestamp: Optional[int] = Query(None, description="Posts after timestamp"),
    before_timestamp: Optional[int] = Query(None, description="Posts before timestamp")
):
    """Get saved feed items from database."""
    # Build FeedFilters from query parameters
    filters = None
    if any([min_likes, max_likes, min_replies, min_reposts, min_shares, max_shares, 
            has_media is not None, username, text_contains, after_timestamp, before_timestamp]):
        filters = FeedFilters(
            min_likes=min_likes,
            max_likes=max_likes,
            min_replies=min_replies,
            min_reposts=min_reposts,
            min_shares=min_shares,
            max_shares=max_shares,
            has_media=has_media,
            username=username,
            text_contains=text_contains,
            after_timestamp=after_timestamp,
            before_timestamp=before_timestamp
        )
    
    return await controller.get_saved_feed(
        account_id=account_id,
        limit=limit,
        offset=offset,
        filters=filters
    )


@router.get("/saved/{post_id}/history")
async def get_post_history(
    post_id: str = Path(..., description="Post ID"),
    account_id: Optional[str] = Query(None, description="Account ID filter")
):
    """Get history of a post (all fetched_at timestamps)."""
    return await controller.get_post_history(
        post_id=post_id,
        account_id=account_id
    )


@router.get("/{post_id}")
async def get_feed_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: Optional[str] = Query(None, description="Account ID for browser context"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Get một post cụ thể theo ID."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.get_feed_post(post_id=post_id, account_id=final_account_id, profile_path=final_profile_path)


@router.get("/user/{username}/posts")
async def get_user_posts(
    username: str = Path(..., description="Username (with or without @)"),
    account_id: Optional[str] = Query(None, description="Account ID for browser context"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    min_likes: Optional[int] = Query(None, description="Minimum like count"),
    max_likes: Optional[int] = Query(None, description="Maximum like count"),
    min_replies: Optional[int] = Query(None, description="Minimum reply count"),
    min_reposts: Optional[int] = Query(None, description="Minimum repost count"),
    min_shares: Optional[int] = Query(None, description="Minimum share count"),
    max_shares: Optional[int] = Query(None, description="Maximum share count"),
    has_media: Optional[bool] = Query(None, description="Only posts with media"),
    text_contains: Optional[str] = Query(None, description="Filter posts containing text"),
    after_timestamp: Optional[int] = Query(None, description="Posts after timestamp"),
    before_timestamp: Optional[int] = Query(None, description="Posts before timestamp"),
    limit: Optional[int] = Query(None, description="Limit number of items")
):
    """Get posts từ user profile."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    filters = FeedFilters(
        min_likes=min_likes,
        max_likes=max_likes,
        min_replies=min_replies,
        min_reposts=min_reposts,
        min_shares=min_shares,
        max_shares=max_shares,
        has_media=has_media,
        text_contains=text_contains,
        after_timestamp=after_timestamp,
        before_timestamp=before_timestamp,
        limit=limit
    )
    return await controller.get_user_posts(
        username=username,
        filters=filters,
        account_id=final_account_id,
        profile_path=final_profile_path
    )


@router.post("/refresh")
async def refresh_feed(
    account_id: Optional[str] = Query(None, description="Account ID for browser context"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    filters: Optional[FeedFilters] = Body(None, description="Feed filters")
):
    """Force refresh feed (bypass cache)."""
    # Extract profile_path from body if present
    body_profile_path = None
    body_profile_id = None
    body_base_directory = None
    if filters and hasattr(filters, 'profile_path'):
        body_profile_path = getattr(filters, 'profile_path', None)
    if filters and hasattr(filters, 'profile_id'):
        body_profile_id = getattr(filters, 'profile_id', None)
    if filters and hasattr(filters, 'base_directory'):
        body_base_directory = getattr(filters, 'base_directory', None)
    
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=None,  # Not in body
        profile_id=profile_id or body_profile_id,
        base_directory=base_directory or body_base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.refresh_feed(filters=filters, account_id=final_account_id, profile_path=final_profile_path)


# Cache Management
@router.delete("/cache")
async def clear_cache(
    username: Optional[str] = Query(None, description="Username to clear cache for"),
    account_id: Optional[str] = Query(None, description="Account ID for session isolation"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Clear cache."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.clear_cache(username=username, account_id=final_account_id, profile_path=final_profile_path)


# Stats & Config
@router.get("/stats")
async def get_stats(
    account_id: Optional[str] = Query(None, description="Account ID for session isolation"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Get feed statistics."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.get_stats(account_id=final_account_id, profile_path=final_profile_path)


@router.get("/config")
async def get_config(
    account_id: Optional[str] = Query(None, description="Account ID (for logging)"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Get Qrtools configuration."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.get_config(account_id=final_account_id, profile_path=final_profile_path)


@router.get("/health")
async def get_health(
    account_id: Optional[str] = Query(None, description="Account ID (for logging)"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Get health check."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.get_health(account_id=final_account_id, profile_path=final_profile_path)


# Post Interactions
@router.post("/post/{post_id}/like")
async def like_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    request: Optional[PostInteractionRequest] = Body(None, description="Post interaction request")
):
    """Like a post."""
    # Extract profile_path from body if present
    body_profile_path = None
    if request and hasattr(request, 'profile_path'):
        body_profile_path = getattr(request, 'profile_path', None)
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.like_post(post_id=post_id, account_id=final_account_id, request=request, profile_path=final_profile_path)


@router.delete("/post/{post_id}/like")
async def unlike_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Unlike a post."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.unlike_post(post_id=post_id, account_id=final_account_id, profile_path=final_profile_path)


@router.post("/post/{post_id}/comment")
async def comment_on_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    request: PostInteractionRequest = Body(..., description="Comment request")
):
    """Comment on a post."""
    # Extract profile_path from body if present
    body_profile_path = None
    if request and hasattr(request, 'profile_path'):
        body_profile_path = getattr(request, 'profile_path', None)
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.comment_on_post(post_id=post_id, account_id=final_account_id, request=request, profile_path=final_profile_path)


@router.post("/post/{post_id}/repost")
async def repost_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    request: Optional[PostInteractionRequest] = Body(None, description="Repost request")
):
    """Repost a post."""
    # Extract profile_path from body if present
    body_profile_path = None
    if request and hasattr(request, 'profile_path'):
        body_profile_path = getattr(request, 'profile_path', None)
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.repost_post(post_id=post_id, account_id=final_account_id, request=request, profile_path=final_profile_path)


@router.post("/post/{post_id}/quote")
async def quote_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    request: PostInteractionRequest = Body(..., description="Quote request")
):
    """Quote a post with comment."""
    # Extract profile_path from body if present
    body_profile_path = None
    if request and hasattr(request, 'profile_path'):
        body_profile_path = getattr(request, 'profile_path', None)
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.quote_post(post_id=post_id, account_id=final_account_id, request=request, profile_path=final_profile_path)


@router.delete("/post/{post_id}/repost")
async def unrepost_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Unrepost a post."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.unrepost_post(post_id=post_id, account_id=final_account_id, profile_path=final_profile_path)


@router.get("/post/{post_id}/interactions")
async def get_post_interactions(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Get post interaction status."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.get_post_interactions(post_id=post_id, account_id=final_account_id, profile_path=final_profile_path)


@router.get("/post/{post_id}/repost-status")
async def get_repost_status(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    request: Optional[PostInteractionRequest] = Body(None, description="Repost status request")
):
    """Get repost status."""
    # Extract profile_path from body if present
    body_profile_path = None
    if request and hasattr(request, 'profile_path'):
        body_profile_path = getattr(request, 'profile_path', None)
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.get_repost_status(post_id=post_id, account_id=final_account_id, request=request, profile_path=final_profile_path)


@router.post("/post/{post_id}/share")
async def share_post(
    post_id: str = Path(..., description="Post ID"),
    account_id: str = Query(None, description="Account ID"),
    platform: str = Query("copy", description="Platform for share (default: copy)"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Share a post."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.share_post(post_id=post_id, account_id=final_account_id, platform=platform, profile_path=final_profile_path)


# User Interactions
@router.post("/user/{username}/follow")
async def follow_user(
    username: str = Path(..., description="Username (with or without @)"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Follow a user."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.follow_user(username=username, account_id=final_account_id, profile_path=final_profile_path)


@router.delete("/user/{username}/follow")
async def unfollow_user(
    username: str = Path(..., description="Username (with or without @)"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Unfollow a user."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.unfollow_user(username=username, account_id=final_account_id, profile_path=final_profile_path)


@router.get("/user/{username}/follow-status")
async def get_user_follow_status(
    username: str = Path(..., description="Username (with or without @)"),
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """Get user follow status."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.get_user_follow_status(username=username, account_id=final_account_id, profile_path=final_profile_path)


@router.post("/user/{username}/comment-posts")
async def comment_user_posts(
    username: str = Path(..., description="Username (with or without @)"),
    account_id: str = Query(..., description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    config: Dict = Body(..., description="Comment posts configuration")
):
    """Comment on posts from a user."""
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.comment_user_posts(username=username, account_id=final_account_id, config=config, profile_path=final_profile_path)


# Feed Browsing
@router.post("/browse-and-comment")
async def browse_and_comment(
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    config: BrowseCommentConfig = Body(..., description="Browse and comment configuration")
):
    """Browse feed and auto comment."""
    # Extract profile_path from body if present
    body_profile_path = None
    body_profile_id = None
    body_base_directory = None
    if config and hasattr(config, 'profile_path'):
        body_profile_path = getattr(config, 'profile_path', None)
    if config and hasattr(config, 'profile_id'):
        body_profile_id = getattr(config, 'profile_id', None)
    if config and hasattr(config, 'base_directory'):
        body_base_directory = getattr(config, 'base_directory', None)
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id or body_profile_id,
        base_directory=base_directory or body_base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    return await controller.browse_and_comment(account_id=final_account_id, config=config, profile_path=final_profile_path)


@router.post("/select-user-and-comment")
async def select_user_and_comment(
    # Query parameters for config fields (alternative to request body)
    username: Optional[str] = Query(None, description="Username cụ thể để chọn (null = random)"),
    min_likes: Optional[int] = Query(None, description="Minimum like count", ge=0),
    max_likes: Optional[int] = Query(None, description="Maximum like count", ge=0),
    has_media: Optional[bool] = Query(None, description="Chỉ lấy posts có media"),
    min_replies: Optional[int] = Query(None, description="Minimum reply count", ge=0),
    min_reposts: Optional[int] = Query(None, description="Minimum repost count", ge=0),
    min_shares: Optional[int] = Query(None, description="Minimum share count", ge=0),
    max_posts_to_comment: Optional[int] = Query(None, description="Maximum posts để comment", ge=1, le=100, alias="maxPostsToComment"),
    random_selection: Optional[bool] = Query(None, description="Chọn posts ngẫu nhiên", alias="randomSelection"),
    target_url: Optional[str] = Query(None, description="Target URL cho feed extraction", alias="targetUrl"),
    max_items: Optional[int] = Query(None, description="Maximum items để extract từ feed", ge=1, le=500, alias="maxItems"),
    user_max_items: Optional[int] = Query(None, description="Maximum items để extract từ user profile", ge=1, le=500, alias="userMaxItems"),
    comment_delay_min: Optional[int] = Query(None, description="Delay tối thiểu giữa comments (ms)", ge=1000, alias="commentDelayMin"),
    comment_delay_max: Optional[int] = Query(None, description="Delay tối đa giữa comments (ms)", ge=1000, alias="commentDelayMax"),
    # Query parameters for account/profile
    account_id: str = Query(None, description="Account ID"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    # Headers
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)"),
    # Request body (optional if query params are provided)
    config: Optional[SelectUserCommentConfig] = Body(None, description="Select user and comment configuration")
):
    """
    Select user from feed and comment on their posts.
    
    Supports both request body and query parameters:
    - Request Body: Full config object (JSON)
    - Query Parameters: Individual fields (alternative)
    - Mixed: Combine both (body takes precedence)
    
    NOTE: This endpoint only forwards the request to qrtools service.
    Browser context creation happens ONLY in qrtools service (API), not in this backend.
    This prevents browser from being launched twice.
    """
    # Build config from query parameters if body is not provided
    if config is None:
        # Create config from query parameters
        filter_criteria = None
        if any([min_likes is not None, max_likes is not None, has_media is not None, 
                min_replies is not None, min_reposts is not None, min_shares is not None]):
            from backend.app.modules.feed.schemas import FeedFilters
            filter_criteria = FeedFilters(
                min_likes=min_likes,
                max_likes=max_likes,
                has_media=has_media,
                min_replies=min_replies,
                min_reposts=min_reposts,
                min_shares=min_shares
            )
        
        config = SelectUserCommentConfig(
            username=username,
            filter_criteria=filter_criteria,
            max_posts_to_comment=max_posts_to_comment,
            random_selection=random_selection if random_selection is not None else True,
            comment_delay_min=comment_delay_min,
            comment_delay_max=comment_delay_max,
            target_url=target_url,
            max_items=max_items,
            user_max_items=user_max_items
        )
    else:
        # Merge query parameters into config (query params override body)
        if username is not None:
            config.username = username
        if max_posts_to_comment is not None:
            config.max_posts_to_comment = max_posts_to_comment
        if random_selection is not None:
            config.random_selection = random_selection
        if comment_delay_min is not None:
            config.comment_delay_min = comment_delay_min
        if comment_delay_max is not None:
            config.comment_delay_max = comment_delay_max
        if target_url is not None:
            config.target_url = target_url
        if max_items is not None:
            config.max_items = max_items
        if user_max_items is not None:
            config.user_max_items = user_max_items
        
        # Merge filter criteria
        if any([min_likes is not None, max_likes is not None, has_media is not None,
                min_replies is not None, min_reposts is not None, min_shares is not None]):
            from backend.app.modules.feed.schemas import FeedFilters
            if config.filter_criteria is None:
                config.filter_criteria = FeedFilters()
            if min_likes is not None:
                config.filter_criteria.min_likes = min_likes
            if max_likes is not None:
                config.filter_criteria.max_likes = max_likes
            if has_media is not None:
                config.filter_criteria.has_media = has_media
            if min_replies is not None:
                config.filter_criteria.min_replies = min_replies
            if min_reposts is not None:
                config.filter_criteria.min_reposts = min_reposts
            if min_shares is not None:
                config.filter_criteria.min_shares = min_shares
    
    # Extract profile_path from body if present
    body_profile_path = None
    body_profile_id = None
    body_base_directory = None
    if config and hasattr(config, 'profile_path'):
        body_profile_path = getattr(config, 'profile_path', None)
    if config and hasattr(config, 'profile_id'):
        body_profile_id = getattr(config, 'profile_id', None)
    if config and hasattr(config, 'base_directory'):
        body_base_directory = getattr(config, 'base_directory', None)
    final_profile_path = resolve_profile_path(
        profile_path=profile_path or body_profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id or body_profile_id,
        base_directory=base_directory or body_base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    if not final_account_id:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("Account ID is required")
    # Forward to qrtools service - browser context creation happens there only
    return await controller.select_user_and_comment(account_id=final_account_id, config=config, profile_path=final_profile_path)


# Profile Management Endpoints
@router.get("/profiles")
async def list_profiles(
    base_directory: str = Query(..., description="Base directory path on client machine"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header")
):
    """List all profiles in base directory."""
    final_base_directory = base_directory or x_base_directory
    if not final_base_directory:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("base_directory is required. Provide it via query parameter, request body, or X-Base-Directory header.")
    return await controller.list_profiles(base_directory=final_base_directory)


@router.get("/profiles/{profile_id}")
async def get_profile(
    profile_id: str = Path(..., description="Profile ID"),
    base_directory: str = Query(..., description="Base directory path on client machine"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header")
):
    """Get profile info by ID."""
    final_base_directory = base_directory or x_base_directory
    if not final_base_directory:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("base_directory is required. Provide it via query parameter, request body, or X-Base-Directory header.")
    return await controller.get_profile(profile_id=profile_id, base_directory=final_base_directory)


# Authentication
@router.post("/login")
async def login(
    username: str = Body(..., description="Threads username"),
    password: str = Body(..., description="Threads password"),
    account_id: Optional[str] = Body(None, description="Account ID for session storage"),
    profile_path: Optional[str] = Query(None, description="Browser profile path (client-side)"),
    profile_dir: Optional[str] = Query(None, description="Browser profile directory (alias for profile_path)"),
    profile_id: Optional[str] = Query(None, description="Profile ID (requires base_directory)"),
    base_directory: Optional[str] = Query(None, description="Base directory for profile_id"),
    x_profile_path: Optional[str] = Header(None, alias="X-Profile-Path", description="Browser profile path via header"),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id", description="Profile ID via header"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    x_account_id: Optional[str] = Header(None, alias="X-Account-ID", description="Account ID via header"),
    account_id_header: Optional[str] = Header(None, alias="account-id", description="Account ID via header (alternative)")
):
    """
    Login to Threads.
    
    Session will be saved to:
    - profile_threads/{accountId}/threads_session.json (if account_id provided)
    - output/threads_session.json (if no account_id)
    
    Profile path can be passed via query param, header, or request body.
    """
    final_profile_path = resolve_profile_path(
        profile_path=profile_path,
        profile_dir=profile_dir,
        profile_id=profile_id,
        base_directory=base_directory,
        x_profile_path=x_profile_path,
        x_profile_id=x_profile_id,
        x_base_directory=x_base_directory
    )
    final_account_id = extract_account_id(
        account_id=account_id,
        x_account_id=x_account_id,
        account_id_header=account_id_header
    )
    return await controller.login(username=username, password=password, account_id=final_account_id, profile_path=final_profile_path)


@router.post("/login/bulk")
async def bulk_login(
    base_directory: str = Query(None, description="Base directory path on client machine"),
    x_base_directory: Optional[str] = Header(None, alias="X-Base-Directory", description="Base directory via header"),
    request: Optional[Dict] = Body(None, description="Bulk login request")
):
    """Login multiple accounts."""
    # Extract base_directory from body if present
    body_base_directory = None
    if request and isinstance(request, dict):
        body_base_directory = request.get('base_directory')
    
    final_base_directory = base_directory or x_base_directory or body_base_directory
    if not final_base_directory:
        from backend.app.core.exceptions import ValidationError
        raise ValidationError("base_directory is required. Provide it via query parameter, request body, or X-Base-Directory header.")
    
    return await controller.bulk_login(request=request, base_directory=final_base_directory)


