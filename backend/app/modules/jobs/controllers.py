"""
Jobs controller.

Request/response handling layer.
Transforms service responses to API responses.
"""

# Standard library
from typing import Dict, List, Optional

# Local
from backend.app.core.responses import success_response, paginated_response
from backend.app.core.exceptions import NotFoundError, ValidationError, InternalError
from backend.app.modules.jobs.services.jobs_service import JobsService
from backend.app.modules.jobs.schemas import JobCreate, JobUpdate


class JobsController:
    """
    Controller for jobs endpoints.

    Handles:
    - Request validation (using schemas)
    - Calling service layer
    - Transforming service response to API response
    - HTTP status codes
    """

    def __init__(self, service: Optional[JobsService] = None):
        """
        Initialize jobs controller.

        Args:
            service: JobsService instance. If None, creates new instance.
        """
        self.service = service or JobsService()

    async def list_jobs(
        self,
        account_id: Optional[str] = None,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        scheduled_from: Optional[str] = None,
        scheduled_to: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        reload: bool = False,
    ) -> Dict:
        """
        List jobs endpoint with optional filters and pagination.

        Args:
            account_id: Optional account ID filter
            status: Optional status filter
            platform: Optional platform filter
            scheduled_from: Optional scheduled from date filter
            scheduled_to: Optional scheduled to date filter
            page: Optional page number for pagination
            limit: Optional items per page for pagination
            reload: Whether to reload jobs from storage

        Returns:
            Standard success response with jobs data (paginated if page/limit provided)
        """
        try:
            result = self.service.get_all_jobs(
                account_id=account_id,
                status=status,
                platform=platform,
                scheduled_from=scheduled_from,
                scheduled_to=scheduled_to,
                page=page,
                limit=limit,
                reload=reload,
            )

            # Handle response format (could be list or dict with data and pagination)
            if isinstance(result, dict) and "data" in result:
                pagination_meta = result.get("_pagination") or result.get("pagination")
                if pagination_meta:
                    # Response has pagination - use paginated_response
                    return paginated_response(
                        data=result["data"],
                        page=pagination_meta.get("page", page or 1),
                        limit=pagination_meta.get("limit", limit or 20),
                        total=pagination_meta.get("total", len(result["data"])),
                        message="Jobs retrieved successfully",
                    )
                elif page is not None and limit is not None:
                    # No pagination metadata but page/limit requested - add pagination
                    data_list = (
                        result["data"] if isinstance(result["data"], list) else []
                    )
                    total = len(data_list)
                    offset = (page - 1) * limit
                    paginated_data = data_list[offset : offset + limit]

                    return paginated_response(
                        data=paginated_data,
                        page=page,
                        limit=limit,
                        total=total,
                        message="Jobs retrieved successfully",
                    )
                else:
                    # No pagination requested - return as-is
                    return success_response(
                        data=result["data"], message="Jobs retrieved successfully"
                    )
            elif isinstance(result, list):
                # Response is just a list
                if page is not None and limit is not None:
                    # Apply pagination to the list
                    total = len(result)
                    offset = (page - 1) * limit
                    paginated_data = result[offset : offset + limit]

                    return paginated_response(
                        data=paginated_data,
                        page=page,
                        limit=limit,
                        total=total,
                        message="Jobs retrieved successfully",
                    )
                else:
                    # No pagination requested - return as-is
                    return success_response(
                        data=result, message="Jobs retrieved successfully"
                    )
            else:
                # Unexpected format - return as-is
                return success_response(
                    data=result, message="Jobs retrieved successfully"
                )
        except Exception as e:
            raise InternalError(
                message=f"Failed to retrieve jobs: {str(e)}",
                details={"account_id": account_id},
            )

    async def get_job(self, job_id: str) -> Dict:
        """
        Get job by ID endpoint.

        Args:
            job_id: Job ID

        Returns:
            Standard success response with job data

        Raises:
            NotFoundError: If job not found
        """
        try:
            job = self.service.get_job_by_id(job_id)
            if not job:
                raise NotFoundError(resource="Job", details={"job_id": job_id})
            return success_response(data=job, message="Job retrieved successfully")
        except NotFoundError:
            raise
        except Exception as e:
            raise InternalError(
                message=f"Failed to retrieve job: {str(e)}", details={"job_id": job_id}
            )

    async def create_job(self, job_data: JobCreate) -> Dict:
        """
        Create job endpoint.

        Args:
            job_data: Job creation data (validated by Pydantic)

        Returns:
            Standard success response with job ID

        Raises:
            ValidationError: If validation fails
        """
        try:
            job_id = self.service.create_job(
                account_id=job_data.account_id,
                content=job_data.content,
                scheduled_time=job_data.scheduled_time,
                priority=job_data.priority,
                platform=job_data.platform,
                link_aff=job_data.link_aff,
            )
            return success_response(
                data={"job_id": job_id}, message="Job created successfully"
            )
        except ValidationError:
            raise
        except Exception as e:
            raise InternalError(
                message=f"Failed to create job: {str(e)}",
                details={"account_id": job_data.account_id},
            )

    async def update_job(self, job_id: str, job_data: JobUpdate) -> Dict:
        """
        Update job endpoint.

        Args:
            job_id: Job ID
            job_data: Job update data (Pydantic model)

        Returns:
            Standard success response
        """
        try:
            # Import JobsAPI to use existing update logic
            from backend.api.adapters.jobs_adapter import JobsAPI
            from backend.api.dependencies import get_jobs_api
            from backend.app.core.validation import (
                validate_job_input,
                sanitize_job_input,
            )
            from datetime import datetime

            # Convert Pydantic model to dict
            job_dict = (
                job_data.model_dump(exclude_unset=True)
                if hasattr(job_data, "model_dump")
                else job_data.dict(exclude_unset=True)
            )

            # Validate input for update (fields can be optional)
            is_valid, error_message = validate_job_input(job_dict, is_update=True)
            if not is_valid:
                raise ValidationError(
                    error_code="VALIDATION_ERROR",
                    message=error_message or "Invalid job update input",
                    details={"field": "job_data"},
                )

            # Sanitize input
            sanitized_data = sanitize_job_input(job_dict)

            # Get JobsAPI instance
            jobs_api = get_jobs_api()

            # Check if job exists first (using service to get job)
            # This allows us to return NotFoundError instead of generic InternalError
            job_exists = self.service.get_job_by_id(job_id)
            if not job_exists:
                raise NotFoundError(resource="Job", details={"job_id": job_id})

            # Parse scheduled_time if provided
            scheduled_time = None
            if sanitized_data.get("scheduled_time"):
                try:
                    from services.utils.datetime_utils import vn_to_utc

                    scheduled_time = datetime.fromisoformat(
                        sanitized_data["scheduled_time"].replace("Z", "+00:00")
                    )
                    if scheduled_time.tzinfo is None:
                        # Naive → treat as VN time
                        scheduled_time = vn_to_utc(scheduled_time)
                    else:
                        # Has timezone → convert to UTC
                        from datetime import timezone

                        scheduled_time = scheduled_time.astimezone(timezone.utc)
                except (ValueError, AttributeError):
                    raise ValidationError(
                        error_code="VALIDATION_ERROR",
                        message="Invalid scheduled_time format",
                        details={"field": "scheduled_time"},
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
                link_aff=sanitized_data.get("link_aff"),
            )

            if not success:
                raise InternalError(message="Failed to update job")

            return success_response(
                data={"job_id": job_id}, message="Job updated successfully"
            )
        except (ValidationError, NotFoundError, InternalError):
            raise
        except Exception as e:
            raise InternalError(message=f"Failed to update job: {str(e)}")

    async def delete_job(self, job_id: str) -> Dict:
        """
        Delete job endpoint.

        Args:
            job_id: Job ID

        Returns:
            Standard success response

        Raises:
            NotFoundError: If job not found
        """
        try:
            success = self.service.delete_job(job_id)
            if not success:
                raise NotFoundError(resource="Job", details={"job_id": job_id})
            return success_response(
                data={"job_id": job_id}, message="Job deleted successfully"
            )
        except NotFoundError:
            raise
        except Exception as e:
            raise InternalError(
                message=f"Failed to delete job: {str(e)}", details={"job_id": job_id}
            )

    async def get_stats(self, account_id: Optional[str] = None) -> Dict:
        """
        Get job statistics endpoint.

        Args:
            account_id: Optional account ID filter

        Returns:
            Standard success response with statistics
        """
        try:
            stats = self.service.get_stats(account_id=account_id)
            return success_response(
                data=stats, message="Statistics retrieved successfully"
            )
        except Exception as e:
            raise InternalError(
                message=f"Failed to retrieve statistics: {str(e)}",
                details={"account_id": account_id},
            )
