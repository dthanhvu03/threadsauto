"""
Selectors service.

Business logic layer for selector operations.
"""

# Standard library
from typing import Dict, List, Optional, Any

# Local
from services.logger import StructuredLogger
from backend.app.shared.base_service import BaseService
from backend.app.modules.selectors.repositories.selectors_repository import SelectorsRepository
from backend.app.core.exceptions import ValidationError, NotFoundError, InternalError


class SelectorsService(BaseService):
    """
    Service for selectors business logic.
    
    Handles:
    - Selector retrieval
    - Selector updates
    - Version management
    - Metadata retrieval
    """
    
    def __init__(self, repository: Optional[SelectorsRepository] = None):
        """
        Initialize selectors service.
        
        Args:
            repository: SelectorsRepository instance. If None, creates new instance.
        """
        super().__init__("selectors_service")
        self.repository = repository or SelectorsRepository()
    
    def get_selectors(self, platform: str, version: str) -> Dict:
        """
        Get selectors for platform and version.
        
        Args:
            platform: Platform name
            version: Selector version
        
        Returns:
            Dictionary with platform, version, and selectors
        """
        try:
            selectors = self.repository.get_selectors(platform, version)
            return {
                "platform": platform,
                "version": version,
                "selectors": selectors
            }
        except Exception as e:
            self.logger.log_step(
                step="GET_SELECTORS",
                result="ERROR",
                error=f"Failed to get selectors: {str(e)}",
                platform=platform,
                version=version,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to retrieve selectors: {str(e)}")
    
    def update_selectors(
        self,
        platform: str,
        version: str,
        selectors: Dict[str, List[str]]
    ) -> Dict:
        """
        Update selectors.
        
        Args:
            platform: Platform name
            version: Version
            selectors: Dict with selectors
        
        Returns:
            Dictionary with updated selectors
        
        Raises:
            ValidationError: If selectors is empty
            InternalError: If save fails
        """
        if not selectors:
            raise ValidationError(
                message="Selectors data is required",
                details={"field": "selectors"}
            )
        
        try:
            success = self.repository.save_selectors(platform, version, selectors)
            if not success:
                raise InternalError(
                    message="Failed to save selectors",
                    details={"platform": platform, "version": version}
                )
            
            return {
                "platform": platform,
                "version": version,
                "selectors": selectors
            }
        except (ValidationError, InternalError):
            raise
        except Exception as e:
            self.logger.log_step(
                step="UPDATE_SELECTORS",
                result="ERROR",
                error=f"Failed to update selectors: {str(e)}",
                platform=platform,
                version=version,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to update selectors: {str(e)}")
    
    def get_versions(self, platform: str) -> Dict:
        """
        Get all versions for platform.
        
        Args:
            platform: Platform name
        
        Returns:
            Dictionary with platform and versions list
        """
        try:
            versions = self.repository.get_versions(platform)
            return {
                "platform": platform,
                "versions": versions
            }
        except Exception as e:
            self.logger.log_step(
                step="GET_VERSIONS",
                result="ERROR",
                error=f"Failed to get versions: {str(e)}",
                platform=platform,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to retrieve versions: {str(e)}")
    
    def get_metadata(self, platform: str, version: str) -> Dict:
        """
        Get metadata for version.
        
        Args:
            platform: Platform name
            version: Version
        
        Returns:
            Dictionary with platform, version, and metadata
        """
        try:
            metadata = self.repository.get_metadata(platform, version)
            return {
                "platform": platform,
                "version": version,
                "metadata": metadata or {}
            }
        except Exception as e:
            self.logger.log_step(
                step="GET_METADATA",
                result="ERROR",
                error=f"Failed to get metadata: {str(e)}",
                platform=platform,
                version=version,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to retrieve metadata: {str(e)}")
    
    def delete_version(self, platform: str, version: str) -> Dict:
        """
        Delete a version.
        
        Args:
            platform: Platform name
            version: Version to delete
        
        Returns:
            Dictionary with deletion result
        
        Raises:
            NotFoundError: If version not found
        """
        try:
            deleted = self.repository.delete_version(platform, version)
            if not deleted:
                raise NotFoundError(
                    resource="Selector version",
                    details={"platform": platform, "version": version}
                )
            
            return {
                "platform": platform,
                "version": version,
                "deleted": True
            }
        except (NotFoundError, InternalError):
            raise
        except Exception as e:
            self.logger.log_step(
                step="DELETE_VERSION",
                result="ERROR",
                error=f"Failed to delete version: {str(e)}",
                platform=platform,
                version=version,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to delete version: {str(e)}")
