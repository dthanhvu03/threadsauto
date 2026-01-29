"""
Module: config/storage_config_loader.py

Helper functions để load storage config từ environment variables và config.yaml.
"""

# Standard library
import os
from pathlib import Path
from typing import Optional

# Third-party
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Local
from config.config import StorageConfig, MySQLStorageConfig


def load_env_file(env_path: Optional[Path] = None) -> None:
    """
    Load .env file nếu có và dotenv available.
    
    Args:
        env_path: Path to .env file (default: .env in current directory)
    """
    if not DOTENV_AVAILABLE:
        return
    
    if env_path is None:
        env_path = Path(".env")
    
    if env_path.exists():
        load_dotenv(env_path)


def get_storage_config_from_env(
    default_storage_type: str = "mysql"  # Default: mysql (after migration)
) -> StorageConfig:
    """
    Get storage config từ environment variables.
    
    Environment variables:
    - STORAGE_TYPE: "json" or "mysql" (default: "json")
    - JOBS_DIR: Directory for JSON storage (default: "./jobs")
    - MYSQL_HOST: MySQL host (default: "localhost")
    - MYSQL_PORT: MySQL port (default: 3306)
    - MYSQL_USER: MySQL user (default: "threads_user")
    - MYSQL_PASSWORD: MySQL password (default: "")
    - MYSQL_DATABASE: Database name (default: "threads_analytics")
    - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME: Alternative names
    
    Args:
        default_storage_type: Default storage type nếu not set in env
    
    Returns:
        StorageConfig instance
    """
    # Load .env file if available
    load_env_file()
    
    # Get storage type
    storage_type = os.getenv("STORAGE_TYPE", default_storage_type).lower()
    
    # Get JSON config
    jobs_dir = os.getenv("JOBS_DIR", "./jobs")
    
    # Get MySQL config (check both MYSQL_* and DB_* prefixes)
    mysql_host = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER") or os.getenv("DB_USER", "threads_user")
    mysql_password = os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", "")
    mysql_database = os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME", "threads_analytics")
    mysql_charset = os.getenv("MYSQL_CHARSET", "utf8mb4")
    
    mysql_config = MySQLStorageConfig(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database,
        charset=mysql_charset
    )
    
    return StorageConfig(
        storage_type=storage_type,
        jobs_dir=jobs_dir,
        mysql=mysql_config
    )


def get_storage_config(
    config_yaml: Optional[dict] = None,
    default_storage_type: str = "mysql"  # Default: mysql (after migration)
) -> StorageConfig:
    """
    Get storage config từ config.yaml hoặc environment variables.
    
    Args:
        config_yaml: Config dict từ YAML file (optional)
        default_storage_type: Default storage type
    
    Returns:
        StorageConfig instance
    
    Priority:
    1. Environment variables (if set)
    2. config_yaml['storage']
    3. Defaults
    """
    # Load .env first
    load_env_file()
    
    # Check environment variables first (highest priority)
    if os.getenv("STORAGE_TYPE"):
        return get_storage_config_from_env(default_storage_type)
    
    # Use config_yaml if provided
    if config_yaml and "storage" in config_yaml:
        storage_config = config_yaml["storage"]
        
        storage_type = storage_config.get("storage_type", default_storage_type).lower()
        jobs_dir = storage_config.get("jobs_dir", "./jobs")
        
        # MySQL config from YAML
        mysql_config_dict = storage_config.get("mysql", {})
        mysql_config = MySQLStorageConfig(
            host=mysql_config_dict.get("host", "localhost"),
            port=int(mysql_config_dict.get("port", 3306)),
            user=mysql_config_dict.get("user", "threads_user"),
            password=os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD") or mysql_config_dict.get("password", ""),
            database=mysql_config_dict.get("database", "threads_analytics"),
            charset=mysql_config_dict.get("charset", "utf8mb4")
        )
        
        return StorageConfig(
            storage_type=storage_type,
            jobs_dir=jobs_dir,
            mysql=mysql_config
        )
    
    # Default: use environment variables or defaults
    return get_storage_config_from_env(default_storage_type)
