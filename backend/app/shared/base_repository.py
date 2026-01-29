"""
Base repository class.

Provides common CRUD operations and data access patterns.
All repositories should inherit from this class.
"""

# Standard library
from typing import Any, Dict, Generic, List, Optional, TypeVar
from abc import ABC, abstractmethod

# Type variable for entity type
T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Base repository with common CRUD operations.
    
    This is an abstract base class. Subclasses must implement
    data access methods specific to their storage backend.
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all entities, optionally filtered.
        
        Args:
            filters: Optional filter criteria
            limit: Optional limit on number of results
            offset: Optional offset for pagination
        
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    def create(self, entity_data: Dict[str, Any]) -> T:
        """
        Create new entity.
        
        Args:
            entity_data: Entity data
        
        Returns:
            Created entity
        """
        pass
    
    @abstractmethod
    def update(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[T]:
        """
        Update existing entity.
        
        Args:
            entity_id: Entity identifier
            entity_data: Updated entity data
        
        Returns:
            Updated entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if deleted, False if not found
        """
        pass
    
    def exists(self, entity_id: str) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if exists, False otherwise
        """
        return self.get_by_id(entity_id) is not None
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.
        
        Args:
            filters: Optional filter criteria
        
        Returns:
            Number of matching entities
        """
        return len(self.get_all(filters=filters))
