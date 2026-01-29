"""
Standard API response format.

Provides consistent response structure across all API endpoints.
Follows the contract defined in the refactoring plan.
"""

# Standard library
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import uuid

# Third-party
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    pagination: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create standard success response.
    
    Args:
        data: Response data (can be dict, list, or any serializable object)
        message: Optional success message
        pagination: Optional pagination metadata
        request_id: Optional request ID for tracing
    
    Returns:
        Dict with standard success response format:
        {
            "success": true,
            "data": {...},
            "message": "...",
            "meta": {
                "timestamp": "...",
                "request_id": "..."
            },
            "pagination": {...}  # Only if pagination provided
        }
    
    Example:
        >>> response = success_response(
        ...     data={"id": 1, "name": "Job"},
        ...     message="Job retrieved successfully"
        ... )
    """
    response = {
        "success": True,
        "data": data,
        "message": message,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "request_id": request_id or str(uuid.uuid4())
        }
    }
    
    if pagination:
        response["pagination"] = pagination
    
    return response


def error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create standard error response.
    
    Args:
        error_code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Error message
        details: Optional error details (validation errors, etc.)
        status_code: HTTP status code
        request_id: Optional request ID for tracing
    
    Returns:
        JSONResponse with standard error format:
        {
            "success": false,
            "error": {
                "code": "...",
                "message": "...",
                "details": {...}
            },
            "meta": {
                "timestamp": "...",
                "request_id": "..."
            }
        }
    
    Example:
        >>> response = error_response(
        ...     error_code="VALIDATION_ERROR",
        ...     message="Invalid input",
        ...     details={"field": "email", "reason": "Invalid format"},
        ...     status_code=400
        ... )
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            },
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": request_id or str(uuid.uuid4())
            }
        }
    )


def paginated_response(
    data: list,
    page: int,
    limit: int,
    total: int,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create paginated response.
    
    Args:
        data: List of items for current page
        page: Current page number (1-indexed)
        limit: Items per page
        total: Total number of items
        message: Optional success message
        request_id: Optional request ID for tracing
    
    Returns:
        Dict with paginated response format including pagination metadata
    
    Example:
        >>> response = paginated_response(
        ...     data=[{"id": 1}, {"id": 2}],
        ...     page=1,
        ...     limit=20,
        ...     total=100
        ... )
    """
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    
    return success_response(
        data=data,
        message=message,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        request_id=request_id
    )
