"""
Custom exceptions for API layer.

Provides domain-specific exceptions that map to HTTP status codes
and standard error response format.
"""

# Standard library
from typing import Any, Dict, Optional


class APIException(Exception):
    """
    Base exception for all API exceptions.
    
    All custom exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ):
        """
        Initialize API exception.
        
        Args:
            error_code: Error code (e.g., "VALIDATION_ERROR")
            message: Error message
            details: Optional error details
            status_code: HTTP status code
        """
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dict for error response."""
        return {
            "code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(APIException):
    """Validation error (400)."""
    
    def __init__(
        self,
        error_code: str = "VALIDATION_ERROR",
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details,
            status_code=400
        )


class UnauthorizedError(APIException):
    """Unauthorized error (401)."""
    
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="UNAUTHORIZED",
            message=message,
            details=details,
            status_code=401
        )


class ForbiddenError(APIException):
    """Forbidden error (403)."""
    
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="FORBIDDEN",
            message=message,
            details=details,
            status_code=403
        )


class NotFoundError(APIException):
    """Not found error (404)."""
    
    def __init__(self, resource: str = "Resource", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="NOT_FOUND",
            message=f"{resource} not found",
            details=details,
            status_code=404
        )


class ConflictError(APIException):
    """Conflict error (409)."""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="CONFLICT",
            message=message,
            details=details,
            status_code=409
        )


class InternalError(APIException):
    """Internal server error (500)."""
    
    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="INTERNAL_ERROR",
            message=message,
            details=details,
            status_code=500
        )
