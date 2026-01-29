"""
FastAPI backend cho Threads Automation Tool.

Main entry point cho REST API server.
"""

# Standard library
import os
import sys
from pathlib import Path

# Add parent directory to path để import các modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Third-party
from fastapi import FastAPI, Request, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

# Local
from backend.api.routes import (
    jobs,
    accounts,
    dashboard,
    excel,
    scheduler,
    config,
    selectors
)
from backend.api.websocket.routes import websocket_endpoint
from backend.app.core.responses import success_response, error_response
from backend.app.core.exceptions import APIException
from backend.app.core.middleware import RequestLoggingMiddleware, RequestValidationMiddleware
from services.logger import StructuredLogger
from utils.sanitize import sanitize_error

# Initialize logger
logger = StructuredLogger(name="fastapi_backend")

# Create FastAPI app
app = FastAPI(
    title="Threads Automation API",
    description="REST API cho Threads Automation Tool",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request validation middleware (must be before logging)
app.add_middleware(RequestValidationMiddleware)

# Rate limiting middleware (simple in-memory rate limiting)
from backend.app.core.middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
# Import migration flags utility
from backend.app.core.migration_flags import get_enabled_modules, is_module_enabled

# New module-based routes (conditionally registered based on ENV flag)
# Jobs module (already migrated)
try:
    from backend.app.modules.jobs.routes import router as jobs_module_router
    app.include_router(jobs_module_router, prefix="/api/jobs", tags=["jobs"])
except ImportError as e:
    # Fallback to legacy routes if new module not available
    logger.log_step(
        step="ROUTER_SETUP",
        result="WARNING",
        error=f"Could not import new jobs module routes: {str(e)}, using legacy routes",
        error_type=type(e).__name__
    )
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

# Accounts module (conditionally registered)
# Note: When new routes are enabled, they are registered AFTER legacy routes
# so legacy routes take precedence (adapter pattern)
# Legacy routes will delegate to new controller when available
if is_module_enabled("accounts"):
    try:
        from backend.app.modules.accounts.routes import router as accounts_module_router
        # Register new routes AFTER legacy routes so legacy routes take precedence
        # Legacy routes will use adapter pattern to call new controller
        logger.log_step(
            step="ROUTER_SETUP",
            result="INFO",
            note="New accounts module available (legacy routes will delegate to it)",
            enabled_modules=list(get_enabled_modules())
        )
    except ImportError as e:
        logger.log_step(
            step="ROUTER_SETUP",
            result="WARNING",
            error=f"Could not import new accounts module routes: {str(e)}, using legacy routes only",
            error_type=type(e).__name__
        )

# Dashboard module (conditionally registered)
# Note: When new routes are enabled, they are registered AFTER legacy routes
# so legacy routes take precedence (adapter pattern)
if is_module_enabled("dashboard"):
    try:
        from backend.app.modules.dashboard.routes import router as dashboard_module_router
        logger.log_step(
            step="ROUTER_SETUP",
            result="INFO",
            note="New dashboard module available (legacy routes will delegate to it)",
            enabled_modules=list(get_enabled_modules())
        )
    except ImportError as e:
        logger.log_step(
            step="ROUTER_SETUP",
            result="WARNING",
            error=f"Could not import new dashboard module routes: {str(e)}, using legacy routes only",
            error_type=type(e).__name__
        )

# Scheduler module (conditionally registered)
# CRITICAL: SchedulerService is the single source of truth for scheduler instance
if is_module_enabled("scheduler"):
    try:
        from backend.app.modules.scheduler.routes import router as scheduler_module_router
        logger.log_step(
            step="ROUTER_SETUP",
            result="INFO",
            note="New scheduler module available (legacy routes will delegate to it)",
            enabled_modules=list(get_enabled_modules())
        )
    except ImportError as e:
        logger.log_step(
            step="ROUTER_SETUP",
            result="WARNING",
            error=f"Could not import new scheduler module routes: {str(e)}, using legacy routes only",
            error_type=type(e).__name__
        )

# Legacy routes (kept for backward compatibility - will be removed)
# Note: Legacy routes use adapter pattern to call new services when available
# These routes are ALWAYS registered and take precedence over new routes
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
# Excel module (conditionally registered)
if is_module_enabled("excel"):
    try:
        from backend.app.modules.excel.routes import router as excel_module_router
        logger.log_step(
            step="ROUTER_SETUP",
            result="INFO",
            note="New excel module available (legacy routes will delegate to it)",
            enabled_modules=list(get_enabled_modules())
        )
    except ImportError as e:
        logger.log_step(
            step="ROUTER_SETUP",
            result="WARNING",
            error=f"Could not import new excel module routes: {str(e)}, using legacy routes only",
            error_type=type(e).__name__
        )

app.include_router(excel.router, prefix="/api/excel", tags=["excel"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])

# Config module (conditionally registered)
if is_module_enabled("config"):
    try:
        from backend.app.modules.config.routes import router as config_module_router
        logger.log_step(
            step="ROUTER_SETUP",
            result="INFO",
            note="New config module available (legacy routes will delegate to it)",
            enabled_modules=list(get_enabled_modules())
        )
    except ImportError as e:
        logger.log_step(
            step="ROUTER_SETUP",
            result="WARNING",
            error=f"Could not import new config module routes: {str(e)}, using legacy routes only",
            error_type=type(e).__name__
        )

# Selectors module (conditionally registered)
if is_module_enabled("selectors"):
    try:
        from backend.app.modules.selectors.routes import router as selectors_module_router
        logger.log_step(
            step="ROUTER_SETUP",
            result="INFO",
            note="New selectors module available (legacy routes will delegate to it)",
            enabled_modules=list(get_enabled_modules())
        )
    except ImportError as e:
        logger.log_step(
            step="ROUTER_SETUP",
            result="WARNING",
            error=f"Could not import new selectors module routes: {str(e)}, using legacy routes only",
            error_type=type(e).__name__
        )

app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(selectors.router, prefix="/api/selectors", tags=["selectors"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, room: str = "default", account_id: str = None):
    """WebSocket endpoint for real-time updates."""
    await websocket_endpoint(websocket, room=room, account_id=account_id)


# Exception handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions."""
    logger.log_step(
        step="API_EXCEPTION",
        result="ERROR",
        error_code=exc.error_code,
        error=exc.message,
        path=request.url.path,
        method=request.method
    )
    return error_response(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
        request_id=getattr(request.state, "request_id", None)
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.log_step(
        step="HTTP_EXCEPTION",
        result="ERROR",
        error=f"{exc.status_code}: {exc.detail}",
        path=request.url.path,
        method=request.method
    )
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        500: "INTERNAL_ERROR"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return error_response(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=getattr(request.state, "request_id", None)
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.log_step(
        step="VALIDATION_ERROR",
        result="ERROR",
        error=str(exc.errors()),
        path=request.url.path,
        method=request.method
    )
    return error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=getattr(request.state, "request_id", None)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler - không expose thông tin nhạy cảm.
    
    Log chi tiết vào file, nhưng chỉ trả về generic error message.
    """
    # Log chi tiết vào file (với sanitize)
    logger.log_step(
        step="UNHANDLED_EXCEPTION",
        result="ERROR",
        error=sanitize_error(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method
    )
    # Trả về generic error message (không expose stack trace hoặc error type)
    return error_response(
        error_code="INTERNAL_ERROR",
        message="An internal error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=getattr(request.state, "request_id", None)
    )


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return success_response(
        data={"message": "Threads Automation API", "version": "1.0.0"},
        message="API is running"
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return success_response(
        data={"status": "healthy"},
        message="API is healthy"
    )


if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
