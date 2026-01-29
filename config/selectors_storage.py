"""
Module: config/selectors_storage.py

Selector storage and loading utilities.
Quản lý selectors từ JSON file thay vì hardcode.
"""

# Standard library
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Local
from config.storage_config_loader import get_storage_config_from_env
from services.storage.selectors_storage import SelectorStorage
from services.logger import StructuredLogger


SELECTORS_FILE = Path("./selectors.json")
XPATH_PREFIX = "xpath="
_USE_MYSQL_SELECTORS = True  # Use MySQL by default


def load_selectors(
    platform: str = "threads",
    version: str = "v1",
    use_mysql: Optional[bool] = None
) -> Dict[str, List[str]]:
    """
    Load selectors từ MySQL (if enabled), JSON file, hoặc hardcoded defaults.
    
    Priority:
    1. MySQL (if use_mysql=True and available)
    2. JSON file (selectors.json)
    3. Hardcoded defaults
    
    Args:
        platform: Platform name ("threads" hoặc "facebook")
        version: Selector version (default: "v1")
        use_mysql: If True, use MySQL. If None, use default (MySQL).
    
    Returns:
        Dict với selector names và lists of selectors
    """
    if use_mysql is None:
        use_mysql = _USE_MYSQL_SELECTORS
    
    # Try MySQL first
    if use_mysql:
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            selector_storage = SelectorStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                charset=mysql_config.charset,
                logger=StructuredLogger(name="selector_storage")
            )
            selectors = selector_storage.load_selectors(platform, version)
            if selectors:
                return selectors
        except Exception:
            # Fall through to JSON file
            pass
    
    # Fallback to JSON file
    if not SELECTORS_FILE.exists():
        # Fallback to hardcoded selectors
        return _get_default_selectors(platform, version)
    
    try:
        with open(SELECTORS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get selectors for platform and version
        platform_data = data.get(platform, {})
        version_data = platform_data.get(version, {})
        
        if version_data:
            return version_data
        
        # Fallback to default if not found
        return _get_default_selectors(platform, version)
    except Exception as e:
        print(f"Warning: Failed to load selectors: {e}, using defaults")
        return _get_default_selectors(platform, version)


def save_selectors(
    platform: str,
    version: str,
    selectors: Dict[str, List[str]],
    use_mysql: Optional[bool] = None
) -> None:
    """
    Save selectors to MySQL (if enabled) và JSON file.
    
    Args:
        platform: Platform name ("threads" hoặc "facebook")
        version: Selector version (default: "v1")
        selectors: Dict với selector names và lists of selectors
        use_mysql: If True, save to MySQL. If None, use default (MySQL).
    """
    if use_mysql is None:
        use_mysql = _USE_MYSQL_SELECTORS
    
    # Save to MySQL if enabled
    if use_mysql:
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            selector_storage = SelectorStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                charset=mysql_config.charset,
                logger=StructuredLogger(name="selector_storage")
            )
            metadata = {
                "last_updated": datetime.now().isoformat(),
                "platform": platform,
                "version": version
            }
            selector_storage.save_selectors(platform, version, selectors, metadata)
        except Exception as e:
            # Log warning but continue to save to JSON file
            print(f"Warning: Failed to save selectors to MySQL: {e}, saving to JSON file")
    
    # Also save to JSON file (for backup/backward compatibility)
    # Load existing data
    if SELECTORS_FILE.exists():
        try:
            with open(SELECTORS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}
    
    # Update data structure
    if platform not in data:
        data[platform] = {}
    
    data[platform][version] = selectors
    
    # Add metadata
    if "_metadata" not in data:
        data["_metadata"] = {}
    
    data["_metadata"][f"{platform}_{version}"] = {
        "last_updated": datetime.now().isoformat(),
        "platform": platform,
        "version": version
    }
    
    # Save to file
    try:
        with open(SELECTORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError, TypeError) as e:
        raise RuntimeError(f"Failed to save selectors: {str(e)}") from e


def get_all_selector_versions(
    platform: str,
    use_mysql: Optional[bool] = None
) -> List[str]:
    """
    Get all available versions for a platform.
    
    Args:
        platform: Platform name
    
    Returns:
        List of version strings
    """
    if not SELECTORS_FILE.exists():
        return ["v1"]
    
    try:
        with open(SELECTORS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        platform_data = data.get(platform, {})
        versions = [v for v in platform_data.keys() if not v.startswith("_")]
        return sorted(versions) if versions else ["v1"]
    except Exception:
        return ["v1"]


def delete_selector_version(
    platform: str,
    version: str,
    use_mysql: Optional[bool] = None
) -> bool:
    """
    Delete a selector version.
    
    Args:
        platform: Platform name
        version: Version to delete
        use_mysql: If True, use MySQL. If None, use default (MySQL).
    
    Returns:
        True if deleted, False if not found
    """
    if use_mysql is None:
        use_mysql = _USE_MYSQL_SELECTORS
    
    deleted = False
    
    # Delete from MySQL if enabled
    if use_mysql:
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            selector_storage = SelectorStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                charset=mysql_config.charset,
                logger=StructuredLogger(name="selector_storage")
            )
            deleted = selector_storage.delete_version(platform, version)
        except Exception:
            # Continue to try JSON file
            pass
    
    # Also delete from JSON file
    if not SELECTORS_FILE.exists():
        return deleted
    
    try:
        with open(SELECTORS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if platform in data and version in data[platform]:
            del data[platform][version]
            
            # Remove metadata
            if "_metadata" in data:
                key = f"{platform}_{version}"
                if key in data["_metadata"]:
                    del data["_metadata"][key]
            
            # Save updated data
            with open(SELECTORS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    
    return deleted


def _get_default_selectors(platform: str, version: str) -> Dict[str, List[str]]:
    """
    Get default hardcoded selectors (fallback).
    
    Args:
        platform: Platform name
        version: Version
    
    Returns:
        Dict với selectors
    """
    if platform == "threads":
        from threads.selectors import SELECTORS
        return SELECTORS.get(version, SELECTORS.get("v1", {}))
    elif platform == "facebook":
        from facebook.selectors import SELECTORS
        return SELECTORS.get(version, SELECTORS.get("v1", {}))
    else:
        return {}


def get_selector_metadata(
    platform: str,
    version: str,
    use_mysql: Optional[bool] = None
) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a selector version.
    
    Args:
        platform: Platform name
        version: Version
        use_mysql: If True, use MySQL. If None, use default (MySQL).
    
    Returns:
        Metadata dict or None
    """
    if use_mysql is None:
        use_mysql = _USE_MYSQL_SELECTORS
    
    # Try MySQL first
    if use_mysql:
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            selector_storage = SelectorStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                charset=mysql_config.charset,
                logger=StructuredLogger(name="selector_storage")
            )
            metadata = selector_storage.get_metadata(platform, version)
            if metadata:
                return metadata
        except Exception:
            # Fall through to JSON file
            pass
    
    # Fallback to JSON file
    if not SELECTORS_FILE.exists():
        return None
    
    try:
        with open(SELECTORS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{platform}_{version}"
        return data.get("_metadata", {}).get(key)
    except Exception:
        return None

