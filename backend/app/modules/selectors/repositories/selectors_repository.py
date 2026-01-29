"""
Selectors repository.

Data access layer for selector operations.
Wraps config.selectors_storage functions.
"""

# Standard library
from typing import Dict, List, Optional, Any

# Local
from services.logger import StructuredLogger
from config.selectors_storage import (
    load_selectors,
    save_selectors,
    get_all_selector_versions,
    delete_selector_version,
    get_selector_metadata
)
from backend.app.shared.base_repository import BaseRepository


class SelectorsRepository(BaseRepository):
    """
    Repository for selectors data access.
    
    Wraps config.selectors_storage functions.
    No business logic - only data access.
    """
    
    def __init__(self):
        """Initialize selectors repository."""
        self.logger = StructuredLogger(name="selectors_repository")
    
    def get_selectors(self, platform: str, version: str) -> Dict[str, List[str]]:
        """
        Get selectors for platform and version.
        
        Args:
            platform: Platform name
            version: Selector version
        
        Returns:
            Dict with selector names and lists of selectors
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
            selectors: Dict with selectors
        
        Returns:
            True if successful
        """
        try:
            save_selectors(platform, version, selectors)
            return True
        except Exception as e:
            self.logger.log_step(
                step="SAVE_SELECTORS",
                result="ERROR",
                error=f"Failed to save selectors: {str(e)}",
                platform=platform,
                version=version,
                error_type=type(e).__name__
            )
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
    
    def get_metadata(self, platform: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for version.
        
        Args:
            platform: Platform name
            version: Version
        
        Returns:
            Metadata dict or None
        """
        return get_selector_metadata(platform, version)
    
    # BaseRepository abstract methods (not applicable for selectors)
    def get_by_id(self, entity_id: str):
        return None
    
    def get_all(self, filters=None, limit=None, offset=None):
        return []
    
    def create(self, entity_data):
        return None
    
    def update(self, entity_id: str, entity_data):
        return None
    
    def delete(self, entity_id: str) -> bool:
        return False
