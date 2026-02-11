"""
Feed repository.

Data access layer for feed items. Wraps FeedStorage.
"""

# Standard library
import json
from typing import List, Dict, Optional

# Local
from services.logger import StructuredLogger
from services.storage.feed_storage import FeedStorage
from config.storage_config_loader import get_storage_config_from_env
from backend.app.shared.base_repository import BaseRepository
from backend.app.modules.feed.schemas import FeedItem, FeedFilters


class FeedRepository(BaseRepository):
    """
    Repository for feed data access.
    
    Handles all interactions with FeedStorage.
    No business logic - only data access.
    """
    
    def __init__(self, use_mysql: bool = True):
        """
        Initialize feed repository.
        
        Args:
            use_mysql: If True, use MySQL storage. If False, raise error (no file system fallback for feed).
        """
        self.logger = StructuredLogger(name="feed_repository")
        self.use_mysql = use_mysql
        
        # Initialize FeedStorage
        self.feed_storage = None
        if use_mysql:
            try:
                storage_config = get_storage_config_from_env()
                mysql_config = storage_config.mysql
                self.feed_storage = FeedStorage(
                    host=mysql_config.host,
                    port=mysql_config.port,
                    user=mysql_config.user,
                    password=mysql_config.password,
                    database=mysql_config.database,
                    charset=mysql_config.charset,
                    logger=self.logger
                )
            except Exception as e:
                self.logger.log_step(
                    step="INIT_FEED_REPOSITORY",
                    result="ERROR",
                    error=f"Failed to initialize MySQL storage: {str(e)}",
                    error_type=type(e).__name__
                )
                raise
        else:
            raise ValueError("Feed repository requires MySQL storage. File system fallback not supported.")
    
    def save_feed_items(
        self,
        account_id: str,
        feed_items: List[FeedItem],
        fetched_at: Optional[str] = None
    ) -> int:
        """
        Save feed items to database.
        
        Args:
            account_id: Account ID
            feed_items: List of FeedItem objects
            fetched_at: Optional fetch timestamp (ISO format string)
        
        Returns:
            Number of items saved
        """
        if not self.feed_storage:
            raise ValueError("Feed storage not initialized")
        
        # Convert FeedItem objects to dicts
        feed_items_dicts = [item.dict() for item in feed_items]
        
        # Parse fetched_at if provided
        from datetime import datetime
        fetched_at_dt = None
        if fetched_at:
            try:
                fetched_at_dt = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
            except Exception:
                pass
        
        return self.feed_storage.save_feed_items(
            account_id=account_id,
            feed_items=feed_items_dicts,
            fetched_at=fetched_at_dt
        )
    
    def get_feed_items(
        self,
        account_id: Optional[str] = None,
        post_id: Optional[str] = None,
        username: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "fetched_at DESC",
        filters: Optional["FeedFilters"] = None
    ) -> List[FeedItem]:
        """
        Get feed items from database.
        
        Args:
            account_id: Filter by account ID
            post_id: Filter by post ID
            username: Filter by username
            limit: Limit number of results
            offset: Offset for pagination
            order_by: Order by clause
            filters: Optional FeedFilters object for advanced filtering
        
        Returns:
            FeedItemsList wrapper with FeedItem objects and metadata
        """
        if not self.feed_storage:
            raise ValueError("Feed storage not initialized")
        
        # Convert FeedFilters to dict if provided
        filters_dict = None
        if filters:
            filters_dict = filters.dict(exclude_none=True)
            # Remove limit and refresh from filters dict (handled separately)
            filters_dict.pop("limit", None)
            filters_dict.pop("refresh", None)
        
        result = self.feed_storage.get_feed_items(
            account_id=account_id,
            post_id=post_id,
            username=username,
            limit=limit,
            offset=offset,
            order_by=order_by,
            filters=filters_dict
        )
        
        # Handle both old format (list) and new format (dict with items and total)
        if isinstance(result, dict) and "items" in result:
            items_dicts = result["items"]
            total_count = result.get("total", len(items_dicts))
            filtered_total = result.get("filtered_total", total_count)
        else:
            # Backward compatibility: if result is a list
            items_dicts = result if isinstance(result, list) else []
            total_count = len(items_dicts)
            filtered_total = total_count
        
        # Convert dicts to FeedItem objects
        feed_items = [FeedItem(**item) for item in items_dicts]
        
        # Store total count and filtered_total as attributes for access by service layer
        # Use a wrapper class or store in a way that doesn't break list operations
        class FeedItemsList(list):
            def __init__(self, items, total_count, filtered_total):
                super().__init__(items)
                self._total_count = total_count
                self._filtered_total = filtered_total
        
        result_list = FeedItemsList(feed_items, total_count, filtered_total)
        # #region agent log
        with open("/home/zusem/threads/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"location":"feed_repository.py:165","message":"Returning FeedItemsList","data":{"total_count":total_count,"filtered_total":filtered_total,"items_count":len(feed_items),"_total_count":result_list._total_count,"_filtered_total":result_list._filtered_total},"timestamp":int(__import__("time").time()*1000),"runId":"run1","hypothesisId":"D"})+"\n")
        # #endregion
        return result_list
    
    def get_latest_feed_items(
        self,
        account_id: str,
        limit: int = 100
    ) -> List[FeedItem]:
        """
        Get latest feed items for account.
        
        Args:
            account_id: Account ID
            limit: Number of items to return
        
        Returns:
            List of latest FeedItem objects
        """
        return self.get_feed_items(
            account_id=account_id,
            limit=limit,
            order_by="fetched_at DESC"
        )
    
    def get_feed_item_history(
        self,
        post_id: str,
        account_id: Optional[str] = None
    ) -> List[FeedItem]:
        """
        Get history of a feed item (all fetched_at timestamps).
        
        Args:
            post_id: Post ID
            account_id: Optional account ID filter
        
        Returns:
            List of FeedItem objects with different fetched_at timestamps
        """
        return self.get_feed_items(
            post_id=post_id,
            account_id=account_id,
            order_by="fetched_at ASC"
        )
    
    # BaseRepository abstract methods implementation
    def get_by_id(self, entity_id: str):
        """Get feed item by ID (not applicable, use get_feed_items with post_id instead)."""
        raise NotImplementedError("Use get_feed_items with post_id parameter instead")
    
    def get_all(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[FeedItem]:
        """
        Get all feed items with optional filters.
        
        Args:
            filters: Optional filter dict (account_id, post_id, username)
            limit: Limit number of results
            offset: Offset for pagination
        
        Returns:
            List of FeedItem objects
        """
        account_id = filters.get("account_id") if filters else None
        post_id = filters.get("post_id") if filters else None
        username = filters.get("username") if filters else None
        
        return self.get_feed_items(
            account_id=account_id,
            post_id=post_id,
            username=username,
            limit=limit,
            offset=offset
        )
    
    def create(self, entity_data: Dict) -> FeedItem:
        """Create feed item (not applicable, use save_feed_items instead)."""
        raise NotImplementedError("Use save_feed_items instead")
    
    def update(self, entity_id: str, entity_data: Dict) -> Optional[FeedItem]:
        """Update feed item (not applicable, feed items are updated via save_feed_items)."""
        raise NotImplementedError("Feed items are updated via save_feed_items with ON DUPLICATE KEY UPDATE")
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete feed item (not supported - feed items are historical tracking data).
        
        Args:
            entity_id: Entity identifier (post_id in this case)
        
        Returns:
            Always raises NotImplementedError
        """
        raise NotImplementedError(
            "Deletion of feed items is not supported. "
            "Feed items are historical tracking data and should be preserved. "
            "If you need to clean up old data, use a separate cleanup script."
        )
