"""
Config controller.

Request/response handling layer.
"""

# Standard library
from typing import Dict

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import InternalError
from backend.app.modules.config.services.config_service import ConfigService


class ConfigController:
    """
    Controller for config endpoints.
    """
    
    def __init__(self, service: Optional[ConfigService] = None):
        """
        Initialize config controller.
        
        Args:
            service: ConfigService instance. If None, creates new instance.
        """
        self.service = service or ConfigService()
    
    async def get_config(self) -> Dict:
        """Get current configuration endpoint."""
        config_dict = self.service.get_config()
        return success_response(
            data=config_dict,
            message="Configuration retrieved successfully"
        )
    
    async def update_config(self, config_data: Dict) -> Dict:
        """Update configuration endpoint."""
        updated_config = self.service.update_config(config_data)
        return success_response(
            data=updated_config,
            message="Configuration updated successfully"
        )
