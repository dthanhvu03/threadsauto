"""
Standard API response helpers.
"""

from fastapi.responses import JSONResponse


def success_response(data=None, message: str = None):
    """Create success response."""
    return {
        "success": True,
        "data": data,
        "error": None,
        "message": message
    }


def error_response(error: str, message: str = None, status_code: int = 400):
    """Create error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": error,
            "message": message
        }
    )
