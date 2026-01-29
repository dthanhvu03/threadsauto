"""
Module: services/scheduler/storage.py

Storage logic cho scheduler: load/save jobs từ file.
"""

# Standard library
import sys
from pathlib import Path

# Add parent directory to path để có thể import utils modules
# Điều này đảm bảo Python có thể tìm thấy utils.exception_utils
_parent_dir = Path(__file__).resolve().parent.parent.parent
_parent_dir_str = str(_parent_dir)
if _parent_dir_str not in sys.path:
    sys.path.insert(0, _parent_dir_str)
elif sys.path[0] != _parent_dir_str:
    sys.path.remove(_parent_dir_str)
    sys.path.insert(0, _parent_dir_str)

import json
from datetime import datetime
from typing import List, Dict, Optional

# Local
from services.logger import StructuredLogger
from services.exceptions import StorageError
from services.scheduler.models import ScheduledJob, JobStatus
from services.scheduler.storage.base import JobStorageBase
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message
)


class JobStorage(JobStorageBase):
    """
    Storage manager cho jobs.
    
    Quản lý load/save jobs từ các file theo structure mới:
    - jobs_YYYY-MM-DD_{status}.json (structure mới)
    - jobs_YYYY-MM-DD.json (structure cũ - backward compatible)
    
    Xem thêm: docs/jobs_structure_by_status.md
    """
    
    def __init__(
        self,
        storage_dir: Path,
        logger: StructuredLogger
    ):
        """
        Khởi tạo storage manager.
        
        Args:
            storage_dir: Thư mục lưu jobs
            logger: Logger instance
        """
        # Initialize base class
        super().__init__(logger)
        
        self.storage_dir = storage_dir
        
        # Tạo thư mục storage nếu chưa có với error handling
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            self.logger.log_step(
                step="INIT_STORAGE",
                result="ERROR",
                error=f"Permission denied creating storage directory: {str(e)}",
                error_type="PermissionError",
                storage_dir=str(self.storage_dir)
            )
            raise StorageError(f"Permission denied creating storage directory: {str(e)}") from e
        except OSError as e:
            self.logger.log_step(
                step="INIT_STORAGE",
                result="ERROR",
                error=f"OS error creating storage directory: {str(e)}",
                error_type="OSError",
                storage_dir=str(self.storage_dir)
            )
            raise StorageError(f"OS error creating storage directory: {str(e)}") from e
    
    def _get_job_file_path(self, date: datetime, status: JobStatus = None) -> Path:
        """
        Lấy đường dẫn file job cho một ngày và status cụ thể.
        
        Args:
            date: Ngày để lấy file path
            status: Status của job (nếu None, dùng structure cũ: jobs_YYYY-MM-DD.json)
        
        Returns:
            Path đến file job:
            - Structure mới: jobs/YYYY-MM-DD_{status}.json
            - Structure cũ: jobs/YYYY-MM-DD.json (nếu status=None)
        """
        try:
            if not isinstance(date, datetime):
                raise TypeError(f"date must be datetime object, got {type(date)}")
            date_str = date.strftime("%Y-%m-%d")
            
            if status:
                # Structure mới: jobs_YYYY-MM-DD_{status}.json
                return self.storage_dir / f"jobs_{date_str}_{status.value}.json"
            else:
                # Structure cũ: jobs_YYYY-MM-DD.json (backward compatible)
                return self.storage_dir / f"jobs_{date_str}.json"
        except (AttributeError, TypeError) as e:
            self.logger.log_step(
                step="GET_JOB_FILE_PATH",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e)
            )
            raise ValueError(f"Invalid date parameter: {safe_get_exception_message(e)}") from e
    
    def _parse_job_filename(self, job_file: Path) -> tuple[str, str]:
        """
        Parse job filename để extract date và status.
        
        Hỗ trợ cả structure cũ (jobs_YYYY-MM-DD.json) và structure mới (jobs_YYYY-MM-DD_{status}.json).
        
        Args:
            job_file: Path đến file job
        
        Returns:
            Tuple (date_str, status_str):
            - date_str: "YYYY-MM-DD"
            - status_str: status từ filename hoặc "unknown" nếu structure cũ
        
        Raises:
            ValueError: Nếu filename không đúng format
        """
        try:
            stem = job_file.stem  # jobs_YYYY-MM-DD_{status} hoặc jobs_YYYY-MM-DD
            date_str = stem.replace("jobs_", "")
            
            # Nếu có format mới với status (YYYY-MM-DD_{status}), extract cả date và status
            if "_" in date_str:
                parts = date_str.split("_", 1)  # Split chỉ lần đầu tiên
                date_str = parts[0]
                status_str = parts[1] if len(parts) > 1 else "unknown"
            else:
                # Structure cũ: không có status trong filename
                status_str = "unknown"
            
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
            
            return (date_str, status_str)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid job filename format: {job_file.name}") from e
    
    def _get_job_file_key(self, job: ScheduledJob) -> tuple[str, str]:
        """
        Tính toán (date_key, status_key) để xác định file đúng cho job.
        
        Logic:
        - Nếu job có completed_at → (completed_at_date, "completed")
        - Nếu job status = RUNNING → (scheduled_time_date, "running")
        - Các trường hợp khác → (scheduled_time_date, status.value)
        
        Args:
            job: ScheduledJob instance
        
        Returns:
            Tuple (date_key, status_key):
            - date_key: "YYYY-MM-DD"
            - status_key: status string (e.g., "completed", "running", "scheduled")
        """
        if job.completed_at:
            date_key = job.completed_at.strftime("%Y-%m-%d")
            status_key = "completed"  # Force completed nếu có completed_at
        elif job.status == JobStatus.RUNNING:
            date_key = job.scheduled_time.strftime("%Y-%m-%d")
            status_key = "running"
        else:
            date_key = job.scheduled_time.strftime("%Y-%m-%d")
            status_key = job.status.value  # scheduled, pending, failed, expired, cancelled
        
        return (date_key, status_key)
    
    def _resolve_duplicate_job(
        self,
        existing_job: ScheduledJob,
        new_job: ScheduledJob,
        source_file: str
    ) -> ScheduledJob:
        """
        Resolve duplicate job khi load từ nhiều files.
        
        Logic:
        - Ưu tiên COMPLETED (không bao giờ overwrite COMPLETED bằng SCHEDULED)
        - Ưu tiên RUNNING (không overwrite RUNNING bằng SCHEDULED)
        - Nếu cả 2 đều SCHEDULED/PENDING, dùng job từ file mới hơn
        
        Args:
            existing_job: Job đã có trong memory
            new_job: Job mới từ file
            source_file: Tên file nguồn (để log)
        
        Returns:
            Job được chọn (existing hoặc new)
        """
        existing_status = existing_job.status
        new_status = new_job.status
        
        # BẢO VỆ: Không overwrite COMPLETED bằng bất kỳ status nào khác
        if existing_status == JobStatus.COMPLETED:
            # Giữ job COMPLETED, bỏ qua job mới
            self.logger.log_step(
                step="LOAD_JOBS",
                result="INFO",
                note=f"Preserving COMPLETED job {existing_job.job_id} (ignoring duplicate from {source_file})",
                job_file=source_file,
                existing_status=existing_status.value if hasattr(existing_status, 'value') else str(existing_status),
                new_status=new_status.value if hasattr(new_status, 'value') else str(new_status)
            )
            return existing_job
        
        # BẢO VỆ: Nếu job mới là COMPLETED, luôn dùng job mới (restore COMPLETED)
        if new_status == JobStatus.COMPLETED:
            self.logger.log_step(
                step="LOAD_JOBS",
                result="WARNING",
                note=f"Restoring COMPLETED job {new_job.job_id} from {source_file} (was {existing_status.value if hasattr(existing_status, 'value') else str(existing_status)} in memory)",
                job_file=source_file,
                old_status=existing_status.value if hasattr(existing_status, 'value') else str(existing_status)
            )
            return new_job
        
        # BẢO VỆ: Không overwrite RUNNING bằng SCHEDULED/PENDING
        if existing_status == JobStatus.RUNNING and new_status in [JobStatus.SCHEDULED, JobStatus.PENDING]:
            # Giữ job RUNNING, bỏ qua job mới
            self.logger.log_step(
                step="LOAD_JOBS",
                result="INFO",
                note=f"Preserving RUNNING job {existing_job.job_id} (ignoring duplicate from {source_file})",
                job_file=source_file,
                existing_status=existing_status.value if hasattr(existing_status, 'value') else str(existing_status),
                new_status=new_status.value if hasattr(new_status, 'value') else str(new_status)
            )
            return existing_job
        
        # Các trường hợp khác: update bằng job từ file mới hơn
        self.logger.log_step(
            step="LOAD_JOBS",
            result="INFO",
            note=f"Updating job {new_job.job_id} from {source_file}",
            job_file=source_file,
            old_status=existing_status.value if hasattr(existing_status, 'value') else str(existing_status),
            new_status=new_status.value if hasattr(new_status, 'value') else str(new_status)
        )
        return new_job
    
    def _get_all_job_files(self) -> List[Path]:
        """
        Lấy danh sách tất cả các file job.
        
        Hỗ trợ cả structure cũ (jobs_YYYY-MM-DD.json) và structure mới (jobs_YYYY-MM-DD_{status}.json).
        
        Returns:
            List các Path đến các file job
        """
        try:
            if not self.storage_dir.exists():
                return []
            
            # Tìm tất cả file jobs_*.json (cả structure cũ và mới)
            try:
                job_files = list(self.storage_dir.glob("jobs_*.json"))
                # Loại bỏ temp files và backup files
                job_files = [
                    f for f in job_files 
                    if not f.name.endswith('.tmp') 
                    and not f.name.startswith('backup_')
                ]
            except Exception as e:
                self.logger.log_step(
                    step="GET_ALL_JOB_FILES",
                    result="WARNING",
                    error=safe_get_exception_message(e),
                    error_type=safe_get_exception_type_name(e)
                )
                return []
            
            # Sort theo tên file DESC (file mới hơn trước) để ưu tiên job từ file mới hơn khi có duplicate
            try:
                job_files.sort(reverse=True)
            except Exception as e:
                self.logger.log_step(
                    step="GET_ALL_JOB_FILES",
                    result="WARNING",
                    error=safe_get_exception_message(e),
                    error_type=safe_get_exception_type_name(e)
                )
                # Return unsorted list if sort fails
            
            return job_files
        except Exception as e:
            self.logger.log_step(
                step="GET_ALL_JOB_FILES",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e)
            )
            return []
    
    def load_jobs(self) -> Dict[str, ScheduledJob]:
        """
        Load jobs từ tất cả các file job theo ngày.
        
        Returns:
            Dict mapping job_id -> ScheduledJob
        """
        job_files = self._get_all_job_files()
        
        if not job_files:
            self.logger.log_step(
                step="LOAD_JOBS",
                result="INFO",
                note="No job files found, starting with empty job list",
                storage_dir=str(self.storage_dir)
            )
            return {}
        
        jobs: Dict[str, ScheduledJob] = {}
        loaded_count = 0
        failed_count = 0
        files_processed = 0
        
        for job_file in job_files:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for job_data in data.get('jobs', []):
                        try:
                            job = ScheduledJob.from_dict(job_data)
                            # Kiểm tra duplicate (có thể có job trong nhiều file)
                            if job.job_id not in jobs:
                                jobs[job.job_id] = job
                                loaded_count += 1
                            else:
                                # Nếu duplicate, resolve bằng logic thông minh
                                existing_job = jobs[job.job_id]
                                resolved_job = self._resolve_duplicate_job(existing_job, job, job_file.name)
                                if resolved_job != existing_job:
                                    # Job đã được update
                                    jobs[job.job_id] = resolved_job
                        except (KeyError, ValueError, TypeError) as e:
                            failed_count += 1
                            self.logger.log_step(
                                step="LOAD_JOBS",
                                result="WARNING",
                                error=f"Failed to load job {job_data.get('job_id', 'unknown')}: {safe_get_exception_message(e)}",
                                error_type=safe_get_exception_type_name(e),
                                job_file=job_file.name
                            )
                        except Exception as e:
                            failed_count += 1
                            self.logger.log_step(
                                step="LOAD_JOBS",
                                result="ERROR",
                                error=f"Unexpected error loading job {job_data.get('job_id', 'unknown')}: {safe_get_exception_message(e)}",
                                error_type=safe_get_exception_type_name(e),
                                job_file=job_file.name
                            )
                
                files_processed += 1
                
            except json.JSONDecodeError as e:
                self.logger.log_step(
                    step="LOAD_JOBS",
                    result="ERROR",
                    error=f"Invalid JSON in {job_file.name}: {str(e)}",
                    error_type="JSONDecodeError"
                )
                continue
            except PermissionError as e:
                self.logger.log_step(
                    step="LOAD_JOBS",
                    result="ERROR",
                    error=f"Permission denied reading {job_file.name}: {str(e)}",
                    error_type="PermissionError"
                )
                continue
            except Exception as e:
                self.logger.log_step(
                    step="LOAD_JOBS",
                    result="ERROR",
                    error=f"Failed to load {job_file.name}: {safe_get_exception_message(e)}",
                    error_type=safe_get_exception_type_name(e)
                )
                continue
        
        self.logger.log_step(
            step="LOAD_JOBS",
            result="SUCCESS",
            jobs_count=len(jobs),
            loaded_count=loaded_count,
            failed_count=failed_count,
            files_processed=files_processed,
            storage_dir=str(self.storage_dir)
        )
        
        return jobs
    
    def save_jobs(self, jobs: Dict[str, ScheduledJob]) -> None:
        """
        Lưu jobs vào các file theo ngày và status (structure mới).
        
        Logic xác định file:
        - Nếu job có completed_at → File: jobs_{completed_at_date}_completed.json
        - Nếu job status = RUNNING → File: jobs_{scheduled_time_date}_running.json
        - Các trường hợp khác → File: jobs_{scheduled_time_date}_{status}.json
        
        Xem thêm: docs/excel_upload_job_completion_flow.md
        
        Args:
            jobs: Dict mapping job_id -> ScheduledJob
        
        Raises:
            StorageError: Nếu không thể lưu jobs
        """
        try:
            # Nhóm jobs theo ngày và status (structure mới)
            # Format: jobs_by_status_date[status][date] = [jobs]
            jobs_by_status_date: Dict[str, Dict[str, List[ScheduledJob]]] = {}
            
            for job in jobs.values():
                # Xác định ngày và status để lưu job
                # Logic theo tài liệu: excel_upload_job_completion_flow.md
                # Ưu tiên: completed_at > scheduled_time > created_at
                
                date_key, status_key = self._get_job_file_key(job)
                
                # Nhóm theo status và date
                if status_key not in jobs_by_status_date:
                    jobs_by_status_date[status_key] = {}
                if date_key not in jobs_by_status_date[status_key]:
                    jobs_by_status_date[status_key][date_key] = []
                
                jobs_by_status_date[status_key][date_key].append(job)
            
            # Lưu từng file theo status và ngày (structure mới)
            saved_files = 0
            for status_key, dates_dict in jobs_by_status_date.items():
                for date_key, jobs_list in dates_dict.items():
                    try:
                        # Parse date_key với error handling
                        try:
                            date_obj = datetime.strptime(date_key, "%Y-%m-%d")
                        except (ValueError, TypeError) as e:
                            self.logger.log_step(
                                step="SAVE_JOBS",
                                result="WARNING",
                                error=f"Invalid date_key format: {date_key}, skipping",
                                error_type=safe_get_exception_type_name(e)
                            )
                            continue
                        
                        # Lấy status enum từ status_key
                        try:
                            status_enum = JobStatus[status_key.upper()]
                        except KeyError:
                            self.logger.log_step(
                                step="SAVE_JOBS",
                                result="WARNING",
                                error=f"Invalid status_key: {status_key}, skipping",
                                status_key=status_key
                            )
                            continue
                        
                        # Structure mới: jobs_YYYY-MM-DD_{status}.json
                        job_file_path = self._get_job_file_path(date_obj, status=status_enum)
                        
                        # Convert jobs to dict với error handling
                        jobs_dict_list = []
                        for job in jobs_list:
                            try:
                                if hasattr(job, 'to_dict') and callable(job.to_dict):
                                    jobs_dict_list.append(job.to_dict())
                                else:
                                    self.logger.log_step(
                                        step="SAVE_JOBS",
                                        result="WARNING",
                                        error=f"Job {getattr(job, 'job_id', 'unknown')} has no to_dict method, skipping",
                                        job_id=getattr(job, 'job_id', 'unknown')
                                    )
                            except Exception as e:
                                self.logger.log_step(
                                    step="SAVE_JOBS",
                                    result="WARNING",
                                    error=f"Error converting job {getattr(job, 'job_id', 'unknown')} to dict: {safe_get_exception_message(e)}",
                                    error_type=safe_get_exception_type_name(e),
                                    job_id=getattr(job, 'job_id', 'unknown')
                                )
                                continue
                        
                        data = {
                            'jobs': jobs_dict_list,
                            'updated_at': datetime.now().isoformat(),
                            'date': date_key,
                            'status': status_key  # Thêm status vào metadata
                        }
                    except Exception as e:
                        self.logger.log_step(
                            step="SAVE_JOBS",
                            result="WARNING",
                            error=f"Error processing date {date_key}: {safe_get_exception_message(e)}, skipping",
                            error_type=safe_get_exception_type_name(e),
                            date=date_key
                        )
                        continue
                    
                    # Write to temporary file first, then rename (atomic operation)
                    temp_path = job_file_path.with_suffix('.json.tmp')
                    try:
                        # Write và flush ngay lập tức để đảm bảo realtime update
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                            f.flush()  # Flush buffer trước khi close
                            # Force sync to disk để đảm bảo file được write ngay
                            try:
                                import os
                                os.fsync(f.fileno())
                            except (OSError, AttributeError, IOError):
                                # Ignore nếu không thể fsync (một số hệ thống không support)
                                pass
                        
                        # Atomic rename (sau khi đã flush và fsync)
                        temp_path.replace(job_file_path)
                        
                        # Sync directory để đảm bảo rename được persist
                        # (fsync file sau rename không đảm bảo metadata được sync)
                        try:
                            import os
                            dir_fd = os.open(str(self.storage_dir), os.O_DIRECTORY)
                            os.fsync(dir_fd)
                            os.close(dir_fd)
                        except (OSError, AttributeError, IOError):
                            # Ignore nếu không thể fsync directory
                            pass
                        
                        saved_files += 1
                        
                    except PermissionError as e:
                        self.logger.log_step(
                            step="SAVE_JOBS",
                            result="ERROR",
                            error=f"Permission denied writing to {job_file_path}: {str(e)}",
                            error_type="PermissionError",
                            date=date_key
                        )
                        # Clean up temp file
                        try:
                            temp_path.unlink(missing_ok=True)
                        except Exception:
                            pass
                        raise StorageError(f"Permission denied writing to storage file {job_file_path}: {str(e)}") from e
                    except OSError as e:
                        self.logger.log_step(
                            step="SAVE_JOBS",
                            result="ERROR",
                            error=f"OS error writing to {job_file_path}: {str(e)}",
                            error_type="OSError",
                            date=date_key
                        )
                        # Clean up temp file
                        try:
                            temp_path.unlink(missing_ok=True)
                        except Exception:
                            pass
                        raise StorageError(f"OS error writing to storage file {job_file_path}: {str(e)}") from e
            
            # Collect tất cả dates từ jobs_by_status_date để cleanup empty files
            all_dates = set()
            for status_dict in jobs_by_status_date.values():
                all_dates.update(status_dict.keys())
            
            # Cache file list để tránh đọc lại nhiều lần (fix N+1 query pattern)
            # Các cleanup methods sẽ dùng cùng file list này
            all_files = self._get_all_job_files()
            
            # Cleanup job khỏi các file cũ (nếu job đã bị xóa khỏi memory)
            # Nếu job không có trong jobs dict nhưng vẫn còn trong file cũ, xóa nó
            # CHÚ Ý: Phải gọi SAU KHI save để đảm bảo files mới đã được write
            # nhưng trước khi log SUCCESS để có thể log cleanup results
            try:
                jobs_count_before_cleanup = len(jobs)
                job_ids_sample = list(jobs.keys())[:5] if jobs else []
                self.logger.log_step(
                    step="SAVE_JOBS_BEFORE_CLEANUP",
                    result="INFO",
                    note=f"About to cleanup deleted jobs, jobs in memory: {jobs_count_before_cleanup}",
                    jobs_count=jobs_count_before_cleanup,
                    job_ids_sample=job_ids_sample
                )
                # Pass cached file list để tránh đọc lại
                self._cleanup_deleted_jobs(jobs, all_files=all_files)
                self.logger.log_step(
                    step="SAVE_JOBS_AFTER_CLEANUP",
                    result="INFO",
                    note="Cleanup completed successfully"
                )
            except Exception as e:
                # Log nhưng không fail save operation
                self.logger.log_step(
                    step="CLEANUP_DELETED_JOBS",
                    result="ERROR",
                    error=safe_get_exception_message(e),
                    error_type=safe_get_exception_type_name(e)
                )
                import traceback
                print(f"[Storage.save_jobs] ERROR in cleanup: {safe_get_exception_message(e)}")
                traceback.print_exc()
            
            # Cleanup các file rỗng (không còn jobs nào)
            # Pass cached file list để tránh đọc lại
            self._cleanup_empty_files(all_dates, all_files=all_files)
            
            self.logger.log_step(
                step="SAVE_JOBS",
                result="SUCCESS",
                jobs_count=len(jobs),
                files_saved=saved_files,
                dates=len(all_dates),
                statuses=len(jobs_by_status_date)
            )
        except StorageError:
            # Re-raise storage errors
            raise
        except Exception as e:
            self.logger.log_step(
                step="SAVE_JOBS",
                result="ERROR",
                error=safe_get_exception_message(e),
                error_type=safe_get_exception_type_name(e)
            )
            raise StorageError(f"Failed to save jobs: {safe_get_exception_message(e)}") from e
    
    def _cleanup_deleted_jobs(self, jobs: Dict[str, ScheduledJob], all_files: Optional[List[Path]] = None) -> None:
        """
        Xóa các job đã bị xóa khỏi memory hoặc được save vào file khác khỏi file hiện tại.
        
        Có 2 trường hợp:
        1. Job bị xóa khỏi memory → xóa khỏi tất cả files
        2. Job được save vào file khác (ví dụ: completed job chuyển sang file theo completed_at)
           → xóa khỏi file cũ
        
        Args:
            jobs: Dict các jobs hiện có trong memory (job_id -> ScheduledJob)
            all_files: Optional cached file list. Nếu None, sẽ gọi _get_all_job_files()
                      (dùng để tránh N+1 query pattern)
        """
        # Use cached file list if provided, otherwise get fresh list
        if all_files is None:
            all_files = self._get_all_job_files()
        job_ids_in_memory = set(jobs.keys())
        
        # Tính toán file đúng cho mỗi job (theo logic save_jobs)
        # File đúng = (date, status) - không chỉ date
        job_correct_files: Dict[str, tuple[str, str]] = {}
        for job_id, job in jobs.items():
            # Xác định ngày và status file đúng (theo logic save_jobs)
            date_key, status_key = self._get_job_file_key(job)
            job_correct_files[job_id] = (date_key, status_key)
        
        # Log để debug
        self.logger.log_step(
            step="CLEANUP_DELETED_JOBS",
            result="INFO",
            note=f"Starting cleanup, checking {len(all_files)} files, {len(job_ids_in_memory)} jobs in memory"
        )
        
        total_deleted = 0
        for job_file in all_files:
            try:
                # Extract date và status từ tên file: jobs_YYYY-MM-DD_{status}.json hoặc jobs_YYYY-MM-DD.json
                try:
                    file_date, file_status = self._parse_job_filename(job_file)
                except ValueError:
                    # Tên file không đúng format, bỏ qua
                    self.logger.log_step(
                        step="CLEANUP_DELETED_JOBS",
                        result="WARNING",
                        note=f"Skipping file with invalid format: {job_file.name}",
                        file=job_file.name
                    )
                    continue
                
                with open(job_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                jobs_in_file = data.get('jobs', [])
                updated_jobs = []
                
                for job_data in jobs_in_file:
                    job_id = job_data.get('job_id')
                    job_status = job_data.get('status')
                    
                    # Case 1: Job không có trong memory → xóa (tất cả jobs, kể cả completed/expired/failed)
                    # Nếu user đã explicitly xóa job khỏi memory (qua delete_job), 
                    # job đó phải bị xóa khỏi file bất kể status là gì
                    if job_id not in job_ids_in_memory:
                        # Job đã bị xóa khỏi memory → xóa khỏi file
                        self.logger.log_step(
                            step="CLEANUP_DELETED_JOBS",
                            result="INFO",
                            note=f"Removing job {job_id[:8]}... from file {job_file.name} (not in memory, status: {job_status})",
                            job_id=job_id,
                            file=job_file.name,
                            job_status=job_status,
                            jobs_in_file_count=len(jobs_in_file),
                            jobs_in_memory_count=len(job_ids_in_memory)
                        )
                        continue  # Skip job này, không thêm vào updated_jobs
                    # Case 2: Job có trong memory nhưng file này không phải file đúng → xóa
                    if job_id in job_correct_files:
                        correct_file_date, correct_file_status = job_correct_files[job_id]
                        if (file_date, file_status) != (correct_file_date, correct_file_status):
                            # Job ở file sai (có thể đã được move sang file khác) → xóa khỏi file này
                            self.logger.log_step(
                                step="CLEANUP_DELETED_JOBS",
                                result="INFO",
                                note=f"Removing job {job_id[:8]}... from file {job_file.name} (wrong file: ({file_date}, {file_status}) != ({correct_file_date}, {correct_file_status}))",
                                job_id=job_id,
                                file=job_file.name,
                                file_date=file_date,
                                file_status=file_status,
                                correct_file_date=correct_file_date,
                                correct_file_status=correct_file_status
                            )
                            continue  # Skip job này
                    
                    # Job đúng file và có trong memory → giữ lại
                    updated_jobs.append(job_data)
                
                # Nếu có job bị xóa khỏi file, update file
                if len(updated_jobs) < len(jobs_in_file):
                    deleted_count = len(jobs_in_file) - len(updated_jobs)
                    
                    # Update data
                    data['jobs'] = updated_jobs
                    data['updated_at'] = datetime.now().isoformat()
                    
                    # Atomic write
                    temp_path = job_file.with_suffix('.json.tmp')
                    try:
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        temp_path.replace(job_file)
                        
                        total_deleted += deleted_count
                        # Fix: updated_jobs là list dict, cần extract job_ids để so sánh
                        updated_job_ids = {j.get('job_id') for j in updated_jobs}
                        deleted_job_ids = [
                            j.get('job_id') 
                            for j in jobs_in_file 
                            if j.get('job_id') not in updated_job_ids
                        ]
                        self.logger.log_step(
                            step="CLEANUP_DELETED_JOBS",
                            result="SUCCESS",
                            deleted_count=deleted_count,
                            file=job_file.name,
                            job_ids_deleted=deleted_job_ids
                        )
                    except Exception as e:
                        # Clean up temp file
                        try:
                            temp_path.unlink(missing_ok=True)
                        except Exception:
                            pass
                        self.logger.log_step(
                            step="CLEANUP_DELETED_JOBS",
                            result="ERROR",
                            error=f"Failed to update {job_file.name}: {safe_get_exception_message(e)}",
                            error_type=safe_get_exception_type_name(e)
                        )
            except Exception as e:
                # Skip files that can't be read
                self.logger.log_step(
                    step="CLEANUP_DELETED_JOBS",
                    result="WARNING",
                    error=f"Could not process {job_file.name}: {safe_get_exception_message(e)}",
                    error_type=safe_get_exception_type_name(e)
                )
        
        # Log tổng kết
        if total_deleted > 0:
            self.logger.log_step(
                step="CLEANUP_DELETED_JOBS",
                result="SUCCESS",
                total_deleted=total_deleted,
                files_checked=len(all_files)
            )
    
    def _cleanup_empty_files(self, active_dates: set, all_files: Optional[List[Path]] = None) -> None:
        """
        Xóa các file job không còn jobs nào (đã cleanup hết).
        
        Args:
            active_dates: Set các ngày hiện có jobs
            all_files: Optional cached file list. Nếu None, sẽ gọi _get_all_job_files()
                      (dùng để tránh N+1 query pattern)
        """
        # Use cached file list if provided, otherwise get fresh list
        if all_files is None:
            all_files = self._get_all_job_files()
        deleted_count = 0
        
        for job_file in all_files:
            # Extract date từ tên file: jobs_YYYY-MM-DD_{status}.json hoặc jobs_YYYY-MM-DD.json
            try:
                file_date, _ = self._parse_job_filename(job_file)
                
                # Nếu file không thuộc active dates, kiểm tra xem có jobs không
                if file_date not in active_dates:
                    try:
                        with open(job_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            jobs = data.get('jobs', [])
                            # Xóa nếu file rỗng (không còn jobs nào)
                            if not jobs:
                                job_file.unlink()
                                deleted_count += 1
                                self.logger.log_step(
                                    step="CLEANUP_EMPTY_FILES",
                                    result="SUCCESS",
                                    deleted_file=job_file.name
                                )
                    except Exception:
                        # Không thể đọc file, bỏ qua
                        pass
            except ValueError:
                # Tên file không đúng format, bỏ qua
                pass
        
        if deleted_count > 0:
            self.logger.log_step(
                step="CLEANUP_EMPTY_FILES",
                result="SUCCESS",
                deleted_count=deleted_count
            )

