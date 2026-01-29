"""
Config service.

Business logic layer for configuration operations.
"""

# Standard library
from typing import Dict, Optional

# Local
from services.logger import StructuredLogger
from backend.app.shared.base_service import BaseService
from backend.app.modules.config.repositories.config_repository import ConfigRepository
from backend.app.core.exceptions import InternalError
from config.config import RunMode


class ConfigService(BaseService):
    """
    Service for config business logic.
    
    Handles:
    - Config loading
    - Config updating
    - Validation
    """
    
    def __init__(self, repository: Optional[ConfigRepository] = None):
        """
        Initialize config service.
        
        Args:
            repository: ConfigRepository instance. If None, creates new instance.
        """
        super().__init__("config_service")
        self.repository = repository or ConfigRepository()
    
    def get_config(self) -> Dict:
        """
        Get current configuration.
        
        Returns:
            Dictionary representation of config
        """
        try:
            config = self.repository.load_config()
            return self.repository.config_to_dict(config)
        except Exception as e:
            self.logger.log_step(
                step="GET_CONFIG",
                result="ERROR",
                error=f"Failed to get config: {str(e)}",
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to retrieve configuration: {str(e)}")
    
    def update_config(self, config_data: Dict) -> Dict:
        """
        Update configuration.
        
        Args:
            config_data: Dictionary with config data
        
        Returns:
            Dictionary representation of updated config
        
        Raises:
            InternalError: If update fails
        """
        try:
            # Load current config
            current_config = self.repository.load_config()
            
            # Convert dict to Config object
            updated_config = self.repository.dict_to_config(config_data)
            
            # Handle run_mode separately
            if "run_mode" in config_data:
                try:
                    updated_config.mode = RunMode(config_data["run_mode"])
                except (ValueError, KeyError):
                    pass  # Keep current mode if invalid
            
            # Save to storage
            self.repository.save_config(updated_config)
            
            # Return updated config as dict
            return self.repository.config_to_dict(updated_config)
        except Exception as e:
            self.logger.log_step(
                step="UPDATE_CONFIG",
                result="ERROR",
                error=f"Failed to update config: {str(e)}",
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to update configuration: {str(e)}")
