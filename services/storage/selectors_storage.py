"""
Module: services/storage/selectors_storage.py

MySQL storage implementation cho selectors.
"""

# Standard library
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

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


class SelectorStorage:
    """MySQL storage cho selectors."""
    
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
        """Initialize selector storage."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.logger = logger or StructuredLogger(name="selector_storage")
        
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
    
    def load_selectors(
        self,
        platform: str = "threads",
        version: str = "v1"
    ) -> Dict[str, List[str]]:
        """
        Load selectors từ MySQL.
        
        Sau migration: mỗi row = 1 selector string, cần group lại theo selector_name.
        Hỗ trợ cả format cũ (JSON array) và format mới (string đơn).
        
        Args:
            platform: Platform name
            version: Version
        
        Returns:
            Dict với selector names và lists of selectors
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT selector_name, selector_value
                    FROM selectors
                    WHERE platform = %s AND version = %s
                    ORDER BY selector_name, id
                """, (platform, version))
                
                rows = cursor.fetchall()
                
                selectors = {}
                for row in rows:
                    selector_name = row["selector_name"]
                    selector_value = row["selector_value"]
                    
                    # Parse selector_value từ MySQL JSON type
                    # MySQL JSON có thể trả về: string (JSON string), list, dict, hoặc đã parse
                    parsed_value = None
                    
                    if isinstance(selector_value, str):
                        # Try to parse as JSON
                        try:
                            parsed_value = json.loads(selector_value)
                        except (json.JSONDecodeError, TypeError):
                            # Nếu không parse được, coi như string đơn
                            parsed_value = selector_value
                    else:
                        # Đã được MySQL/pymysql parse sẵn
                        parsed_value = selector_value
                    
                    # Handle parsed value
                    if isinstance(parsed_value, list):
                        # Old format: JSON array (backward compatibility)
                        if selector_name not in selectors:
                            selectors[selector_name] = []
                        selectors[selector_name].extend(parsed_value)
                    elif isinstance(parsed_value, str):
                        # New format: string đơn (sau migration)
                        if selector_name not in selectors:
                            selectors[selector_name] = []
                        selectors[selector_name].append(parsed_value)
                    else:
                        # Fallback: convert to string
                        if selector_name not in selectors:
                            selectors[selector_name] = []
                        selectors[selector_name].append(str(parsed_value))
                
                return selectors
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="LOAD_SELECTORS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                platform=platform,
                version=version
            )
            raise StorageError(f"Failed to load selectors: {error_msg}") from e
    
    def save_selectors(
        self,
        platform: str,
        version: str,
        selectors: Dict[str, List[str]],
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save selectors to MySQL.
        
        Sau migration: mỗi selector string = 1 row riêng.
        Với mỗi selector_name, xóa rows cũ và insert rows mới.
        
        Args:
            platform: Platform name
            version: Version
            selectors: Dict với selector names và lists of selectors
            metadata: Optional metadata
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
                
                # Save each selector_name
                for selector_name, selector_list in selectors.items():
                    # Xóa tất cả rows cũ cho selector_name này
                    cursor.execute("""
                        DELETE FROM selectors
                        WHERE platform = %s AND version = %s AND selector_name = %s
                    """, (platform, version, selector_name))
                    
                    # Insert từng selector string thành row riêng
                    for selector_string in selector_list:
                        if not isinstance(selector_string, str):
                            # Skip non-string values
                            continue
                        
                        # Wrap string trong JSON string vì column là JSON type
                        selector_value_json = json.dumps(selector_string)
                        
                        cursor.execute("""
                            INSERT INTO selectors (
                                platform,
                                version,
                                selector_name,
                                selector_value,
                                metadata
                            ) VALUES (%s, %s, %s, %s, %s)
                        """, (
                            platform,
                            version,
                            selector_name,
                            selector_value_json,  # JSON string: "selector_string"
                            metadata_json
                        ))
                
                conn.commit()
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="SAVE_SELECTORS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                platform=platform,
                version=version
            )
            raise StorageError(f"Failed to save selectors: {error_msg}") from e
    
    def get_all_versions(self, platform: str) -> List[str]:
        """Get all versions for platform."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT version
                    FROM selectors
                    WHERE platform = %s
                    ORDER BY version ASC
                """, (platform,))
                
                rows = cursor.fetchall()
                return [row["version"] for row in rows]
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="GET_ALL_VERSIONS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                platform=platform
            )
            raise StorageError(f"Failed to get versions: {error_msg}") from e
    
    def delete_version(self, platform: str, version: str) -> bool:
        """Delete a version."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM selectors
                    WHERE platform = %s AND version = %s
                """, (platform, version))
                conn.commit()
                return cursor.rowcount > 0
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="DELETE_VERSION",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                platform=platform,
                version=version
            )
            raise StorageError(f"Failed to delete version: {error_msg}") from e
    
    def get_metadata(
        self,
        platform: str,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata for version."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT metadata
                    FROM selectors
                    WHERE platform = %s AND version = %s
                    LIMIT 1
                """, (platform, version))
                
                row = cursor.fetchone()
                if row and row.get("metadata"):
                    metadata = row["metadata"]
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    return metadata
                return None
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="GET_METADATA",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                platform=platform,
                version=version
            )
            raise StorageError(f"Failed to get metadata: {error_msg}") from e
