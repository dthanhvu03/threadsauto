"""
Custom exceptions for Flask API layer.

Reuses exceptions from FastAPI backend for consistency.
"""

# Local - Import from existing FastAPI exceptions
from backend.app.core.exceptions import (
    APIException,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    InternalError
)

# Re-export for Flask usage
__all__ = [
    'APIException',
    'ValidationError',
    'UnauthorizedError',
    'ForbiddenError',
    'NotFoundError',
    'ConflictError',
    'InternalError'
]
