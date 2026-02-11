"""
Feed schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Optional, List, Dict, Any
from datetime import datetime

# Third-party
from pydantic import BaseModel, Field, validator


class FeedFilters(BaseModel):
    """Schema for feed filters."""

    min_likes: Optional[int] = Field(None, description="Minimum like count", ge=0)
    max_likes: Optional[int] = Field(None, description="Maximum like count", ge=0)
    min_replies: Optional[int] = Field(None, description="Minimum reply count", ge=0)
    min_reposts: Optional[int] = Field(None, description="Minimum repost count", ge=0)
    min_shares: Optional[int] = Field(None, description="Minimum share count", ge=0)
    max_shares: Optional[int] = Field(None, description="Maximum share count", ge=0)
    has_media: Optional[bool] = Field(None, description="Only posts with media")
    username: Optional[str] = Field(
        None, description="Filter by username (exact match)"
    )
    text_contains: Optional[str] = Field(
        None, description="Filter posts containing text"
    )
    after_timestamp: Optional[int] = Field(
        None, description="Posts after timestamp (Unix seconds)", ge=0
    )
    before_timestamp: Optional[int] = Field(
        None, description="Posts before timestamp (Unix seconds)", ge=0
    )
    limit: Optional[int] = Field(
        None, description="Limit number of items", ge=1, le=1000
    )
    refresh: Optional[bool] = Field(False, description="Force refresh cache")

    @validator("max_likes")
    def validate_max_likes(cls, v, values):
        """Validate max_likes >= min_likes."""
        if v is not None and "min_likes" in values and values["min_likes"] is not None:
            if v < values["min_likes"]:
                raise ValueError("max_likes must be >= min_likes")
        return v

    @validator("max_shares")
    def validate_max_shares(cls, v, values):
        """Validate max_shares >= min_shares."""
        if (
            v is not None
            and "min_shares" in values
            and values["min_shares"] is not None
        ):
            if v < values["min_shares"]:
                raise ValueError("max_shares must be >= min_shares")
        return v

    @validator("before_timestamp")
    def validate_before_timestamp(cls, v, values):
        """Validate before_timestamp >= after_timestamp."""
        if (
            v is not None
            and "after_timestamp" in values
            and values["after_timestamp"] is not None
        ):
            if v < values["after_timestamp"]:
                raise ValueError("before_timestamp must be >= after_timestamp")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "min_likes": 100,
                "max_likes": 10000,
                "has_media": True,
                "limit": 50,
            }
        }


class FeedItem(BaseModel):
    """Schema for feed item (internal use, includes URLs)."""

    post_id: str = Field(..., description="Post ID")
    username: str = Field(..., description="Post author username")
    text: str = Field(..., description="Post text content")
    like_count: int = Field(..., description="Number of likes", ge=0)
    reply_count: int = Field(..., description="Number of replies", ge=0)
    repost_count: int = Field(..., description="Number of reposts", ge=0)
    share_count: int = Field(..., description="Number of shares", ge=0)
    media_urls: List[str] = Field(
        default_factory=list, description="Array of media URLs"
    )
    timestamp: int = Field(..., description="Unix timestamp (seconds)", ge=0)
    timestamp_iso: str = Field(..., description="ISO 8601 timestamp")
    user_id: str = Field(..., description="User ID")
    user_display_name: Optional[str] = Field(None, description="User display name")
    user_avatar_url: Optional[str] = Field(None, description="User avatar URL")
    is_verified: bool = Field(default=False, description="Is user verified")
    post_url: str = Field(..., description="Post URL")
    shortcode: str = Field(..., description="Post shortcode")
    is_reply: bool = Field(default=False, description="Is this a reply")
    parent_post_id: Optional[str] = Field(None, description="Parent post ID (if reply)")
    thread_id: str = Field(..., description="Thread ID")
    quoted_post: Optional[Dict[str, Any]] = Field(None, description="Quoted post data")
    hashtags: List[str] = Field(default_factory=list, description="Array of hashtags")
    mentions: List[str] = Field(default_factory=list, description="Array of mentions")
    links: List[str] = Field(default_factory=list, description="Array of links")
    media_type: Optional[int] = Field(None, description="Media type (1=image, 2=video)")
    video_duration: Optional[int] = Field(None, description="Video duration (seconds)")
    view_count: Optional[int] = Field(None, description="View count")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "post_id": "3817952812169631580",
                "username": "may__lily",
                "text": "Post content...",
                "like_count": 11476,
                "reply_count": 38,
                "repost_count": 468,
                "share_count": 75,
                "media_urls": ["https://..."],
                "timestamp": 1769355464,
                "timestamp_iso": "2026-01-25T15:37:44.000Z",
                "user_id": "63414013443",
                "user_display_name": "Phuong Ly",
                "is_verified": True,
                "post_url": "https://www.threads.com/@may__lily/post/DT8F9qykxdc",
                "shortcode": "DT8F9qykxdc",
                "thread_id": "3817952812169631580",
            }
        }


class FeedItemResponse(BaseModel):
    """Schema for feed item response (excludes CDN URLs, uses identifiers instead)."""

    post_id: str = Field(..., description="Post ID")
    username: str = Field(..., description="Post author username")
    text: str = Field(..., description="Post text content")
    like_count: int = Field(..., description="Number of likes", ge=0)
    reply_count: int = Field(..., description="Number of replies", ge=0)
    repost_count: int = Field(..., description="Number of reposts", ge=0)
    share_count: int = Field(..., description="Number of shares", ge=0)
    media_count: int = Field(..., description="Number of media items", ge=0)
    timestamp: int = Field(..., description="Unix timestamp (seconds)", ge=0)
    timestamp_iso: str = Field(..., description="ISO 8601 timestamp")
    user_id: str = Field(..., description="User ID")
    user_display_name: Optional[str] = Field(None, description="User display name")
    is_verified: bool = Field(default=False, description="Is user verified")
    post_url: str = Field(..., description="Post URL")
    shortcode: str = Field(..., description="Post shortcode")
    is_reply: bool = Field(default=False, description="Is this a reply")
    parent_post_id: Optional[str] = Field(None, description="Parent post ID (if reply)")
    thread_id: str = Field(..., description="Thread ID")
    quoted_post: Optional[Dict[str, Any]] = Field(None, description="Quoted post data")
    hashtags: List[str] = Field(default_factory=list, description="Array of hashtags")
    mentions: List[str] = Field(default_factory=list, description="Array of mentions")
    links: List[str] = Field(default_factory=list, description="Array of links")
    media_type: Optional[int] = Field(None, description="Media type (1=image, 2=video)")
    video_duration: Optional[int] = Field(None, description="Video duration (seconds)")
    view_count: Optional[int] = Field(None, description="View count")

    @classmethod
    def from_feed_item(cls, item: FeedItem) -> "FeedItemResponse":
        """
        Create FeedItemResponse from FeedItem, excluding URLs.

        Args:
            item: FeedItem instance

        Returns:
            FeedItemResponse instance
        """
        return cls(
            post_id=item.post_id,
            username=item.username,
            text=item.text,
            like_count=item.like_count,
            reply_count=item.reply_count,
            repost_count=item.repost_count,
            share_count=item.share_count,
            media_count=len(item.media_urls) if item.media_urls else 0,
            timestamp=item.timestamp,
            timestamp_iso=item.timestamp_iso,
            user_id=item.user_id,
            user_display_name=item.user_display_name,
            is_verified=item.is_verified,
            post_url=item.post_url,
            shortcode=item.shortcode,
            is_reply=item.is_reply,
            parent_post_id=item.parent_post_id,
            thread_id=item.thread_id,
            quoted_post=item.quoted_post,
            hashtags=item.hashtags,
            mentions=item.mentions,
            links=item.links,
            media_type=item.media_type,
            video_duration=item.video_duration,
            view_count=item.view_count,
        )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "post_id": "3817952812169631580",
                "username": "may__lily",
                "text": "Post content...",
                "like_count": 11476,
                "reply_count": 38,
                "repost_count": 468,
                "share_count": 75,
                "media_count": 1,
                "timestamp": 1769355464,
                "timestamp_iso": "2026-01-25T15:37:44.000Z",
                "user_id": "63414013443",
                "user_display_name": "Phuong Ly",
                "is_verified": True,
                "post_url": "https://www.threads.com/@may__lily/post/DT8F9qykxdc",
                "shortcode": "DT8F9qykxdc",
                "thread_id": "3817952812169631580",
            }
        }


class FeedResponse(BaseModel):
    """Schema for feed response."""

    success: bool = Field(..., description="Success status")
    data: List[FeedItemResponse] = Field(
        ..., description="Feed items (without CDN URLs)"
    )
    meta: Dict[str, Any] = Field(..., description="Response metadata")
    timestamp: str = Field(..., description="Response timestamp")


class PostInteractionRequest(BaseModel):
    """Schema for post interaction request."""

    comment: Optional[str] = Field(None, description="Comment text (for comment/quote)")
    quote: Optional[str] = Field(None, description="Quote text (for quote)")
    username: Optional[str] = Field(None, description="Username for post URL")
    shortcode: Optional[str] = Field(None, description="Shortcode for post URL")
    post_url: Optional[str] = Field(None, description="Post URL (highest priority)")
    platform: Optional[str] = Field(
        "copy", description="Platform for share (default: copy)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "comment": "Great post! 👍",
                "username": "may__lily",
                "shortcode": "DT8F9qykxdc",
            }
        }


class BrowseCommentConfig(BaseModel):
    """Schema for browse and comment configuration."""

    filter_criteria: Optional[FeedFilters] = Field(
        None, description="Filter criteria", alias="filterCriteria"
    )
    max_posts_to_comment: Optional[int] = Field(
        None,
        description="Max posts to comment",
        ge=1,
        le=100,
        alias="maxPostsToComment",
    )
    random_selection: bool = Field(
        True, description="Random selection", alias="randomSelection"
    )
    comment_templates: List[str] = Field(
        default_factory=list, description="Comment templates", alias="commentTemplates"
    )
    comment_delay_min: Optional[int] = Field(
        5000,
        description="Min delay between comments (ms)",
        ge=1000,
        alias="commentDelayMin",
    )
    comment_delay_max: Optional[int] = Field(
        15000,
        description="Max delay between comments (ms)",
        ge=1000,
        alias="commentDelayMax",
    )
    target_url: Optional[str] = Field(
        None, description="Target URL for feed extraction", alias="targetUrl"
    )
    max_items: Optional[int] = Field(
        None,
        description="Max items to extract from feed",
        ge=1,
        le=500,
        alias="maxItems",
    )

    @validator("comment_delay_max")
    def validate_comment_delay_max(cls, v, values):
        """Validate comment_delay_max >= comment_delay_min."""
        if (
            v is not None
            and "comment_delay_min" in values
            and values["comment_delay_min"] is not None
        ):
            if v < values["comment_delay_min"]:
                raise ValueError("comment_delay_max must be >= comment_delay_min")
        return v

    class Config:
        """Pydantic config."""

        allow_population_by_field_name = True  # Allow both snake_case and camelCase
        json_schema_extra = {
            "example": {
                "filterCriteria": {"min_likes": 500},
                "maxPostsToComment": 10,
                "randomSelection": True,
                "commentTemplates": [
                    "ủa đúng k ta",
                    "có ai thấy giống v k",
                    "này là sao trời",
                ],
                "commentDelayMin": 5000,
                "commentDelayMax": 15000,
                "targetUrl": "https://www.threads.net",
                "maxItems": 100,
            }
        }


class SelectUserCommentConfig(BaseModel):
    """Schema for select user and comment configuration."""

    username: Optional[str] = Field(
        None, description="Username to select", alias="username"
    )
    filter_criteria: Optional[FeedFilters] = Field(
        None, description="Filter criteria", alias="filterCriteria"
    )
    max_posts_to_comment: Optional[int] = Field(
        None,
        description="Max posts to comment",
        ge=1,
        le=100,
        alias="maxPostsToComment",
    )
    random_selection: bool = Field(
        True, description="Random selection", alias="randomSelection"
    )
    comment_templates: List[str] = Field(
        default_factory=list, description="Comment templates", alias="commentTemplates"
    )
    comment_delay_min: Optional[int] = Field(
        5000,
        description="Min delay between comments (ms)",
        ge=1000,
        alias="commentDelayMin",
    )
    comment_delay_max: Optional[int] = Field(
        15000,
        description="Max delay between comments (ms)",
        ge=1000,
        alias="commentDelayMax",
    )
    target_url: Optional[str] = Field(
        None, description="Target URL for feed extraction", alias="targetUrl"
    )
    max_items: Optional[int] = Field(
        None,
        description="Max items to extract from feed",
        ge=1,
        le=500,
        alias="maxItems",
    )
    user_max_items: Optional[int] = Field(
        None,
        description="Max items to extract from user profile",
        ge=1,
        le=500,
        alias="userMaxItems",
    )

    @validator("comment_delay_max")
    def validate_comment_delay_max(cls, v, values):
        """Validate comment_delay_max >= comment_delay_min."""
        if (
            v is not None
            and "comment_delay_min" in values
            and values["comment_delay_min"] is not None
        ):
            if v < values["comment_delay_min"]:
                raise ValueError("comment_delay_max must be >= comment_delay_min")
        return v

    class Config:
        """Pydantic config."""

        allow_population_by_field_name = True  # Allow both snake_case and camelCase
        json_schema_extra = {
            "example": {
                "username": "may__lily",
                "filterCriteria": {"min_likes": 10, "has_media": True},
                "maxPostsToComment": 3,
                "randomSelection": True,
                "commentTemplates": ["Nice post! 👍", "Great content!"],
                "commentDelayMin": 5000,
                "commentDelayMax": 15000,
                "targetUrl": "https://www.threads.net",
                "maxItems": 50,
                "userMaxItems": 20,
            }
        }


class BulkLoginAccount(BaseModel):
    """Schema for a single account in bulk login."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    account_id: Optional[str] = Field(
        None, description="Account ID (auto-generated from username if not provided)"
    )


class BulkLoginOptions(BaseModel):
    """Schema for bulk login options."""

    continue_on_error: bool = Field(
        True, description="Continue with next account if one fails"
    )
    delay_between_logins: int = Field(
        5000, description="Delay between logins (ms)", ge=1000
    )


class BulkLoginRequest(BaseModel):
    """Schema for bulk login request."""

    base_directory: str = Field(
        ..., description="Base directory path on client machine"
    )
    accounts: List[BulkLoginAccount] = Field(
        ..., description="List of accounts to login", min_items=1
    )
    options: Optional[BulkLoginOptions] = Field(None, description="Bulk login options")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "base_directory": "/home/user/profiles",
                "accounts": [
                    {
                        "username": "user1",
                        "password": "pass1",
                        "account_id": "account_01",
                    },
                    {
                        "username": "user2",
                        "password": "pass2",
                        "account_id": "account_02",
                    },
                ],
                "options": {"continue_on_error": True, "delay_between_logins": 5000},
            }
        }


class UserCommentPostsConfig(BaseModel):
    """Schema for user comment posts configuration."""

    filter_criteria: Optional[FeedFilters] = Field(None, description="Filter criteria")
    max_posts_to_comment: Optional[int] = Field(
        None, description="Max posts to comment", ge=1, le=100
    )
    random_selection: bool = Field(True, description="Random selection")
    comment_templates: List[str] = Field(
        default_factory=list, description="Comment templates"
    )
    comment_delay_min: Optional[int] = Field(
        5000, description="Min delay between comments (ms)", ge=1000
    )
    comment_delay_max: Optional[int] = Field(
        15000, description="Max delay between comments (ms)", ge=1000
    )
    max_items: Optional[int] = Field(
        None, description="Max items to extract", ge=1, le=500
    )

    @validator("comment_delay_max")
    def validate_comment_delay_max(cls, v, values):
        """Validate comment_delay_max >= comment_delay_min."""
        if (
            v is not None
            and "comment_delay_min" in values
            and values["comment_delay_min"] is not None
        ):
            if v < values["comment_delay_min"]:
                raise ValueError("comment_delay_max must be >= comment_delay_min")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "filter_criteria": {"min_likes": 10, "has_media": True},
                "max_posts_to_comment": 3,
                "random_selection": True,
                "comment_templates": ["Nice post! 👍", "Great content!"],
                "max_items": 20,
            }
        }


class ProfileInfo(BaseModel):
    """Schema for profile information."""

    profile_id: str = Field(..., description="Profile ID")
    path: str = Field(..., description="Profile path")
    full_path: str = Field(..., description="Full profile path")
    exists: bool = Field(..., description="Whether profile directory exists")
    size: Optional[int] = Field(None, description="Profile size in bytes")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO 8601)")
    has_session: bool = Field(False, description="Whether profile has session file")


class ProfileListResponse(BaseModel):
    """Schema for profile list response."""

    profiles: List[ProfileInfo] = Field(..., description="List of profiles")
    total: int = Field(..., description="Total number of profiles")
    base_directory: str = Field(..., description="Base directory path")
