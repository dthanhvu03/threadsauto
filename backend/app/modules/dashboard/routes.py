"""
Dashboard API routes.

FastAPI routes for dashboard operations.
"""

# Standard library
from typing import Optional
from fastapi import APIRouter, Query

# Local
from backend.app.modules.dashboard.controllers import DashboardController

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        _controller = DashboardController()
    return _controller


@router.get("/stats")
async def get_dashboard_stats(
    account_id: Optional[str] = Query(None, description="Filter by account ID")
):
    """Get dashboard statistics."""
    controller = _get_controller()
    return await controller.get_stats(account_id=account_id)


@router.get("/metrics")
async def get_dashboard_metrics(
    account_id: Optional[str] = Query(None, description="Filter by account ID")
):
    """Get dashboard metrics."""
    controller = _get_controller()
    return await controller.get_metrics(account_id=account_id)


@router.get("/activity")
async def get_recent_activity(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    limit: int = Query(10, description="Number of activities to return")
):
    """Get recent activity."""
    controller = _get_controller()
    return await controller.get_activity(account_id=account_id, limit=limit)
