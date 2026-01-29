"""
Module: services/scheduler/storage/mysql_storage.py

MySQL database storage implementation cho scheduler.
Replaces JSON file-based storage with MySQL database.
"""

# Standard library
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from contextlib import contextmanager

# Add parent directory to path
_parent_dir = Path(__file__).resolve().parent.parent.parent.parent
_parent_dir_str = str(_parent_dir)
if _parent_dir_str not in sys.path:
    sys.path.insert(0, _parent_dir_str)

# Third-party
import pymysql
from pymysql.cursors import DictCursor

# Local
from services.scheduler.storage.base import JobStorageBase
from services.scheduler.models import (
    ScheduledJob,
    JobStatus,
    JobPriority,
    Platform
)
from services.logger import StructuredLogger
from services.exceptions import StorageError
from services.storage.connection_pool import get_connection_pool
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message
)


class MySQLJobStorage(JobStorageBase):
    """
    MySQL implementation của job storage.
    
    Replaces JSON file-based storage with MySQL database.
    All operations use transactions for data integrity.
    
    Attributes:
        host: MySQL host
        port: MySQL port
        user: MySQL user
        password: MySQL password
        database: Database name
        charset: Character set (default: utf8mb4)
        logger: Structured logger
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
        """
        Initialize MySQL job storage.
        
        Args:
            host: MySQL host
            port: MySQL port
            user: MySQL user
            password: MySQL password
            database: Database name
            charset: Character set (default: utf8mb4 for emoji support)
            logger: Structured logger (optional)
        
        Raises:
            StorageError: Nếu không thể connect to MySQL
        """
        # Initialize base class
        super().__init__(logger or StructuredLogger(name="mysql_job_storage"))
        
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        
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
        
        # Test connection
        try:
            with self._get_connection() as conn:
                conn.ping(reconnect=True)
            
            self.logger.log_step(
                step="INIT_MYSQL_JOB_STORAGE",
                result="SUCCESS",
                host=host,
                port=port,
                database=database
            )
        except Exception as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="INIT_MYSQL_JOB_STORAGE",
                result="ERROR",
                error=error_msg,
                error_type=error_type,
                host=host,
                database=database
            )
            
            raise StorageError(
                f"Failed to connect to MySQL: {error_msg}"
            ) from e
    
    @contextmanager
    def _get_connection(self):
        """
        Get MySQL connection from pool (context manager).
        
        Uses connection pool for better performance.
        
        Yields:
            pymysql.Connection instance
        
        Raises:
            StorageError: Nếu connection fails
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
    
    def load_jobs(self) -> Dict[str, ScheduledJob]:
        """
        Load tất cả jobs từ MySQL.
        
        Returns:
            Dict mapping job_id -> ScheduledJob
        
        Raises:
            StorageError: Nếu có lỗi khi load
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        job_id,
                        account_id,
                        content,
                        scheduled_time,
                        priority,
                        status,
                        platform,
                        max_retries,
                        retry_count,
                        created_at,
                        started_at,
                        completed_at,
                        error,
                        thread_id,
                        status_message,
                        link_aff
                    FROM jobs
                    ORDER BY scheduled_time ASC
                """)
                
                rows = cursor.fetchall()
                
                jobs: Dict[str, ScheduledJob] = {}
                loaded_count = 0
                failed_count = 0
                
                for row in rows:
                    try:
                        job = self._row_to_job(row)
                        jobs[job.job_id] = job
                        loaded_count += 1
                    except (KeyError, ValueError, TypeError) as e:
                        failed_count += 1
                        job_id = row.get('job_id', 'unknown')
                        error_msg = safe_get_exception_message(e)
                        error_type = safe_get_exception_type_name(e)
                        
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="WARNING",
                            error=f"Failed to parse job {job_id}: {error_msg}",
                            error_type=error_type,
                            job_id=job_id
                        )
                        continue
                    except Exception as e:
                        failed_count += 1
                        job_id = row.get('job_id', 'unknown')
                        error_msg = safe_get_exception_message(e)
                        error_type = safe_get_exception_type_name(e)
                        
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="ERROR",
                            error=f"Unexpected error parsing job {job_id}: {error_msg}",
                            error_type=error_type,
                            job_id=job_id
                        )
                        continue
                
                self.logger.log_step(
                    step="LOAD_JOBS",
                    result="SUCCESS",
                    jobs_count=len(jobs),
                    loaded_count=loaded_count,
                    failed_count=failed_count
                )
                
                return jobs
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="LOAD_JOBS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=error_type
            )
            
            raise StorageError(f"Failed to load jobs from MySQL: {error_msg}") from e
        except Exception as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="LOAD_JOBS",
                result="ERROR",
                error=f"Unexpected error: {error_msg}",
                error_type=error_type
            )
            
            raise StorageError(f"Unexpected error loading jobs: {error_msg}") from e
    
    def save_jobs(self, jobs: Dict[str, ScheduledJob]) -> None:
        """
        Save jobs to MySQL (atomic transaction).
        
        Uses INSERT ... ON DUPLICATE KEY UPDATE for upsert operation.
        All jobs saved in single transaction for atomicity.
        
        Args:
            jobs: Dict mapping job_id -> ScheduledJob
        
        Raises:
            StorageError: Nếu có lỗi khi save
        """
        if not jobs:
            self.logger.log_step(
                step="SAVE_JOBS",
                result="INFO",
                note="No jobs to save"
            )
            return
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Start transaction
                conn.begin()
                
                try:
                    saved_count = 0
                    failed_count = 0
                    
                    # Save/update jobs
                    for job in jobs.values():
                        try:
                            self._save_job(cursor, job)
                            saved_count += 1
                        except Exception as e:
                            failed_count += 1
                            error_msg = safe_get_exception_message(e)
                            error_type = safe_get_exception_type_name(e)
                            
                            self.logger.log_step(
                                step="SAVE_JOBS",
                                result="WARNING",
                                error=f"Failed to save job {job.job_id}: {error_msg}",
                                error_type=error_type,
                                job_id=job.job_id
                            )
                            # Continue với các jobs khác
                            continue
                    
                    # Cleanup: Delete jobs from database that are not in memory
                    # This handles explicit deletions via remove_job()
                    job_ids_in_memory = set(jobs.keys())
                    if job_ids_in_memory:
                        # Build parameterized query for job_ids NOT IN memory
                        # Use tuple for IN clause
                        placeholders = ','.join(['%s'] * len(job_ids_in_memory))
                        delete_query = f"DELETE FROM jobs WHERE job_id NOT IN ({placeholders})"
                        cursor.execute(delete_query, tuple(job_ids_in_memory))
                        deleted_count = cursor.rowcount
                        
                        if deleted_count > 0:
                            self.logger.log_step(
                                step="CLEANUP_DELETED_JOBS",
                                result="INFO",
                                note=f"Deleted {deleted_count} jobs from database that are not in memory",
                                deleted_count=deleted_count,
                                jobs_in_memory_count=len(job_ids_in_memory)
                            )
                    else:
                        # If no jobs in memory, delete all jobs from database
                        cursor.execute("DELETE FROM jobs")
                        deleted_count = cursor.rowcount
                        
                        if deleted_count > 0:
                            self.logger.log_step(
                                step="CLEANUP_DELETED_JOBS",
                                result="INFO",
                                note=f"Deleted all {deleted_count} jobs from database (no jobs in memory)",
                                deleted_count=deleted_count
                            )
                    
                    # Commit transaction
                    conn.commit()
                    
                    self.logger.log_step(
                        step="SAVE_JOBS",
                        result="SUCCESS",
                        total_jobs=len(jobs),
                        saved_count=saved_count,
                        failed_count=failed_count
                    )
                    
                    if failed_count > 0:
                        self.logger.log_step(
                            step="SAVE_JOBS",
                            result="WARNING",
                            note=f"{failed_count} jobs failed to save (partial success)"
                        )
                        
                except Exception as e:
                    # Rollback transaction on error
                    conn.rollback()
                    
                    error_msg = safe_get_exception_message(e)
                    error_type = safe_get_exception_type_name(e)
                    
                    self.logger.log_step(
                        step="SAVE_JOBS",
                        result="ERROR",
                        error=f"Transaction failed, rolled back: {error_msg}",
                        error_type=error_type
                    )
                    
                    raise StorageError(
                        f"Failed to save jobs (transaction rolled back): {error_msg}"
                    ) from e
                    
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="SAVE_JOBS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=error_type
            )
            
            raise StorageError(f"MySQL error saving jobs: {error_msg}") from e
        except Exception as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="SAVE_JOBS",
                result="ERROR",
                error=f"Unexpected error: {error_msg}",
                error_type=error_type
            )
            
            raise StorageError(f"Unexpected error saving jobs: {error_msg}") from e
    
    def _save_job(self, cursor, job: ScheduledJob) -> None:
        """
        Save single job (used in transaction).
        
        Args:
            cursor: MySQL cursor
            job: ScheduledJob to save
        
        Raises:
            pymysql.Error: Nếu SQL execution fails
        """
        cursor.execute("""
            INSERT INTO jobs (
                job_id, account_id, content, scheduled_time, priority, status,
                platform, max_retries, retry_count, created_at, started_at,
                completed_at, error, thread_id, status_message, link_aff
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                account_id = VALUES(account_id),
                content = VALUES(content),
                scheduled_time = VALUES(scheduled_time),
                priority = VALUES(priority),
                status = VALUES(status),
                platform = VALUES(platform),
                max_retries = VALUES(max_retries),
                retry_count = VALUES(retry_count),
                started_at = VALUES(started_at),
                completed_at = VALUES(completed_at),
                error = VALUES(error),
                thread_id = VALUES(thread_id),
                status_message = VALUES(status_message),
                link_aff = VALUES(link_aff)
        """, (
            job.job_id,
            job.account_id,
            job.content,
            job.scheduled_time,
            job.priority.value,
            job.status.value,
            job.platform.value,
            job.max_retries,
            job.retry_count,
            job.created_at,
            job.started_at,
            job.completed_at,
            job.error,
            job.thread_id,
            job.status_message,
            job.link_aff
        ))
    
    def get_job_by_id(self, job_id: str) -> Optional[ScheduledJob]:
        """
        Get job by ID (optimized with direct query).
        
        Args:
            job_id: Job ID to find
        
        Returns:
            ScheduledJob nếu tìm thấy, None nếu không
        
        Raises:
            StorageError: Nếu có lỗi khi query
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        job_id,
                        account_id,
                        content,
                        scheduled_time,
                        priority,
                        status,
                        platform,
                        max_retries,
                        retry_count,
                        created_at,
                        started_at,
                        completed_at,
                        error,
                        thread_id,
                        status_message,
                        link_aff
                    FROM jobs
                    WHERE job_id = %s
                """, (job_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_job(row)
                return None
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="GET_JOB_BY_ID",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=error_type,
                job_id=job_id
            )
            
            raise StorageError(f"Failed to get job by ID: {error_msg}") from e
        except Exception as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="GET_JOB_BY_ID",
                result="ERROR",
                error=f"Unexpected error: {error_msg}",
                error_type=error_type,
                job_id=job_id
            )
            
            raise StorageError(f"Unexpected error getting job: {error_msg}") from e
    
    def get_jobs_by_status(
        self,
        status: JobStatus,
        limit: Optional[int] = None
    ) -> List[ScheduledJob]:
        """
        Get jobs by status (optimized with direct query).
        
        Args:
            status: JobStatus to filter by
            limit: Optional limit on number of results
        
        Returns:
            List of ScheduledJob với status matching, sorted by scheduled_time
        
        Raises:
            StorageError: Nếu có lỗi khi query
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        job_id,
                        account_id,
                        content,
                        scheduled_time,
                        priority,
                        status,
                        platform,
                        max_retries,
                        retry_count,
                        created_at,
                        started_at,
                        completed_at,
                        error,
                        thread_id,
                        status_message,
                        link_aff
                    FROM jobs
                    WHERE status = %s
                    ORDER BY scheduled_time ASC
                """
                
                params = [status.value]
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                jobs = []
                for row in rows:
                    try:
                        jobs.append(self._row_to_job(row))
                    except Exception as e:
                        self.logger.log_step(
                            step="GET_JOBS_BY_STATUS",
                            result="WARNING",
                            error=f"Failed to parse job: {safe_get_exception_message(e)}",
                            job_id=row.get('job_id', 'unknown')
                        )
                        continue
                
                return jobs
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="GET_JOBS_BY_STATUS",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=error_type,
                status=status.value
            )
            
            raise StorageError(f"Failed to get jobs by status: {error_msg}") from e
        except Exception as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="GET_JOBS_BY_STATUS",
                result="ERROR",
                error=f"Unexpected error: {error_msg}",
                error_type=error_type,
                status=status.value
            )
            
            raise StorageError(f"Unexpected error getting jobs: {error_msg}") from e
    
    def get_jobs_by_account(
        self,
        account_id: str,
        status: Optional[JobStatus] = None
    ) -> List[ScheduledJob]:
        """
        Get jobs by account ID (optimized with direct query).
        
        Args:
            account_id: Account ID to filter by
            status: Optional JobStatus to filter by (if None, returns all statuses)
        
        Returns:
            List of ScheduledJob cho account, sorted by scheduled_time
        
        Raises:
            StorageError: Nếu có lỗi khi query
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute("""
                        SELECT 
                            job_id,
                            account_id,
                            content,
                            scheduled_time,
                            priority,
                            status,
                            platform,
                            max_retries,
                            retry_count,
                            created_at,
                            started_at,
                            completed_at,
                            error,
                            thread_id,
                            status_message,
                            link_aff
                        FROM jobs
                        WHERE account_id = %s AND status = %s
                        ORDER BY scheduled_time ASC
                    """, (account_id, status.value))
                else:
                    cursor.execute("""
                        SELECT 
                            job_id,
                            account_id,
                            content,
                            scheduled_time,
                            priority,
                            status,
                            platform,
                            max_retries,
                            retry_count,
                            created_at,
                            started_at,
                            completed_at,
                            error,
                            thread_id,
                            status_message,
                            link_aff
                        FROM jobs
                        WHERE account_id = %s
                        ORDER BY scheduled_time ASC
                    """, (account_id,))
                
                rows = cursor.fetchall()
                
                jobs = []
                for row in rows:
                    try:
                        jobs.append(self._row_to_job(row))
                    except Exception as e:
                        self.logger.log_step(
                            step="GET_JOBS_BY_ACCOUNT",
                            result="WARNING",
                            error=f"Failed to parse job: {safe_get_exception_message(e)}",
                            job_id=row.get('job_id', 'unknown')
                        )
                        continue
                
                return jobs
                
        except pymysql.Error as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="GET_JOBS_BY_ACCOUNT",
                result="ERROR",
                error=f"MySQL error: {error_msg}",
                error_type=error_type,
                account_id=account_id
            )
            
            raise StorageError(f"Failed to get jobs by account: {error_msg}") from e
        except Exception as e:
            error_msg = safe_get_exception_message(e)
            error_type = safe_get_exception_type_name(e)
            
            self.logger.log_step(
                step="GET_JOBS_BY_ACCOUNT",
                result="ERROR",
                error=f"Unexpected error: {error_msg}",
                error_type=error_type,
                account_id=account_id
            )
            
            raise StorageError(f"Unexpected error getting jobs: {error_msg}") from e
    
    def _row_to_job(self, row: Dict) -> ScheduledJob:
        """
        Convert database row to ScheduledJob.
        
        Args:
            row: Database row (dict)
        
        Returns:
            ScheduledJob instance
        
        Raises:
            ValueError: Nếu row data is invalid
            KeyError: Nếu required fields missing
        """
        try:
            # Parse priority
            priority_value = row.get('priority', 2)
            if isinstance(priority_value, int):
                priority = JobPriority(priority_value)
            elif isinstance(priority_value, JobPriority):
                priority = priority_value
            else:
                priority = JobPriority.NORMAL
            
            # Parse status
            status_value = row.get('status')
            if isinstance(status_value, str):
                status = JobStatus(status_value)
            elif isinstance(status_value, JobStatus):
                status = status_value
            else:
                raise ValueError(f"Invalid status value: {status_value}")
            
            # Parse platform
            platform_value = row.get('platform', 'threads')
            if isinstance(platform_value, str):
                platform = Platform(platform_value)
            elif isinstance(platform_value, Platform):
                platform = platform_value
            else:
                platform = Platform.THREADS
            
            # Parse datetime fields
            # pymysql với DictCursor returns datetime objects, not strings
            scheduled_time = row['scheduled_time']
            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            elif scheduled_time is not None and not isinstance(scheduled_time, datetime):
                # Convert other types to datetime if needed
                scheduled_time = datetime.fromisoformat(str(scheduled_time))
            
            created_at = row.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                elif not isinstance(created_at, datetime):
                    created_at = datetime.fromisoformat(str(created_at))
            
            started_at = row.get('started_at')
            if started_at:
                if isinstance(started_at, str):
                    started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                elif not isinstance(started_at, datetime):
                    started_at = datetime.fromisoformat(str(started_at))
            
            completed_at = row.get('completed_at')
            if completed_at:
                if isinstance(completed_at, str):
                    completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                elif not isinstance(completed_at, datetime):
                    completed_at = datetime.fromisoformat(str(completed_at))
            
            # Set created_at if None (for old jobs that don't have created_at)
            # Use scheduled_time as fallback, or current time if scheduled_time is also None
            if created_at is None:
                created_at = scheduled_time if scheduled_time else datetime.now(timezone.utc)
            
            return ScheduledJob(
                job_id=row['job_id'],
                account_id=row['account_id'],
                content=row['content'],
                scheduled_time=scheduled_time,
                priority=priority,
                status=status,
                platform=platform,
                max_retries=row.get('max_retries', 3),
                retry_count=row.get('retry_count', 0),
                created_at=created_at,
                started_at=started_at,
                completed_at=completed_at,
                error=row.get('error'),
                thread_id=row.get('thread_id'),
                status_message=row.get('status_message'),
                link_aff=row.get('link_aff')
            )
            
        except (KeyError, ValueError, TypeError) as e:
            error_msg = safe_get_exception_message(e)
            raise ValueError(
                f"Failed to convert row to ScheduledJob: {error_msg}. "
                f"Row data: {row}"
            ) from e
    
    def close(self) -> None:
        """
        Close storage connection (cleanup).
        
        For MySQL, connections are managed via context manager,
        so this is mostly for interface compatibility.
        """
        # Connections are closed automatically via context manager
        # This method is for interface compatibility
        pass
