"""
Config repository.

Data access layer for configuration operations.
Wraps config.storage functions.
"""

# Local
from services.logger import StructuredLogger
from config.storage import load_config, save_config, _config_to_dict, _dict_to_config
from config.config import Config, RunMode
from backend.app.shared.base_repository import BaseRepository


class ConfigRepository(BaseRepository):
    """
    Repository for config data access.
    
    Wraps config.storage functions.
    No business logic - only data access.
    """
    
    def __init__(self):
        """Initialize config repository."""
        self.logger = StructuredLogger(name="config_repository")
    
    def load_config(self) -> Config:
        """
        Load configuration from storage.
        
        Returns:
            Config object
        """
        return load_config()
    
    def save_config(self, config: Config) -> None:
        """
        Save configuration to storage.
        
        Args:
            config: Config object to save
        """
        save_config(config)
    
    def config_to_dict(self, config: Config) -> Dict:
        """
        Convert Config object to dictionary.
        
        Args:
            config: Config object
        
        Returns:
            Dictionary representation of config
        """
        config_dict = _config_to_dict(config)
        config_dict["run_mode"] = config.mode.value
        return config_dict
    
    def dict_to_config(self, config_dict: Dict) -> Config:
        """
        Convert dictionary to Config object.
        
        Args:
            config_dict: Dictionary representation of config
        
        Returns:
            Config object
        """
        return _dict_to_config(config_dict)
    
    # BaseRepository abstract methods (not applicable for config)
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
