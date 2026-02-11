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
    request_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standard success response matching API documentation format.
    
    Args:
        data: Response data (can be dict, list, or any serializable object)
        message: Optional success message
        pagination: Optional pagination metadata
        request_id: Optional request ID for tracing
        meta: Optional additional metadata (will be merged with default meta)
    
    Returns:
        Dict with standard success response format:
        {
            "success": true,
            "data": {...},
            "meta": {...},  # Optional metadata
            "timestamp": "..."  # ISO 8601 timestamp at root level
        }
    
    Example:
        >>> response = success_response(
        ...     data={"id": 1, "name": "Job"},
        ...     message="Job retrieved successfully"
        ... )
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    # Build meta dict
    response_meta = {
        "request_id": request_id or str(uuid.uuid4())
    }
    if meta:
        response_meta.update(meta)
    
    response = {
        "success": True,
        "data": data,
        "timestamp": timestamp
    }
    
    # Add meta only if it has content beyond request_id
    if response_meta:
        response["meta"] = response_meta
    
    # Add message if provided
    if message:
        response["message"] = message
    
    # Add pagination if provided
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
    Create standard error response matching API documentation format.
    
    Args:
        error_code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Error message (will be used as simple string in response)
        details: Optional error details (for logging, not included in response)
        status_code: HTTP status code
        request_id: Optional request ID for tracing
    
    Returns:
        JSONResponse with standard error format:
        {
            "success": false,
            "error": "...",  # Simple error message string
            "timestamp": "..."  # ISO 8601 timestamp at root level
        }
    
    Example:
        >>> response = error_response(
        ...     error_code="VALIDATION_ERROR",
        ...     message="Invalid input",
        ...     status_code=400
        ... )
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": message,  # Simple string format matching documentation
            "timestamp": timestamp
        }
    )


def timeout_error_response(
    operation: str,
    timeout: int,
    elapsed_time: Optional[int] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create timeout error response matching API documentation format.
    
    Args:
        operation: Operation name that timed out
        timeout: Timeout value in milliseconds
        elapsed_time: Actual elapsed time in milliseconds (optional)
        request_id: Optional request ID for tracing
    
    Returns:
        JSONResponse with timeout error format:
        {
            "success": false,
            "error": "Operation \"{operation}\" timed out after {timeout}ms",
            "errorCode": "TIMEOUT_ERROR",
            "timeout": timeout,
            "operation": operation,
            "elapsedTime": elapsed_time or timeout,
            "timestamp": "..."
        }
    
    Example:
        >>> response = timeout_error_response(
        ...     operation="feed_extraction",
        ...     timeout=300000,
        ...     elapsed_time=300123
        ... )
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    error_message = f'Operation "{operation}" timed out after {timeout}ms'
    
    return JSONResponse(
        status_code=504,
        content={
            "success": False,
            "error": error_message,
            "errorCode": "TIMEOUT_ERROR",
            "timeout": timeout,
            "operation": operation,
            "elapsedTime": elapsed_time or timeout,
            "timestamp": timestamp
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
