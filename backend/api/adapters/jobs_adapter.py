"""
API wrapper cho job operations.
Tách biệt UI logic với business logic.

⚠️ DEPRECATED: This class is deprecated in favor of the new module-based architecture.
Use `backend.app.modules.jobs.services.JobsService` instead.

This class is kept for backward compatibility and will be removed in a future version.
"""

# Standard library
import warnings
from typing import List, Dict, Optional
from datetime import datetime

# Third-party
import pymysql

# Local
from services.scheduler import Scheduler, JobPriority, JobStatus
from services.scheduler.models import Platform
from services.exceptions import JobNotFoundError, StorageError
from services.logger import StructuredLogger
from backend.api.adapters.job_serializer import serialize_job
from utils.sanitize import sanitize_error
from backend.api.adapters.jobs_helpers import (
    convert_jobs_to_dicts,
    resolve_target_scheduler,
    safe_reload_jobs,
)


class JobsAPI:
    """
    API wrapper cho job operations (orchestration layer giữa UI ↔ Scheduler ↔ Storage).
    
    Cung cấp interface đơn giản cho UI để tương tác với scheduler.
    
    NOTE: JobsAPI hiện tại đang làm nhiều việc (Service + Orchestrator + Adapter + Presenter).
    Có thể refactor thành các components riêng trong tương lai:
    - SchedulerResolver (active vs fallback)
    - JobSyncService (reload / merge)
    - JobSerializer (_to_dict)
    - SafetyGuard (optional)
    """
    
    def __init__(self):
        """
        Khởi tạo JobsAPI.
        
        ⚠️ DEPRECATED: Use JobsService from backend.app.modules.jobs.services instead.
        """
        # Deprecation warning
        warnings.warn(
            "JobsAPI is deprecated. Use JobsService from backend.app.modules.jobs.services instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Initialize logger
        self.logger = StructuredLogger(name="jobs_api")
        
        # QUAN TRỌNG: Dùng active scheduler nếu có, nếu không mới tạo mới
        # Để đảm bảo add_job/delete_job tương tác với scheduler đang chạy
        try:
            from ui.utils import get_active_scheduler
            active_scheduler = get_active_scheduler()
            if active_scheduler:
                self.scheduler = active_scheduler
                self.logger.log_step(
                    step="INIT_JOBS_API",
                    result="SUCCESS",
                    note="Using active scheduler instance",
                    scheduler_id=id(active_scheduler),
                    scheduler_running=active_scheduler.running
                )
            else:
                self.scheduler = Scheduler()
                self.logger.log_step(
                    step="INIT_JOBS_API",
                    result="SUCCESS",
                    note="Created new scheduler instance (no active scheduler)",
                    scheduler_id=id(self.scheduler)
                )
        except Exception as e:
            # Fallback: tạo scheduler mới nếu không thể get active scheduler
            self.logger.log_step(
                step="INIT_JOBS_API",
                result="WARNING",
                error=f"Could not get active scheduler: {str(e)}, creating new instance",
                error_type=type(e).__name__
            )
            self.scheduler = Scheduler()
            self.logger.log_step(
                step="INIT_JOBS_API",
                result="SUCCESS",
                note="Created new scheduler instance (fallback)",
                scheduler_id=id(self.scheduler)
            )
    
    def get_all_jobs(
        self,
        account_id: Optional[str] = None,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        scheduled_from: Optional[str] = None,
        scheduled_to: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        reload: bool = False
    ):
        """
        Get jobs with optional filters and pagination.
        
        ⚠️ DEPRECATED: Use JobsService.get_all_jobs() instead.
        This method delegates to JobsService for consistency.
        
        Args:
            account_id: Account ID để filter (None = all accounts)
            status: Status to filter by
            platform: Platform to filter by
            scheduled_from: Filter jobs scheduled after this date (YYYY-MM-DD)
            scheduled_to: Filter jobs scheduled before this date (YYYY-MM-DD)
            page: Page number (1-based) for pagination
            limit: Items per page for pagination
            reload: Nếu True, reload jobs từ storage trước khi list
        
        Returns:
            List of job dicts hoặc dict with 'data' and '_pagination' if pagination requested
        """
        try:
            # Delegate to JobsService for consistency
            from backend.app.modules.jobs.services.jobs_service import JobsService
            jobs_service = JobsService()
            
            result = jobs_service.get_all_jobs(
                account_id=account_id,
                status=status,
                platform=platform,
                scheduled_from=scheduled_from,
                scheduled_to=scheduled_to,
                page=page,
                limit=limit,
                reload=reload
            )
            
            return result
        except Exception as e:
            # Log error và return empty list or empty paginated response
            self.logger.log_step(
                step="GET_ALL_JOBS",
                result="ERROR",
                error=f"Failed to get jobs: {str(e)}",
                error_type=type(e).__name__
            )
            import traceback
            traceback.print_exc()
            if page and limit:
                return {"data": [], "_pagination": None}
            return []
    
    def add_job(
        self,
        account_id: Optional[str],
        content: str,
        scheduled_time: str,
        priority: str = "NORMAL",
        platform: str = "THREADS",
        link_aff: Optional[str] = None
    ) -> str:
        """
        Add new job.
        
        Args:
            account_id: Account ID
            content: Content string
            scheduled_time: ISO format datetime string
            priority: Priority string (NORMAL, HIGH, URGENT)
            platform: Platform string (THREADS, FACEBOOK)
            link_aff: Link affiliate (optional) - sẽ được đăng trong comment
        
        Returns:
            Job ID
        
        Raises:
            ValueError: If validation fails
            KeyError: If priority or platform is invalid
        """
        # Validate inputs
        self._validate_add_job_inputs(account_id, content, scheduled_time)
        
        # Parse and convert inputs
        dt = self._parse_scheduled_time(scheduled_time)
        priority_enum = self._convert_priority(priority)
        platform_enum = self._convert_platform(platform)
        
        # Safety guard check
        self._check_safety_guard(account_id, content)
        
        # Resolve target scheduler
        target_scheduler, active_scheduler = self._resolve_target_scheduler()
        
        # Add job to scheduler
        job_id = self._add_job_to_scheduler(
            target_scheduler=target_scheduler,
            account_id=account_id,
            content=content,
            scheduled_time=dt,
            priority=priority_enum,
            platform=platform_enum,
            link_aff=link_aff
        )
        
        # Sync with active scheduler if needed
        self._sync_job_with_active_scheduler(
            active_scheduler=active_scheduler,
            target_scheduler=target_scheduler,
            job_id=job_id
        )
        
        return job_id
    
    def _validate_add_job_inputs(
        self,
        account_id: Optional[str],
        content: str,
        scheduled_time: str
    ) -> None:
        """
        Validate add_job inputs.
        
        Args:
            account_id: Account ID (optional, can be None or empty)
            content: Content string
            scheduled_time: Scheduled time string
        
        Raises:
            ValueError: If validation fails
        """
        # account_id is optional - allow None or empty string
        if account_id is not None and account_id != "":
            if not isinstance(account_id, str):
                raise ValueError("account_id must be a string")
        
        if not content or not isinstance(content, str):
            raise ValueError("content must be a non-empty string")
        if not scheduled_time or not isinstance(scheduled_time, str):
            raise ValueError("scheduled_time must be a non-empty string")
    
    def _parse_scheduled_time(self, scheduled_time: str) -> datetime:
        """
        Parse scheduled_time from ISO format string.
        
        Args:
            scheduled_time: ISO format datetime string
        
        Returns:
            Parsed datetime object
        
        Raises:
            ValueError: If format is invalid
        """
        try:
            return datetime.fromisoformat(scheduled_time)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid scheduled_time format: {scheduled_time}. Expected ISO format."
            ) from e
    
    def _convert_priority(self, priority: str) -> JobPriority:
        """
        Convert priority string to JobPriority enum.
        
        Args:
            priority: Priority string (NORMAL, HIGH, URGENT, LOW)
        
        Returns:
            JobPriority enum
        
        Raises:
            ValueError: If priority is invalid
        """
        try:
            return JobPriority[priority.upper()]
        except KeyError:
            valid_priorities = [p.name for p in JobPriority]
            raise ValueError(
                f"Invalid priority: {priority}. Valid priorities: {', '.join(valid_priorities)}"
            ) from None
    
    def _convert_platform(self, platform: str) -> Platform:
        """
        Convert platform string to Platform enum.
        
        Args:
            platform: Platform string (THREADS, FACEBOOK)
        
        Returns:
            Platform enum
        
        Raises:
            ValueError: If platform is invalid
        """
        try:
            return Platform[platform.upper()]
        except KeyError:
            valid_platforms = [p.name for p in Platform]
            raise ValueError(
                f"Invalid platform: {platform}. Valid platforms: {', '.join(valid_platforms)}"
            ) from None
    
    def _check_safety_guard(self, account_id: Optional[str], content: str) -> None:
        """
        Check safety guard if available.
        
        Args:
            account_id: Account ID (optional, can be None)
            content: Content string
        
        Raises:
            ValueError: If safety check fails
        """
        # Skip safety check if account_id is None
        if account_id is None or account_id == "":
            return
        
        try:
            from backend.api.adapters.safety_adapter import SafetyAPI
            safety_api = SafetyAPI()
            allowed, error_msg, risk_level = safety_api.check_can_post(account_id, content)
            if not allowed:
                raise ValueError(
                    f"Safety check failed: {error_msg} (Risk level: {risk_level})"
                )
        except ImportError:
            # Safety guard not available, skip check
            pass
        except ValueError:
            # Re-raise ValueError from safety check
            raise
        except Exception as e:
            # Log but don't fail if safety check has issues
            self.logger.log_step(
                step="ADD_JOB_SAFETY_CHECK",
                result="WARNING",
                error=f"Safety guard check failed: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
    
    def _resolve_target_scheduler(self):
        """
        Resolve target scheduler (active scheduler or fallback).
        
        Returns:
            Tuple of (target_scheduler, active_scheduler)
        """
        from ui.utils import get_active_scheduler
        active_scheduler = get_active_scheduler()
        target_scheduler = active_scheduler if active_scheduler else self.scheduler
        return target_scheduler, active_scheduler
    
    def _add_job_to_scheduler(
        self,
        target_scheduler,
        account_id: Optional[str],
        content: str,
        scheduled_time: datetime,
        priority: JobPriority,
        platform: Platform,
        link_aff: Optional[str]
    ) -> str:
        """
        Add job to scheduler with link_aff handling.
        
        Args:
            target_scheduler: Scheduler instance
            account_id: Account ID (optional, can be None)
            content: Content string
            scheduled_time: Scheduled datetime
            priority: JobPriority enum
            platform: Platform enum
            link_aff: Optional affiliate link
        
        Returns:
            Job ID
        
        Raises:
            RuntimeError: If adding job fails
        """
        try:
            # Check if scheduler supports link_aff (backward compatibility)
            import inspect
            sig = inspect.signature(target_scheduler.add_job)
            if 'link_aff' in sig.parameters:
                job_id = target_scheduler.add_job(
                    account_id=account_id,
                    content=content,
                    scheduled_time=scheduled_time,
                    priority=priority,
                    platform=platform,
                    link_aff=link_aff
                )
            else:
                # Old scheduler doesn't support link_aff, skip it
                self.logger.log_step(
                    step="ADD_JOB",
                    result="WARNING",
                    note="Scheduler instance does not support link_aff parameter, skipping link_aff",
                    account_id=account_id
                )
                job_id = target_scheduler.add_job(
                    account_id=account_id,
                    content=content,
                    scheduled_time=scheduled_time,
                    priority=priority,
                    platform=platform
                )
            
            self.logger.log_step(
                step="ADD_JOB",
                result="SUCCESS",
                job_id=job_id,
                account_id=account_id,
                target_scheduler_id=id(target_scheduler)
            )
            return job_id
        except Exception as e:
            self.logger.log_step(
                step="ADD_JOB",
                result="ERROR",
                error=f"Failed to add job to scheduler: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Failed to add job to scheduler: {str(e)}") from e
    
    def _sync_job_with_active_scheduler(
        self,
        active_scheduler,
        target_scheduler,
        job_id: str
    ) -> None:
        """
        Sync job with active scheduler if needed.
        
        Args:
            active_scheduler: Active scheduler instance (may be None)
            target_scheduler: Target scheduler where job was added
            job_id: Job ID that was added
        """
        if not active_scheduler or target_scheduler == active_scheduler:
            # Already added to active scheduler, no sync needed
            if active_scheduler and active_scheduler.running:
                active_scheduler.logger.log_step(
                    step="ADD_JOB",
                    result="SUCCESS",
                    note="Job added directly to active scheduler (already in memory)",
                    job_id=job_id
                )
            return
        
        # Need to sync: job was added to different scheduler
        try:
            running_jobs = [
                j for j in active_scheduler.jobs.values()
                if j.status == JobStatus.RUNNING
            ]
            
            if not running_jobs:
                # No running jobs, safe to reload all
                active_scheduler._load_jobs()
                active_scheduler.logger.log_step(
                    step="ADD_JOB_RELOAD",
                    result="SUCCESS",
                    note="Reloaded all jobs in active scheduler (no running jobs)",
                    job_id=job_id
                )
            else:
                # Has running jobs, merge carefully
                self._merge_jobs_into_active_scheduler(active_scheduler, job_id, running_jobs)
        except Exception as e:
            # Log but don't fail add operation
            if active_scheduler:
                active_scheduler.logger.log_step(
                    step="ADD_JOB_RELOAD",
                    result="ERROR",
                    error=f"Could not update jobs in active scheduler: {str(e)}",
                    error_type=type(e).__name__,
                    job_id=job_id
                )
    
    def _merge_jobs_into_active_scheduler(
        self,
        active_scheduler,
        job_id: str,
        running_jobs: List
    ) -> None:
        """
        Merge jobs into active scheduler while preserving running jobs.
        
        Args:
            active_scheduler: Active scheduler instance
            job_id: Job ID that was added
            running_jobs: List of currently running jobs
        """
        try:
            # Load all jobs from storage
            new_jobs = active_scheduler.storage.load_jobs()
            
            # Merge: Keep running jobs, update/add others
            added_count = 0
            updated_count = 0
            for new_job_id, new_job in new_jobs.items():
                existing_job = active_scheduler.jobs.get(new_job_id)
                if existing_job and existing_job.status == JobStatus.RUNNING:
                    # Keep running job unchanged
                    continue
                else:
                    # Update or add job
                    if existing_job:
                        updated_count += 1
                    else:
                        added_count += 1
                    active_scheduler.jobs[new_job_id] = new_job
            
            active_scheduler.logger.log_step(
                step="ADD_JOB_MERGE",
                result="SUCCESS",
                note=f"Merged jobs in active scheduler: {added_count} added, {updated_count} updated",
                job_id=job_id,
                added_count=added_count,
                updated_count=updated_count,
                running_jobs_count=len(running_jobs)
            )
        except Exception as load_error:
            # If can't load, scheduler will load next time
            active_scheduler.logger.log_step(
                step="ADD_JOB_MERGE",
                result="ERROR",
                error=f"Could not merge jobs in active scheduler: {str(load_error)}",
                error_type=type(load_error).__name__,
                job_id=job_id
            )
    
    def update_job(
        self,
        job_id: str,
        content: Optional[str] = None,
        account_id: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        priority: Optional[str] = None,
        platform: Optional[str] = None,
        max_retries: Optional[int] = None,
        link_aff: Optional[str] = None
    ) -> bool:
        """
        Update job.
        
        Args:
            job_id: Job ID to update
            content: Updated content (optional)
            account_id: Updated account ID (optional)
            scheduled_time: Updated scheduled time (optional)
            priority: Updated priority (optional, "low", "normal", "high", "urgent")
            platform: Updated platform (optional, "threads", "facebook")
            max_retries: Updated max retries (optional)
            link_aff: Updated affiliate link (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate job_id
            if not job_id or not isinstance(job_id, str):
                self.logger.log_step(
                    step="UPDATE_JOB",
                    result="ERROR",
                    error=f"Invalid job_id: {job_id}",
                    job_id=job_id
                )
                return False
            
            job_id = job_id.strip()
            
            # QUAN TRỌNG: Luôn dùng active scheduler nếu có để đảm bảo consistency
            # Use helper function to safely get active scheduler
            from backend.api.adapters.jobs_helpers import resolve_target_scheduler
            target_scheduler = resolve_target_scheduler(self.scheduler)
            
            # Get job
            job = target_scheduler.jobs.get(job_id)
            if not job:
                self.logger.log_step(
                    step="UPDATE_JOB",
                    result="ERROR",
                    error=f"Job not found: {job_id}",
                    job_id=job_id
                )
                return False
            
            # Don't allow updating completed or running jobs
            from services.scheduler.models import JobStatus
            if job.status == JobStatus.COMPLETED or job.status == JobStatus.RUNNING:
                self.logger.log_step(
                    step="UPDATE_JOB",
                    result="ERROR",
                    error=f"Cannot update job with status: {job.status.value}",
                    job_id=job_id,
                    status=job.status.value
                )
                return False
            
            # Update fields
            if content is not None:
                job.content = content
            if account_id is not None:
                job.account_id = account_id
            if scheduled_time is not None:
                if isinstance(scheduled_time, str):
                    from datetime import datetime
                    job.scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                else:
                    job.scheduled_time = scheduled_time
            if priority is not None:
                from services.scheduler.models import JobPriority
                priority_map = {
                    "low": JobPriority.LOW,
                    "normal": JobPriority.NORMAL,
                    "high": JobPriority.HIGH,
                    "urgent": JobPriority.URGENT
                }
                job.priority = priority_map.get(priority.lower(), JobPriority.NORMAL)
            if platform is not None:
                from services.scheduler.models import Platform
                platform_map = {
                    "threads": Platform.THREADS,
                    "facebook": Platform.FACEBOOK
                }
                job.platform = platform_map.get(platform.lower(), Platform.THREADS)
            if max_retries is not None:
                job.max_retries = max_retries
            if link_aff is not None:
                job.link_aff = link_aff
            
            # Save jobs
            target_scheduler._save_jobs()
            
            self.logger.log_step(
                step="UPDATE_JOB",
                result="SUCCESS",
                job_id=job_id,
                target_scheduler_id=id(target_scheduler)
            )
            
            return True
            
        except Exception as e:
            self.logger.log_step(
                step="UPDATE_JOB",
                result="ERROR",
                error=f"Failed to update job: {str(e)}",
                error_type=type(e).__name__,
                job_id=job_id
            )
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete job.
        
        Args:
            job_id: Job ID to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate job_id
            if not job_id or not isinstance(job_id, str):
                self.logger.log_step(
                    step="DELETE_JOB",
                    result="ERROR",
                    error=f"Invalid job_id: {job_id}",
                    job_id=job_id
                )
                return False
            
            job_id = job_id.strip()
            
            # QUAN TRỌNG: Luôn dùng active scheduler nếu có để đảm bảo consistency
            from ui.utils import get_active_scheduler
            active_scheduler = get_active_scheduler()
            target_scheduler = active_scheduler if active_scheduler else self.scheduler
            
            # Let remove_job handle validation and deletion
            # It will raise JobNotFoundError if job doesn't exist
            # It will automatically save via save_callback
            jobs_before = len(target_scheduler.jobs)
            target_scheduler.remove_job(job_id)
            jobs_after = len(target_scheduler.jobs)
            
            self.logger.log_step(
                step="DELETE_JOB",
                result="SUCCESS",
                job_id=job_id,
                jobs_before=jobs_before,
                jobs_after=jobs_after,
                target_scheduler_id=id(target_scheduler)
            )
            
            return True
            
        except JobNotFoundError as e:
            # Job không tồn tại - không phải error nghiêm trọng
            self.logger.log_step(
                step="DELETE_JOB",
                result="FAILED",
                error=f"Job not found: {str(e)}",
                job_id=job_id
            )
            return False
            
        except StorageError as e:
            # Storage error - nghiêm trọng, log và return False
            self.logger.log_step(
                step="DELETE_JOB",
                result="ERROR",
                error=f"Storage error: {str(e)}",
                error_type=type(e).__name__,
                job_id=job_id
            )
            import traceback
            traceback.print_exc()
            return False
            
        except Exception as e:
            # Unexpected error
            self.logger.log_step(
                step="DELETE_JOB",
                result="ERROR",
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__,
                job_id=job_id
            )
            import traceback
            traceback.print_exc()
            return False
    
    def get_stats(self, account_id: Optional[str] = None) -> Dict:
        """
        Get basic stats.
        
        Args:
            account_id: Account ID để filter (None = all accounts)
        
        Returns:
            Dict với stats
        """
        try:
            # Resolve target scheduler
            target_scheduler, _ = self._resolve_target_scheduler()
            
            # Normalize account_id
            if account_id:
                account_id = str(account_id).strip()
            
            # Get jobs
            jobs = target_scheduler.list_jobs(account_id=account_id)
            total = len(jobs)
            
            # Count by status
            status_counts = self._count_jobs_by_status(jobs)
            
            # Calculate today's posts
            today_posts = self._calculate_today_posts(jobs)
            
            # Calculate success rate
            success_rate = self._calculate_success_rate(
                status_counts["completed"],
                total
            )
            
            return {
                "total": total,
                "completed": status_counts["completed"],
                "failed": status_counts["failed"],
                "pending": status_counts["pending"],
                "running": status_counts["running"],
                "today_posts": today_posts,
                "success_rate": success_rate
            }
        except Exception as e:
            # Return default stats on error
            self.logger.log_step(
                step="GET_STATS",
                result="ERROR",
                error=f"Failed to get stats: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            import traceback
            traceback.print_exc()
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "running": 0,
                "today_posts": 0,
                "success_rate": 0.0
            }
    
    def _count_jobs_by_status(self, jobs: List) -> Dict[str, int]:
        """
        Count jobs by status.
        
        Args:
            jobs: List of job objects
        
        Returns:
            Dict with counts: completed, failed, pending, running
        """
        completed = 0
        failed = 0
        pending = 0
        running = 0
        
        for j in jobs:
            try:
                if j.status == JobStatus.COMPLETED:
                    completed += 1
                elif j.status == JobStatus.FAILED:
                    failed += 1
                elif j.status in [JobStatus.PENDING, JobStatus.SCHEDULED]:
                    pending += 1
                elif j.status == JobStatus.RUNNING:
                    running += 1
            except (AttributeError, TypeError):
                # Skip jobs with invalid status
                continue
        
        return {
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running
        }
    
    def _calculate_today_posts(self, jobs: List) -> int:
        """
        Calculate today's completed posts.
        
        Args:
            jobs: List of job objects
        
        Returns:
            Number of posts completed today
        """
        today = datetime.now().date()
        today_posts = 0
        
        for j in jobs:
            try:
                if (j.status == JobStatus.COMPLETED
                    and j.completed_at
                    and hasattr(j.completed_at, 'date')):
                    if j.completed_at.date() == today:
                        today_posts += 1
            except (AttributeError, TypeError):
                # Skip jobs with invalid completed_at
                continue
        
        return today_posts
    
    def _calculate_success_rate(self, completed: int, total: int) -> float:
        """
        Calculate success rate.
        
        Args:
            completed: Number of completed jobs
            total: Total number of jobs
        
        Returns:
            Success rate as percentage (0.0-100.0)
        """
        return (completed / total * 100) if total > 0 else 0.0
    
    def _to_dict(self, job) -> Dict:
        """
        Convert job to dict (delegates to job_serializer.serialize_job).

        NOTE: Serialization logic được tách sang `backend/api/adapters/job_serializer.py`
        để `JobsAPI` bớt gánh phần presentation logic.
        """
        try:
            return serialize_job(job)
        except Exception as e:
            # Log và fallback về dict tối thiểu nếu serialize thất bại
            job_id_attr = getattr(job, "job_id", "unknown")
            self.logger.log_step(
                step="TO_DICT",
                result="ERROR",
                error=f"Failed to convert job to dict: {str(e)}",
                error_type=type(e).__name__,
                job_id=job_id_attr,
            )
            import traceback
            traceback.print_exc()
            # Sanitize error message
            sanitized_error = sanitize_error(e)
            return {
                "job_id": getattr(job, "job_id", "N/A"),
                "account_id": getattr(job, "account_id", "N/A"),
                "content": "[REDACTED]",
                "content_full": "[REDACTED]",
                "scheduled_time": None,
                "status": "unknown",
                "status_message": f"Error: {sanitized_error}",
                "thread_id": None,
                "error": sanitized_error,
                "priority": None,
                "retry_count": 0,
                "created_at": None,
                "started_at": None,
                "completed_at": None,
                "running_duration": None,
            }
    
    def get_jobs_with_metrics(
        self,
        account_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get completed jobs with their latest metrics (views, likes, replies, shares).
        
        Queries the `jobs_with_metrics` VIEW from MySQL which joins jobs with thread_metrics.
        
        Args:
            account_id: Account ID để filter (None = all accounts)
            limit: Maximum number of jobs to return (None = no limit)
        
        Returns:
            List of job dicts with metrics fields:
            - latest_views: Latest view count
            - latest_likes: Latest like count
            - latest_replies: Latest reply count
            - latest_shares: Latest share count
            - last_metrics_fetch: Timestamp of last metrics fetch
            - hours_since_post: Hours since job was completed
        """
        try:
            # Get MySQL connection pool
            from services.storage.connection_pool import get_connection_pool
            from config.storage_config_loader import get_storage_config_from_env
            
            storage_config = get_storage_config_from_env()
            
            # Get MySQL config from StorageConfig
            mysql_config = storage_config.mysql
            
            # Get connection from pool
            pool = get_connection_pool(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database
            )
            
            with pool.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    # Build query
                    query = "SELECT * FROM jobs_with_metrics WHERE 1=1"
                    params = []
                    
                    # Add account filter if provided
                    if account_id:
                        query += " AND account_id = %s"
                        params.append(str(account_id).strip())
                    
                    # Add limit if provided
                    if limit:
                        query += " ORDER BY completed_at DESC LIMIT %s"
                        params.append(int(limit))
                    else:
                        query += " ORDER BY completed_at DESC"
                    
                    # Execute query
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    self.logger.log_step(
                        step="GET_JOBS_WITH_METRICS",
                        result="SUCCESS",
                        count=len(results),
                        account_id=account_id,
                        limit=limit
                    )
                    
                    # Convert to list of dicts
                    jobs_with_metrics = []
                    for row in results:
                        # Trả về content thực tế cho UI
                        # CHỈ sanitize trong logs, KHÔNG sanitize trong API responses
                        content = row.get('content', '')
                        
                        job_dict = {
                            "job_id": row.get('job_id'),
                            "account_id": row.get('account_id'),
                            "thread_id": row.get('thread_id'),
                            "content": content,
                            "scheduled_time": row.get('scheduled_time').isoformat() if row.get('scheduled_time') else None,
                            "completed_at": row.get('completed_at').isoformat() if row.get('completed_at') else None,
                            "status": row.get('status'),
                            "platform": row.get('platform'),
                            "latest_views": row.get('latest_views'),
                            "latest_likes": row.get('latest_likes'),
                            "latest_replies": row.get('latest_replies'),
                            "latest_shares": row.get('latest_shares'),
                            "last_metrics_fetch": row.get('last_metrics_fetch').isoformat() if row.get('last_metrics_fetch') else None,
                            "hours_since_post": row.get('hours_since_post')
                        }
                        jobs_with_metrics.append(job_dict)
                    
                    return jobs_with_metrics
                    
        except ImportError as e:
            # Connection pool not available
            self.logger.log_step(
                step="GET_JOBS_WITH_METRICS",
                result="ERROR",
                error=f"Connection pool not available: {str(e)}",
                error_type=type(e).__name__
            )
            return []
        except Exception as e:
            # Log error and return empty list
            self.logger.log_step(
                step="GET_JOBS_WITH_METRICS",
                result="ERROR",
                error=f"Failed to get jobs with metrics: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            import traceback
            traceback.print_exc()
            return []
    
    def update_job_thread_id(self, job_id: str, thread_id: str) -> bool:
        """
        Update thread_id cho job.
        
        Args:
            job_id: Job ID cần update
            thread_id: Thread ID mới
        
        Returns:
            True nếu update thành công, False nếu không
        """
        try:
            if not job_id or not thread_id:
                self.logger.log_step(
                    step="UPDATE_JOB_THREAD_ID",
                    result="FAILED",
                    error="job_id and thread_id are required",
                    job_id=job_id,
                    thread_id=thread_id
                )
                return False
            
            job_id = job_id.strip()
            thread_id = thread_id.strip()
            
            # QUAN TRỌNG: Luôn dùng active scheduler nếu có để đảm bảo consistency
            from ui.utils import get_active_scheduler
            active_scheduler = get_active_scheduler()
            target_scheduler = active_scheduler if active_scheduler else self.scheduler
            
            # Check if job exists
            if job_id not in target_scheduler.jobs:
                self.logger.log_step(
                    step="UPDATE_JOB_THREAD_ID",
                    result="FAILED",
                    error="Job not found",
                    job_id=job_id
                )
                return False
            
            # Update job thread_id
            job = target_scheduler.jobs[job_id]
            old_thread_id = job.thread_id
            job.thread_id = thread_id
            job.status_message = f"Thread ID updated: {thread_id}"
            
            # Save jobs
            try:
                target_scheduler._save_jobs()
                self.logger.log_step(
                    step="UPDATE_JOB_THREAD_ID",
                    result="SUCCESS",
                    job_id=job_id,
                    old_thread_id=old_thread_id,
                    new_thread_id=thread_id
                )
                return True
            except Exception as save_error:
                # Rollback
                job.thread_id = old_thread_id
                self.logger.log_step(
                    step="UPDATE_JOB_THREAD_ID",
                    result="ERROR",
                    error=f"Failed to save: {str(save_error)}",
                    error_type=type(save_error).__name__,
                    job_id=job_id
                )
                return False
                
        except Exception as e:
            self.logger.log_step(
                step="UPDATE_JOB_THREAD_ID",
                result="ERROR",
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__,
                job_id=job_id
            )
            import traceback
            traceback.print_exc()
            return False
    
    def update_jobs_thread_ids(self, updates: Dict[str, str]) -> Dict[str, bool]:
        """
        Update thread_id cho nhiều jobs.
        
        Args:
            updates: Dict mapping job_id -> thread_id
        
        Returns:
            Dict mapping job_id -> success (True/False)
        """
        results = {}
        for job_id, thread_id in updates.items():
            results[job_id] = self.update_job_thread_id(job_id, thread_id)
        return results
