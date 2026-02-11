"""
Scheduler service.

Business logic layer for scheduler operations.
CRITICAL: Only this service holds scheduler instance (singleton pattern).

This is the SINGLE SOURCE OF TRUTH for scheduler instance.
No other code (routes, controllers, legacy APIs) should maintain separate scheduler references.
"""

# Standard library
import asyncio
from typing import Optional, List, Dict

# Local
from services.logger import StructuredLogger
from services.scheduler import Scheduler
from backend.app.shared.base_service import BaseService
from backend.app.core.exceptions import InternalError


class SchedulerService(BaseService):
    """
    Service for scheduler business logic.

    CRITICAL RULE: Only this service holds scheduler instance reference.
    This prevents split-brain state and ensures single source of truth.

    Handles:
    - Scheduler lifecycle (start/stop)
    - Status queries
    - Active jobs retrieval
    """

    # Class-level singleton instance
    _instance = None
    _scheduler_instance = None

    def __new__(cls):
        """Singleton pattern - ensure only one SchedulerService instance."""
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize scheduler service.

        CRITICAL: Only creates scheduler instance if it doesn't exist.
        Reuses existing scheduler instance to maintain state consistency.
        """
        if not hasattr(self, "_initialized"):
            super().__init__("scheduler_service")

            # Get or create scheduler instance (singleton)
            if SchedulerService._scheduler_instance is None:
                try:
                    # Try to get active scheduler first (if one exists)
                    from ui.utils import get_active_scheduler

                    active_scheduler = get_active_scheduler()
                    if active_scheduler:
                        SchedulerService._scheduler_instance = active_scheduler
                        self.logger.log_step(
                            step="INIT_SCHEDULER_SERVICE",
                            result="SUCCESS",
                            note="Reusing existing scheduler instance",
                            scheduler_id=id(active_scheduler),
                        )
                    else:
                        # Create new scheduler instance
                        SchedulerService._scheduler_instance = Scheduler()
                        self.logger.log_step(
                            step="INIT_SCHEDULER_SERVICE",
                            result="SUCCESS",
                            note="Created new scheduler instance",
                            scheduler_id=id(SchedulerService._scheduler_instance),
                        )
                except Exception as e:
                    # Fallback: create new scheduler
                    SchedulerService._scheduler_instance = Scheduler()
                    self.logger.log_step(
                        step="INIT_SCHEDULER_SERVICE",
                        result="WARNING",
                        error=f"Could not get active scheduler, created new: {str(e)}",
                        error_type=type(e).__name__,
                        scheduler_id=id(SchedulerService._scheduler_instance),
                    )

            self._initialized = True

    @property
    def scheduler(self) -> Scheduler:
        """
        Get scheduler instance.

        Returns:
            Scheduler instance (singleton)
        """
        return SchedulerService._scheduler_instance

    def start(self, account_id: Optional[str] = None) -> Dict:
        """
        Start scheduler.

        Args:
            account_id: Optional account ID filter

        Returns:
            Dictionary with status
        """
        try:
            scheduler = self.scheduler

            if scheduler.running:
                return {"status": "running", "message": "Scheduler is already running"}

            # Start scheduler
            # Create post_callback_factory and pass to scheduler.start()
            if hasattr(scheduler, "start"):
                # Create post_callback_factory
                from backend.app.modules.scheduler.utils.callback_factory import (
                    create_post_callback_factory,
                )

                post_callback_factory = create_post_callback_factory()
                scheduler.start(post_callback_factory)

            self.logger.log_step(
                step="START_SCHEDULER",
                result="SUCCESS",
                account_id=account_id,
                scheduler_id=id(scheduler),
            )

            return {"status": "started", "message": "Scheduler started successfully"}
        except Exception as e:
            self.logger.log_step(
                step="START_SCHEDULER",
                result="ERROR",
                error=f"Failed to start scheduler: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__,
            )
            raise InternalError(message=f"Failed to start scheduler: {str(e)}")

    async def stop(self) -> Dict:
        """
        Stop scheduler.

        Returns:
            Dictionary with status
        """
        try:
            scheduler = self.scheduler

            if not scheduler.running:
                return {"status": "stopped", "message": "Scheduler is already stopped"}

            # Stop scheduler
            if hasattr(scheduler, "stop"):
                try:
                    await scheduler.stop()
                except asyncio.CancelledError:
                    # CancelledError is expected when stopping scheduler - task is cancelled
                    # This is normal behavior, not an error
                    pass

            self.logger.log_step(
                step="STOP_SCHEDULER", result="SUCCESS", scheduler_id=id(scheduler)
            )

            return {"status": "stopped", "message": "Scheduler stopped successfully"}
        except Exception as e:
            self.logger.log_step(
                step="STOP_SCHEDULER",
                result="ERROR",
                error=f"Failed to stop scheduler: {str(e)}",
                error_type=type(e).__name__,
            )
            raise InternalError(message=f"Failed to stop scheduler: {str(e)}")

    def get_status(self) -> Dict:
        """
        Get scheduler status.

        Returns:
            Dictionary with running status and active_jobs_count
        """
        try:
            scheduler = self.scheduler

            # Get active jobs count
            active_jobs_count = 0
            if hasattr(scheduler, "get_active_jobs"):
                active_jobs = scheduler.get_active_jobs()
                active_jobs_count = len(active_jobs) if active_jobs else 0
            elif hasattr(scheduler, "jobs"):
                # Fallback: count jobs with active statuses (PENDING, SCHEDULED, RUNNING)
                from services.scheduler.models import JobStatus

                active_statuses = [
                    JobStatus.PENDING,
                    JobStatus.SCHEDULED,
                    JobStatus.RUNNING,
                ]
                all_jobs = scheduler.jobs if scheduler.jobs else {}
                for job in all_jobs.values():
                    if hasattr(job, "status") and job.status in active_statuses:
                        active_jobs_count += 1

            status_data = {
                "running": (
                    scheduler.running if hasattr(scheduler, "running") else False
                ),
                "active_jobs_count": active_jobs_count,
            }

            return status_data
        except Exception as e:
            self.logger.log_step(
                step="GET_SCHEDULER_STATUS",
                result="ERROR",
                error=f"Failed to get scheduler status: {str(e)}",
                error_type=type(e).__name__,
            )
            raise InternalError(
                message=f"Failed to retrieve scheduler status: {str(e)}"
            )

    def get_active_jobs(self) -> List[Dict]:
        """
        Get active jobs from scheduler.

        Active jobs = jobs with status PENDING, SCHEDULED, or RUNNING.

        IMPORTANT: Reloads jobs from storage before returning to ensure
        newly created jobs (e.g., from Excel upload) are included.

        Returns:
            List of active job dictionaries
        """
        try:
            scheduler = self.scheduler

            # QUAN TRỌNG: Reload jobs từ storage trước khi lấy active jobs
            # Điều này đảm bảo jobs mới được tạo (từ Excel upload) được nhận
            # Use force=False để tránh race condition nếu vừa save (< 2 giây)
            if hasattr(scheduler, "reload_jobs"):
                try:
                    scheduler.reload_jobs(force=False)
                except Exception as reload_error:
                    # Log nhưng không fail - vẫn có thể lấy jobs từ memory
                    self.logger.log_step(
                        step="GET_ACTIVE_JOBS_RELOAD",
                        result="WARNING",
                        error=f"Failed to reload jobs before getting active jobs: {str(reload_error)}",
                        error_type=type(reload_error).__name__,
                    )

            # Check if scheduler has get_active_jobs method
            if hasattr(scheduler, "get_active_jobs"):
                active_jobs = scheduler.get_active_jobs()
            else:
                # Fallback: Get jobs with active statuses (PENDING, SCHEDULED, RUNNING)
                from services.scheduler.models import JobStatus

                active_statuses = [
                    JobStatus.PENDING,
                    JobStatus.SCHEDULED,
                    JobStatus.RUNNING,
                ]
                all_jobs = getattr(scheduler, "jobs", {})
                active_jobs = []
                for job in all_jobs.values():
                    if hasattr(job, "status") and job.status in active_statuses:
                        active_jobs.append(job)

            # Convert to list of dicts if needed
            if active_jobs:
                # Import serialize_job for consistent datetime formatting (VN timezone)
                from backend.api.adapters.job_serializer import serialize_job

                # If jobs are ScheduledJob objects, convert to dicts using serialize_job
                result = []
                for job in active_jobs:
                    try:
                        # Use serialize_job for proper VN timezone formatting
                        job_dict = serialize_job(job)
                        result.append(job_dict)
                    except Exception as e:
                        # Fallback: try basic serialization
                        try:
                            if hasattr(job, "to_dict"):
                                job_dict = job.to_dict()
                                result.append(job_dict)
                            elif hasattr(job, "__dict__"):
                                result.append(job.__dict__)
                            elif isinstance(job, dict):
                                result.append(job)
                            else:
                                result.append(
                                    {
                                        "job_id": (
                                            str(job.job_id)
                                            if hasattr(job, "job_id")
                                            else None
                                        ),
                                        "status": (
                                            job.status.value
                                            if hasattr(job, "status")
                                            and hasattr(job.status, "value")
                                            else (
                                                str(job.status)
                                                if hasattr(job, "status")
                                                else "unknown"
                                            )
                                        ),
                                    }
                                )
                        except Exception as fallback_err:
                            # Skip jobs that fail to serialize
                            self.logger.log_step(
                                step="GET_ACTIVE_JOBS",
                                result="WARNING",
                                error=f"Failed to serialize job: {str(e)}, fallback error: {str(fallback_err)}",
                                error_type=type(e).__name__,
                            )
                            continue

                return result
            else:
                return []
        except Exception as e:
            self.logger.log_step(
                step="GET_ACTIVE_JOBS",
                result="ERROR",
                error=f"Failed to get active jobs: {str(e)}",
                error_type=type(e).__name__,
            )
            raise InternalError(message=f"Failed to retrieve active jobs: {str(e)}")
