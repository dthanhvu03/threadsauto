"""
Module: services/scheduler/scheduler.py

Main Scheduler class cho Threads automation.
Quản lý job queue với priority, datetime-based scheduling, và retry policy.
"""

# Standard library
import sys
from pathlib import Path

# Add parent directory to path để có thể import utils modules
# CRITICAL: Phải setup TRƯỚC KHI import bất kỳ module nào từ utils
_parent_dir = Path(__file__).resolve().parent.parent.parent
_parent_dir_str = str(_parent_dir)
if _parent_dir_str not in sys.path:
    sys.path.insert(0, _parent_dir_str)
elif sys.path[0] != _parent_dir_str:
    sys.path.remove(_parent_dir_str)
    sys.path.insert(0, _parent_dir_str)

import asyncio
from datetime import datetime
from typing import Optional, Dict, Callable, Any

# Local - Import các modules khác TRƯỚC utils
from services.logger import StructuredLogger
from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform

# Import storage TRƯỚC utils để đảm bảo storage cũng có sys.path setup
from services.scheduler.storage import JobStorage
from services.scheduler.storage.factory import create_job_storage
from services.scheduler.storage.base import JobStorageBase
from services.scheduler.recovery import JobRecovery
from services.scheduler.job_manager import JobManager
from services.scheduler.execution import JobExecutor

# Import utils SAU KHI đã import tất cả các modules khác
from utils.exception_utils import (
    safe_get_exception_type_name
)


class Scheduler:
    """
    Scheduler cho Threads automation.
    
    Quản lý job queue với:
    - Priority-based scheduling
    - Datetime-based execution
    - Retry policy với exponential backoff
    - Dead job handling
    - Expired job skipping
    """
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        logger: Optional[StructuredLogger] = None,
        storage: Optional[JobStorageBase] = None,
        storage_type: Optional[str] = None,  # None = auto-detect from config
        # MySQL parameters (if storage_type="mysql", None = load from config)
        mysql_host: Optional[str] = None,
        mysql_port: Optional[int] = None,
        mysql_user: Optional[str] = None,
        mysql_password: Optional[str] = None,
        mysql_database: Optional[str] = None
    ):
        """
        Khởi tạo scheduler.
        
        Args:
            storage_dir: Thư mục lưu jobs theo ngày (mặc định: ./jobs, chỉ dùng cho JSON storage)
            logger: Instance structured logger (tùy chọn)
            storage: JobStorageBase instance (nếu provided, sẽ dùng instance này thay vì tạo mới)
            storage_type: Storage type ("json" or "mysql", None = auto-load from config)
            mysql_host: MySQL host (None = auto-load from config)
            mysql_port: MySQL port (None = auto-load from config)
            mysql_user: MySQL user (None = auto-load from config)
            mysql_password: MySQL password (None = auto-load from config)
            mysql_database: Database name (None = auto-load from config)
        """
        self.storage_dir = storage_dir or Path("./jobs")
        self.logger = logger or StructuredLogger(name="scheduler")
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._last_save_time = datetime.min  # Track save time để tránh reload ngay sau save
        
        # Load scheduler config để lấy overdue_threshold_hours
        self.overdue_threshold_hours = None
        try:
            from config.storage import load_config
            config = load_config()
            if config and config.scheduler:
                self.overdue_threshold_hours = config.scheduler.overdue_threshold_hours
                self.logger.log_step(
                    step="INIT_SCHEDULER",
                    result="INFO",
                    note=f"Loaded overdue_threshold_hours: {self.overdue_threshold_hours}"
                )
        except Exception as e:
            # Log warning nhưng không fail initialization
            self.logger.log_step(
                step="INIT_SCHEDULER",
                result="WARNING",
                error=f"Failed to load scheduler config: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
        
        # Load storage config từ environment/config nếu parameters không được provide
        if storage_type is None or mysql_password is None or mysql_password == "":
            try:
                from config.storage_config_loader import get_storage_config_from_env
                storage_config = get_storage_config_from_env()
                
                # Override với config values nếu not provided
                if storage_type is None:
                    storage_type = storage_config.storage_type
                if mysql_host is None:
                    mysql_host = storage_config.mysql.host
                if mysql_port is None:
                    mysql_port = storage_config.mysql.port
                if mysql_user is None:
                    mysql_user = storage_config.mysql.user
                if mysql_password is None or mysql_password == "":
                    mysql_password = storage_config.mysql.password
                if mysql_database is None:
                    mysql_database = storage_config.mysql.database
                
                self.logger.log_step(
                    step="INIT_SCHEDULER",
                    result="INFO",
                    note=f"Loaded storage config from environment: type={storage_type}"
                )
            except Exception as e:
                self.logger.log_step(
                    step="INIT_SCHEDULER",
                    result="WARNING",
                    error=f"Failed to load storage config: {str(e)}, using defaults",
                    error_type=type(e).__name__
                )
                # Use defaults if config loading fails
                if storage_type is None:
                    storage_type = "mysql"
                if mysql_host is None:
                    mysql_host = "localhost"
                if mysql_port is None:
                    mysql_port = 3306
                if mysql_user is None:
                    mysql_user = "threads_user"
                if mysql_password is None or mysql_password == "":
                    mysql_password = ""  # Will fail connection but at least we tried
                if mysql_database is None:
                    mysql_database = "threads_analytics"
        
        # Initialize storage first với error handling
        try:
            if storage is not None:
                # Use provided storage instance
                self.storage = storage
                self.logger.log_step(
                    step="INIT_SCHEDULER",
                    result="INFO",
                    note=f"Using provided storage instance: {type(storage).__name__}"
                )
            else:
                # Create storage using factory
                self.storage = create_job_storage(
                    storage_type=storage_type,
                    storage_dir=self.storage_dir,
                    logger=self.logger,
                    mysql_host=mysql_host,
                    mysql_port=mysql_port,
                    mysql_user=mysql_user,
                    mysql_password=mysql_password or "",  # Ensure string
                    mysql_database=mysql_database
                )
                self.logger.log_step(
                    step="INIT_SCHEDULER",
                    result="INFO",
                    note=f"Created storage using factory: {type(self.storage).__name__}"
                )
        except Exception as e:
            self.logger.log_step(
                step="INIT_SCHEDULER",
                result="ERROR",
                error=f"Failed to initialize storage: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            raise RuntimeError(f"Failed to initialize scheduler storage: {str(e)}") from e
        
        # Load jobs từ tất cả các file TRƯỚC KHI tạo components
        # Điều này đảm bảo self.jobs được populate trước
        try:
            self._load_jobs()
        except Exception as e:
            self.logger.log_step(
                step="INIT_SCHEDULER",
                result="WARNING",
                error=f"Failed to load jobs: {str(e)}, starting with empty jobs",
                error_type=safe_get_exception_type_name(e)
            )
            # Continue with empty jobs dict
            self.jobs = {}
        
        # Initialize components với self.jobs đã được load
        try:
            self.recovery = JobRecovery(self.logger)
        except Exception as e:
            self.logger.log_step(
                step="INIT_SCHEDULER",
                result="ERROR",
                error=f"Failed to initialize recovery: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            raise RuntimeError(f"Failed to initialize scheduler recovery: {str(e)}") from e
        
        try:
            self.job_manager = JobManager(self.jobs, self.logger)
        except Exception as e:
            self.logger.log_step(
                step="INIT_SCHEDULER",
                result="ERROR",
                error=f"Failed to initialize job manager: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            raise RuntimeError(f"Failed to initialize scheduler job manager: {str(e)}") from e
        
        try:
            self.executor = JobExecutor(
                self.jobs,
                self.logger,
                self._save_jobs
            )
        except Exception as e:
            self.logger.log_step(
                step="INIT_SCHEDULER",
                result="ERROR",
                error=f"Failed to initialize executor: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            raise RuntimeError(f"Failed to initialize scheduler executor: {str(e)}") from e
        
        # Recover TẤT CẢ jobs RUNNING khi scheduler start (do crash/mất mạng)
        # Không chỉ stuck > 30 phút, mà TẤT CẢ jobs RUNNING đều cần recover
        try:
            self.recover_all_running_jobs()
        except Exception as e:
            self.logger.log_step(
                step="INIT_SCHEDULER",
                result="WARNING",
                error=f"Failed to recover running jobs: {str(e)}, continuing anyway",
                error_type=safe_get_exception_type_name(e)
            )
            # Continue even if recovery fails
    
    def reload_jobs(self, force: bool = False) -> None:
        """
        Reload jobs từ storage (public method).
        
        Args:
            force: Nếu True, reload ngay cả khi vừa save (< 2 giây)
                   Nếu False, skip reload nếu vừa save để tránh race condition
        
        QUAN TRỌNG: Method này được gọi từ UI/CLI để đảm bảo jobs được cập nhật realtime.
        """
        try:
            # BẢO VỆ: Không reload nếu vừa save (< 2 giây) trừ khi force=True
            if not force:
                time_since_save = (datetime.now() - self._last_save_time).total_seconds()
                if time_since_save < 2:
                    self.logger.log_step(
                        step="RELOAD_JOBS",
                        result="SKIPPED",
                        note=f"Skipped reload (just saved {time_since_save:.2f}s ago, use force=True to override)",
                        time_since_save=time_since_save
                    )
                    return
            
            # Reload jobs từ storage
            self._load_jobs(force=force)
            self.logger.log_step(
                step="RELOAD_JOBS",
                result="SUCCESS",
                total_jobs=len(self.jobs),
                note="Jobs reloaded from storage (realtime update)"
            )
        except Exception as e:
            self.logger.log_step(
                step="RELOAD_JOBS",
                result="ERROR",
                error=f"Failed to reload jobs: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            # Không raise để UI/CLI vẫn có thể hiển thị jobs cũ
            # Log error nhưng không fail operation
    
    def _load_jobs(self, force: bool = False) -> None:
        """
        Load jobs từ storage với merge strategy thông minh.
        
        Không overwrite jobs đang RUNNING hoặc đã COMPLETED trong memory
        bằng jobs từ storage (tránh mất state hiện tại).
        
        Args:
            force: Nếu True, chỉ preserve RUNNING jobs, remove jobs không có trong storage
                   Nếu False, preserve RUNNING, SCHEDULED, PENDING jobs không có trong storage
        """
        try:
            jobs_from_storage = self.storage.load_jobs()
            
            # Merge strategy: Bảo vệ jobs RUNNING và COMPLETED
            # Nếu job trong memory là RUNNING hoặc COMPLETED, không overwrite bằng job từ storage
            # JobStatus đã được import ở đầu file
            
            merged_jobs = {}
            
            # BƯỚC 1: Thêm jobs từ storage, nhưng kiểm tra COMPLETED jobs từ storage có priority cao hơn
            for job_id, job_from_storage in jobs_from_storage.items():
                existing_job = self.jobs.get(job_id)
                storage_status = job_from_storage.status
                
                if existing_job:
                    # Nếu job đã tồn tại trong memory
                    existing_status = existing_job.status
                    
                    # BẢO VỆ 1: Storage có COMPLETED, memory có SCHEDULED → Ưu tiên COMPLETED từ storage
                    if storage_status == JobStatus.COMPLETED and existing_status != JobStatus.COMPLETED:
                        # Job đã COMPLETED trong storage, không thể chạy lại
                        merged_jobs[job_id] = job_from_storage
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="WARNING",
                            note=f"Job {job_id} was COMPLETED in storage but has different status in memory. Restoring COMPLETED status.",
                            job_id=job_id,
                            memory_status=existing_status.value if hasattr(existing_status, 'value') else str(existing_status),
                            storage_status=storage_status.value if hasattr(storage_status, 'value') else str(storage_status)
                        )
                        continue
                    
                    # BẢO VỆ 2: Không overwrite jobs RUNNING trong memory
                    if existing_status == JobStatus.RUNNING:
                        # Giữ job RUNNING trong memory, không overwrite
                        merged_jobs[job_id] = existing_job
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="INFO",
                            note=f"Preserving RUNNING job {job_id} from memory (not overwriting with storage)",
                            job_id=job_id
                        )
                        continue
                    
                    # BẢO VỆ 3: Không overwrite jobs COMPLETED trong memory (nếu storage không có COMPLETED)
                    if existing_status == JobStatus.COMPLETED:
                        # Giữ job COMPLETED trong memory, không overwrite
                        merged_jobs[job_id] = existing_job
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="INFO",
                            note=f"Preserving COMPLETED job {job_id} from memory (not overwriting with storage)",
                            job_id=job_id
                        )
                        continue
                
                # BẢO VỆ 4: Thêm COMPLETED jobs từ storage (ngay cả khi không có trong memory)
                if storage_status == JobStatus.COMPLETED:
                    merged_jobs[job_id] = job_from_storage
                    self.logger.log_step(
                        step="LOAD_JOBS",
                        result="INFO",
                        note=f"Loading COMPLETED job {job_id} from storage",
                        job_id=job_id
                    )
                    continue
                
                # Các trường hợp khác: thêm job từ storage
                merged_jobs[job_id] = job_from_storage
            
            # Thêm các jobs còn lại trong memory (nếu có jobs mới được tạo nhưng chưa lưu)
            # CHỈ giữ jobs RUNNING hoặc jobs mới chưa lưu (SCHEDULED/PENDING) - TRỪ KHI force=True
            # KHÔNG giữ jobs đã bị xóa khỏi storage (trừ khi đang RUNNING)
            jobs_preserved_count = 0
            jobs_removed_from_memory_count = 0
            for job_id, job in self.jobs.items():
                if job_id not in merged_jobs:
                    # Job trong memory nhưng không có trong storage
                    if job.status == JobStatus.RUNNING:
                        # Giữ job RUNNING (đang chạy, không thể xóa) - luôn preserve
                        merged_jobs[job_id] = job
                        jobs_preserved_count += 1
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="INFO",
                            note=f"Keeping RUNNING job {job_id} from memory (not in storage, but running)",
                            job_id=job_id
                        )
                    elif not force and job.status in [JobStatus.SCHEDULED, JobStatus.PENDING]:
                        # Nếu force=False: Có thể là job mới chưa lưu, giữ lại
                        # Nếu force=True: Job đã bị xóa trên DB, KHÔNG giữ lại (sẽ bị remove ở else block)
                        merged_jobs[job_id] = job
                        jobs_preserved_count += 1
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="INFO",
                            note=f"Keeping new job {job_id} from memory (not yet in storage, force={force})",
                            job_id=job_id,
                            force=force
                        )
                    else:
                        # Job không có trong storage và:
                        # - Không phải RUNNING
                        # - VÀ (force=True HOẶC không phải SCHEDULED/PENDING)
                        # => Đã bị xóa khỏi database, KHÔNG giữ lại
                        jobs_removed_from_memory_count += 1
                        self.logger.log_step(
                            step="LOAD_JOBS",
                            result="INFO",
                            note=f"Removing job {job_id} from memory (not in storage, force={force}, status={job.status})",
                            job_id=job_id,
                            status=job.status.value if hasattr(job.status, 'value') else str(job.status),
                            force=force
                        )
            
            # CRITICAL: Update dict in-place để giữ nguyên reference
            # Nếu dùng self.jobs = merged_jobs, job_manager.jobs vẫn trỏ đến dict cũ
            # và remove_job sẽ xóa khỏi dict cũ trong khi scheduler.jobs trỏ đến dict mới
            self.jobs.clear()
            self.jobs.update(merged_jobs)
            
            # Optimize: Single pass filter thay vì multiple list comprehensions (fix N+1 filter pattern)
            running_count = 0
            completed_count = 0
            for j in self.jobs.values():
                if j.status == JobStatus.RUNNING:
                    running_count += 1
                elif j.status == JobStatus.COMPLETED:
                    completed_count += 1
            
            self.logger.log_step(
                step="LOAD_JOBS",
                result="SUCCESS",
                total_jobs=len(self.jobs),
                from_storage=len(jobs_from_storage),
                preserved_running=running_count,
                preserved_completed=completed_count
            )
        except Exception as e:
            self.logger.log_step(
                step="LOAD_JOBS",
                result="ERROR",
                error=f"Failed to load jobs: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            # Re-raise để caller có thể handle
            raise
    
    def _save_jobs(self) -> None:
        """
        Save jobs to storage.
        
        QUAN TRỌNG: Method này được gọi từ nhiều nơi để đảm bảo jobs được persist.
        - Sau khi job completed (trong run_job)
        - Trong finally block của run_job
        - Khi scheduler stop
        - Khi cleanup/recover jobs
        """
        try:
            # DEBUG: Log jobs count before save
            jobs_count_before = len(self.jobs)
            # CRITICAL: Log reference IDs để debug dict reference issues
            jobs_dict_id = id(self.jobs)
            job_manager_dict_id = id(self.job_manager.jobs) if hasattr(self, 'job_manager') and hasattr(self.job_manager, 'jobs') else None
            executor_dict_id = id(self.executor.jobs) if hasattr(self, 'executor') and hasattr(self.executor, 'jobs') else None
            
            self.logger.log_step(
                step="SAVE_JOBS_START",
                result="INFO",
                note=f"Starting save, jobs in scheduler.jobs: {jobs_count_before}",
                jobs_count=jobs_count_before,
                jobs_dict_id=jobs_dict_id,
                job_manager_dict_id=job_manager_dict_id,
                executor_dict_id=executor_dict_id,
                same_ref_job_manager=(jobs_dict_id == job_manager_dict_id) if job_manager_dict_id else None,
                same_ref_executor=(jobs_dict_id == executor_dict_id) if executor_dict_id else None
            )
            
            # Đảm bảo jobs dict được sync với executor
            # Executor có thể đã update job status nhưng chưa sync với scheduler.jobs
            if hasattr(self, 'executor') and hasattr(self.executor, 'jobs'):
                # Sync jobs từ executor về scheduler (executor là source of truth)
                # CHỈ UPDATE jobs đã có, KHÔNG ADD jobs mới (executor không thể có jobs mới)
                for job_id, job in self.executor.jobs.items():
                    if job_id in self.jobs:
                        # Update job trong scheduler.jobs với job từ executor
                        self.jobs[job_id] = job
            
            # DEBUG: Log jobs count after executor sync
            jobs_count_after_sync = len(self.jobs)
            if jobs_count_after_sync != jobs_count_before:
                self.logger.log_step(
                    step="SAVE_JOBS_SYNC",
                    result="INFO",
                    note=f"Jobs count changed after executor sync: {jobs_count_before} → {jobs_count_after_sync}",
                    before=jobs_count_before,
                    after=jobs_count_after_sync
                )
            
            self.storage.save_jobs(self.jobs)
            # Track save time để tránh reload ngay sau save
            self._last_save_time = datetime.now()
            
            # Optimize: Single pass filter thay vì multiple list comprehensions (fix N+1 filter pattern)
            completed_count = 0
            running_count = 0
            for j in self.jobs.values():
                if j.status == JobStatus.COMPLETED:
                    completed_count += 1
                elif j.status == JobStatus.RUNNING:
                    running_count += 1
            
            self.logger.log_step(
                step="SAVE_JOBS",
                result="SUCCESS",
                jobs_count=len(self.jobs),
                completed_count=completed_count,
                running_count=running_count
            )
        except Exception as e:
            self.logger.log_step(
                step="SAVE_JOBS",
                result="ERROR",
                error=f"Failed to save jobs: {str(e)}",
                error_type=safe_get_exception_type_name(e),
                jobs_count=len(self.jobs) if hasattr(self, 'jobs') else 0
            )
            # Re-raise để caller có thể handle (storage errors should be handled)
            raise
    
    # Job management methods (delegate to JobManager)
    def add_job(
        self,
        account_id: Optional[str],
        content: str,
        scheduled_time: datetime,
        priority: JobPriority = JobPriority.NORMAL,
        platform: Platform = Platform.THREADS,
        max_retries: int = 3,
        link_aff: Optional[str] = None
    ) -> str:
        """Thêm job mới vào scheduler."""
        return self.job_manager.add_job(
            account_id=account_id,
            content=content,
            scheduled_time=scheduled_time,
            priority=priority,
            platform=platform,
            max_retries=max_retries,
            save_callback=self._save_jobs,
            link_aff=link_aff
        )
    
    def remove_job(self, job_id: str) -> bool:
        """Xóa job khỏi scheduler."""
        return self.job_manager.remove_job(
            job_id=job_id,
            save_callback=self._save_jobs
        )
    
    def list_jobs(
        self,
        account_id: Optional[str] = None,
        status: Optional[JobStatus] = None
    ) -> list:
        """Liệt kê jobs."""
        return self.job_manager.list_jobs(account_id=account_id, status=status)
    
    def get_ready_jobs(self) -> list:
        """Lấy danh sách jobs sẵn sàng chạy."""
        return self.job_manager.get_ready_jobs()
    
    def get_active_jobs(self) -> list:
        """
        Lấy danh sách active jobs (PENDING, SCHEDULED, RUNNING).
        
        Returns:
            List of ScheduledJob objects với status PENDING, SCHEDULED, hoặc RUNNING
        """
        active_statuses = [JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.RUNNING]
        active_jobs = []
        for job in self.jobs.values():
            if hasattr(job, 'status') and job.status in active_statuses:
                active_jobs.append(job)
        return active_jobs
    
    def cleanup_expired_jobs(self) -> int:
        """Xóa các jobs đã hết hạn."""
        return self.job_manager.cleanup_expired_jobs(save_callback=self._save_jobs)
    
    # Recovery methods (delegate to JobRecovery)
    def recover_stuck_jobs(self, max_running_minutes: int = 30) -> int:
        """Recover các jobs bị stuck ở trạng thái RUNNING."""
        try:
            count = self.recovery.recover_stuck_jobs(
                self.jobs,
                max_running_minutes=max_running_minutes
            )
            if count > 0:
                try:
                    self._save_jobs()
                except Exception as e:
                    self.logger.log_step(
                        step="RECOVER_STUCK_JOBS",
                        result="WARNING",
                        error=f"Failed to save after recovery: {str(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
            return count
        except Exception as e:
            self.logger.log_step(
                step="RECOVER_STUCK_JOBS",
                result="ERROR",
                error=f"Failed to recover stuck jobs: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            return 0
    
    def recover_all_running_jobs(self) -> int:
        """Recover TẤT CẢ jobs đang ở trạng thái RUNNING khi scheduler start."""
        try:
            count = self.recovery.recover_all_running_jobs(self.jobs)
            if count > 0:
                try:
                    self._save_jobs()
                except Exception as e:
                    self.logger.log_step(
                        step="RECOVER_ALL_RUNNING_JOBS",
                        result="WARNING",
                        error=f"Failed to save after recovery: {str(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
            return count
        except Exception as e:
            self.logger.log_step(
                step="RECOVER_ALL_RUNNING_JOBS",
                result="ERROR",
                error=f"Failed to recover running jobs: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            return 0
    
    # Execution methods
    async def _scheduler_loop(
        self,
        post_callback_factory: Callable[[Platform], Callable[[str, str], Any]]
    ) -> None:
        """Vòng lặp scheduler chính."""
        await self.executor.scheduler_loop(
            post_callback_factory=post_callback_factory,
            running_flag_getter=lambda: self.running,
            running_flag_setter=lambda value: setattr(self, 'running', value),
            get_ready_jobs=self.get_ready_jobs,
            cleanup_expired_jobs=self.cleanup_expired_jobs,
            recover_stuck_jobs=self.recover_stuck_jobs,
            reload_jobs_callback=self._load_jobs,  # Reload jobs để pick up jobs mới
            get_last_save_time=lambda: self._last_save_time  # Pass save time để check delay
        )
    
    def start(
        self,
        post_callback_factory: Callable[[Platform], Callable[[str, str], Any]]
    ) -> None:
        """
        Bắt đầu scheduler.
        
        Args:
            post_callback_factory: Factory function để lấy callback dựa trên platform
        """
        # Atomic check-and-set to prevent race conditions
        if self.running:
            self.logger.log_step(
                step="START_SCHEDULER",
                result="WARNING",
                note="Scheduler already running"
            )
            return
        
        try:
            # Validate post_callback_factory
            if not callable(post_callback_factory):
                raise ValueError("post_callback_factory must be callable")
            
            # Atomic state change: set running flag and create task atomically
            # This prevents multiple start() calls from creating multiple tasks
            try:
                self._task = asyncio.create_task(self._scheduler_loop(post_callback_factory))
                # Only set running flag after task is successfully created
                self.running = True
            except (RuntimeError, ValueError, TypeError) as e:
                # Reset running flag if task creation fails
                self.running = False
                self.logger.log_step(
                    step="START_SCHEDULER",
                    result="ERROR",
                    error=f"Failed to create scheduler task: {str(e)}",
                    error_type=safe_get_exception_type_name(e)
                )
                raise RuntimeError(f"Failed to start scheduler: {str(e)}") from e
            
            self.logger.log_step(
                step="START_SCHEDULER",
                result="SUCCESS",
                jobs_count=len(self.jobs)
            )
        except (ValueError, RuntimeError) as e:
            # Only catch expected exceptions, let others propagate
            self.logger.log_step(
                step="START_SCHEDULER",
                result="ERROR",
                error=f"Failed to start scheduler: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
            raise
    
    async def stop(self) -> None:
        """Dừng scheduler."""
        # Log stop request (luôn log, kể cả khi đã stopped)
        self.logger.log_step(
            step="STOP_SCHEDULER",
            result="INFO",
            note=f"Stop requested, running: {self.running}, has_task: {self._task is not None}"
        )
        # Force flush log handlers để đảm bảo log được ghi ngay
        try:
            for handler in self.logger.logger.handlers:
                try:
                    handler.flush()
                except Exception:
                    # Skip handlers that fail to flush
                    pass
        except Exception:
            # Ignore errors when flushing handlers
            pass
        
        # Set running = False ngay lập tức để loop có thể exit
        was_running = self.running
        self.running = False
        
        if not was_running and not self._task:
            # Đã stopped và không có task
            self.logger.log_step(
                step="STOP_SCHEDULER",
                result="INFO",
                note="Scheduler already stopped"
            )
            return
        
        if self._task:
            # Cancel task
            self._task.cancel()
            try:
                # Wait for task to finish (will raise CancelledError)
                await self._task
            except asyncio.CancelledError:
                # Task đã được cancel thành công
                # Log trước khi raise để đảm bảo log được ghi
                self.logger.log_step(
                    step="STOP_SCHEDULER",
                    result="SUCCESS",
                    note="Scheduler task cancelled successfully"
                )
                # Force flush log handlers để đảm bảo log được ghi ngay
                try:
                    for handler in self.logger.logger.handlers:
                        try:
                            handler.flush()
                        except Exception:
                            pass
                except Exception:
                    pass
                # Save jobs trước khi raise với error handling
                try:
                    self._save_jobs()
                except Exception as save_error:
                    self.logger.log_step(
                        step="STOP_SCHEDULER",
                        result="WARNING",
                        error=f"Failed to save jobs on cancel: {str(save_error)}",
                        error_type=safe_get_exception_type_name(save_error)
                    )
                # Re-raise để đảm bảo cancellation được propagate
                raise
            except Exception as e:
                # Lỗi khác khi await task
                self.logger.log_step(
                    step="STOP_SCHEDULER",
                    result="ERROR",
                    error=f"Error awaiting task: {str(e)}"
                )
                raise
        
        # Save jobs trước khi stop với error handling
        try:
            self._save_jobs()
        except Exception as e:
            self.logger.log_step(
                step="STOP_SCHEDULER",
                result="WARNING",
                error=f"Failed to save jobs on stop: {str(e)}",
                error_type=safe_get_exception_type_name(e)
            )
        
        # Log success nếu không có task hoặc task đã finish
        if not self._task:
            self.logger.log_step(
                step="STOP_SCHEDULER",
                result="SUCCESS",
                note="Scheduler stopped (no task to cancel)"
            )

