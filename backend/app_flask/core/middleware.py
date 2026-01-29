"""
Middleware for Flask application.

Provides request/response processing, logging, and other cross-cutting concerns.
"""

# Standard library
import time
import uuid
from functools import wraps

# Third-party
from flask import request, g

# Local
from services.logger import StructuredLogger

logger = StructuredLogger(name="flask_middleware")


def register_middleware(app):
    """
    Register middleware for Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Process request before handling."""
        # Generate request ID
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()
        
        # Log request
        logger.log_step(
            step="REQUEST_START",
            result="IN_PROGRESS",
            method=request.method,
            path=request.path,
            query_params=str(request.args) if request.args else None,
            request_id=g.request_id
        )
    
    @app.after_request
    def after_request(response):
        """Process response after handling."""
        # Calculate process time
        if hasattr(g, 'start_time'):
            process_time = time.time() - g.start_time
            
            # Log response
            logger.log_step(
                step="REQUEST_END",
                result="SUCCESS",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                time_ms=process_time * 1000
            )
            
            # Add response time header
            response.headers['X-Process-Time'] = str(process_time)
        
        # Add request ID to response headers
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    @app.teardown_request
    def teardown_request(exception):
        """Clean up after request."""
        if exception:
            logger.log_step(
                step="REQUEST_ERROR",
                result="ERROR",
                method=request.method,
                path=request.path,
                error=str(exception),
                error_type=type(exception).__name__
            )
