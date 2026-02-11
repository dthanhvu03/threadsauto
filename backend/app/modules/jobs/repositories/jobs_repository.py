"""
Jobs repository.

Data access layer for jobs. Interacts with scheduler storage.
"""

# Standard library
from typing import Dict, List, Optional

# Local
from services.scheduler import Scheduler
from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform
from services.exceptions import JobNotFoundError
from services.logger import StructuredLogger
from backend.app.shared.base_repository import BaseRepository


class JobsRepository(BaseRepository[ScheduledJob]):
    """
    Repository for job data access.
    
    Handles all interactions with scheduler storage.
    No business logic - only data access.
    """
    
    def __init__(self, scheduler: Optional[Scheduler] = None):
        """
        Initialize jobs repository.
        
        Args:
            scheduler: Scheduler instance. If None, creates new instance.
        """
        self.logger = StructuredLogger(name="jobs_repository")
        
        # Use provided scheduler or create new one
        if scheduler:
            self.scheduler = scheduler
        else:
            # Try to get active scheduler first
            try:
                from ui.utils import get_active_scheduler
                active_scheduler = get_active_scheduler()
                self.scheduler = active_scheduler if active_scheduler else Scheduler()
            except Exception:
                self.scheduler = Scheduler()
        
        self.logger.log_step(
            step="INIT_JOBS_REPOSITORY",
            result="SUCCESS",
            scheduler_id=id(self.scheduler)
        )
    
    def get_by_id(self, entity_id: str) -> Optional[ScheduledJob]:
        """
        Get job by ID.
        
        Args:
            entity_id: Job ID
        
        Returns:
            ScheduledJob if found, None otherwise
        """
        try:
            # Get job from scheduler
            job = self.scheduler.jobs.get(entity_id)
            if job:
                return job
            
            # If not in memory, try to load from storage
            try:
                self.scheduler._load_jobs()
                return self.scheduler.jobs.get(entity_id)
            except Exception as e:
                self.logger.log_step(
                    step="GET_JOB_BY_ID_LOAD",
                    result="WARNING",
                    error=f"Failed to load jobs from storage: {str(e)}",
                    job_id=entity_id
                )
                return None
        
        except Exception as e:
            self.logger.log_step(
                step="GET_JOB_BY_ID",
                result="ERROR",
                error=f"Error getting job: {str(e)}",
                job_id=entity_id
            )
            return None
    
    def get_all(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ScheduledJob]:
        """
        Get all jobs, optionally filtered.
        
        Args:
            filters: Optional filter criteria:
                - account_id: Filter by account ID
                - status: Filter by job status
                - platform: Filter by platform
                - scheduled_from: Filter jobs scheduled after this date (YYYY-MM-DD)
                - scheduled_to: Filter jobs scheduled before this date (YYYY-MM-DD)
            limit: Optional limit on number of results
            offset: Optional offset for pagination
        
        Returns:
            List of ScheduledJob objects
        """
        try:
            from datetime import datetime, date
            from services.utils.datetime_utils import normalize_to_utc
            
            account_id = filters.get("account_id") if filters else None
            status = filters.get("status") if filters else None
            platform = filters.get("platform") if filters else None
            scheduled_from = filters.get("scheduled_from") if filters else None
            scheduled_to = filters.get("scheduled_to") if filters else None
            
            # Get jobs from scheduler (don't pass status to list_jobs - we'll filter after)
            # We filter status ourselves to have more control
            try:
                jobs = self.scheduler.list_jobs(account_id=account_id, status=None)
            except Exception as e:
                self.logger.log_step(
                    step="GET_ALL_JOBS",
                    result="ERROR",
                    error=f"Error getting jobs from scheduler: {str(e)}",
                    account_id=account_id,
                    error_type=type(e).__name__
                )
                return []
            
            # Filter by status if provided
            if status:
                status_str = str(status).strip() if status else None
                status_enum = None
                
                if status_str:
                    try:
                        # Convert to enum: "scheduled" -> JobStatus.SCHEDULED
                        status_enum = JobStatus[status_str.upper()]
                        self.logger.log_step(
                            step="GET_ALL_JOBS",
                            result="DEBUG",
                            note=f"Filtering by status: '{status_str}' -> {status_enum} (value: {status_enum.value})",
                            account_id=account_id,
                            jobs_before_filter=len(jobs)
                        )
                    except (KeyError, AttributeError) as e:
                        self.logger.log_step(
                            step="GET_ALL_JOBS",
                            result="WARNING",
                            error=f"Invalid status filter: {status_str} (error: {str(e)})",
                            account_id=account_id
                        )
                        status_enum = None
                elif isinstance(status, JobStatus):
                    # Already an enum
                    status_enum = status
                
                if status_enum:
                    jobs_before = len(jobs)
                    
                    # Filter jobs by status with robust comparison
                    # Handle both enum and string status values
                    filtered_jobs = []
                    status_matches = 0
                    status_mismatches = 0
                    
                    for j in jobs:
                        try:
                            job_status = j.status
                            match = False
                            
                            # Handle enum comparison
                            if isinstance(job_status, JobStatus):
                                match = (job_status == status_enum)
                            # Handle string comparison (if status was loaded as string from JSON)
                            elif isinstance(job_status, str):
                                match = (job_status.lower() == status_enum.value.lower())
                            # Handle case where status might be stored as enum value
                            elif hasattr(job_status, 'value'):
                                match = (job_status.value.lower() == status_enum.value.lower())
                            # Fallback: compare string representations
                            else:
                                match = (str(job_status).lower() == status_enum.value.lower())
                            
                            if match:
                                filtered_jobs.append(j)
                                status_matches += 1
                            else:
                                status_mismatches += 1
                                # Log first few mismatches for debugging
                                if status_mismatches <= 3:
                                    self.logger.log_step(
                                        step="GET_ALL_JOBS",
                                        result="DEBUG",
                                        note=f"Job {getattr(j, 'job_id', 'unknown')} status mismatch: {job_status} (type: {type(job_status).__name__}) != {status_enum} (value: {status_enum.value})",
                                        account_id=account_id,
                                        job_id=getattr(j, 'job_id', None)
                                    )
                        except Exception as e:
                            # Skip jobs that error during status comparison
                            self.logger.log_step(
                                step="GET_ALL_JOBS",
                                result="WARNING",
                                error=f"Error comparing status for job {getattr(j, 'job_id', 'unknown')}: {str(e)}",
                                account_id=account_id,
                                error_type=type(e).__name__
                            )
                            continue
                    
                    jobs = filtered_jobs
                    
                    self.logger.log_step(
                        step="GET_ALL_JOBS",
                        result="DEBUG",
                        note=f"Status filter applied: {jobs_before} -> {len(jobs)} jobs (filter: {status_enum.value}, matches: {status_matches}, mismatches: {status_mismatches})",
                        account_id=account_id,
                        status_filter=status_enum.value,
                        jobs_before=jobs_before,
                        jobs_after=len(jobs),
                        matches=status_matches,
                        mismatches=status_mismatches
                    )
            
            # Filter by platform if provided
            if platform:
                platform_str = str(platform).strip().upper()
                platform_enum = None
                
                try:
                    platform_enum = Platform[platform_str]
                except (KeyError, AttributeError) as e:
                    self.logger.log_step(
                        step="GET_ALL_JOBS",
                        result="WARNING",
                        error=f"Invalid platform filter: {platform} (error: {str(e)})",
                        account_id=account_id
                    )
                    platform_enum = None
                
                if platform_enum:
                    filtered_platform_jobs = []
                    for j in jobs:
                        try:
                            job_platform = j.platform
                            match = False
                            
                            # Handle both enum and string comparison
                            if isinstance(job_platform, Platform):
                                match = (job_platform == platform_enum)
                            elif isinstance(job_platform, str):
                                match = (job_platform.upper() == platform_str)
                            elif hasattr(job_platform, 'value'):
                                match = (job_platform.value.upper() == platform_str)
                            else:
                                match = (str(job_platform).upper() == platform_str)
                            
                            if match:
                                filtered_platform_jobs.append(j)
                        except Exception as e:
                            # Skip jobs that error during platform comparison
                            self.logger.log_step(
                                step="GET_ALL_JOBS",
                                result="WARNING",
                                error=f"Error comparing platform for job {getattr(j, 'job_id', 'unknown')}: {str(e)}",
                                account_id=account_id
                            )
                            continue
                    
                    jobs = filtered_platform_jobs
            
            # Filter by scheduled_time range if provided
            if scheduled_from or scheduled_to:
                filtered_jobs = []
                for job in jobs:
                    try:
                        if not hasattr(job, 'scheduled_time') or not job.scheduled_time:
                            continue
                        
                        job_scheduled_utc = normalize_to_utc(job.scheduled_time)
                        job_date = job_scheduled_utc.date()
                        
                        # Parse filter dates
                        from_date = None
                        to_date = None
                        
                        if scheduled_from:
                            try:
                                from_date = datetime.strptime(scheduled_from, "%Y-%m-%d").date()
                            except (ValueError, TypeError) as e:
                                self.logger.log_step(
                                    step="GET_ALL_JOBS",
                                    result="WARNING",
                                    error=f"Invalid scheduled_from date format: {scheduled_from} (error: {str(e)})",
                                    account_id=account_id
                                )
                                # Skip this filter if date is invalid
                                from_date = None
                        
                        if scheduled_to:
                            try:
                                to_date = datetime.strptime(scheduled_to, "%Y-%m-%d").date()
                            except (ValueError, TypeError) as e:
                                self.logger.log_step(
                                    step="GET_ALL_JOBS",
                                    result="WARNING",
                                    error=f"Invalid scheduled_to date format: {scheduled_to} (error: {str(e)})",
                                    account_id=account_id
                                )
                                # Skip this filter if date is invalid
                                to_date = None
                        
                        # Apply date filters
                        if from_date and job_date < from_date:
                            continue
                        if to_date and job_date > to_date:
                            continue
                        
                        filtered_jobs.append(job)
                    except Exception as e:
                        # Skip jobs that error during date comparison
                        self.logger.log_step(
                            step="GET_ALL_JOBS",
                            result="WARNING",
                            error=f"Error comparing scheduled_time for job {getattr(job, 'job_id', 'unknown')}: {str(e)}",
                            account_id=account_id,
                            error_type=type(e).__name__
                        )
                        continue
                
                jobs = filtered_jobs
            
            # Apply pagination with error handling
            try:
                jobs_before_pagination = len(jobs)
                
                if offset is not None and offset > 0:
                    jobs = jobs[offset:]
                if limit is not None and limit > 0:
                    jobs = jobs[:limit]
            except (IndexError, TypeError) as e:
                self.logger.log_step(
                    step="GET_ALL_JOBS",
                    result="WARNING",
                    error=f"Error applying pagination (offset={offset}, limit={limit}): {str(e)}",
                    account_id=account_id
                )
                # Return empty list if pagination fails
                return []
            
            return jobs
        
        except Exception as e:
            self.logger.log_step(
                step="GET_ALL_JOBS",
                result="ERROR",
                error=f"Error getting jobs: {str(e)}",
                account_id=filters.get("account_id") if filters else None
            )
            return []
    
    def get_count(
        self,
        filters: Optional[Dict] = None
    ) -> int:
        """
        Get total count of jobs matching filters (before pagination).
        
        Args:
            filters: Optional filter criteria (same as get_all)
        
        Returns:
            Total count of matching jobs
        """
        try:
            # Get all jobs with filters but without pagination
            jobs = self.get_all(filters=filters, limit=None, offset=None)
            return len(jobs)
        except Exception as e:
            self.logger.log_step(
                step="GET_JOBS_COUNT",
                result="ERROR",
                error=f"Error getting jobs count: {str(e)}",
                account_id=filters.get("account_id") if filters else None
            )
            return 0
    
    def create(self, entity_data: Dict) -> ScheduledJob:
        """
        Create new job.
        
        Args:
            entity_data: Job data with keys:
                - account_id: Account ID
                - content: Job content
                - scheduled_time: Datetime object
                - priority: JobPriority enum
                - platform: Platform enum
                - link_aff: Optional affiliate link
        
        Returns:
            Created ScheduledJob
        
        Raises:
            ValueError: If validation fails
            RuntimeError: If creation fails
        """
        try:
            # Extract job data
            account_id = entity_data["account_id"]
            content = entity_data["content"]
            scheduled_time = entity_data["scheduled_time"]
            priority = entity_data.get("priority", JobPriority.NORMAL)
            platform = entity_data.get("platform", Platform.THREADS)
            link_aff = entity_data.get("link_aff")
            
            # Add job to scheduler
            # Check if scheduler supports link_aff
            import inspect
            sig = inspect.signature(self.scheduler.add_job)
            
            if 'link_aff' in sig.parameters:
                job_id = self.scheduler.add_job(
                    account_id=account_id,
                    content=content,
                    scheduled_time=scheduled_time,
                    priority=priority,
                    platform=platform,
                    link_aff=link_aff
                )
            else:
                job_id = self.scheduler.add_job(
                    account_id=account_id,
                    content=content,
                    scheduled_time=scheduled_time,
                    priority=priority,
                    platform=platform
                )
            
            # Get created job
            job = self.scheduler.jobs.get(job_id)
            if not job:
                raise RuntimeError(f"Job {job_id} was created but not found in scheduler")
            
            self.logger.log_step(
                step="CREATE_JOB",
                result="SUCCESS",
                job_id=job_id,
                account_id=account_id
            )
            
            return job
        
        except Exception as e:
            self.logger.log_step(
                step="CREATE_JOB",
                result="ERROR",
                error=f"Error creating job: {str(e)}",
                account_id=entity_data.get("account_id")
            )
            raise
    
    def update(self, entity_id: str, entity_data: Dict) -> Optional[ScheduledJob]:
        """
        Update existing job.
        
        Note: Scheduler doesn't have direct update method.
        This would need to be implemented by removing and recreating,
        or by modifying the job object directly.
        
        Args:
            entity_id: Job ID
            entity_data: Updated job data
        
        Returns:
            Updated ScheduledJob if found, None otherwise
        """
        # For now, scheduler doesn't support direct update
        # This would need scheduler support or workaround
        self.logger.log_step(
            step="UPDATE_JOB",
            result="WARNING",
            note="Job update not fully supported by scheduler",
            job_id=entity_id
        )
        return None
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete job by ID.
        
        Args:
            entity_id: Job ID
        
        Returns:
            True if deleted, False if not found
        """
        try:
            # Remove job from scheduler
            # NOTE: Scheduler.remove_job() already passes save_callback=self._save_jobs internally
            # So we don't need to pass it again
            result = self.scheduler.remove_job(entity_id)
            
            self.logger.log_step(
                step="DELETE_JOB",
                result="SUCCESS",
                job_id=entity_id
            )
            
            return True
        
        except JobNotFoundError:
            self.logger.log_step(
                step="DELETE_JOB",
                result="FAILED",
                error="Job not found",
                job_id=entity_id
            )
            return False
        
        except Exception as e:
            self.logger.log_step(
                step="DELETE_JOB",
                result="ERROR",
                error=f"Error deleting job: {str(e)}",
                job_id=entity_id
            )
            return False
    
    def reload_jobs(self, force: bool = False) -> None:
        """
        Reload jobs from storage.
        
        Args:
            force: If True, force reload even if jobs already loaded
        """
        try:
            self.scheduler.reload_jobs(force=force)
            self.logger.log_step(
                step="RELOAD_JOBS",
                result="SUCCESS",
                jobs_count=len(self.scheduler.jobs)
            )
        except Exception as e:
            self.logger.log_step(
                step="RELOAD_JOBS",
                result="ERROR",
                error=f"Error reloading jobs: {str(e)}"
            )
