"""
Selectors controller.

Request/response handling layer.
"""

# Standard library
from typing import Dict, Optional

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import NotFoundError, InternalError, ValidationError
from backend.app.modules.selectors.services.selectors_service import SelectorsService


class SelectorsController:
    """
    Controller for selectors endpoints.
    """
    
    def __init__(self, service: Optional[SelectorsService] = None):
        """
        Initialize selectors controller.
        
        Args:
            service: SelectorsService instance. If None, creates new instance.
        """
        self.service = service or SelectorsService()
    
    async def get_selectors(self, platform: str, version: str) -> Dict:
        """Get selectors endpoint."""
        result = self.service.get_selectors(platform=platform, version=version)
        return success_response(
            data=result,
            message="Selectors retrieved successfully"
        )
    
    async def update_selectors(self, selectors_data: Dict) -> Dict:
        """Update selectors endpoint."""
        platform = selectors_data.get("platform", "threads")
        version = selectors_data.get("version", "v1")
        selectors = selectors_data.get("selectors", {})
        
        result = self.service.update_selectors(
            platform=platform,
            version=version,
            selectors=selectors
        )
        return success_response(
            data=result,
            message="Selectors updated successfully"
        )
    
    async def get_versions(self, platform: str) -> Dict:
        """Get versions endpoint."""
        result = self.service.get_versions(platform=platform)
        return success_response(
            data=result,
            message="Versions retrieved successfully"
        )
    
    async def get_metadata(self, platform: str, version: str) -> Dict:
        """Get metadata endpoint."""
        result = self.service.get_metadata(platform=platform, version=version)
        return success_response(
            data=result,
            message="Metadata retrieved successfully"
        )
    
    async def delete_version(self, platform: str, version: str) -> Dict:
        """Delete version endpoint."""
        result = self.service.delete_version(platform=platform, version=version)
        return success_response(
            data=result,
            message="Version deleted successfully"
        )
