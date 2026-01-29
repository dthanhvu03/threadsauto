"""
Module: services/storage/connection_pool.py

MySQL connection pooling for storage operations.
Improves performance by reusing connections instead of creating new ones.
"""

import sys
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from queue import Queue, Empty
from threading import Lock
import time

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


class ConnectionPool:
    """
    MySQL connection pool.
    
    Reuses connections to improve performance and reduce overhead.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "threads_user",
        password: str = "",
        database: str = "threads_analytics",
        charset: str = "utf8mb4",
        pool_size: int = 10,
        max_overflow: int = 20,
        connection_timeout: int = 10,
        read_timeout: int = 30,
        write_timeout: int = 30,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize connection pool.
        
        Args:
            host: MySQL host
            port: MySQL port
            user: MySQL user
            password: MySQL password
            database: Database name
            charset: Character set
            pool_size: Number of connections to keep in pool
            max_overflow: Maximum additional connections beyond pool_size
            connection_timeout: Connection timeout in seconds
            logger: Logger instance
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.logger = logger or StructuredLogger(name="connection_pool")
        
        # Connection pool
        self._pool: Queue = Queue(maxsize=pool_size)
        self._overflow_count = 0  # Track overflow connections
        self._lock = Lock()  # Thread-safe operations
        self._total_created = 0
        self._total_reused = 0
        
        # Initialize pool with some connections
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize pool with initial connections."""
        try:
            # Create initial connections (half of pool_size)
            initial_size = max(1, self.pool_size // 2)
            for _ in range(initial_size):
                try:
                    conn = self._create_connection()
                    self._pool.put(conn)
                    self._total_created += 1
                except Exception as e:
                    self.logger.log_step(
                        step="POOL_INIT",
                        result="WARNING",
                        error=f"Failed to create initial connection: {str(e)}"
                    )
                    break
        except Exception as e:
            self.logger.log_step(
                step="POOL_INIT",
                result="ERROR",
                error=str(e)
            )
    
    def _create_connection(self) -> pymysql.Connection:
        """
        Create a new MySQL connection.
        
        Raises:
            StorageError: If connection fails
        """
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
                connect_timeout=self.connection_timeout,
                read_timeout=self.read_timeout,
                write_timeout=self.write_timeout
            )
            return conn
        except pymysql.err.OperationalError as e:
            error_code = e.args[0] if e.args else 0
            error_msg = str(e)
            
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
            elif error_code == 2003:  # Can't connect
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
            raise StorageError(f"Database error: {str(e)}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error connecting to database: {str(e)}") from e
    
    def _is_connection_alive(self, conn: pymysql.Connection) -> bool:
        """Check if connection is still alive."""
        try:
            conn.ping(reconnect=False)
            return True
        except Exception:
            return False
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            MySQL connection
            
        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = None
        created_new = False
        
        try:
            # Try to get connection from pool
            try:
                conn = self._pool.get_nowait()
                
                # Check if connection is still alive
                if not self._is_connection_alive(conn):
                    # Connection is dead, create new one
                    try:
                        conn.close()
                    except Exception:
                        pass
                    conn = self._create_connection()
                    created_new = True
                    self._total_created += 1
                else:
                    self._total_reused += 1
                    
            except Empty:
                # Pool is empty, create new connection
                with self._lock:
                    if self._overflow_count < self.max_overflow:
                        conn = self._create_connection()
                        created_new = True
                        self._overflow_count += 1
                        self._total_created += 1
                    else:
                        # Wait for connection to become available
                        conn = self._pool.get(timeout=self.connection_timeout)
                        if not self._is_connection_alive(conn):
                            try:
                                conn.close()
                            except Exception:
                                pass
                            conn = self._create_connection()
                            created_new = True
                            self._total_created += 1
                        else:
                            self._total_reused += 1
            
            # Yield connection
            yield conn
            
        except Exception as e:
            # On error, don't return connection to pool (might be corrupted)
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
                if created_new:
                    with self._lock:
                        self._overflow_count = max(0, self._overflow_count - 1)
            raise
        finally:
            # Return connection to pool (if healthy)
            if conn and not created_new:
                try:
                    # Check if connection is still healthy
                    if self._is_connection_alive(conn):
                        try:
                            # Reset connection state
                            conn.rollback()
                            self._pool.put_nowait(conn)
                        except Exception:
                            # Pool full or error, close connection
                            try:
                                conn.close()
                            except Exception:
                                pass
                    else:
                        # Connection is dead, close it
                        try:
                            conn.close()
                        except Exception:
                            pass
                except Exception:
                    # Error returning to pool, close connection
                    try:
                        conn.close()
                    except Exception:
                        pass
            elif conn and created_new:
                # New connection created, try to return to pool if there's space
                try:
                    if self._is_connection_alive(conn):
                        try:
                            conn.rollback()
                            self._pool.put_nowait(conn)
                            with self._lock:
                                self._overflow_count = max(0, self._overflow_count - 1)
                        except Exception:
                            # Pool full, close overflow connection
                            try:
                                conn.close()
                            except Exception:
                                pass
                            with self._lock:
                                self._overflow_count = max(0, self._overflow_count - 1)
                except Exception:
                    # Error, close connection
                    try:
                        conn.close()
                    except Exception:
                        pass
                    with self._lock:
                        self._overflow_count = max(0, self._overflow_count - 1)
    
    def close_all(self) -> None:
        """Close all connections in pool."""
        connections_closed = 0
        while True:
            try:
                conn = self._pool.get_nowait()
                try:
                    conn.close()
                    connections_closed += 1
                except Exception:
                    pass
            except Empty:
                break
        
        self.logger.log_step(
            step="POOL_CLOSE",
            result="SUCCESS",
            connections_closed=connections_closed
        )
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        return {
            "pool_size": self.pool_size,
            "current_connections": self._pool.qsize(),
            "overflow_connections": self._overflow_count,
            "total_created": self._total_created,
            "total_reused": self._total_reused,
            "reuse_rate": (
                self._total_reused / (self._total_created + self._total_reused) * 100
                if (self._total_created + self._total_reused) > 0
                else 0
            )
        }


# Global connection pool instance (lazy initialization)
_global_pool: Optional[ConnectionPool] = None
_pool_lock = Lock()


def get_connection_pool(
    host: str = "localhost",
    port: int = 3306,
    user: str = "threads_user",
    password: str = "",
    database: str = "threads_analytics",
    charset: str = "utf8mb4",
    pool_size: int = 10,
    max_overflow: int = 20,
    read_timeout: int = 30,
    write_timeout: int = 30,
    logger: Optional[StructuredLogger] = None
) -> ConnectionPool:
    """
    Get or create global connection pool.
    
    Returns:
        ConnectionPool instance
    """
    global _global_pool
    
    with _pool_lock:
        if _global_pool is None:
            _global_pool = ConnectionPool(
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
                logger=logger
            )
        return _global_pool


def reset_connection_pool() -> None:
    """Reset global connection pool (useful for testing)."""
    global _global_pool
    
    with _pool_lock:
        if _global_pool is not None:
            _global_pool.close_all()
            _global_pool = None
