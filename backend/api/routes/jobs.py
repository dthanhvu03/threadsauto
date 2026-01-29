"""
Jobs API routes.

REST API endpoints cho job operations.
"""

# Standard library
from typing import List, Optional
from fastapi import APIRouter, Query

# Local
from backend.api.adapters.jobs_adapter import JobsAPI
from backend.api.dependencies import get_jobs_api
from backend.app.core.responses import success_response, paginated_response
from backend.app.core.exceptions import NotFoundError, InternalError, ValidationError
from backend.app.core.validation import validate_job_input, sanitize_job_input

router = APIRouter()


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
    try:
        jobs_api = get_jobs_api()
        result = jobs_api.get_all_jobs(
            account_id=account_id,
            status=status,
            platform=platform,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            page=page,
            limit=limit,
            reload=reload
        )
        
        # Extract data and determine if we need to add pagination
        data_list = None
        existing_pagination = None
        
        if isinstance(result, dict) and "data" in result:
            data_list = result["data"] if isinstance(result["data"], list) else []
            existing_pagination = result.get("_pagination") or result.get("pagination")
        elif isinstance(result, list):
            data_list = result
            existing_pagination = None
        else:
            data_list = [] if result is None else [result] if not isinstance(result, (list, dict)) else []
        
        # Ensure data_list is a list
        if not isinstance(data_list, list):
            data_list = []
        
        # If page/limit are provided, ALWAYS return pagination (even if not in result)
        if page is not None and limit is not None:
            if existing_pagination:
                # Use existing pagination metadata
                return paginated_response(
                    data=data_list,
                    page=existing_pagination.get("page", page),
                    limit=existing_pagination.get("limit", limit),
                    total=existing_pagination.get("total", len(data_list)),
                    message="Jobs retrieved successfully"
                )
            else:
                # Calculate pagination from data
                total = len(data_list) if isinstance(data_list, list) else 0
                offset = (page - 1) * limit
                paginated_data = data_list[offset:offset + limit] if isinstance(data_list, list) else []
                
                return paginated_response(
                    data=paginated_data,
                    page=page,
                    limit=limit,
                    total=total,
                    message="Jobs retrieved successfully"
                )
        else:
            # No pagination requested - return as-is
            if isinstance(result, dict) and "data" in result:
                return success_response(data=result["data"], message="Jobs retrieved successfully")
            else:
                return success_response(data=result, message="Jobs retrieved successfully")
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve jobs: {str(e)}")


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get job by ID."""
    try:
        jobs_api = get_jobs_api()
        job = jobs_api.get_job_by_id(job_id)
        if not job:
            raise NotFoundError(resource="Job", details={"job_id": job_id})
        return success_response(data=job, message="Job retrieved successfully")
    except (NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve job: {str(e)}")


@router.post("")
async def create_job(job_data: dict):
    """Create a new job."""
    try:
        # Validate input
        is_valid, error_message = validate_job_input(job_data)
        if not is_valid:
            raise ValidationError(
                error_code="VALIDATION_ERROR",
                message=error_message or "Invalid job input",
                details={"field": "job_data"}
            )
        
        # Sanitize input
        sanitized_data = sanitize_job_input(job_data)
        
        jobs_api = get_jobs_api()
        job_id = jobs_api.add_job(
            content=sanitized_data.get("content"),
            account_id=sanitized_data.get("account_id"),
            platform=sanitized_data.get("platform", "threads"),
            scheduled_time=sanitized_data.get("scheduled_time"),
            priority=sanitized_data.get("priority", "normal"),
            link_aff=sanitized_data.get("link_aff")
        )
        return success_response(
            data={"job_id": job_id},
            message="Job created successfully"
        )
    except (ValidationError, NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message="Failed to create job")


@router.put("/{job_id}")
async def update_job(job_id: str, job_data: dict):
    """Update an existing job."""
    try:
        # Validate input
        is_valid, error_message = validate_job_input(job_data, is_update=True)
        if not is_valid:
            raise ValidationError(
                error_code="VALIDATION_ERROR",
                message=error_message or "Invalid job input",
                details={"field": "job_data"}
            )
        
        # Sanitize input
        sanitized_data = sanitize_job_input(job_data)
        
        jobs_api = get_jobs_api()
        
        # Get existing job first to check if it exists
        job = jobs_api.get_job_by_id(job_id)
        if not job:
            raise NotFoundError(resource="Job", details={"job_id": job_id})
        
        # Parse scheduled_time if provided
        scheduled_time = None
        if sanitized_data.get("scheduled_time"):
            from datetime import datetime
            try:
                scheduled_time = datetime.fromisoformat(sanitized_data["scheduled_time"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValidationError(
                    error_code="VALIDATION_ERROR",
                    message="Invalid scheduled_time format",
                    details={"field": "scheduled_time"}
                )
        
        # Update job
        success = jobs_api.update_job(
            job_id=job_id,
            content=sanitized_data.get("content"),
            account_id=sanitized_data.get("account_id"),
            scheduled_time=scheduled_time,
            priority=sanitized_data.get("priority"),
            platform=sanitized_data.get("platform"),
            max_retries=sanitized_data.get("max_retries"),
            link_aff=sanitized_data.get("link_aff")
        )
        
        if not success:
            raise InternalError(message="Failed to update job")
        
        return success_response(
            data={"job_id": job_id},
            message="Job updated successfully"
        )
    except (ValidationError, NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message="Failed to update job")


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job."""
    try:
        jobs_api = get_jobs_api()
        success = jobs_api.delete_job(job_id)
        if not success:
            raise NotFoundError(resource="Job", details={"job_id": job_id})
        return success_response(
            data={"job_id": job_id},
            message="Job deleted successfully"
        )
    except (NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to delete job: {str(e)}")
