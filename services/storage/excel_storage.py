"""
Module: services/storage/excel_storage.py

MySQL storage implementation cho Excel processed files metadata.
"""

# Standard library
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import contextmanager

# Add parent directory to path
_parent_dir = Path(__file__).resolve().parent.parent.parent
_parent_dir_str = str(_parent_dir)
if _parent_dir_str not in sys.path:
    sys.path.insert(0, _parent_dir_str)

# Third-party
import pymysql
import pymysql.err
from pymysql.cursors import DictCursor

# Local
from services.logger import StructuredLogger
from services.exceptions import StorageError
from services.storage.connection_pool import get_connection_pool
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message
)


class ExcelStorage:
    """
    MySQL storage cho Excel processed files metadata.
    
    Manages both processed files and processing locks.
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
        """Initialize Excel storage."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.logger = logger or StructuredLogger(name="excel_storage")
        self.lock_timeout_minutes = 10  # Lock expires after 10 minutes
        
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
        Get MySQL connection with error handling.
        
        Raises:
            StorageError: If connection fails or table doesn't exist
        """
        conn = None
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=DictCursor,
                autocommit=False,
                connect_timeout=10,  # 10 second timeout
                read_timeout=30,     # 30 second read timeout
                write_timeout=30     # 30 second write timeout
            )
            yield conn
        except pymysql.err.OperationalError as e:
            error_code = e.args[0] if e.args else 0
            error_msg = str(e)
            
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            
            # Handle specific MySQL errors
            if error_code == 1146:  # Table doesn't exist
                raise StorageError(
                    f"Database table does not exist. Please ensure migrations have been run. "
                    f"Error: {error_msg}"
                ) from e
            elif error_code == 1045:  # Access denied
                raise StorageError(
                    f"Database access denied. Please check credentials. "
                    f"Error: {error_msg}"
                ) from e
            elif error_code == 2003:  # Can't connect to MySQL server
                raise StorageError(
                    f"Cannot connect to MySQL server at {self.host}:{self.port}. "
                    f"Please check if MySQL is running. Error: {error_msg}"
                ) from e
            elif error_code == 1049:  # Unknown database
                raise StorageError(
                    f"Database '{self.database}' does not exist. "
                    f"Please create the database first. Error: {error_msg}"
                ) from e
            else:
                raise StorageError(f"Database connection error: {error_msg}") from e
        except pymysql.err.Error as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise StorageError(f"Database error: {str(e)}") from e
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                    conn.close()
                except Exception:
                    pass
            raise StorageError(f"Unexpected error connecting to database: {str(e)}") from e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def load_processed_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all processed files.
        
        Returns:
            Dict mapping file_hash -> metadata
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            file_hash,
                            file_name,
                            account_id,
                            processed_at,
                            total_jobs,
                            scheduled_jobs,
                            immediate_jobs,
                            success_count,
                            failed_count,
                            created_at,
                            updated_at
                        FROM excel_processed_files
                        ORDER BY processed_at DESC
                    """)
                    rows = cursor.fetchall()
                    
                    result = {}
                    for row in rows:
                        result[row['file_hash']] = {
                            'file_name': row['file_name'],
                            'account_id': row['account_id'],
                            'processed_at': row['processed_at'].isoformat() if isinstance(row['processed_at'], datetime) else row['processed_at'],
                            'total_jobs': row['total_jobs'],
                            'scheduled_jobs': row['scheduled_jobs'],
                            'immediate_jobs': row['immediate_jobs'],
                            'success_count': row['success_count'],
                            'failed_count': row['failed_count'],
                            'file_hash': row['file_hash']
                        }
                    
                    self.logger.log_step(
                        step="LOAD_PROCESSED_FILES",
                        result="SUCCESS",
                        count=len(result)
                    )
                    return result
        except Exception as e:
            self.logger.log_step(
                step="LOAD_PROCESSED_FILES",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e)
            )
            raise StorageError(f"Failed to load processed files: {str(e)}") from e
    
    def save_processed_file(
        self,
        file_hash: str,
        file_name: str,
        account_id: str,
        total_jobs: int,
        scheduled_jobs: int,
        immediate_jobs: int,
        success_count: int,
        failed_count: int
    ) -> None:
        """
        Save processed file metadata.
        
        Args:
            file_hash: SHA256 hash of file
            file_name: Original file name
            account_id: Account ID used for processing
            total_jobs: Total jobs created
            scheduled_jobs: Number of scheduled jobs
            immediate_jobs: Number of immediate jobs
            success_count: Number of successful jobs
            failed_count: Number of failed jobs
        
        Raises:
            ValueError: If required parameters are invalid
            StorageError: If database operation fails
        """
        # Input validation
        if not file_hash or not isinstance(file_hash, str) or len(file_hash) > 255:
            raise ValueError(f"Invalid file_hash: must be non-empty string <= 255 chars, got {type(file_hash)}")
        
        if not file_name or not isinstance(file_name, str) or len(file_name) > 500:
            raise ValueError(f"Invalid file_name: must be non-empty string <= 500 chars, got {type(file_name)}")
        
        if not account_id or not isinstance(account_id, str) or len(account_id) > 255:
            raise ValueError(f"Invalid account_id: must be non-empty string <= 255 chars, got {type(account_id)}")
        
        # Validate counts are non-negative integers
        for param_name, param_value in [
            ('total_jobs', total_jobs),
            ('scheduled_jobs', scheduled_jobs),
            ('immediate_jobs', immediate_jobs),
            ('success_count', success_count),
            ('failed_count', failed_count)
        ]:
            if not isinstance(param_value, int) or param_value < 0:
                raise ValueError(f"Invalid {param_name}: must be non-negative integer, got {type(param_value)}: {param_value}")
        
        try:
            processed_at = datetime.now()
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO excel_processed_files (
                            file_hash, file_name, account_id, processed_at,
                            total_jobs, scheduled_jobs, immediate_jobs,
                            success_count, failed_count
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON DUPLICATE KEY UPDATE
                            file_name = VALUES(file_name),
                            account_id = VALUES(account_id),
                            processed_at = VALUES(processed_at),
                            total_jobs = VALUES(total_jobs),
                            scheduled_jobs = VALUES(scheduled_jobs),
                            immediate_jobs = VALUES(immediate_jobs),
                            success_count = VALUES(success_count),
                            failed_count = VALUES(failed_count),
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        file_hash, file_name, account_id, processed_at,
                        total_jobs, scheduled_jobs, immediate_jobs,
                        success_count, failed_count
                    ))
                    conn.commit()
                    
                    self.logger.log_step(
                        step="SAVE_PROCESSED_FILE",
                        result="SUCCESS",
                        file_hash=file_hash,
                        file_name=file_name
                    )
        except Exception as e:
            self.logger.log_step(
                step="SAVE_PROCESSED_FILE",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e),
                file_hash=file_hash
            )
            raise StorageError(f"Failed to save processed file: {str(e)}") from e
    
    def remove_processed_file(self, file_hash: str) -> bool:
        """
        Remove processed file from storage.
        
        Args:
            file_hash: SHA256 hash of file
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            ValueError: If file_hash is invalid
        """
        # Input validation
        if not file_hash or not isinstance(file_hash, str):
            raise ValueError(f"Invalid file_hash: must be non-empty string, got {type(file_hash)}")
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM excel_processed_files WHERE file_hash = %s",
                        (file_hash,)
                    )
                    deleted = cursor.rowcount > 0
                    conn.commit()
                    
                    self.logger.log_step(
                        step="REMOVE_PROCESSED_FILE",
                        result="SUCCESS" if deleted else "NOT_FOUND",
                        file_hash=file_hash
                    )
                    return deleted
        except Exception as e:
            self.logger.log_step(
                step="REMOVE_PROCESSED_FILE",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e),
                file_hash=file_hash
            )
            return False
    
    def clear_all_processed_files(self) -> bool:
        """
        Clear all processed files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM excel_processed_files")
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    self.logger.log_step(
                        step="CLEAR_ALL_PROCESSED_FILES",
                        result="SUCCESS",
                        deleted_count=deleted_count
                    )
                    return True
        except Exception as e:
            self.logger.log_step(
                step="CLEAR_ALL_PROCESSED_FILES",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e)
            )
            return False
    
    def get_processing_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active processing locks (not expired).
        
        Also cleans up expired locks automatically.
        
        Returns:
            Dict mapping file_hash -> processing_info
        """
        try:
            # Clean up expired locks first
            self._cleanup_expired_locks()
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            file_hash,
                            file_name,
                            started_at
                        FROM excel_processing_locks
                        WHERE expires_at > NOW()
                        ORDER BY started_at DESC
                    """)
                    rows = cursor.fetchall()
                    
                    result = {}
                    for row in rows:
                        result[row['file_hash']] = {
                            'file_name': row['file_name'],
                            'started_at': row['started_at'].isoformat() if isinstance(row['started_at'], datetime) else row['started_at'],
                            'file_hash': row['file_hash']
                        }
                    
                    return result
        except Exception as e:
            self.logger.log_step(
                step="GET_PROCESSING_FILES",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e)
            )
            return {}
    
    def set_processing_lock(self, file_hash: str, file_name: str) -> bool:
        """
        Set processing lock for file (atomic operation).
        
        Args:
            file_hash: SHA256 hash of file
            file_name: File name
        
        Returns:
            True if lock successful (file not already locked), False if already locked
        
        Raises:
            ValueError: If parameters are invalid
            StorageError: If database operation fails
        """
        # Input validation
        if not file_hash or not isinstance(file_hash, str) or len(file_hash) > 255:
            raise ValueError(f"Invalid file_hash: must be non-empty string <= 255 chars, got {type(file_hash)}")
        
        if not file_name or not isinstance(file_name, str) or len(file_name) > 500:
            raise ValueError(f"Invalid file_name: must be non-empty string <= 500 chars, got {type(file_name)}")
        
        try:
            started_at = datetime.now()
            expires_at = started_at + timedelta(minutes=self.lock_timeout_minutes)
            
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if already locked (and not expired)
                    cursor.execute("""
                        SELECT file_hash 
                        FROM excel_processing_locks 
                        WHERE file_hash = %s AND expires_at > NOW()
                    """, (file_hash,))
                    if cursor.fetchone():
                        # Already locked
                        return False
                    
                    # Insert new lock
                    cursor.execute("""
                        INSERT INTO excel_processing_locks (
                            file_hash, file_name, started_at, expires_at
                        ) VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            file_name = VALUES(file_name),
                            started_at = VALUES(started_at),
                            expires_at = VALUES(expires_at)
                    """, (file_hash, file_name, started_at, expires_at))
                    conn.commit()
                    
                    self.logger.log_step(
                        step="SET_PROCESSING_LOCK",
                        result="SUCCESS",
                        file_hash=file_hash,
                        file_name=file_name
                    )
                    return True
        except Exception as e:
            self.logger.log_step(
                step="SET_PROCESSING_LOCK",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e),
                file_hash=file_hash
            )
            return False
    
    def release_processing_lock(self, file_hash: str) -> None:
        """
        Release processing lock for file.
        
        Args:
            file_hash: SHA256 hash of file
        
        Raises:
            ValueError: If file_hash is invalid
        """
        # Input validation
        if not file_hash or not isinstance(file_hash, str):
            raise ValueError(f"Invalid file_hash: must be non-empty string, got {type(file_hash)}")
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM excel_processing_locks WHERE file_hash = %s",
                        (file_hash,)
                    )
                    conn.commit()
                    
                    self.logger.log_step(
                        step="RELEASE_PROCESSING_LOCK",
                        result="SUCCESS",
                        file_hash=file_hash
                    )
        except Exception as e:
            self.logger.log_step(
                step="RELEASE_PROCESSING_LOCK",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e),
                file_hash=file_hash
            )
    
    def _cleanup_expired_locks(self) -> None:
        """Clean up expired processing locks."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM excel_processing_locks WHERE expires_at <= NOW()"
                    )
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        conn.commit()
                        self.logger.log_step(
                            step="CLEANUP_EXPIRED_LOCKS",
                            result="SUCCESS",
                            deleted_count=deleted_count
                        )
        except Exception as e:
            self.logger.log_step(
                step="CLEANUP_EXPIRED_LOCKS",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e)
            )
