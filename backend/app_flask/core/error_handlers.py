"""
Error handlers for Flask application.

Handles exceptions and returns standard error responses.
"""

# Third-party
from flask import jsonify, g

# Local
from backend.app_flask.core.exceptions import APIException
from backend.app_flask.core.responses import error_response
from backend.app.core.exceptions import (
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    InternalError
)


def register_error_handlers(app):
    """
    Register error handlers for Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(APIException)
    def handle_api_exception(e):
        """Handle custom API exceptions."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code=e.error_code,
            message=e.message,
            details=e.details,
            status_code=e.status_code,
            request_id=request_id
        ), e.status_code
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        """Handle validation errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="VALIDATION_ERROR",
            message=e.message,
            details=e.details,
            status_code=400,
            request_id=request_id
        ), 400
    
    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(e):
        """Handle unauthorized errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="UNAUTHORIZED",
            message=e.message,
            details=e.details,
            status_code=401,
            request_id=request_id
        ), 401
    
    @app.errorhandler(ForbiddenError)
    def handle_forbidden_error(e):
        """Handle forbidden errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="FORBIDDEN",
            message=e.message,
            details=e.details,
            status_code=403,
            request_id=request_id
        ), 403
    
    @app.errorhandler(NotFoundError)
    def handle_not_found_error(e):
        """Handle not found errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="NOT_FOUND",
            message=e.message,
            details=e.details,
            status_code=404,
            request_id=request_id
        ), 404
    
    @app.errorhandler(ConflictError)
    def handle_conflict_error(e):
        """Handle conflict errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="CONFLICT",
            message=e.message,
            details=e.details,
            status_code=409,
            request_id=request_id
        ), 409
    
    @app.errorhandler(InternalError)
    def handle_internal_error(e):
        """Handle internal errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="INTERNAL_ERROR",
            message=e.message,
            details=e.details,
            status_code=500,
            request_id=request_id
        ), 500
    
    @app.errorhandler(404)
    def handle_404(e):
        """Handle 404 errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="NOT_FOUND",
            message="Resource not found",
            status_code=404,
            request_id=request_id
        ), 404
    
    @app.errorhandler(500)
    def handle_500(e):
        """Handle 500 errors."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            status_code=500,
            request_id=request_id
        ), 500
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        """Handle general exceptions."""
        request_id = getattr(g, 'request_id', None)
        return error_response(
            error_code="INTERNAL_ERROR",
            message="Internal server error",
            details={"error_type": type(e).__name__},
            status_code=500,
            request_id=request_id
        ), 500
