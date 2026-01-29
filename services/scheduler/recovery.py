"""
Module: services/scheduler/recovery.py

Recovery logic cho scheduler: recover stuck jobs và running jobs.
"""

# Standard library
import sys
from pathlib import Path

# Add parent directory to path để có thể import utils modules
_parent_dir = Path(__file__).resolve().parent.parent.parent
_parent_dir_str = str(_parent_dir)
if _parent_dir_str not in sys.path:
    sys.path.insert(0, _parent_dir_str)
elif sys.path[0] != _parent_dir_str:
    sys.path.remove(_parent_dir_str)
    sys.path.insert(0, _parent_dir_str)

from datetime import datetime, timedelta
from typing import Dict

# Local
from services.logger import StructuredLogger
from services.scheduler.models import ScheduledJob, JobStatus
from utils.exception_utils import (
    safe_get_exception_type_name
)


class JobRecovery:
    """
    Recovery manager cho jobs.
    
    Xử lý recovery các jobs bị stuck hoặc đang RUNNING khi scheduler start.
    """
    
    def __init__(
        self,
        logger: StructuredLogger
    ):
        """
        Khởi tạo recovery manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def recover_stuck_jobs(
        self,
        jobs: Dict[str, ScheduledJob],
        max_running_minutes: int = 30
    ) -> int:
        """
        Recover các jobs bị stuck ở trạng thái RUNNING (do crash/mất mạng).
        
        Jobs bị stuck sẽ được:
        - Reset về SCHEDULED nếu có thể retry
        - Đánh dấu FAILED nếu đã hết retry
        
        Args:
            jobs: Dict mapping job_id -> ScheduledJob
            max_running_minutes: Số phút tối đa job có thể ở trạng thái RUNNING (mặc định: 30 phút)
        
        Returns:
            Số lượng jobs đã được recover
        """
        stuck_jobs = []
        try:
            for job_id, job in jobs.items():
                try:
                    # BẢO VỆ: Chỉ recover jobs RUNNING, không touch COMPLETED
                    if not hasattr(job, 'status') or job.status != JobStatus.RUNNING:
                        continue
                    
                    if hasattr(job, 'is_stuck') and callable(job.is_stuck):
                        if job.is_stuck(max_running_minutes):
                            stuck_jobs.append(job_id)
                except Exception:
                    # Skip jobs that error when checking is_stuck
                    continue
        except (AttributeError, TypeError):
            # Nếu jobs dict có vấn đề, return 0
            return 0
        
        recovered_count = 0
        
        for job_id in stuck_jobs:
            try:
                job = jobs.get(job_id)
                if not job:
                    continue
                
                # Tính thời gian đã chạy với error handling
                started_at = getattr(job, 'started_at', None)
                if started_at:
                    try:
                        running_duration = datetime.now() - started_at
                        running_minutes = int(running_duration.total_seconds() / 60)
                    except (TypeError, AttributeError):
                        running_minutes = max_running_minutes + 1  # Fallback
                else:
                    running_minutes = max_running_minutes + 1  # Fallback
            
                # Kiểm tra có thể retry không với error handling
                can_retry = False
                try:
                    if hasattr(job, 'can_retry') and callable(job.can_retry):
                        can_retry = job.can_retry()
                except Exception:
                    can_retry = False
                
                if can_retry:
                    # Reset về SCHEDULED để retry
                    try:
                        retry_count = getattr(job, 'retry_count', 0)
                        max_retries = getattr(job, 'max_retries', 3)
                        job.retry_count = retry_count + 1
                        job.status = JobStatus.SCHEDULED
                        # Exponential backoff: 2^retry_count minutes
                        backoff_minutes = 2 ** job.retry_count
                        job.scheduled_time = datetime.now() + timedelta(minutes=backoff_minutes)
                        job.started_at = None  # Reset started_at
                        job.status_message = (
                            f"Recovered từ stuck (đã chạy {running_minutes} phút), "
                            f"sẽ thử lại sau {backoff_minutes} phút (lần thử {job.retry_count}/{max_retries})"
                        )
                        
                        # Log với safe access
                        account_id = getattr(job, 'account_id', 'N/A')
                        scheduled_time_str = None
                        try:
                            if hasattr(job.scheduled_time, 'isoformat'):
                                scheduled_time_str = job.scheduled_time.isoformat()
                            else:
                                scheduled_time_str = str(job.scheduled_time)
                        except Exception:
                            scheduled_time_str = str(job.scheduled_time) if job.scheduled_time else None
                        
                        self.logger.log_step(
                            step="RECOVER_STUCK_JOB",
                            result="RETRY_SCHEDULED",
                            job_id=job_id,
                            account_id=account_id,
                            running_minutes=running_minutes,
                            retry_count=job.retry_count,
                            next_run=scheduled_time_str,
                            status_message=job.status_message
                        )
                        recovered_count += 1
                    except Exception as e:
                        # Log error nhưng continue với các jobs khác
                        self.logger.log_step(
                            step="RECOVER_STUCK_JOB",
                            result="ERROR",
                            job_id=job_id,
                            error=f"Error recovering job: {str(e)}",
                            error_type=safe_get_exception_type_name(e)
                        )
                        continue
                else:
                    # Đánh dấu FAILED nếu đã hết retry
                    try:
                        retry_count = getattr(job, 'retry_count', 0)
                        max_retries = getattr(job, 'max_retries', 3)
                        job.status = JobStatus.FAILED
                        job.started_at = None  # Reset started_at
                        job.error = f"Job bị stuck {running_minutes} phút và đã hết retry ({retry_count}/{max_retries})"
                        job.status_message = f"Thất bại - {job.error}"
                        
                        # Log với safe access
                        account_id = getattr(job, 'account_id', 'N/A')
                        self.logger.log_step(
                            step="RECOVER_STUCK_JOB",
                            result="FAILED",
                            job_id=job_id,
                            account_id=account_id,
                            running_minutes=running_minutes,
                            retry_count=retry_count,
                            error=job.error,
                            status_message=job.status_message
                        )
                        recovered_count += 1
                    except Exception as e:
                        # Log error nhưng continue với các jobs khác
                        self.logger.log_step(
                            step="RECOVER_STUCK_JOB",
                            result="ERROR",
                            job_id=job_id,
                            error=f"Error marking job as failed: {str(e)}",
                            error_type=safe_get_exception_type_name(e)
                        )
                        continue
            except Exception as e:
                # Log error nhưng continue với các jobs khác
                self.logger.log_step(
                    step="RECOVER_STUCK_JOB",
                    result="ERROR",
                    job_id=job_id,
                    error=f"Error processing stuck job: {str(e)}",
                    error_type=safe_get_exception_type_name(e)
                )
                continue
        
        if recovered_count > 0:
            self.logger.log_step(
                step="RECOVER_STUCK_JOBS",
                result="SUCCESS",
                recovered_count=recovered_count,
                max_running_minutes=max_running_minutes
            )
        
        return recovered_count
    
    def recover_all_running_jobs(
        self,
        jobs: Dict[str, ScheduledJob]
    ) -> int:
        """
        Recover TẤT CẢ jobs đang ở trạng thái RUNNING khi scheduler start.
        
        Được gọi khi scheduler khởi động để đảm bảo không có jobs RUNNING "mồ côi"
        do crash/mất mạng. Tất cả jobs RUNNING sẽ được recover ngay lập tức.
        
        Args:
            jobs: Dict mapping job_id -> ScheduledJob
        
        Returns:
            Số lượng jobs đã được recover
        """
        running_jobs = []
        try:
            for job_id, job in jobs.items():
                try:
                    # BẢO VỆ: Chỉ recover jobs RUNNING, bỏ qua COMPLETED
                    if hasattr(job, 'status') and job.status == JobStatus.RUNNING:
                        running_jobs.append(job_id)
                    # Bỏ qua COMPLETED - không recover jobs đã hoàn thành
                except Exception:
                    # Skip jobs that error when checking status
                    continue
        except (AttributeError, TypeError):
            # Nếu jobs dict có vấn đề, return 0
            return 0
        
        if not running_jobs:
            return 0
        
        recovered_count = 0
        
        for job_id in running_jobs:
            try:
                job = jobs.get(job_id)
                if not job:
                    continue
                
                # Tính thời gian đã chạy (nếu có started_at) với error handling
                started_at = getattr(job, 'started_at', None)
                if started_at:
                    try:
                        running_duration = datetime.now() - started_at
                        running_minutes = int(running_duration.total_seconds() / 60)
                    except (TypeError, AttributeError):
                        # Không có started_at - coi như đã chạy 0 phút (hoặc không rõ)
                        running_minutes = 0
                else:
                    # Không có started_at - coi như đã chạy 0 phút (hoặc không rõ)
                    running_minutes = 0
                
                # Kiểm tra có thể retry không với error handling
                can_retry = False
                try:
                    if hasattr(job, 'can_retry') and callable(job.can_retry):
                        can_retry = job.can_retry()
                except Exception:
                    can_retry = False
                
                if can_retry:
                    # Reset về SCHEDULED để retry
                    try:
                        retry_count = getattr(job, 'retry_count', 0)
                        max_retries = getattr(job, 'max_retries', 3)
                        job.retry_count = retry_count + 1
                        job.status = JobStatus.SCHEDULED
                        # Exponential backoff: 2^retry_count minutes
                        backoff_minutes = 2 ** job.retry_count
                        job.scheduled_time = datetime.now() + timedelta(minutes=backoff_minutes)
                        job.started_at = None  # Reset started_at
                        job.status_message = (
                            f"Recovered từ RUNNING khi scheduler start (đã chạy {running_minutes} phút), "
                            f"sẽ thử lại sau {backoff_minutes} phút (lần thử {job.retry_count}/{max_retries})"
                        )
                        
                        # Log với safe access
                        account_id = getattr(job, 'account_id', 'N/A')
                        scheduled_time_str = None
                        try:
                            if hasattr(job.scheduled_time, 'isoformat'):
                                scheduled_time_str = job.scheduled_time.isoformat()
                            else:
                                scheduled_time_str = str(job.scheduled_time)
                        except Exception:
                            scheduled_time_str = str(job.scheduled_time) if job.scheduled_time else None
                        
                        self.logger.log_step(
                            step="RECOVER_RUNNING_JOB",
                            result="RETRY_SCHEDULED",
                            job_id=job_id,
                            account_id=account_id,
                            running_minutes=running_minutes,
                            retry_count=job.retry_count,
                            next_run=scheduled_time_str,
                            status_message=job.status_message
                        )
                        recovered_count += 1
                    except Exception as e:
                        # Log error nhưng continue với các jobs khác
                        self.logger.log_step(
                            step="RECOVER_RUNNING_JOB",
                            result="ERROR",
                            job_id=job_id,
                            error=f"Error recovering job: {str(e)}",
                            error_type=safe_get_exception_type_name(e)
                        )
                        continue
                else:
                    # Đánh dấu FAILED nếu đã hết retry
                    try:
                        retry_count = getattr(job, 'retry_count', 0)
                        max_retries = getattr(job, 'max_retries', 3)
                        job.status = JobStatus.FAILED
                        job.started_at = None  # Reset started_at
                        job.error = f"Job bị RUNNING khi scheduler start và đã hết retry ({retry_count}/{max_retries})"
                        job.status_message = f"Thất bại - {job.error}"
                        
                        # Log với safe access
                        account_id = getattr(job, 'account_id', 'N/A')
                        self.logger.log_step(
                            step="RECOVER_RUNNING_JOB",
                            result="FAILED",
                            job_id=job_id,
                            account_id=account_id,
                            running_minutes=running_minutes,
                            retry_count=retry_count,
                            error=job.error,
                            status_message=job.status_message
                        )
                        recovered_count += 1
                    except Exception as e:
                        # Log error nhưng continue với các jobs khác
                        self.logger.log_step(
                            step="RECOVER_RUNNING_JOB",
                            result="ERROR",
                            job_id=job_id,
                            error=f"Error marking job as failed: {str(e)}",
                            error_type=safe_get_exception_type_name(e)
                        )
                        continue
            except Exception as e:
                # Log error nhưng continue với các jobs khác
                self.logger.log_step(
                    step="RECOVER_RUNNING_JOB",
                    result="ERROR",
                    job_id=job_id,
                    error=f"Error processing running job: {str(e)}",
                    error_type=safe_get_exception_type_name(e)
                )
                continue
        
        if recovered_count > 0:
            self.logger.log_step(
                step="RECOVER_ALL_RUNNING_JOBS",
                result="SUCCESS",
                recovered_count=recovered_count,
                total_running=len(running_jobs)
            )
        
        return recovered_count

