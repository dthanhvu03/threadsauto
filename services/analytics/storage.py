"""
Module: services/analytics/storage.py

MySQL storage implementation cho thread metrics.
"""

# Standard library
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

# Third-party
import pymysql
from pymysql.cursors import DictCursor

# Local
from services.logger import StructuredLogger
from services.exceptions import StorageError
from services.storage.connection_pool import get_connection_pool


class MetricsStorage:
    """
    MySQL storage cho thread metrics.
    
    Lưu trữ metrics theo thời gian trong MySQL database.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "threads_user",
        password: str = "",
        database: str = "threads_analytics",
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize metrics storage.
        
        Args:
            host: MySQL host
            port: MySQL port
            user: MySQL user
            password: MySQL password
            database: Database name
            logger: Structured logger
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.logger = logger or StructuredLogger(name="metrics_storage")
        
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
            pool_size=pool_size,
            max_overflow=max_overflow,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            logger=self.logger
        )
    
    def save_metrics(
        self,
        thread_id: str,
        account_id: str,
        views: Optional[int],
        likes: int,
        replies: int,
        reposts: int,
        shares: int,
        fetched_at: Optional[datetime] = None
    ) -> bool:
        """
        Save metrics to database.
        
        Args:
            thread_id: Thread ID
            account_id: Account ID
            views: View count (optional)
            likes: Like count
            replies: Reply count
            reposts: Repost count (Đăng lại)
            shares: Share count (Chia sẻ)
            fetched_at: Fetch timestamp (default: now)
        
        Returns:
            True if successful, False otherwise
        """
        if fetched_at is None:
            fetched_at = datetime.now()
        
        try:
            with self._pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        INSERT INTO thread_metrics 
                        (thread_id, account_id, views, likes, replies, reposts, shares, fetched_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            views = VALUES(views),
                            likes = VALUES(likes),
                            replies = VALUES(replies),
                            reposts = VALUES(reposts),
                            shares = VALUES(shares),
                            fetched_at = VALUES(fetched_at)
                    """
                    
                    cursor.execute(query, (
                        thread_id,
                        account_id,
                        views,
                        likes,
                        replies,
                        reposts,
                        shares,
                        fetched_at
                    ))
                    
                    conn.commit()
                    
                    self.logger.log_step(
                        step="SAVE_METRICS",
                        result="SUCCESS",
                        thread_id=thread_id,
                        account_id=account_id,
                        likes=likes,
                        replies=replies,
                        shares=shares
                    )
                    
                    return True
                    
        except Exception as e:
            self.logger.log_step(
                step="SAVE_METRICS",
                result="ERROR",
                error=f"Failed to save metrics: {str(e)}",
                error_type=type(e).__name__,
                thread_id=thread_id
            )
            return False
    
    def get_latest_metrics(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get latest metrics for a thread.
        
        Args:
            thread_id: Thread ID
        
        Returns:
            Metrics dict or None
        """
        try:
            with self._pool.get_connection() as conn:
                with conn.cursor(DictCursor) as cursor:
                    query = """
                        SELECT * FROM thread_metrics
                        WHERE thread_id = %s
                        ORDER BY fetched_at DESC
                        LIMIT 1
                    """
                    
                    cursor.execute(query, (thread_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        return {
                            "thread_id": row["thread_id"],
                            "account_id": row["account_id"],
                            "views": row["views"],
                            "likes": row["likes"],
                            "replies": row["replies"],
                            "reposts": row.get("reposts", 0),
                            "shares": row["shares"],
                            "fetched_at": row["fetched_at"]
                        }
                    
                    return None
                    
        except Exception as e:
            self.logger.log_step(
                step="GET_LATEST_METRICS",
                result="ERROR",
                error=f"Failed to get latest metrics: {str(e)}",
                error_type=type(e).__name__,
                thread_id=thread_id
            )
            return None
    
    def has_recent_metrics(self, thread_id: str, hours: int = 1) -> bool:
        """
        Check if thread has metrics fetched within specified hours.
        
        Args:
            thread_id: Thread ID
            hours: Number of hours
        
        Returns:
            True if recent metrics exist, False otherwise
        """
        try:
            with self._pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT COUNT(*) as count FROM thread_metrics
                        WHERE thread_id = %s
                        AND fetched_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                    """
                    
                    cursor.execute(query, (thread_id, hours))
                    row = cursor.fetchone()
                    
                    return row[0] > 0 if row else False
                    
        except Exception as e:
            self.logger.log_step(
                step="HAS_RECENT_METRICS",
                result="ERROR",
                error=f"Failed to check recent metrics: {str(e)}",
                error_type=type(e).__name__,
                thread_id=thread_id
            )
            return False
    
    def get_account_metrics_history(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metrics history for an account.
        
        Args:
            account_id: Account ID
            start_date: Optional start date
            end_date: Optional end date
        
        Returns:
            List of metrics dicts
        """
        try:
            with self._pool.get_connection() as conn:
                with conn.cursor(DictCursor) as cursor:
                    query = """
                        SELECT * FROM thread_metrics
                        WHERE account_id = %s
                    """
                    params = [account_id]
                    
                    if start_date:
                        query += " AND fetched_at >= %s"
                        params.append(start_date)
                    
                    if end_date:
                        query += " AND fetched_at <= %s"
                        params.append(end_date)
                    
                    query += " ORDER BY fetched_at ASC"
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    return [
                        {
                            "thread_id": row["thread_id"],
                            "account_id": row["account_id"],
                            "views": row.get("views"),
                            "likes": row["likes"],
                            "replies": row["replies"],
                            "reposts": row.get("reposts", 0),
                            "shares": row["shares"],
                            "fetched_at": row["fetched_at"]
                        }
                        for row in rows
                    ]
                    
        except Exception as e:
            self.logger.log_step(
                step="GET_ACCOUNT_METRICS_HISTORY",
                result="ERROR",
                error=f"Failed to get account metrics history: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return []
    
    def get_thread_metrics_history(
        self,
        thread_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metrics history for a thread.
        
        Args:
            thread_id: Thread ID
            start_date: Optional start date
            end_date: Optional end date
        
        Returns:
            List of metrics dicts
        """
        try:
            with self._pool.get_connection() as conn:
                with conn.cursor(DictCursor) as cursor:
                    query = """
                        SELECT * FROM thread_metrics
                        WHERE thread_id = %s
                    """
                    params = [thread_id]
                    
                    if start_date:
                        query += " AND fetched_at >= %s"
                        params.append(start_date)
                    
                    if end_date:
                        query += " AND fetched_at <= %s"
                        params.append(end_date)
                    
                    query += " ORDER BY fetched_at ASC"
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    return [
                        {
                            "thread_id": row["thread_id"],
                            "account_id": row["account_id"],
                            "views": row.get("views"),
                            "likes": row["likes"],
                            "replies": row["replies"],
                            "reposts": row.get("reposts", 0),
                            "shares": row["shares"],
                            "fetched_at": row["fetched_at"]
                        }
                        for row in rows
                    ]
                    
        except Exception as e:
            self.logger.log_step(
                step="GET_THREAD_METRICS_HISTORY",
                result="ERROR",
                error=f"Failed to get thread metrics history: {str(e)}",
                error_type=type(e).__name__,
                thread_id=thread_id
            )
            return []