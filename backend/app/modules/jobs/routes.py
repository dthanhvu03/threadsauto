"""
Jobs routes.

FastAPI routes for jobs endpoints.
Thin layer that calls controller.
"""

# Standard library
from typing import Optional
from fastapi import APIRouter, Query

# Local
from backend.app.modules.jobs.controllers import JobsController
from backend.app.modules.jobs.schemas import JobCreate, JobUpdate

router = APIRouter()
controller = JobsController()


@router.get("")
async def list_jobs(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    scheduled_from: Optional[str] = Query(None, description="Filter jobs scheduled after this date (YYYY-MM-DD)"),
    scheduled_to: Optional[str] = Query(None, description="Filter jobs scheduled before this date (YYYY-MM-DD)"),
    page: Optional[int] = Query(None, description="Page number (1-based) for pagination"),
    limit: Optional[int] = Query(None, description="Items per page for pagination"),
    reload: bool = Query(False, description="Reload jobs from storage")
):
    """List all jobs with optional filters and pagination."""
    return await controller.list_jobs(
        account_id=account_id,
        status=status,
        platform=platform,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        page=page,
        limit=limit,
        reload=reload
    )


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get job by ID."""
    return await controller.get_job(job_id)


@router.post("")
async def create_job(job_data: JobCreate):
    """Create a new job."""
    return await controller.create_job(job_data)


@router.put("/{job_id}")
async def update_job(job_id: str, job_data: JobUpdate):
    """Update an existing job."""
    return await controller.update_job(job_id, job_data)


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job."""
    return await controller.delete_job(job_id)


@router.get("/stats/summary")
async def get_stats(
    account_id: Optional[str] = Query(None, description="Filter by account ID")
):
    """Get job statistics."""
    return await controller.get_stats(account_id=account_id)
