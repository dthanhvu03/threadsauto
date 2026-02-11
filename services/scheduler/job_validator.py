"""
Module: services/scheduler/job_validator.py

Job validation logic với business rules nghiêm ngặt.
Đảm bảo jobs không có lỗi trước khi add/execute.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from enum import Enum

from services.logger import StructuredLogger
from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform
from services.utils.datetime_utils import ensure_utc


class ValidationSeverity(Enum):
    """Mức độ nghiêm trọng của validation error."""

    ERROR = "error"  # Block operation
    WARNING = "warning"  # Allow but warn
    INFO = "info"  # Informational only


class ValidationResult:
    """Kết quả validation."""

    def __init__(self):
        self.errors: List[Tuple[ValidationSeverity, str]] = []
        self.is_valid = True

    def add_error(self, severity: ValidationSeverity, message: str):
        """Thêm validation error."""
        self.errors.append((severity, message))
        if severity == ValidationSeverity.ERROR:
            self.is_valid = False

    def has_errors(self) -> bool:
        """Check có errors không."""
        return any(severity == ValidationSeverity.ERROR for severity, _ in self.errors)

    def has_warnings(self) -> bool:
        """Check có warnings không."""
        return any(
            severity == ValidationSeverity.WARNING for severity, _ in self.errors
        )

    def get_error_messages(self) -> List[str]:
        """Lấy danh sách error messages."""
        return [
            msg for severity, msg in self.errors if severity == ValidationSeverity.ERROR
        ]

    def get_warning_messages(self) -> List[str]:
        """Lấy danh sách warning messages."""
        return [
            msg
            for severity, msg in self.errors
            if severity == ValidationSeverity.WARNING
        ]


class JobValidator:
    """
    Validator cho jobs với business rules nghiêm ngặt.

    Đảm bảo:
    - Jobs không có data invalid
    - Business rules được tuân thủ
    - Tránh các edge cases gây lỗi
    """

    # Business rules constants
    MAX_CONTENT_LENGTH = 500  # Threads limit
    MIN_CONTENT_LENGTH = 1
    MAX_SCHEDULE_DAYS_AHEAD = 365  # Không lên lịch quá 1 năm
    MAX_SCHEDULE_DAYS_PAST = (
        -1
    )  # Không lên lịch quá khứ (cho phép 1 ngày để handle timezone)
    MIN_TIME_BETWEEN_JOBS_SECONDS = 5  # Tối thiểu 5 giây giữa các jobs
    MAX_RETRIES = 10  # Giới hạn retry
    MIN_RETRIES = 0

    def __init__(self, logger: StructuredLogger):
        """Initialize validator."""
        self.logger = logger

    def validate_add_job(
        self,
        account_id: Optional[str],
        content: str,
        scheduled_time: datetime,
        priority: JobPriority,
        platform: Platform,
        max_retries: int,
        existing_jobs: Optional[List[ScheduledJob]] = None,
    ) -> ValidationResult:
        """
        Validate job trước khi add.

        Args:
            account_id: Account ID (optional, can be None)
            content: Content
            scheduled_time: Scheduled time
            priority: Priority
            platform: Platform
            max_retries: Max retries
            existing_jobs: Existing jobs để check conflicts

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # 1. Validate account_id (optional - allow None or empty)
        if account_id is not None and account_id != "":
            if not isinstance(account_id, str):
                result.add_error(ValidationSeverity.ERROR, "account_id phải là string")
            elif len(account_id.strip()) == 0:
                result.add_error(
                    ValidationSeverity.ERROR,
                    "account_id không được rỗng (chỉ whitespace)",
                )
            elif len(account_id) > 100:
                result.add_error(
                    ValidationSeverity.WARNING,
                    f"account_id quá dài ({len(account_id)} chars), có thể gây vấn đề",
                )

        # 2. Validate content
        if not content or not isinstance(content, str):
            result.add_error(
                ValidationSeverity.ERROR, "content phải là non-empty string"
            )
        else:
            content_trimmed = content.strip()
            if len(content_trimmed) < self.MIN_CONTENT_LENGTH:
                result.add_error(
                    ValidationSeverity.ERROR,
                    f"content quá ngắn (tối thiểu {self.MIN_CONTENT_LENGTH} ký tự)",
                )
            elif len(content) > self.MAX_CONTENT_LENGTH:
                result.add_error(
                    ValidationSeverity.ERROR,
                    f"content quá dài ({len(content)} chars, tối đa {self.MAX_CONTENT_LENGTH} chars)",
                )

            # Check for suspicious content
            if self._is_suspicious_content(content):
                result.add_error(
                    ValidationSeverity.WARNING,
                    "content có dấu hiệu suspicious (có thể là spam hoặc invalid)",
                )

        # 3. Validate scheduled_time
        if not isinstance(scheduled_time, datetime):
            result.add_error(
                ValidationSeverity.ERROR, "scheduled_time phải là datetime object"
            )
        else:
            # Normalize scheduled_time to UTC for consistent comparison
            scheduled_time_utc = ensure_utc(scheduled_time)
            now = datetime.now(timezone.utc)
            time_diff = scheduled_time_utc - now

            # Check quá khứ
            if time_diff.total_seconds() < self.MAX_SCHEDULE_DAYS_PAST * 86400:
                result.add_error(
                    ValidationSeverity.ERROR,
                    f"scheduled_time quá xa quá khứ (tối đa {abs(self.MAX_SCHEDULE_DAYS_PAST)} ngày)",
                )

            # Check quá tương lai
            if time_diff.days > self.MAX_SCHEDULE_DAYS_AHEAD:
                result.add_error(
                    ValidationSeverity.ERROR,
                    f"scheduled_time quá xa tương lai (tối đa {self.MAX_SCHEDULE_DAYS_AHEAD} ngày)",
                )

            # Warning nếu quá gần (có thể không kịp)
            if 0 < time_diff.total_seconds() < 10:
                result.add_error(
                    ValidationSeverity.WARNING,
                    f"scheduled_time quá gần ({int(time_diff.total_seconds())}s), có thể không kịp xử lý",
                )

        # 4. Validate priority
        if not isinstance(priority, JobPriority):
            result.add_error(
                ValidationSeverity.ERROR, "priority phải là JobPriority enum"
            )

        # 5. Validate platform
        if not isinstance(platform, Platform):
            result.add_error(ValidationSeverity.ERROR, "platform phải là Platform enum")

        # 6. Validate max_retries
        if not isinstance(max_retries, int):
            result.add_error(ValidationSeverity.ERROR, "max_retries phải là integer")
        elif max_retries < self.MIN_RETRIES:
            result.add_error(
                ValidationSeverity.ERROR,
                f"max_retries không được nhỏ hơn {self.MIN_RETRIES}",
            )
        elif max_retries > self.MAX_RETRIES:
            result.add_error(
                ValidationSeverity.WARNING,
                f"max_retries quá lớn ({max_retries}), có thể gây spam retry",
            )

        # 7. Check conflicts với existing jobs
        if existing_jobs:
            conflicts = self._check_schedule_conflicts(
                account_id=account_id,
                scheduled_time=scheduled_time,
                platform=platform,
                existing_jobs=existing_jobs,
            )
            if conflicts:
                result.add_error(
                    ValidationSeverity.WARNING,
                    f"Có {len(conflicts)} jobs khác cùng account/platform trong khoảng thời gian gần ({self.MIN_TIME_BETWEEN_JOBS_SECONDS}s)",
                )

        return result

    def validate_job_state(self, job: ScheduledJob) -> ValidationResult:
        """
        Validate job state (sau khi load từ storage).

        Args:
            job: Job để validate

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # 1. Validate required fields
        if not hasattr(job, "job_id") or not job.job_id:
            result.add_error(ValidationSeverity.ERROR, "job thiếu job_id")

        if not hasattr(job, "account_id") or not job.account_id:
            result.add_error(ValidationSeverity.ERROR, "job thiếu account_id")

        if not hasattr(job, "content") or not job.content:
            result.add_error(ValidationSeverity.ERROR, "job thiếu content")

        if not hasattr(job, "scheduled_time") or not job.scheduled_time:
            result.add_error(ValidationSeverity.ERROR, "job thiếu scheduled_time")

        if not hasattr(job, "status") or not job.status:
            result.add_error(ValidationSeverity.ERROR, "job thiếu status")

        # 2. Validate status consistency
        if hasattr(job, "status"):
            status = job.status

            # COMPLETED jobs phải có completed_at hoặc thread_id
            if status == JobStatus.COMPLETED:
                if not hasattr(job, "completed_at") or not job.completed_at:
                    result.add_error(
                        ValidationSeverity.WARNING, "COMPLETED job thiếu completed_at"
                    )

            # RUNNING jobs phải có started_at
            if status == JobStatus.RUNNING:
                if not hasattr(job, "started_at") or not job.started_at:
                    result.add_error(
                        ValidationSeverity.WARNING,
                        "RUNNING job thiếu started_at (có thể bị stuck)",
                    )

            # FAILED jobs nên có error message
            if status == JobStatus.FAILED:
                if not hasattr(job, "error") or not job.error:
                    result.add_error(
                        ValidationSeverity.INFO, "FAILED job không có error message"
                    )

            # EXPIRED jobs không nên có scheduled_time quá gần
            if status == JobStatus.EXPIRED:
                if hasattr(job, "scheduled_time") and job.scheduled_time:
                    job_scheduled_utc = ensure_utc(job.scheduled_time)
                    now_utc = datetime.now(timezone.utc)
                    time_since = now_utc - job_scheduled_utc
                    if time_since.total_seconds() < 86400:  # Chưa đủ 24h
                        result.add_error(
                            ValidationSeverity.WARNING,
                            "EXPIRED job có scheduled_time chưa đủ 24h (có thể bị đánh dấu nhầm)",
                        )

        # 3. Validate retry_count
        if hasattr(job, "retry_count") and hasattr(job, "max_retries"):
            if job.retry_count > job.max_retries:
                result.add_error(
                    ValidationSeverity.ERROR,
                    f"retry_count ({job.retry_count}) lớn hơn max_retries ({job.max_retries})",
                )

        # 4. Validate timestamps consistency
        if hasattr(job, "created_at") and job.created_at:
            if hasattr(job, "scheduled_time") and job.scheduled_time:
                if job.created_at > job.scheduled_time + timedelta(days=1):
                    result.add_error(
                        ValidationSeverity.WARNING,
                        "created_at sau scheduled_time quá xa (có thể data không nhất quán)",
                    )

        if hasattr(job, "started_at") and job.started_at:
            if hasattr(job, "scheduled_time") and job.scheduled_time:
                if job.started_at < job.scheduled_time - timedelta(hours=1):
                    result.add_error(
                        ValidationSeverity.WARNING,
                        "started_at trước scheduled_time quá xa (có thể data không nhất quán)",
                    )

        if hasattr(job, "completed_at") and job.completed_at:
            if hasattr(job, "started_at") and job.started_at:
                if job.completed_at < job.started_at:
                    result.add_error(
                        ValidationSeverity.ERROR,
                        "completed_at trước started_at (data không hợp lệ)",
                    )

        return result

    def _check_schedule_conflicts(
        self,
        account_id: str,
        scheduled_time: datetime,
        platform: Platform,
        existing_jobs: List[ScheduledJob],
    ) -> List[ScheduledJob]:
        """
        Check conflicts với existing jobs (cùng account/platform trong khoảng thời gian gần).

        Returns:
            List các jobs conflict
        """
        conflicts = []

        for job in existing_jobs:
            # Skip completed/expired/failed jobs
            if job.status in [
                JobStatus.COMPLETED,
                JobStatus.EXPIRED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            ]:
                continue

            # Check cùng account và platform
            if (
                hasattr(job, "account_id")
                and job.account_id == account_id
                and hasattr(job, "platform")
                and job.platform == platform
            ):

                # Check thời gian gần nhau (normalize both to UTC for comparison)
                job_scheduled_utc = ensure_utc(job.scheduled_time)
                scheduled_time_utc = ensure_utc(scheduled_time)
                time_diff = abs(
                    (job_scheduled_utc - scheduled_time_utc).total_seconds()
                )
                if time_diff < self.MIN_TIME_BETWEEN_JOBS_SECONDS:
                    conflicts.append(job)

        return conflicts

    def _is_suspicious_content(self, content: str) -> bool:
        """
        Check content có suspicious không (spam, invalid, etc.).

        Returns:
            True nếu suspicious
        """
        # Check empty hoặc chỉ whitespace
        if not content or not content.strip():
            return True

        # Check quá nhiều ký tự đặc biệt
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        if len(content) > 0 and special_chars / len(content) > 0.5:
            return True

        # Check quá nhiều spaces liên tiếp
        if "  " * 10 in content:
            return True

        # Check chỉ có emoji hoặc ký tự đặc biệt
        if len(content) > 10 and not any(c.isalnum() for c in content):
            return True

        return False
