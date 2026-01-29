"""
Excel repository.

Data access layer for Excel file operations.
Handles file storage and template retrieval.
"""

# Standard library
from typing import Optional
from pathlib import Path

# Local
from services.logger import StructuredLogger
from services.storage.excel_storage import ExcelStorage
from config.storage_config_loader import get_storage_config_from_env
from backend.app.shared.base_repository import BaseRepository


class ExcelRepository(BaseRepository):
    """
    Repository for Excel file data access.
    
    Handles file storage operations.
    No business logic - only data access.
    """
    
    def __init__(self):
        """Initialize Excel repository."""
        self.logger = StructuredLogger(name="excel_repository")
        
        # Initialize ExcelStorage
        self.excel_storage = None
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            self.excel_storage = ExcelStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                charset=mysql_config.charset,
                logger=self.logger
            )
        except Exception as e:
            self.logger.log_step(
                step="INIT_EXCEL_REPOSITORY",
                result="WARNING",
                error=f"Failed to initialize ExcelStorage: {str(e)}",
                error_type=type(e).__name__
            )
            self.excel_storage = None
        
        # Template path
        self.template_path = Path("schemas/job_template.json")
    
    def get_template_path(self) -> Path:
        """
        Get template file path.
        
        Returns:
            Path to template file
        """
        return self.template_path
    
    def template_exists(self) -> bool:
        """
        Check if template file exists.
        
        Returns:
            True if template exists, False otherwise
        """
        return self.template_path.exists()
    
    def get_by_id(self, entity_id: str):
        """Not applicable for Excel repository."""
        return None
    
    def get_all(self, filters=None, limit=None, offset=None):
        """Not applicable for Excel repository."""
        return []
    
    def create(self, entity_data):
        """Not applicable for Excel repository."""
        return None
    
    def update(self, entity_id: str, entity_data):
        """Not applicable for Excel repository."""
        return None
    
    def delete(self, entity_id: str) -> bool:
        """Not applicable for Excel repository."""
        return False
