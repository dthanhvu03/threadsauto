"""
Scheduler API routes.

REST API endpoints cho scheduler control.

LEGACY ROUTES - Using adapter pattern to call new services when available.
CRITICAL: Legacy routes must NOT maintain separate scheduler instances.
All scheduler access must go through SchedulerService (single source of truth).
"""

# Standard library
import asyncio
from typing import Optional
from fastapi import APIRouter, Query

# Local
from backend.api.adapters.jobs_adapter import JobsAPI
from backend.api.dependencies import get_jobs_api
from backend.app.core.responses import success_response
from backend.app.core.exceptions import InternalError
from backend.app.core.migration_flags import is_module_enabled

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        try:
            from backend.app.modules.scheduler.controllers import SchedulerController
            _controller = SchedulerController()
        except ImportError:
            _controller = None
    return _controller


@router.post("/start")
async def start_scheduler(account_id: Optional[str] = Query(None, description="Account ID filter")):
    """Start the scheduler."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    # CRITICAL: Legacy code must NOT maintain separate scheduler instance
    if is_module_enabled("scheduler"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.start(account_id=account_id)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    # NOTE: This should eventually be removed - scheduler access should only go through SchedulerService
    try:
        jobs_api = get_jobs_api()
        scheduler = jobs_api.scheduler
        
        if scheduler.running:
            return success_response(
                data={"status": "running"},
                message="Scheduler is already running"
            )
        
        # Start scheduler
        # Create post_callback_factory and pass to scheduler.start()
        if hasattr(scheduler, 'start'):
            # Create post_callback_factory
            from backend.app.modules.scheduler.utils.callback_factory import create_post_callback_factory
            post_callback_factory = create_post_callback_factory()
            scheduler.start(post_callback_factory)
        
        return success_response(
            data={"status": "started"},
            message="Scheduler started successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to start scheduler: {str(e)}")


@router.post("/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("scheduler"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.stop()
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        jobs_api = get_jobs_api()
        scheduler = jobs_api.scheduler
        
        if not scheduler.running:
            return success_response(
                data={"status": "stopped"},
                message="Scheduler is already stopped"
            )
        
        # Stop scheduler
        if hasattr(scheduler, 'stop'):
            try:
                await scheduler.stop()
            except asyncio.CancelledError:
                # CancelledError is expected when stopping scheduler - task is cancelled
                # This is normal behavior, not an error
                pass
        
        return success_response(
            data={"status": "stopped"},
            message="Scheduler stopped successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to stop scheduler: {str(e)}")


@router.get("/status")
async def get_scheduler_status():
    """Get scheduler status."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("scheduler"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_status()
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        jobs_api = get_jobs_api()
        scheduler = jobs_api.scheduler
        
        # Count active jobs (PENDING, SCHEDULED, RUNNING)
        active_jobs_count = 0
        if hasattr(scheduler, "get_active_jobs"):
            active_jobs_count = len(scheduler.get_active_jobs())
        elif hasattr(scheduler, "jobs"):
            # Fallback: filter jobs with active statuses
            from services.scheduler.models import JobStatus
            active_statuses = [JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.RUNNING]
            all_jobs = scheduler.jobs if scheduler.jobs else {}
            for job in all_jobs.values():
                if hasattr(job, 'status') and job.status in active_statuses:
                    active_jobs_count += 1
        
        status_data = {
            "running": scheduler.running,
            "active_jobs_count": active_jobs_count
        }
        
        return success_response(
            data=status_data,
            message="Scheduler status retrieved successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve scheduler status: {str(e)}")


@router.get("/jobs")
async def get_active_jobs():
    """Get active jobs from scheduler."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("scheduler"):
        controller = _get_controller()
        if controller:
            try:
                result = await controller.get_active_jobs()
                return result
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        jobs_api = get_jobs_api()
        scheduler = jobs_api.scheduler
        
        # QUAN TRỌNG: Reload jobs từ storage trước khi lấy active jobs
        # Điều này đảm bảo jobs mới được tạo (từ Excel upload) được nhận
        if hasattr(scheduler, "reload_jobs"):
            try:
                scheduler.reload_jobs(force=False)  # Use force=False để tránh race condition
            except Exception as reload_error:
                # Log nhưng không fail - vẫn có thể lấy jobs từ memory
                pass
        
        if hasattr(scheduler, "get_active_jobs"):
            active_jobs = scheduler.get_active_jobs()
        elif hasattr(scheduler, "jobs"):
            # Fallback: filter jobs with active statuses (PENDING, SCHEDULED, RUNNING)
            from services.scheduler.models import JobStatus
            active_statuses = [JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.RUNNING]
            all_jobs = scheduler.jobs if scheduler.jobs else {}
            active_jobs = []
            for job in all_jobs.values():
                if hasattr(job, 'status') and job.status in active_statuses:
                    # Convert to dict if needed
                    if hasattr(job, 'to_dict'):
                        active_jobs.append(job.to_dict())
                    elif hasattr(job, '__dict__'):
                        active_jobs.append(job.__dict__)
                    elif isinstance(job, dict):
                        active_jobs.append(job)
                    else:
                        # Try to serialize
                        active_jobs.append({
                            "job_id": str(job.job_id) if hasattr(job, 'job_id') else None,
                            "status": job.status.value if hasattr(job, 'status') and hasattr(job.status, 'value') else str(job.status) if hasattr(job, 'status') else "unknown"
                        })
        else:
            active_jobs = []
        
        return success_response(
            data=active_jobs,
            message="Active jobs retrieved successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve active jobs: {str(e)}")
