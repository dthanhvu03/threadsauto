"""
Standard API response format for Flask.

Reuses response functions from FastAPI backend for consistency.
"""

# Local - Import from existing FastAPI responses
from backend.app.core.responses import (
    success_response,
    error_response,
    paginated_response
)

# Re-export for Flask usage
__all__ = [
    'success_response',
    'error_response',
    'paginated_response'
]
