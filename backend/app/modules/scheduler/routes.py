"""
Scheduler API routes.

FastAPI routes for scheduler operations.
"""

# Standard library
from typing import Optional
from fastapi import APIRouter, Query

# Local
from backend.app.modules.scheduler.controllers import SchedulerController

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        _controller = SchedulerController()
    return _controller


@router.post("/start")
async def start_scheduler(account_id: Optional[str] = Query(None, description="Account ID filter")):
    """Start the scheduler."""
    controller = _get_controller()
    return await controller.start(account_id=account_id)


@router.post("/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    controller = _get_controller()
    return await controller.stop()


@router.get("/status")
async def get_scheduler_status():
    """Get scheduler status."""
    controller = _get_controller()
    return await controller.get_status()


@router.get("/jobs")
async def get_active_jobs():
    """Get active jobs from scheduler."""
    controller = _get_controller()
    return await controller.get_active_jobs()
