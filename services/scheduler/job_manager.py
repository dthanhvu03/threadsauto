"""
Module: services/scheduler/job_manager.py

Job management logic cho scheduler: add, remove, list, get_ready, cleanup_expired.
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
from typing import Optional, List, Dict, Callable
from uuid import uuid4

# Local
from services.logger import StructuredLogger
from services.exceptions import (
    SchedulerError,
    JobNotFoundError,
    InvalidScheduleTimeError,
    StorageError,
)
from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform
from services.scheduler.job_validator import JobValidator, ValidationSeverity
from utils.exception_utils import safe_get_exception_type_name


class JobManager:
    """
    Job manager cho scheduler.

    Xử lý các operations liên quan đến job management:
    - Add/remove jobs
    - List/filter jobs
    - Get ready jobs
    - Cleanup expired jobs
    """

    def __init__(
        self,
        jobs: Dict[str, ScheduledJob],
        logger: StructuredLogger,
        overdue_threshold_hours: Optional[int] = None,
    ):
        """
        Khởi tạo job manager.

        Args:
            jobs: Dict mapping job_id -> ScheduledJob
            logger: Logger instance
            overdue_threshold_hours: Skip jobs overdue by more than this (None = catch-up all overdue jobs)
        """
        self.jobs = jobs
        self.logger = logger
        self.validator = JobValidator(logger)
        self.overdue_threshold_hours = overdue_threshold_hours

    def _normalize_content(self, content: str) -> str:
        """
        Normalize content để so sánh duplicate.

        Args:
            content: Content string

        Returns:
            Normalized content

        Note: Uses shared utility function from utils.content
        """
        from utils.content import normalize_content

        return normalize_content(content)

    def _check_duplicate_content(
        self, account_id: Optional[str], content: str, platform: Platform
    ) -> Optional[str]:
        """
        Kiểm tra xem content đã có trong jobs chưa (duplicate).

        Args:
            account_id: Account ID (optional, can be None)
            content: Content string
            platform: Platform

        Returns:
            Job ID của job duplicate nếu tìm thấy, None nếu không duplicate
        """
        normalized_content = self._normalize_content(content)
        if not normalized_content:
            return None

        # Tìm jobs có cùng account_id, platform và content tương tự
        for job_id, job in self.jobs.items():
            try:
                # Check account_id match (None matches None, or exact match)
                job_account_id = getattr(job, "account_id", None)
                account_match = job_account_id == account_id  # None == None is True

                # Check platform match
                platform_match = hasattr(job, "platform") and job.platform == platform

                if account_match and platform_match:
                    # Normalize job content để so sánh
                    job_content_normalized = self._normalize_content(
                        getattr(job, "content", "")
                    )

                    # So sánh exact match (sau khi normalize)
                    if job_content_normalized == normalized_content:
                        # Tìm thấy duplicate
                        return job_id
            except (AttributeError, TypeError):
                # Skip jobs với invalid attributes
                continue

        return None

    def add_job(
        self,
        account_id: Optional[str],
        content: str,
        scheduled_time: datetime,
        priority: JobPriority = JobPriority.NORMAL,
        platform: Platform = Platform.THREADS,
        max_retries: int = 3,
        save_callback: Optional[Callable[[], None]] = None,
        link_aff: Optional[str] = None,
    ) -> str:
        """
        Thêm job mới vào scheduler.

        Args:
            account_id: ID tài khoản (optional, can be None)
            content: Nội dung thread
            scheduled_time: Thời gian lên lịch
            priority: Độ ưu tiên (mặc định: NORMAL)
            platform: Platform để đăng bài (mặc định: THREADS)
            max_retries: Số lần retry tối đa (mặc định: 3)
            save_callback: Callback để save jobs sau khi add
            link_aff: Link affiliate để đăng trong comment (optional)

        Returns:
            Job ID

        Raises:
            InvalidScheduleTimeError: Nếu scheduled_time không hợp lệ
            ValueError: Nếu input không hợp lệ hoặc duplicate content
            StorageError: Nếu không thể lưu job
        """
        # Validate inputs với JobValidator (nghiêm ngặt hơn)
        existing_jobs_list = list(self.jobs.values())
        validation_result = self.validator.validate_add_job(
            account_id=account_id,
            content=content,
            scheduled_time=scheduled_time,
            priority=priority,
            platform=platform,
            max_retries=max_retries,
            existing_jobs=existing_jobs_list,
        )

        # Log warnings nếu có
        if validation_result.has_warnings():
            for warning_msg in validation_result.get_warning_messages():
                self.logger.log_step(
                    step="ADD_JOB",
                    result="WARNING",
                    warning=warning_msg,
                    account_id=account_id,
                )

        # Raise errors nếu có
        if validation_result.has_errors():
            error_messages = validation_result.get_error_messages()
            error_msg = "; ".join(error_messages)

            # Phân loại error type
            if "scheduled_time" in error_msg.lower():
                raise InvalidScheduleTimeError(error_msg)
            else:
                raise ValueError(error_msg)

        # KIỂM TRA DUPLICATE CONTENT
        duplicate_job_id = self._check_duplicate_content(account_id, content, platform)
        if duplicate_job_id:
            # Thread-safe access: use .get() instead of direct access
            duplicate_job = self.jobs.get(duplicate_job_id)
            duplicate_status = (
                getattr(duplicate_job, "status", None) if duplicate_job else None
            )
            status_str = (
                duplicate_status.value
                if duplicate_status and hasattr(duplicate_status, "value")
                else str(duplicate_status)
            )

            self.logger.log_step(
                step="ADD_JOB",
                result="FAILED",
                error="Duplicate content detected",
                job_id=duplicate_job_id,
                account_id=account_id,
                duplicate_status=status_str,
                content_preview=content[:50] + "..." if len(content) > 50 else content,
            )

            raise ValueError(
                f"Content đã tồn tại trong job {duplicate_job_id[:8]}... "
                f"(status: {status_str}). Không thể tạo job duplicate."
            )

        try:
            job_id = str(uuid4())
            job = ScheduledJob(
                job_id=job_id,
                account_id=account_id,
                content=content,
                scheduled_time=scheduled_time,
                priority=priority,
                platform=platform,
                status=JobStatus.SCHEDULED,
                max_retries=max_retries,
                link_aff=link_aff,
            )

            from services.utils.datetime_utils import format_vn

            vn_time_str = (
                format_vn(scheduled_time)
                if hasattr(scheduled_time, "strftime")
                else str(scheduled_time)
            )
            job.status_message = f"Đã thêm vào scheduler - sẽ chạy vào {vn_time_str}"
            # Thread-safe: Direct assignment is safe for new keys
            self.jobs[job_id] = job

            # DEBUG: Verify job is in memory before saving
            if job_id not in self.jobs:
                self.logger.log_step(
                    step="ADD_JOB",
                    result="ERROR",
                    error=f"Job {job_id} not found in memory after assignment",
                    job_id=job_id,
                )
                raise SchedulerError(f"Failed to add job to memory: {job_id}")

            # Save jobs nếu có callback
            if save_callback:
                try:
                    # DEBUG: Log before save
                    jobs_count_before = len(self.jobs)
                    self.logger.log_step(
                        step="ADD_JOB_SAVE",
                        result="INFO",
                        note=f"Calling save_callback, jobs in memory: {jobs_count_before}",
                        job_id=job_id,
                    )
                    save_callback()
                    # DEBUG: Verify job is still in memory after save
                    if job_id not in self.jobs:
                        self.logger.log_step(
                            step="ADD_JOB_SAVE",
                            result="WARNING",
                            note=f"Job {job_id} missing from memory after save_callback",
                            job_id=job_id,
                        )
                except Exception as save_error:
                    # Log error nhưng không fail add operation
                    self.logger.log_step(
                        step="ADD_JOB_SAVE",
                        result="ERROR",
                        error=f"save_callback failed: {str(save_error)}",
                        error_type=safe_get_exception_type_name(save_error),
                        job_id=job_id,
                    )
                    # Re-raise để caller biết save failed
                    raise

            self.logger.log_step(
                step="ADD_JOB",
                result="SUCCESS",
                job_id=job_id,
                account_id=account_id,
                scheduled_time=scheduled_time.isoformat(),
                priority=priority.value,
                status_message=job.status_message,
            )

            return job_id
        except StorageError:
            # Re-raise storage errors
            raise
        except Exception as e:
            self.logger.log_step(
                step="ADD_JOB",
                result="ERROR",
                error=f"Failed to add job: {str(e)}",
                error_type=safe_get_exception_type_name(e),
            )
            raise SchedulerError(f"Failed to add job: {str(e)}") from e

    def remove_job(
        self, job_id: str, save_callback: Optional[Callable[[], None]] = None
    ) -> bool:
        """
        Xóa job khỏi scheduler.

        Args:
            job_id: ID của job cần xóa
            save_callback: Callback để save jobs sau khi remove

        Returns:
            True nếu xóa thành công

        Raises:
            JobNotFoundError: Nếu job không tồn tại
            StorageError: Nếu không thể lưu sau khi xóa
        """
        if not job_id or not isinstance(job_id, str):
            raise ValueError("job_id phải là string không rỗng")

        if job_id not in self.jobs:
            self.logger.log_step(
                step="REMOVE_JOB", result="FAILED", job_id=job_id, error="Job not found"
            )
            raise JobNotFoundError(f"Job {job_id} không tồn tại")

        try:
            jobs_count_before = len(self.jobs)
            # CRITICAL: Log dict ID để debug reference issues
            jobs_dict_id = id(self.jobs)
            job_existed = job_id in self.jobs
            del self.jobs[job_id]
            jobs_count_after = len(self.jobs)

            self.logger.log_step(
                step="REMOVE_JOB",
                result="INFO",
                note=f"Deleted job from memory: {jobs_count_before} -> {jobs_count_after}",
                job_id=job_id,
                jobs_before=jobs_count_before,
                jobs_after=jobs_count_after,
                jobs_dict_id=jobs_dict_id,
                job_existed=job_existed,
            )

            # Save jobs nếu có callback
            if save_callback:
                self.logger.log_step(
                    step="REMOVE_JOB_SAVE",
                    result="INFO",
                    note="Calling save_callback to persist deletion",
                    job_id=job_id,
                )
                save_callback()
                self.logger.log_step(
                    step="REMOVE_JOB_SAVE",
                    result="SUCCESS",
                    note="save_callback completed",
                    job_id=job_id,
                )
            else:
                self.logger.log_step(
                    step="REMOVE_JOB_SAVE",
                    result="WARNING",
                    note="No save_callback provided, job deletion not persisted",
                    job_id=job_id,
                )

            self.logger.log_step(step="REMOVE_JOB", result="SUCCESS", job_id=job_id)
            return True
        except StorageError:
            # Re-raise storage errors
            raise
        except Exception as e:
            self.logger.log_step(
                step="REMOVE_JOB",
                result="ERROR",
                job_id=job_id,
                error=f"Failed to remove job: {str(e)}",
                error_type=safe_get_exception_type_name(e),
            )
            raise SchedulerError(f"Failed to remove job: {str(e)}") from e

    def list_jobs(
        self, account_id: Optional[str] = None, status: Optional[JobStatus] = None
    ) -> List[ScheduledJob]:
        """
        Liệt kê jobs.

        Args:
            account_id: Lọc theo account ID (tùy chọn)
            status: Lọc theo status (tùy chọn)

        Returns:
            Danh sách jobs
        """
        try:
            jobs = list(self.jobs.values())
        except (AttributeError, TypeError) as e:
            # Nếu jobs dict có vấn đề, log và return empty list
            self.logger.log_step(
                step="LIST_JOBS",
                result="ERROR",
                error=f"Error accessing jobs dict: {str(e)}",
                error_type=safe_get_exception_type_name(e),
            )
            return []

        # Filter by account_id với error handling
        if account_id:
            filtered_jobs = []
            for j in jobs:
                try:
                    if hasattr(j, "account_id") and j.account_id == account_id:
                        filtered_jobs.append(j)
                except (AttributeError, TypeError):
                    # Skip jobs with invalid account_id
                    continue
            jobs = filtered_jobs

        # Filter by status với error handling
        if status:
            filtered_jobs = []
            for j in jobs:
                try:
                    if hasattr(j, "status") and j.status == status:
                        filtered_jobs.append(j)
                except (AttributeError, TypeError):
                    # Skip jobs with invalid status
                    continue
            jobs = filtered_jobs

        # Sắp xếp theo priority và scheduled_time với error handling
        try:
            jobs.sort(
                key=lambda j: (
                    (
                        j.priority.value
                        if hasattr(j, "priority") and hasattr(j.priority, "value")
                        else 0
                    ),
                    j.scheduled_time if hasattr(j, "scheduled_time") else datetime.min,
                ),
                reverse=True,
            )
        except (AttributeError, TypeError) as e:
            # Log error nhưng return unsorted list
            self.logger.log_step(
                step="LIST_JOBS",
                result="WARNING",
                error=f"Error sorting jobs: {str(e)}",
                error_type=safe_get_exception_type_name(e),
            )

        return jobs

    def validate_all_jobs(self) -> Dict[str, List[str]]:
        """
        Validate tất cả jobs hiện có và báo cáo issues.

        Returns:
            Dict mapping job_id -> List of validation error messages
        """
        issues = {}

        for job_id, job in self.jobs.items():
            validation_result = self.validator.validate_job_state(job)

            if validation_result.has_errors() or validation_result.has_warnings():
                all_messages = [
                    f"[{severity.value.upper()}] {msg}"
                    for severity, msg in validation_result.errors
                ]
                issues[job_id] = all_messages

        return issues

    def get_ready_jobs(self) -> List[ScheduledJob]:
        """
        Lấy danh sách jobs sẵn sàng chạy.

        BẢO VỆ: Chỉ return jobs SCHEDULED/PENDING, không bao giờ return
        COMPLETED, RUNNING, FAILED, CANCELLED, EXPIRED.

        Returns:
            Danh sách jobs sẵn sàng chạy, sắp xếp theo priority
        """
        ready_jobs = []
        try:
            for j in self.jobs.values():
                try:
                    # BẢO VỆ: Double check status trước khi gọi is_ready()
                    # Chặn jobs COMPLETED, RUNNING ngay từ đầu
                    if hasattr(j, "status"):
                        if j.status in [
                            JobStatus.COMPLETED,  # Đã chạy xong - KHÔNG BAO GIỜ chạy lại
                            JobStatus.RUNNING,  # Đang chạy - không thể chạy lại
                            JobStatus.FAILED,  # Đã fail hết retry - không chạy lại
                            JobStatus.CANCELLED,  # Đã bị hủy - không chạy
                            JobStatus.EXPIRED,  # Đã hết hạn - không chạy
                        ]:
                            continue  # Bỏ qua jobs này

                    if hasattr(j, "is_ready") and callable(j.is_ready):
                        # Check if job is overdue beyond threshold (if threshold is set)
                        is_overdue_beyond_threshold = False
                        if (
                            self.overdue_threshold_hours is not None
                            and hasattr(j, "scheduled_time")
                            and j.scheduled_time
                        ):
                            from datetime import datetime, timezone
                            from services.utils.datetime_utils import ensure_utc

                            scheduled_time_utc = ensure_utc(j.scheduled_time)
                            now_utc = datetime.now(timezone.utc)
                            hours_overdue = (
                                now_utc - scheduled_time_utc
                            ).total_seconds() / 3600
                            if hours_overdue > self.overdue_threshold_hours:
                                is_overdue_beyond_threshold = True
                                self.logger.log_step(
                                    step="GET_READY_JOBS",
                                    result="INFO",
                                    note=f"Job {getattr(j, 'job_id', 'unknown')[:8]} overdue by {hours_overdue:.1f}h, exceeding threshold {self.overdue_threshold_hours}h - skipping",
                                    job_id=getattr(j, "job_id", "unknown"),
                                    hours_overdue=hours_overdue,
                                    threshold_hours=self.overdue_threshold_hours,
                                )
                                continue  # Skip this job

                        is_ready_result = j.is_ready()

                        if is_ready_result:
                            ready_jobs.append(j)
                except Exception as e:
                    # Skip jobs that error when checking is_ready
                    self.logger.log_step(
                        step="GET_READY_JOBS",
                        result="WARNING",
                        error=f"Error checking is_ready for job {getattr(j, 'job_id', 'unknown')}: {str(e)}",
                        error_type=safe_get_exception_type_name(e),
                    )
                    continue
        except (AttributeError, TypeError) as e:
            # Nếu jobs dict có vấn đề, log và return empty list
            self.logger.log_step(
                step="GET_READY_JOBS",
                result="ERROR",
                error=f"Error accessing jobs dict: {str(e)}",
                error_type=safe_get_exception_type_name(e),
            )
            return []

        # Sort với error handling
        try:
            ready_jobs.sort(
                key=lambda j: (
                    (
                        j.priority.value
                        if hasattr(j, "priority") and hasattr(j.priority, "value")
                        else 0
                    ),
                    j.scheduled_time if hasattr(j, "scheduled_time") else datetime.min,
                ),
                reverse=True,
            )
        except (AttributeError, TypeError) as e:
            # Log error nhưng return unsorted list
            self.logger.log_step(
                step="GET_READY_JOBS",
                result="WARNING",
                error=f"Error sorting ready jobs: {str(e)}",
                error_type=safe_get_exception_type_name(e),
            )

        return ready_jobs

    def cleanup_expired_jobs(
        self, save_callback: Optional[Callable[[], None]] = None
    ) -> int:
        """
        Xóa các jobs đã hết hạn.

        Chỉ đánh dấu expired các jobs đã quá 24h từ scheduled_time
        và chưa được completed.

        Args:
            save_callback: Callback để save jobs sau khi cleanup

        Returns:
            Số lượng jobs đã đánh dấu expired
        """
        expired_jobs = []
        try:
            for job_id, job in self.jobs.items():
                try:
                    # Check if job is expired và chưa completed/expired
                    if (
                        hasattr(job, "is_expired")
                        and callable(job.is_expired)
                        and hasattr(job, "status")
                    ):
                        if job.is_expired() and job.status not in [
                            JobStatus.COMPLETED,
                            JobStatus.EXPIRED,
                        ]:
                            expired_jobs.append(job_id)
                except Exception as e:
                    # Skip jobs that error when checking is_expired
                    self.logger.log_step(
                        step="CLEANUP_EXPIRED_JOBS",
                        result="WARNING",
                        error=f"Error checking is_expired for job {job_id}: {str(e)}",
                        error_type=safe_get_exception_type_name(e),
                        job_id=job_id,
                    )
                    continue
        except (AttributeError, TypeError) as e:
            # Nếu jobs dict có vấn đề, log và return 0
            self.logger.log_step(
                step="CLEANUP_EXPIRED_JOBS",
                result="ERROR",
                error=f"Error accessing jobs dict: {str(e)}",
                error_type=safe_get_exception_type_name(e),
            )
            return 0

        # Mark expired jobs với error handling
        marked_count = 0
        for job_id in expired_jobs:
            try:
                job = self.jobs.get(job_id)
                if not job:
                    continue

                # Chỉ đánh dấu expired nếu thực sự đã quá 24h
                if hasattr(
                    job, "scheduled_time"
                ) and datetime.now() > job.scheduled_time + timedelta(hours=24):
                    job.status = JobStatus.EXPIRED
                    hours_past = (
                        datetime.now() - job.scheduled_time
                    ).total_seconds() / 3600

                    # Format scheduled_time safely in VN timezone
                    scheduled_str = "N/A"
                    try:
                        from services.utils.datetime_utils import format_vn

                        scheduled_str = (
                            format_vn(job.scheduled_time)
                            if hasattr(job.scheduled_time, "strftime")
                            else str(job.scheduled_time)
                        )
                    except Exception:
                        scheduled_str = (
                            str(job.scheduled_time) if job.scheduled_time else "N/A"
                        )

                    job.status_message = f"Hết hạn - đã quá {int(hours_past)} giờ từ thời gian lên lịch ({scheduled_str})"

                    # Log với safe access
                    try:
                        self.logger.log_step(
                            step="CLEANUP_EXPIRED_JOBS",
                            result="SUCCESS",
                            job_id=job_id,
                            scheduled_time=(
                                job.scheduled_time.isoformat()
                                if hasattr(job.scheduled_time, "isoformat")
                                else str(job.scheduled_time)
                            ),
                            hours_past=hours_past,
                            status_message=job.status_message,
                        )
                    except Exception as log_error:
                        # Log error nhưng continue
                        self.logger.log_step(
                            step="CLEANUP_EXPIRED_JOBS",
                            result="WARNING",
                            error=f"Error logging cleanup for job {job_id}: {str(log_error)}",
                            error_type=safe_get_exception_type_name(log_error),
                            job_id=job_id,
                        )

                    marked_count += 1
            except Exception as e:
                # Log error nhưng continue với các jobs khác
                self.logger.log_step(
                    step="CLEANUP_EXPIRED_JOBS",
                    result="ERROR",
                    error=f"Error marking job {job_id} as expired: {str(e)}",
                    error_type=safe_get_exception_type_name(e),
                    job_id=job_id,
                )
                continue

        # Save jobs nếu có callback và có jobs được marked
        if marked_count > 0 and save_callback:
            try:
                save_callback()
            except Exception as e:
                # Log error nhưng không raise
                self.logger.log_step(
                    step="CLEANUP_EXPIRED_JOBS",
                    result="WARNING",
                    error=f"Error saving jobs after cleanup: {str(e)}",
                    error_type=safe_get_exception_type_name(e),
                )

        return marked_count
