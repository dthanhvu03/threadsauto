"""
Module: services/scheduler/storage/factory.py

Factory pattern để create job storage instances.
Supports both JSON and MySQL storage types.
"""

# Standard library
from pathlib import Path
from typing import Optional

# Local
from services.scheduler.storage.base import JobStorageBase
from services.scheduler.storage.json_storage import JobStorage
from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.logger import StructuredLogger


def create_job_storage(
    storage_type: str = "json",
    storage_dir: Optional[Path] = None,
    logger: Optional[StructuredLogger] = None,
    # MySQL parameters
    mysql_host: str = "localhost",
    mysql_port: int = 3306,
    mysql_user: str = "threads_user",
    mysql_password: str = "",
    mysql_database: str = "threads_analytics",
    mysql_charset: str = "utf8mb4"
) -> JobStorageBase:
    """
    Factory function để create job storage instance.
    
    Args:
        storage_type: Storage type ("json" or "mysql")
        storage_dir: Directory for JSON storage (required if storage_type="json")
        logger: Structured logger (optional)
        mysql_host: MySQL host (for MySQL storage)
        mysql_port: MySQL port (for MySQL storage)
        mysql_user: MySQL user (for MySQL storage)
        mysql_password: MySQL password (for MySQL storage)
        mysql_database: Database name (for MySQL storage)
        mysql_charset: Character set (for MySQL storage)
    
    Returns:
        JobStorageBase instance (JobStorage or MySQLJobStorage)
    
    Raises:
        ValueError: Nếu storage_type is invalid
        ValueError: Nếu storage_dir is None for JSON storage
    
    Example:
        # JSON storage
        storage = create_job_storage(
            storage_type="json",
            storage_dir=Path("./jobs"),
            logger=logger
        )
        
        # MySQL storage
        storage = create_job_storage(
            storage_type="mysql",
            mysql_host="localhost",
            mysql_user="threads_user",
            mysql_password="password",
            mysql_database="threads_analytics",
            logger=logger
        )
    """
    if logger is None:
        logger = StructuredLogger(name="job_storage_factory")
    
    storage_type_lower = storage_type.lower()
    
    if storage_type_lower == "json":
        if storage_dir is None:
            raise ValueError(
                "storage_dir is required for JSON storage type"
            )
        
        return JobStorage(
            storage_dir=storage_dir,
            logger=logger
        )
    
    elif storage_type_lower == "mysql":
        return MySQLJobStorage(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            charset=mysql_charset,
            logger=logger
        )
    
    else:
        raise ValueError(
            f"Invalid storage_type: {storage_type}. "
            f"Must be 'json' or 'mysql'"
        )
