"""
Base service class.

Provides common service patterns and error handling.
All services should inherit from this class.
"""

# Standard library
from typing import Any, Dict, List, Optional
from abc import ABC

# Local
from services.logger import StructuredLogger
from backend.app.core.exceptions import NotFoundError, InternalError


class BaseService(ABC):
    """
    Base service with common patterns.
    
    Provides logging, error handling, and common service methods.
    Subclasses should implement business logic specific to their domain.
    """
    
    def __init__(self, service_name: str):
        """
        Initialize base service.
        
        Args:
            service_name: Name of the service (for logging)
        """
        self.logger = StructuredLogger(name=service_name)
        self.service_name = service_name
    
    def _handle_not_found(self, resource: str, resource_id: str) -> None:
        """
        Handle not found error.
        
        Args:
            resource: Resource type name
            resource_id: Resource identifier
        
        Raises:
            NotFoundError: Always raises NotFoundError
        """
        self.logger.log_step(
            step=f"{resource.upper()}_NOT_FOUND",
            result="FAILED",
            resource_id=resource_id,
            service=self.service_name
        )
        raise NotFoundError(resource=resource, details={"id": resource_id})
    
    def _handle_error(
        self,
        step: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle and log error.
        
        Args:
            step: Step name for logging
            error: Exception that occurred
            context: Optional context information
        
        Raises:
            InternalError: Always raises InternalError
        """
        self.logger.log_step(
            step=step,
            result="ERROR",
            error=str(error),
            error_type=type(error).__name__,
            service=self.service_name,
            **(context or {})
        )
        raise InternalError(
            message=f"Error in {self.service_name}: {str(error)}",
            details=context or {}
        )
    
    def _log_operation(
        self,
        operation: str,
        result: str,
        **kwargs
    ) -> None:
        """
        Log service operation.
        
        Args:
            operation: Operation name
            result: Result status (SUCCESS, FAILED, etc.)
            **kwargs: Additional context
        """
        self.logger.log_step(
            step=f"{self.service_name.upper()}_{operation}",
            result=result,
            service=self.service_name,
            **kwargs
        )
