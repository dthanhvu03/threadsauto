"""
Module: services/storage/config_storage.py

MySQL storage implementation cho application configuration.
"""

# Standard library
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
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
from config.config import Config
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message
)

# Import helper functions (avoid circular import by importing inside methods if needed)
# from config.storage import _dict_to_config, _config_to_dict


class ConfigStorage:
    """MySQL storage cho application configuration."""
    
    CONFIG_KEY = "main"  # Single key for main config
    
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
        """Initialize config storage."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.logger = logger or StructuredLogger(name="config_storage")
        
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
    
    def load_config(self) -> Optional[Config]:
        """
        Load config từ MySQL.
        
        Returns:
            Config instance hoặc None nếu không có
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT config_value
                    FROM app_config
                    WHERE config_key = %s
                """, (self.CONFIG_KEY,))
                
                row = cursor.fetchone()
                if row and row.get("config_value"):
                    # Parse JSON
                    config_dict = json.loads(row["config_value"])
                    # Import here to avoid circular import
                    from config.storage import _dict_to_config
                    return _dict_to_config(config_dict)
                return None
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="LOAD_CONFIG",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e)
            )
            raise StorageError(f"Failed to load config: {error_msg}") from e
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="LOAD_CONFIG",
                result="ERROR",
                error=f"Failed to parse config: {error_msg}",
                error_type=safe_get_exception_type_name(e)
            )
            raise StorageError(f"Failed to parse config: {error_msg}") from e
    
    def save_config(self, config: Config) -> None:
        """Save config to MySQL."""
        try:
            # Import here to avoid circular import
            from config.storage import _config_to_dict
            config_dict = _config_to_dict(config)
            config_json = json.dumps(config_dict, ensure_ascii=False)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO app_config (
                        config_key,
                        config_value,
                        description
                    ) VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        config_value = VALUES(config_value),
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    self.CONFIG_KEY,
                    config_json,
                    "Main application configuration"
                ))
                conn.commit()
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="SAVE_CONFIG",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e)
            )
            raise StorageError(f"Failed to save config: {error_msg}") from e
