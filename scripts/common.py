"""
Common utilities và setup code cho scripts.

Shared code để tránh duplication:
- Path setup
- Config loading
- Database connections
- Browser setup
- Logging setup
"""

import sys
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from config.storage_config_loader import MySQLStorageConfig

# Third-party
try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

# Local
from config import Config, RunMode
from config.storage_config_loader import get_storage_config_from_env
from services.storage.accounts_storage import AccountStorage
from services.logger import StructuredLogger


def setup_path() -> Path:
    """
    Setup sys.path để import từ project root.
    
    Returns:
        Path to project root
    """
    parent_dir = Path(__file__).resolve().parent.parent
    parent_dir_str = str(parent_dir)
    
    if parent_dir_str not in sys.path:
        sys.path.insert(0, parent_dir_str)
    
    return parent_dir


def get_mysql_config() -> 'MySQLStorageConfig':
    """
    Get MySQL configuration từ environment.
    
    Returns:
        MySQLConfig object với host, port, user, password, database
    """
    storage_config = get_storage_config_from_env()
    return storage_config.mysql


def get_account_storage() -> AccountStorage:
    """
    Create AccountStorage instance với config từ environment.
    
    Returns:
        AccountStorage instance
    """
    mysql_config = get_mysql_config()
    
    return AccountStorage(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database
    )


def get_mysql_connection():
    """
    Create direct MySQL connection (pymysql).
    
    Returns:
        pymysql connection object
    
    Raises:
        ImportError: Nếu pymysql không available
        Exception: Nếu connection fails
    """
    if not PYMYSQL_AVAILABLE:
        raise ImportError("pymysql not installed. Install with: pip install pymysql")
    
    mysql_config = get_mysql_config()
    
    return pymysql.connect(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        database=mysql_config.database,
        charset='utf8mb4'
    )


def get_account_username(account_id: str) -> Optional[str]:
    """
    Lấy username từ account metadata.
    
    Args:
        account_id: Account ID
    
    Returns:
        Username hoặc None nếu không tìm thấy
    """
    try:
        storage = get_account_storage()
        account = storage.get_account(account_id)
        
        if not account or not account.get('metadata'):
            return None
        
        metadata = account.get('metadata', {})
        
        # Parse JSON nếu là string
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                return None
        
        # Lấy username từ metadata
        username = metadata.get('username') or metadata.get('threads_username')
        return username
        
    except Exception as e:
        print(f"⚠️  Error getting username: {e}")
        return None


def get_config(mode: RunMode = RunMode.SAFE) -> Config:
    """
    Get Config instance.
    
    Args:
        mode: RunMode (SAFE hoặc FAST)
    
    Returns:
        Config instance
    """
    return Config(mode=mode)


def get_logger(name: str = "script") -> StructuredLogger:
    """
    Get StructuredLogger instance.
    
    Args:
        name: Logger name
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name=name)


def print_header(title: str, width: int = 80):
    """
    Print formatted header.
    
    Args:
        title: Header title
        width: Width of header (default: 80)
    """
    print("=" * width)
    print(title)
    print("=" * width)


def print_section(title: str, width: int = 80):
    """
    Print formatted section.
    
    Args:
        title: Section title
        width: Width (default: 80)
    """
    print("\n" + "-" * width)
    print(title)
    print("-" * width)
