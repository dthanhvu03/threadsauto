"""
Module: services/scheduler/storage/base.py

Abstract base class cho job storage implementations.
Defines interface cho cả JSON và MySQL storage.
"""

# Standard library
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

# Local
from services.scheduler.models import ScheduledJob, JobStatus
from services.logger import StructuredLogger


class JobStorageBase(ABC):
    """
    Abstract base class cho job storage implementations.
    
    Defines interface cho các storage implementations:
    - JobStorage (JSON files)
    - MySQLJobStorage (MySQL database)
    
    All implementations must provide:
    - load_jobs(): Load tất cả jobs
    - save_jobs(): Save jobs (atomic operation)
    
    Optional methods (for future enhancements):
    - get_job_by_id(): Get single job by ID
    - get_jobs_by_status(): Filter jobs by status
    - get_jobs_by_account(): Filter jobs by account
    
    Attributes:
        logger: Structured logger instance (should be set by subclasses)
    """
    
    def __init__(self, logger: StructuredLogger):
        """
        Initialize base storage.
        
        Args:
            logger: Structured logger instance
        """
        self.logger = logger
    
    @abstractmethod
    def load_jobs(self) -> Dict[str, ScheduledJob]:
        """
        Load tất cả jobs từ storage.
        
        Returns:
            Dict mapping job_id -> ScheduledJob
            Empty dict nếu không có jobs
        
        Raises:
            StorageError: Nếu có lỗi khi load
        """
        pass
    
    @abstractmethod
    def save_jobs(self, jobs: Dict[str, ScheduledJob]) -> None:
        """
        Save jobs to storage (atomic operation).
        
        Args:
            jobs: Dict mapping job_id -> ScheduledJob
        
        Raises:
            StorageError: Nếu có lỗi khi save
        
        Note:
            Implementation should ensure atomic operation.
            Nếu save fails, state should be unchanged.
        """
        pass
    
    def get_job_by_id(self, job_id: str) -> Optional[ScheduledJob]:
        """
        Get job by ID (optional method).
        
        Default implementation: Load all jobs và filter.
        Subclasses có thể override để optimize.
        
        Args:
            job_id: Job ID to find
        
        Returns:
            ScheduledJob nếu tìm thấy, None nếu không
        """
        all_jobs = self.load_jobs()
        return all_jobs.get(job_id)
    
    def get_jobs_by_status(
        self,
        status: JobStatus,
        limit: Optional[int] = None
    ) -> List[ScheduledJob]:
        """
        Get jobs by status (optional method).
        
        Default implementation: Load all jobs và filter.
        Subclasses có thể override để optimize với database queries.
        
        Args:
            status: JobStatus to filter by
            limit: Optional limit on number of results
        
        Returns:
            List of ScheduledJob với status matching
        """
        all_jobs = self.load_jobs()
        filtered = [
            job for job in all_jobs.values()
            if job.status == status
        ]
        
        # Sort by scheduled_time
        filtered.sort(key=lambda j: j.scheduled_time)
        
        if limit:
            return filtered[:limit]
        return filtered
    
    def get_jobs_by_account(
        self,
        account_id: str,
        status: Optional[JobStatus] = None
    ) -> List[ScheduledJob]:
        """
        Get jobs by account ID (optional method).
        
        Default implementation: Load all jobs và filter.
        Subclasses có thể override để optimize với database queries.
        
        Args:
            account_id: Account ID to filter by
            status: Optional JobStatus to filter by (if None, returns all statuses)
        
        Returns:
            List of ScheduledJob cho account
        """
        all_jobs = self.load_jobs()
        filtered = [
            job for job in all_jobs.values()
            if job.account_id == account_id
            and (status is None or job.status == status)
        ]
        
        # Sort by scheduled_time
        filtered.sort(key=lambda j: j.scheduled_time)
        
        return filtered
    
    def close(self) -> None:
        """
        Close storage connection (optional cleanup).
        
        Default implementation: No-op.
        Subclasses có thể override để close database connections, etc.
        """
        pass
