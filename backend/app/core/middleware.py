"""
Custom middleware for FastAPI application.

Provides request/response processing, logging, and other cross-cutting concerns.
"""

# Standard library
from typing import Callable
import time
import uuid
import threading

# Third-party
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Local
from services.logger import StructuredLogger
from utils.sanitize import sanitize_error

logger = StructuredLogger(name="api_middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses.
    
    Logs request method, path, status code, and response time.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log response."""
        start_time = time.time()
        
        # Generate request ID and store in request state
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        logger.log_step(
            step="REQUEST_START",
            result="IN_PROGRESS",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            request_id=request_id
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.log_step(
                step="REQUEST_END",
                result="SUCCESS",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                time_ms=process_time * 1000
            )
            
            # Add response time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error (sanitized)
            logger.log_step(
                step="REQUEST_ERROR",
                result="ERROR",
                method=request.method,
                path=request.url.path,
                error=sanitize_error(e),
                error_type=type(e).__name__,
                time_ms=process_time * 1000
            )
            
            raise


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate requests before processing.
    
    Validates Content-Type, request size, and headers.
    """
    
    MAX_REQUEST_SIZE = 1_000_000  # 1MB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request before processing."""
        # Check Content-Type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            # Allow multipart/form-data for file uploads (e.g., /api/excel/upload)
            # Allow application/json for regular API requests
            if "application/json" not in content_type and "multipart/form-data" not in content_type:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": {
                            "code": "INVALID_CONTENT_TYPE",
                            "message": "Content-Type must be application/json or multipart/form-data"
                        },
                        "meta": {
                            "timestamp": time.time(),
                            "request_id": getattr(request.state, "request_id", None)
                        }
                    }
                )
        
        # Check request size
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                content_length_int = int(content_length)
                if content_length_int > self.MAX_REQUEST_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "error": {
                                "code": "REQUEST_TOO_LARGE",
                                "message": f"Request body too large (max {self.MAX_REQUEST_SIZE // 1024 // 1024}MB)"
                            },
                            "meta": {
                                "timestamp": time.time(),
                                "request_id": getattr(request.state, "request_id", None)
                            }
                        }
                    )
            except ValueError:
                # Invalid Content-Length header, but continue processing
                pass
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    
    Limits requests per IP address to prevent DoS attacks.
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # IP -> list of timestamps
        self._lock = threading.Lock()
    
    def _cleanup_old_requests(self, ip: str, current_time: float) -> None:
        """Remove requests older than 1 minute."""
        if ip in self.request_counts:
            # Keep only requests from the last minute
            cutoff_time = current_time - 60.0
            self.request_counts[ip] = [
                ts for ts in self.request_counts[ip] if ts > cutoff_time
            ]
    
    def _check_rate_limit(self, ip: str) -> bool:
        """
        Check if IP has exceeded rate limit.
        
        Returns:
            True if within limit, False if exceeded
        """
        current_time = time.time()
        
        with self._lock:
            self._cleanup_old_requests(ip, current_time)
            
            if ip not in self.request_counts:
                self.request_counts[ip] = []
            
            # Check if limit exceeded
            if len(self.request_counts[ip]) >= self.requests_per_minute:
                return False
            
            # Add current request
            self.request_counts[ip].append(current_time)
            return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        # Exclude dashboard endpoints from rate limiting (they need more frequent updates)
        if request.url.path.startswith('/api/dashboard'):
            return await call_next(request)
        
        # Exclude GET /api/jobs from rate limiting (used by dashboard for filtering)
        # POST/PUT/DELETE are still rate limited for security
        if request.url.path == '/api/jobs' and request.method == 'GET':
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self._check_rate_limit(client_ip):
            logger.log_step(
                step="RATE_LIMIT_EXCEEDED",
                result="WARNING",
                path=request.url.path,
                method=request.method,
                client_ip=client_ip,
                request_id=getattr(request.state, "request_id", None)
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later."
                    },
                    "meta": {
                        "timestamp": time.time(),
                        "request_id": getattr(request.state, "request_id", None)
                    }
                }
            )
        
        return await call_next(request)
