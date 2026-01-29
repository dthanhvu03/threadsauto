"""
Module: backend/api/adapters/selectors_adapter.py

API để quản lý selectors từ UI.
"""

# Standard library
from typing import Dict, List, Optional, Any
from pathlib import Path

# Local
from config.selectors_storage import (
    load_selectors,
    save_selectors,
    get_all_selector_versions,
    delete_selector_version,
    get_selector_metadata,
    SELECTORS_FILE
)


class SelectorsAPI:
    """API để quản lý selectors."""
    
    def __init__(self):
        """Initialize SelectorsAPI."""
        pass
    
    def get_selectors(
        self,
        platform: str = "threads",
        version: str = "v1"
    ) -> Dict[str, List[str]]:
        """
        Get selectors for platform and version.
        
        Args:
            platform: Platform name ("threads" hoặc "facebook")
            version: Selector version
        
        Returns:
            Dict với selector names và lists of selectors
        """
        return load_selectors(platform, version)
    
    def save_selectors(
        self,
        platform: str,
        version: str,
        selectors: Dict[str, List[str]]
    ) -> bool:
        """
        Save selectors.
        
        Args:
            platform: Platform name
            version: Version
            selectors: Dict với selectors
        
        Returns:
            True if successful
        """
        try:
            save_selectors(platform, version, selectors)
            return True
        except Exception:
            return False
    
    def get_versions(self, platform: str) -> List[str]:
        """
        Get all versions for platform.
        
        Args:
            platform: Platform name
        
        Returns:
            List of version strings
        """
        return get_all_selector_versions(platform)
    
    def delete_version(self, platform: str, version: str) -> bool:
        """
        Delete a version.
        
        Args:
            platform: Platform name
            version: Version to delete
        
        Returns:
            True if deleted
        """
        return delete_selector_version(platform, version)
    
    def get_metadata(
        self,
        platform: str,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for version.
        
        Args:
            platform: Platform name
            version: Version
        
        Returns:
            Metadata dict or None
        """
        return get_selector_metadata(platform, version)
    
    def get_default_selectors(
        self,
        platform: str,
        version: str = "v1"
    ) -> Dict[str, List[str]]:
        """
        Get default hardcoded selectors.
        
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
    
    def copy_default_to_custom(
        self,
        platform: str,
        version: str = "v1"
    ) -> bool:
        """
        Copy default hardcoded selectors to custom storage.
        
        Args:
            platform: Platform name
            version: Version
        
        Returns:
            True if successful
        """
        try:
            default_selectors = self.get_default_selectors(platform, version)
            save_selectors(platform, version, default_selectors)
            return True
        except Exception:
            return False
