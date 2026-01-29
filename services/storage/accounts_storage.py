"""
Module: services/storage/accounts_storage.py

MySQL storage implementation cho accounts metadata.
"""

# Standard library
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
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


class AccountStorage:
    """
    MySQL storage cho accounts metadata.
    
    Note: Profile directories vẫn giữ trên file system.
    MySQL chỉ store metadata.
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
        """Initialize account storage."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.logger = logger or StructuredLogger(name="account_storage")
        
        # Get connection pool config từ MySQLStorageConfig nếu có
        # Nếu không có, sẽ dùng defaults từ ConnectionPoolConfig
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
    
    def list_accounts(self) -> List[Dict]:
        """
        List all accounts từ MySQL.
        
        Returns:
            List of account dicts
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        account_id,
                        profile_path,
                        created_at,
                        updated_at,
                        is_active,
                        metadata
                    FROM accounts
                    WHERE is_active = TRUE
                    ORDER BY created_at ASC
                """)
                
                rows = cursor.fetchall()
                
                accounts = []
                for row in rows:
                    metadata = row.get("metadata")
                    # Parse JSON nếu metadata là string
                    if metadata and isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = None
                    
                    accounts.append({
                        "account_id": row["account_id"],
                        "profile_path": row.get("profile_path"),
                        "created_at": row.get("created_at"),
                        "updated_at": row.get("updated_at"),
                        "is_active": row.get("is_active", True),
                        "metadata": metadata
                    })
                
                return accounts
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="LIST_ACCOUNTS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e)
            )
            raise StorageError(f"Failed to list accounts: {error_msg}") from e
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get account by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        account_id,
                        profile_path,
                        created_at,
                        updated_at,
                        is_active,
                        metadata
                    FROM accounts
                    WHERE account_id = %s
                """, (account_id,))
                
                row = cursor.fetchone()
                if row:
                    metadata = row.get("metadata")
                    if metadata and isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = None
                    
                    return {
                        "account_id": row["account_id"],
                        "profile_path": row.get("profile_path"),
                        "created_at": row.get("created_at"),
                        "updated_at": row.get("updated_at"),
                        "is_active": row.get("is_active", True),
                        "metadata": metadata
                    }
                return None
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="GET_ACCOUNT",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                account_id=account_id
            )
            raise StorageError(f"Failed to get account: {error_msg}") from e
    
    def create_account(
        self,
        account_id: str,
        profile_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Create account record."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
                
                cursor.execute("""
                    INSERT INTO accounts (
                        account_id,
                        profile_path,
                        metadata,
                        is_active
                    ) VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        profile_path = VALUES(profile_path),
                        metadata = VALUES(metadata),
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    account_id,
                    profile_path,
                    metadata_json,
                    True
                ))
                conn.commit()
                return True
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                account_id=account_id
            )
            raise StorageError(f"Failed to create account: {error_msg}") from e
    
    def update_account(
        self,
        account_id: str,
        profile_path: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update account."""
        try:
            updates = []
            params = []
            
            if profile_path is not None:
                updates.append("profile_path = %s")
                params.append(profile_path)
            
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
            
            if metadata is not None:
                updates.append("metadata = %s")
                params.append(json.dumps(metadata, ensure_ascii=False))
            
            if not updates:
                return True  # No updates
            
            params.append(account_id)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = f"""
                    UPDATE accounts
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE account_id = %s
                """
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            self.logger.log_step(
                step="UPDATE_ACCOUNT",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=safe_get_exception_type_name(e),
                account_id=account_id
            )
            raise StorageError(f"Failed to update account: {error_msg}") from e
    
    def delete_account(self, account_id: str) -> bool:
        """Delete account (soft delete - set is_active=False)."""
        return self.update_account(account_id, is_active=False)
