"""
Jobs service.

Business logic layer for job operations.
Handles validation, orchestration, and business rules.
"""

# Standard library
from typing import Dict, List, Optional
from datetime import datetime, timezone

# Local
from services.scheduler.models import JobPriority, JobStatus, Platform
from services.logger import StructuredLogger
from services.utils.datetime_utils import normalize_to_utc
from backend.app.shared.base_service import BaseService
from backend.app.modules.jobs.repositories.jobs_repository import JobsRepository
from backend.app.core.exceptions import ValidationError, NotFoundError, InternalError
from backend.api.adapters.job_serializer import serialize_job
from backend.api.adapters.jobs_helpers import (
    convert_jobs_to_dicts,
    resolve_target_scheduler,
    safe_reload_jobs,
)


class JobsService(BaseService):
    """
    Service for job business logic.

    Handles:
    - Validation
    - Business rules
    - Orchestration
    - Safety checks
    """

    def __init__(self, repository: Optional[JobsRepository] = None):
        """
        Initialize jobs service.

        Args:
            repository: JobsRepository instance. If None, creates new instance.
        """
        super().__init__("jobs_service")
        self.repository = repository or JobsRepository()

    def get_all_jobs(
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
        Get all jobs with optional filters and pagination.

        Args:
            account_id: Account ID to filter by (None = all accounts)
            status: Status to filter by (None = all statuses)
            platform: Platform to filter by (None = all platforms)
            scheduled_from: Filter jobs scheduled after this date (YYYY-MM-DD)
            scheduled_to: Filter jobs scheduled before this date (YYYY-MM-DD)
            page: Page number (1-based) for pagination
            limit: Items per page for pagination
            reload: If True, reload jobs from storage before listing

        Returns:
            Dict with 'data' (list of job dictionaries) and 'pagination' metadata
        """
        try:
            # Reload if requested
            if reload:
                self.repository.reload_jobs(
                    force=True
                )  # Force reload to get latest data from storage

            # Prepare filters
            filters = {}
            if account_id:
                filters["account_id"] = str(account_id).strip()
            if status:
                status_str = str(status).strip()
                filters["status"] = status_str
                self.logger.log_step(
                    step="GET_ALL_JOBS",
                    result="DEBUG",
                    note=f"Status filter received: {status_str}",
                    account_id=account_id,
                )
            if platform:
                filters["platform"] = str(platform).strip()
            if scheduled_from:
                filters["scheduled_from"] = scheduled_from
            if scheduled_to:
                filters["scheduled_to"] = scheduled_to

            # Calculate pagination
            offset = None
            if page and limit:
                offset = (page - 1) * limit

            # Get jobs from repository (with filters and pagination)
            jobs = self.repository.get_all(filters=filters, limit=limit, offset=offset)

            # Get total count for pagination (before pagination applied)
            total_count = self.repository.get_count(filters=filters)

            # Convert to dicts
            result = convert_jobs_to_dicts(jobs, serialize_job, self.logger)

            # Build pagination metadata - always return if page/limit provided
            pagination = None
            if page is not None and limit is not None:
                total_pages = (
                    (total_count + limit - 1) // limit
                    if total_count > 0 and limit > 0
                    else 0
                )
                pagination = {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages if total_pages > 0 else False,
                    "has_prev": page > 1,
                }

            self._log_operation(
                "GET_ALL_JOBS",
                "SUCCESS",
                jobs_count=len(result),
                account_id=account_id,
                total_count=total_count,
                page=page,
                limit=limit,
                has_pagination=pagination is not None,
            )

            # Always return data with pagination if pagination was requested
            # This ensures frontend always gets pagination metadata
            if pagination:
                return {"data": result, "_pagination": pagination}
            else:
                # No pagination requested - return array directly
                return result

        except Exception as e:
            self._handle_error(
                "GET_ALL_JOBS",
                e,
                {"account_id": account_id, "page": page, "limit": limit},
            )
            return [] if not (page and limit) else {"data": [], "_pagination": None}

    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job dictionary if found, None otherwise
        """
        try:
            if not job_id or not isinstance(job_id, str):
                raise ValidationError(
                    message="job_id must be a non-empty string",
                    details={"job_id": job_id},
                )

            job_id = job_id.strip()
            job = self.repository.get_by_id(job_id)

            if not job:
                return None

            # Serialize job
            return serialize_job(job)

        except ValidationError:
            raise
        except Exception as e:
            self._handle_error("GET_JOB_BY_ID", e, {"job_id": job_id})
            return None

    def create_job(
        self,
        account_id: str,
        content: str,
        scheduled_time: str,
        priority: str = "NORMAL",
        platform: str = "THREADS",
        link_aff: Optional[str] = None,
    ) -> str:
        """
        Create new job.

        Args:
            account_id: Account ID
            content: Content string
            scheduled_time: ISO format datetime string
            priority: Priority string (NORMAL, HIGH, URGENT)
            platform: Platform string (THREADS, FACEBOOK)
            link_aff: Optional affiliate link

        Returns:
            Job ID

        Raises:
            ValidationError: If validation fails
            InternalError: If creation fails
        """
        try:
            # Validate inputs
            self._validate_create_job_inputs(
                account_id, content, scheduled_time, priority, platform
            )

            # Parse datetime and ensure UTC
            try:
                dt = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    # Naive datetime from form input → treat as VN time
                    from services.utils.datetime_utils import vn_to_utc

                    dt = vn_to_utc(dt)
                else:
                    # Already has timezone → convert to UTC
                    dt = dt.astimezone(timezone.utc)
            except (ValueError, TypeError) as e:
                raise ValidationError(
                    message=f"Invalid scheduled_time format: {scheduled_time}. Expected ISO format.",
                    details={"scheduled_time": scheduled_time},
                ) from e

            # Convert priority
            try:
                priority_enum = JobPriority[priority.upper()]
            except KeyError:
                valid_priorities = [p.name for p in JobPriority]
                raise ValidationError(
                    message=f"Invalid priority: {priority}. Valid priorities: {', '.join(valid_priorities)}",
                    details={
                        "priority": priority,
                        "valid_priorities": valid_priorities,
                    },
                )

            # Convert platform
            try:
                platform_enum = Platform[platform.upper()]
            except KeyError:
                valid_platforms = [p.name for p in Platform]
                raise ValidationError(
                    message=f"Invalid platform: {platform}. Valid platforms: {', '.join(valid_platforms)}",
                    details={"platform": platform, "valid_platforms": valid_platforms},
                )

            # Safety guard check (optional)
            self._check_safety_guard(account_id, content)

            # Create job via repository
            job_data = {
                "account_id": account_id,
                "content": content,
                "scheduled_time": dt,
                "priority": priority_enum,
                "platform": platform_enum,
                "link_aff": link_aff,
            }

            job = self.repository.create(job_data)

            # Sync with active scheduler if needed
            self._sync_with_active_scheduler(job.job_id)

            self._log_operation(
                "CREATE_JOB", "SUCCESS", job_id=job.job_id, account_id=account_id
            )

            return job.job_id

        except (ValidationError, InternalError):
            raise
        except Exception as e:
            self._handle_error(
                "CREATE_JOB",
                e,
                {
                    "account_id": account_id,
                    "content_length": len(content) if content else 0,
                },
            )
            raise InternalError(
                message=f"Failed to create job: {str(e)}",
                details={"account_id": account_id},
            )

    def delete_job(self, job_id: str) -> bool:
        """
        Delete job.

        Args:
            job_id: Job ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if not job_id or not isinstance(job_id, str):
                raise ValidationError(
                    message="job_id must be a non-empty string",
                    details={"job_id": job_id},
                )

            job_id = job_id.strip()

            # Delete via repository
            success = self.repository.delete(job_id)

            if success:
                self._log_operation("DELETE_JOB", "SUCCESS", job_id=job_id)
            else:
                self._log_operation("DELETE_JOB", "FAILED", job_id=job_id)

            return success

        except ValidationError:
            raise
        except Exception as e:
            self._handle_error("DELETE_JOB", e, {"job_id": job_id})
            return False

    def get_stats(self, account_id: Optional[str] = None) -> Dict:
        """
        Get job statistics.

        Args:
            account_id: Account ID to filter by (None = all accounts)

        Returns:
            Dictionary with statistics
        """
        try:
            # Get jobs
            filters = {}
            if account_id:
                filters["account_id"] = str(account_id).strip()

            jobs = self.repository.get_all(filters=filters)

            # Calculate stats
            total = len(jobs)
            completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
            failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
            pending = sum(
                1 for j in jobs if j.status in [JobStatus.PENDING, JobStatus.SCHEDULED]
            )
            running = sum(1 for j in jobs if j.status == JobStatus.RUNNING)

            # Count today's posts (using UTC for consistent date comparison)
            today = datetime.now(timezone.utc).date()
            today_posts = sum(
                1
                for j in jobs
                if (
                    j.status == JobStatus.COMPLETED
                    and j.completed_at
                    and hasattr(j.completed_at, "date")
                    and normalize_to_utc(j.completed_at).date() == today
                )
            )

            # Calculate success rate
            success_rate = (completed / total * 100) if total > 0 else 0.0

            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "running": running,
                "today_posts": today_posts,
                "success_rate": success_rate,
            }

        except Exception as e:
            self._handle_error("GET_STATS", e, {"account_id": account_id})
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "running": 0,
                "today_posts": 0,
                "success_rate": 0.0,
            }

    def _validate_create_job_inputs(
        self,
        account_id: str,
        content: str,
        scheduled_time: str,
        priority: str,
        platform: str,
    ) -> None:
        """Validate create job inputs."""
        if not account_id or not isinstance(account_id, str):
            raise ValidationError(
                message="account_id must be a non-empty string",
                details={"field": "account_id", "value": account_id},
            )

        if not content or not isinstance(content, str):
            raise ValidationError(
                message="content must be a non-empty string",
                details={
                    "field": "content",
                    "value": content[:50] if content else None,
                },
            )

        if not scheduled_time or not isinstance(scheduled_time, str):
            raise ValidationError(
                message="scheduled_time must be a non-empty string",
                details={"field": "scheduled_time", "value": scheduled_time},
            )

    def _check_safety_guard(self, account_id: str, content: str) -> None:
        """Check safety guard (optional)."""
        try:
            from backend.api.adapters.safety_adapter import SafetyAPI

            safety_api = SafetyAPI()
            allowed, error_msg, risk_level = safety_api.check_can_post(
                account_id, content
            )
            if not allowed:
                raise ValidationError(
                    message=f"Safety check failed: {error_msg} (Risk level: {risk_level})",
                    details={"account_id": account_id, "risk_level": risk_level},
                )
        except ImportError:
            # Safety guard not available, skip check
            pass
        except ValidationError:
            raise
        except Exception as e:
            # Log but don't fail if safety check has issues
            self.logger.log_step(
                step="CREATE_JOB_SAFETY_CHECK",
                result="WARNING",
                error=f"Safety guard check failed: {str(e)}",
                account_id=account_id,
            )

    def _sync_with_active_scheduler(self, job_id: str) -> None:
        """Sync job with active scheduler if needed."""
        try:
            from ui.utils import get_active_scheduler

            active_scheduler = get_active_scheduler()

            if active_scheduler and active_scheduler != self.repository.scheduler:
                # Need to sync job to active scheduler
                # This is complex logic from JobsAPI - simplified here
                running_jobs = [
                    j
                    for j in active_scheduler.jobs.values()
                    if j.status == JobStatus.RUNNING
                ]

                if not running_jobs:
                    active_scheduler._load_jobs()
                else:
                    # Merge jobs without affecting running jobs
                    new_jobs = active_scheduler.storage.load_jobs()
                    for new_job_id, new_job in new_jobs.items():
                        existing_job = active_scheduler.jobs.get(new_job_id)
                        if not (
                            existing_job and existing_job.status == JobStatus.RUNNING
                        ):
                            active_scheduler.jobs[new_job_id] = new_job
        except Exception:
            # Sync is optional, don't fail if it doesn't work
            pass
