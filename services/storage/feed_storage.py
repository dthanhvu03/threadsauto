"""
Module: services/storage/feed_storage.py

MySQL storage implementation cho feed items.
"""

# Standard library
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager
from datetime import datetime

# Add parent directory to path
_parent_dir = Path(__file__).resolve().parent.parent.parent
_parent_dir_str = str(_parent_dir)
if _parent_dir_str not in sys.path:
    sys.path.insert(0, _parent_dir_str)

# Third-party
import pymysql
from pymysql.cursors import DictCursor

# Local
from services.logger import StructuredLogger
from services.exceptions import StorageError
from services.storage.connection_pool import get_connection_pool
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message
)


class FeedStorage:
    """
    MySQL storage cho feed items.
    
    Lưu feed posts từ Threads với history tracking.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "threads_user",
        password: str = "",
        database: str = "threads_analytics",
        charset: str = "utf8mb4",
        logger: Optional[StructuredLogger] = None
    ):
        """Initialize feed storage."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.logger = logger or StructuredLogger(name="feed_storage")
        
        # Get connection pool config từ MySQLStorageConfig nếu có
        try:
            from config.storage_config_loader import get_storage_config_from_env
            storage_config = get_storage_config_from_env()
            pool_config = storage_config.mysql.pool if storage_config.mysql else None
            
            pool_size = pool_config.pool_size if pool_config else 10
            max_overflow = pool_config.max_overflow if pool_config else 20
            read_timeout = pool_config.read_timeout_seconds if pool_config else 30
            write_timeout = pool_config.write_timeout_seconds if pool_config else 30
        except Exception:
            # Fallback to defaults nếu không load được config
            pool_size = 10
            max_overflow = 20
            read_timeout = 30
            write_timeout = 30
        
        # Get connection pool
        self._pool = get_connection_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset,
            pool_size=pool_size,
            max_overflow=max_overflow,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            logger=self.logger
        )
    
    @contextmanager
    def _get_connection(self):
        """
        Get MySQL connection from pool.
        
        Uses connection pool for better performance.
        """
        try:
            # Get connection from pool
            with self._pool.get_connection() as conn:
                yield conn
        except StorageError:
            # Re-raise StorageError as-is
            raise
        except Exception as e:
            # Wrap other errors
            raise StorageError(f"Database error: {str(e)}") from e
    
    def save_feed_items(
        self,
        account_id: str,
        feed_items: List[Dict],
        fetched_at: Optional[datetime] = None
    ) -> int:
        """
        Save feed items to database.
        
        Args:
            account_id: Account ID
            feed_items: List of feed item dicts
            fetched_at: Optional fetch timestamp (defaults to now)
        
        Returns:
            Number of items saved
        """
        if not feed_items:
            return 0
        
        if fetched_at is None:
            fetched_at = datetime.utcnow()
        
        try:
            saved_count = 0
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for item in feed_items:
                    # Prepare JSON fields
                    media_urls_json = json.dumps(item.get("media_urls", []), ensure_ascii=False) if item.get("media_urls") else None
                    hashtags_json = json.dumps(item.get("hashtags", []), ensure_ascii=False) if item.get("hashtags") else None
                    mentions_json = json.dumps(item.get("mentions", []), ensure_ascii=False) if item.get("mentions") else None
                    links_json = json.dumps(item.get("links", []), ensure_ascii=False) if item.get("links") else None
                    quoted_post_json = json.dumps(item.get("quoted_post"), ensure_ascii=False) if item.get("quoted_post") else None
                    
                    cursor.execute("""
                        INSERT INTO feed_items (
                            post_id, account_id, username, text,
                            like_count, reply_count, repost_count, share_count, view_count,
                            media_urls, timestamp, timestamp_iso,
                            user_id, user_display_name, user_avatar_url, is_verified,
                            post_url, shortcode, is_reply, parent_post_id, thread_id,
                            quoted_post, hashtags, mentions, links,
                            media_type, video_duration, fetched_at
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s
                        )
                        ON DUPLICATE KEY UPDATE
                            like_count = VALUES(like_count),
                            reply_count = VALUES(reply_count),
                            repost_count = VALUES(repost_count),
                            share_count = VALUES(share_count),
                            view_count = VALUES(view_count),
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        item.get("post_id"),
                        account_id,
                        item.get("username"),
                        item.get("text"),
                        item.get("like_count", 0),
                        item.get("reply_count", 0),
                        item.get("repost_count", 0),
                        item.get("share_count", 0),
                        item.get("view_count"),
                        media_urls_json,
                        item.get("timestamp"),
                        item.get("timestamp_iso"),
                        item.get("user_id"),
                        item.get("user_display_name"),
                        item.get("user_avatar_url"),
                        item.get("is_verified", False),
                        item.get("post_url"),
                        item.get("shortcode"),
                        item.get("is_reply", False),
                        item.get("parent_post_id"),
                        item.get("thread_id"),
                        quoted_post_json,
                        hashtags_json,
                        mentions_json,
                        links_json,
                        item.get("media_type"),
                        item.get("video_duration"),
                        fetched_at
                    ))
                    saved_count += 1
                
                conn.commit()
                
                self.logger.log_step(
                    step="SAVE_FEED_ITEMS",
                    result="SUCCESS",
                    account_id=account_id,
                    items_saved=saved_count,
                    total_items=len(feed_items),
                    fetched_at=str(fetched_at)
                )
                
                return saved_count
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="SAVE_FEED_ITEMS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                account_id=account_id,
                total_items=len(feed_items)
            )
            raise StorageError(f"Failed to save feed items: {error_msg}") from e
    
    def get_feed_items(
        self,
        account_id: Optional[str] = None,
        post_id: Optional[str] = None,
        username: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = "fetched_at DESC",
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        Get feed items from database.
        
        Args:
            account_id: Filter by account ID
            post_id: Filter by post ID
            username: Filter by username
            limit: Limit number of results
            offset: Offset for pagination
            order_by: Order by clause (default: fetched_at DESC)
            filters: Optional FeedFilters dict with min_likes, max_likes, etc.
        
        Returns:
            Dict with:
            - items: List of feed item dicts
            - total: Total count for account_id (without filters)
            - filtered_total: Total count with filters applied
        """
        try:
            self.logger.log_step(
                step="GET_FEED_ITEMS_START",
                result="IN_PROGRESS",
                account_id=account_id,
                post_id=post_id,
                username=username,
                limit=limit,
                offset=offset
            )
            print(f"[FeedStorage] get_feed_items: Starting query for account_id={account_id}")
            
            # Get connection with timeout protection
            import signal
            import threading
            
            connection_timeout = 5  # 5 seconds timeout for getting connection
            query_timeout = 25  # 25 seconds timeout for query execution
            
            with self._get_connection() as conn:
                print(f"[FeedStorage] get_feed_items: Got connection, setting query timeout")
                cursor = conn.cursor()
                # Set query timeout (MySQL 5.7.8+)
                query_timeout = 25  # 25 seconds timeout for query execution
                try:
                    cursor.execute("SET SESSION max_execution_time = %s", (query_timeout * 1000,))  # milliseconds
                    print(f"[FeedStorage] get_feed_items: Query timeout set to {query_timeout}s")
                except Exception as e:
                    print(f"[FeedStorage] Warning: Could not set query timeout (MySQL version may not support it): {e}")
                
                # Build base WHERE clause (account_id, post_id, username)
                base_where_conditions = []
                base_params = []
                
                if account_id:
                    base_where_conditions.append("account_id = %s")
                    base_params.append(account_id)
                
                if post_id:
                    base_where_conditions.append("post_id = %s")
                    base_params.append(post_id)
                
                if username:
                    base_where_conditions.append("username = %s")
                    base_params.append(username)
                
                base_where_clause = " AND ".join(base_where_conditions) if base_where_conditions else "1=1"
                
                # Get total count (without filters, only base conditions)
                total_count_query = f"SELECT COUNT(*) as total FROM feed_items WHERE {base_where_clause}"
                cursor.execute(total_count_query, base_params)
                total_count_result = cursor.fetchone()
                total_count = total_count_result['total'] if total_count_result else 0
                
                # Build filter WHERE conditions
                filter_where_conditions = base_where_conditions.copy()
                filter_params = base_params.copy()
                
                if filters:
                    if filters.get("min_likes") is not None:
                        filter_where_conditions.append("like_count >= %s")
                        filter_params.append(filters["min_likes"])
                    
                    if filters.get("max_likes") is not None:
                        filter_where_conditions.append("like_count <= %s")
                        filter_params.append(filters["max_likes"])
                    
                    if filters.get("min_replies") is not None:
                        filter_where_conditions.append("reply_count >= %s")
                        filter_params.append(filters["min_replies"])
                    
                    if filters.get("min_reposts") is not None:
                        filter_where_conditions.append("repost_count >= %s")
                        filter_params.append(filters["min_reposts"])
                    
                    if filters.get("min_shares") is not None:
                        filter_where_conditions.append("share_count >= %s")
                        filter_params.append(filters["min_shares"])
                    
                    if filters.get("max_shares") is not None:
                        filter_where_conditions.append("share_count <= %s")
                        filter_params.append(filters["max_shares"])
                    
                    if filters.get("has_media") is not None:
                        if filters["has_media"]:
                            filter_where_conditions.append("media_count > 0")
                        else:
                            filter_where_conditions.append("(media_count = 0 OR media_count IS NULL)")
                    
                    if filters.get("text_contains"):
                        filter_where_conditions.append("text LIKE %s")
                        filter_params.append(f"%{filters['text_contains']}%")
                    
                    if filters.get("after_timestamp") is not None:
                        filter_where_conditions.append("timestamp >= %s")
                        filter_params.append(filters["after_timestamp"])
                    
                    if filters.get("before_timestamp") is not None:
                        filter_where_conditions.append("timestamp <= %s")
                        filter_params.append(filters["before_timestamp"])
                
                # Build final WHERE clause with filters
                where_clause = " AND ".join(filter_where_conditions) if filter_where_conditions else "1=1"
                
                # Get filtered count (with filters applied)
                filtered_count_query = f"SELECT COUNT(*) as total FROM feed_items WHERE {where_clause}"
                cursor.execute(filtered_count_query, filter_params)
                filtered_count_result = cursor.fetchone()
                filtered_total = filtered_count_result['total'] if filtered_count_result else 0
                
                # Build main query
                query = f"""
                    SELECT 
                        id, post_id, account_id, username, text,
                        like_count, reply_count, repost_count, share_count, view_count,
                        media_urls, timestamp, timestamp_iso,
                        user_id, user_display_name, user_avatar_url, is_verified,
                        post_url, shortcode, is_reply, parent_post_id, thread_id,
                        quoted_post, hashtags, mentions, links,
                        media_type, video_duration, fetched_at,
                        created_at, updated_at
                    FROM feed_items
                    WHERE {where_clause}
                    ORDER BY {order_by}
                """
                
                query_params = filter_params.copy()
                if limit:
                    query += " LIMIT %s"
                    query_params.append(limit)
                    
                    if offset:
                        query += " OFFSET %s"
                        query_params.append(offset)
                
                self.logger.log_step(
                    step="GET_FEED_ITEMS_EXECUTE",
                    result="IN_PROGRESS",
                    query=query[:200],  # Log first 200 chars
                    params_count=len(query_params),
                    total_count=total_count
                )
                
                print(f"[FeedStorage] get_feed_items: Executing query with {len(query_params)} params")
                print(f"[FeedStorage] get_feed_items: Query: {query[:100]}...")
                print(f"[FeedStorage] get_feed_items: Total count: {total_count}")
                
                import time
                start_time = time.time()
                cursor.execute(query, query_params)
                execute_time = time.time() - start_time
                print(f"[FeedStorage] get_feed_items: Query executed in {execute_time:.2f}s")
                
                start_time = time.time()
                rows = cursor.fetchall()
                fetch_time = time.time() - start_time
                print(f"[FeedStorage] get_feed_items: Fetched {len(rows)} rows in {fetch_time:.2f}s")
                
                self.logger.log_step(
                    step="GET_FEED_ITEMS_FETCHED",
                    result="SUCCESS",
                    rows_count=len(rows),
                    total_count=total_count,
                    filtered_total=filtered_total
                )
                
                # Parse JSON fields
                feed_items = []
                for row in rows:
                    item = dict(row)
                    
                    # Parse JSON fields
                    for json_field in ["media_urls", "hashtags", "mentions", "links", "quoted_post"]:
                        if item.get(json_field) is None:
                            # Normalize None to [] for list fields, None for quoted_post
                            item[json_field] = [] if json_field != "quoted_post" else None
                        elif isinstance(item[json_field], str):
                            try:
                                item[json_field] = json.loads(item[json_field])
                            except json.JSONDecodeError:
                                item[json_field] = [] if json_field != "quoted_post" else None
                        # If already a list/dict, keep it as is
                    
                    feed_items.append(item)
                
                # Return items with total count (without filters) and filtered_total (with filters)
                return {
                    "items": feed_items,
                    "total": total_count,
                    "filtered_total": filtered_total
                }
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="GET_FEED_ITEMS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                account_id=account_id,
                post_id=post_id,
                username=username
            )
            raise StorageError(f"Failed to get feed items: {error_msg}") from e
    
    def get_latest_feed_items(
        self,
        account_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get latest feed items for account.
        
        Args:
            account_id: Account ID
            limit: Number of items to return
        
        Returns:
            List of latest feed item dicts
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
    ) -> List[Dict]:
        """
        Get history of a feed item (all fetched_at timestamps).
        
        Args:
            post_id: Post ID
            account_id: Optional account ID filter
        
        Returns:
            List of feed item dicts with different fetched_at timestamps
        """
        return self.get_feed_items(
            post_id=post_id,
            account_id=account_id,
            order_by="fetched_at ASC"
        )
    
    def get_media_url(self, post_id: str, index: int) -> Optional[str]:
        """
        Get media URL from database for a specific post and index.
        
        Args:
            post_id: Post ID
            index: Media index (0-based)
        
        Returns:
            Media URL or None if not found
        """
        try:
            result = self.get_feed_items(
                post_id=post_id,
                limit=1
            )
            
            items = result.get("items", [])
            if not items:
                return None
            
            item = items[0]
            media_urls = item.get("media_urls", [])
            
            if not isinstance(media_urls, list):
                return None
            
            if index < 0 or index >= len(media_urls):
                return None
            
            return media_urls[index]
            
        except Exception as e:
            self.logger.log_step(
                step="GET_MEDIA_URL",
                result="ERROR",
                error=str(e),
                post_id=post_id,
                index=index
            )
            return None
    
    def get_avatar_url(self, user_id: str) -> Optional[str]:
        """
        Get avatar URL from database for a specific user.
        
        Args:
            user_id: User ID
        
        Returns:
            Avatar URL or None if not found
        """
        try:
            # Query for user_id in recent items
            result = self.get_feed_items(limit=100)
            
            items = result.get("items", [])
            for item in items:
                if item.get("user_id") == user_id:
                    avatar_url = item.get("user_avatar_url")
                    if avatar_url:
                        return avatar_url
            
            return None
            
        except Exception as e:
            self.logger.log_step(
                step="GET_AVATAR_URL",
                result="ERROR",
                error=str(e),
                user_id=user_id
            )
            return None
