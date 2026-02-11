"""
Module: services/scheduler/execution.py

Execution logic cho scheduler: run_job, scheduler_loop.
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

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Callable, Any

# Local
from services.logger import StructuredLogger
from services.exceptions import StorageError
from services.scheduler.models import ScheduledJob, JobStatus, Platform, JobType
from services.safety_guard import RiskLevel, get_shared_safety_guard
from utils.exception_utils import (
    safe_get_exception_type_name,
    safe_get_exception_message,
    format_exception
)


class JobExecutor:
    """
    Job executor cho scheduler.
    
    Xử lý execution logic:
    - Run individual jobs
    - Scheduler loop
    """
    
    def __init__(
        self,
        jobs: Dict[str, ScheduledJob],
        logger: StructuredLogger,
        save_callback: Callable[[], None]
    ):
        """
        Khởi tạo job executor.
        
        Args:
            jobs: Dict mapping job_id -> ScheduledJob
            logger: Logger instance
            save_callback: Callback để save jobs
        """
        self.jobs = jobs
        self.logger = logger
        self.save_jobs = save_callback
        self._last_save_time = datetime.min  # Track save time để tránh reload ngay sau save

        # Safety guard dùng singleton shared (đồng bộ với UI/SafetyAPI)
        self.safety_guard = get_shared_safety_guard(logger=self.logger)
    
    def _update_job_status(self, job: ScheduledJob, message: str) -> None:
        """
        Update job status message và save ngay lập tức để UI có thể hiển thị real-time.
        
        Args:
            job: Job cần update
            message: Status message mới
        """
        job.status_message = message
        try:
            self.save_jobs()
            self._last_save_time = datetime.now()
        except StorageError as e:
            # Log warning nhưng không raise (để không block execution)
            self.logger.log_step(
                step="UPDATE_JOB_STATUS",
                result="WARNING",
                job_id=job.job_id,
                error=f"Failed to save status update: {str(e)}",
                error_type="StorageError"
            )
    
    async def run_job(
        self,
        job: ScheduledJob,
        post_callback_factory: Callable[[Platform], Callable[[str, str, Callable[[str], None]], Any]]
    ) -> None:
        """
        Chạy một job.
        
        Args:
            job: Job cần chạy
            post_callback_factory: Factory function để lấy callback dựa trên platform
                                  Callback nhận (account_id, content, status_updater)
        """
        # --- SAFETY CHECK TRƯỚC KHI CHẠY JOB ---
        # Chỉ check safety guard cho POST jobs, engagement jobs có safety guard riêng
        job_type = getattr(job, 'job_type', JobType.POST)
        if job_type == JobType.POST:
            allowed, safety_error, risk_level = self.safety_guard.can_post(job.account_id, job.content)
            if not allowed:
                # Block job theo SafetyGuard
                job.status = JobStatus.FAILED
                job.error = safety_error
                job.status_message = f"❌ Bị chặn bởi SafetyGuard (risk={risk_level.value}): {safety_error}"
                job.completed_at = datetime.now()

                # Ghi nhận high-risk nếu mức độ cao
                if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                    self.safety_guard.record_high_risk_event(job.account_id, "scheduler_post_blocked")

                self.logger.log_step(
                    step="RUN_JOB_SAFETY_CHECK",
                    result="BLOCKED",
                    job_id=job.job_id,
                    account_id=job.account_id,
                    error=safety_error,
                    risk_level=risk_level.value,
                    status_message=job.status_message
                )

                # Save ngay để UI thấy trạng thái
                try:
                    self.save_jobs()
                    self._last_save_time = datetime.now()
                except StorageError as e:
                    self.logger.log_step(
                        step="RUN_JOB_SAFETY_CHECK",
                        result="WARNING",
                        job_id=job.job_id,
                        error=f"Failed to save blocked job: {safe_get_exception_message(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
                return

        # --- BẮT ĐẦU THỰC THI JOB ---
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()  # Lưu thời gian bắt đầu chạy
        self._update_job_status(job, "🔄 Đang khởi động browser...")
        
        # Create WebSocketLogger for realtime job execution logs
        try:
            from services.websocket_logger import WebSocketLogger
            ws_logger = WebSocketLogger(
                logger=self.logger,
                room="scheduler",
                account_id=job.account_id
            )
        except Exception:
            # Fallback to regular logger if WebSocketLogger not available
            ws_logger = self.logger
        
        try:
            # Log job start via WebSocket
            if hasattr(ws_logger, 'log_start'):
                await ws_logger.log_start(
                    operation="run_job",
                    account_id=job.account_id,
                    job_id=job.job_id
                )
            
            self.logger.log_step(
                step="RUN_JOB",
                result="IN_PROGRESS",
                job_id=job.job_id,
                account_id=job.account_id,
                retry_count=job.retry_count,
                status_message=job.status_message
            )
            
            # Tạo status updater callback để pass vào callback
            def status_updater(message: str) -> None:
                """Update job status message."""
                self._update_job_status(job, message)
            
            # Phân biệt job type: POST hoặc ENGAGEMENT
            job_type = getattr(job, 'job_type', JobType.POST)
            
            if job_type == JobType.ENGAGEMENT:
                # Engagement job: Parse engagement_data và gọi engagement callback
                import json
                engagement_data = getattr(job, 'engagement_data', None)
                if not engagement_data:
                    raise ValueError(f"Engagement job {job.job_id} missing engagement_data")
                
                # Parse engagement_data nếu là string
                if isinstance(engagement_data, str):
                    engagement_data = json.loads(engagement_data)
                
                action_type = engagement_data.get('action_type', '').lower()
                
                # Import engagement callback factory
                try:
                    from backend.app.modules.scheduler.utils.engagement_callback_factory import create_engagement_callback_factory
                    engagement_callback_factory = create_engagement_callback_factory()
                    engagement_callback = engagement_callback_factory(action_type)
                except ImportError:
                    # Fallback: Import directly from threads.engagement.callbacks
                    from threads.engagement.callbacks import like_callback, comment_callback, follow_callback
                    from threads.engagement.types import EngagementAction
                    
                    if action_type == 'like':
                        engagement_callback = like_callback
                    elif action_type == 'comment':
                        engagement_callback = comment_callback
                    elif action_type == 'follow':
                        engagement_callback = follow_callback
                    else:
                        raise ValueError(f"Unknown engagement action_type: {action_type}")
                
                # Prepare criteria from engagement_data
                if action_type == 'like':
                    from threads.engagement.types import LikeCriteria
                    criteria = LikeCriteria(**engagement_data.get('like_criteria', {}))
                    result = await engagement_callback(job.account_id, criteria, status_updater)
                elif action_type == 'comment':
                    from threads.engagement.types import CommentCriteria
                    criteria = CommentCriteria(**engagement_data.get('comment_criteria', {}))
                    result = await engagement_callback(job.account_id, criteria, status_updater)
                elif action_type == 'follow':
                    from threads.engagement.types import FollowCriteria
                    criteria = FollowCriteria(**engagement_data.get('follow_criteria', {}))
                    result = await engagement_callback(job.account_id, criteria, status_updater)
                else:
                    raise ValueError(f"Unknown engagement action_type: {action_type}")
                
                # Engagement callbacks return List[EngagementResult] hoặc EngagementResult
                # Convert to compatible format
                if isinstance(result, list):
                    # List of results - check if all succeeded
                    success_count = sum(1 for r in result if r.success)
                    total_count = len(result)
                    success = success_count > 0
                    # Create a simple result object
                    from types import SimpleNamespace
                    result = SimpleNamespace(
                        success=success,
                        thread_id=None,
                        error=None if success else f"Only {success_count}/{total_count} actions succeeded"
                    )
                elif hasattr(result, 'success'):
                    # Single EngagementResult
                    from types import SimpleNamespace
                    result = SimpleNamespace(
                        success=result.success,
                        thread_id=result.target_id,
                        error=result.error
                    )
            else:
                # POST job: Use existing post callback
                platform = getattr(job, 'platform', Platform.THREADS)
                post_callback = post_callback_factory(platform)
                
                # Lấy link_aff từ job (nếu có)
                link_aff = getattr(job, 'link_aff', None)
                
                # Gọi callback để đăng bài (pass status_updater và link_aff)
                result = await post_callback(job.account_id, job.content, status_updater, link_aff)
            
            # Validate result object
            if not hasattr(result, 'success'):
                raise ValueError(f"post_callback result must have 'success' attribute, got {type(result)}")
            
            if result.success:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.thread_id = result.thread_id if hasattr(result, 'thread_id') else None
                job.status_message = f"Hoàn thành thành công - Thread ID: {job.thread_id or 'N/A'}"

                # Log job completion via WebSocket
                if hasattr(ws_logger, 'log_complete'):
                    await ws_logger.log_complete(
                        operation="run_job",
                        success=True,
                        result={"thread_id": job.thread_id},
                        account_id=job.account_id,
                        job_id=job.job_id
                    )

                # Ghi nhận success cho SafetyGuard để reset counters / cập nhật health
                try:
                    self.safety_guard.record_post_success(job.account_id, job.content)
                except Exception:
                    # Không để lỗi safety ảnh hưởng kết quả job
                    pass
                
                # QUAN TRỌNG: Save ngay sau khi job completed để đảm bảo persistence và realtime update
                # Không đợi đến finally block để tránh mất dữ liệu nếu có exception
                # File JSON sẽ được cập nhật realtime ngay sau khi post thành công
                try:
                    save_start_time = datetime.now()
                    self.save_jobs()
                    save_duration = (datetime.now() - save_start_time).total_seconds() * 1000
                    self._last_save_time = datetime.now()
                    self.logger.log_step(
                        step="RUN_JOB",
                        result="SUCCESS",
                        job_id=job.job_id,
                        thread_id=job.thread_id,
                        status_message=job.status_message,
                        save_duration_ms=save_duration,
                        note="Job completed and saved immediately (realtime update)"
                    )
                except Exception as save_error:
                    # Log error nhưng không fail job (job đã completed thành công)
                    self.logger.log_step(
                        step="RUN_JOB",
                        result="WARNING",
                        job_id=job.job_id,
                        error=f"Job completed but failed to save immediately: {safe_get_exception_message(save_error)}",
                        error_type=safe_get_exception_type_name(save_error),
                        thread_id=job.thread_id,
                        status_message=job.status_message
                    )
                    # Vẫn log success để track job đã completed
                    self.logger.log_step(
                        step="RUN_JOB",
                        result="SUCCESS",
                        job_id=job.job_id,
                        thread_id=job.thread_id,
                        status_message=job.status_message,
                        note="Job completed (save will retry in finally block)"
                    )
            else:
                # Thử retry nếu có thể
                if job.can_retry():
                    job.retry_count += 1
                    job.status = JobStatus.SCHEDULED
                    # Exponential backoff: 2^retry_count minutes
                    backoff_minutes = 2 ** job.retry_count
                    job.scheduled_time = datetime.now() + timedelta(minutes=backoff_minutes)
                    # Safely get error message
                    error_msg = getattr(result, 'error', 'Unknown error')
                    job.status_message = f"Thất bại, sẽ thử lại sau {backoff_minutes} phút (lần thử {job.retry_count}/{job.max_retries}) - Lỗi: {error_msg}"
                    
                    self.logger.log_step(
                        step="RUN_JOB",
                        result="RETRY_SCHEDULED",
                        job_id=job.job_id,
                        retry_count=job.retry_count,
                        next_run=job.scheduled_time.isoformat(),
                        error=error_msg,
                        status_message=job.status_message
                    )
                else:
                    job.status = JobStatus.FAILED
                    # Safely get error message
                    error_msg = getattr(result, 'error', 'Unknown error')
                    job.error = error_msg
                    job.status_message = f"Thất bại hoàn toàn sau {job.retry_count} lần thử - {error_msg}"

                    # Log job error via WebSocket
                    if hasattr(ws_logger, 'log_error'):
                        await ws_logger.log_error(
                            operation="run_job",
                            error=error_msg,
                            error_type="PostError",
                            account_id=job.account_id,
                            job_id=job.job_id
                        )

                    # Ghi nhận lỗi cho SafetyGuard
                    try:
                        self.safety_guard.record_post_error(
                            job.account_id,
                            error_type="PostError",
                            error_message=error_msg
                        )
                    except Exception:
                        pass
                    self.logger.log_step(
                        step="RUN_JOB",
                        result="FAILED",
                        job_id=job.job_id,
                        error=result.error,
                        retry_count=job.retry_count,
                        status_message=job.status_message
                    )
        
        except Exception as e:
            # Thử retry nếu có thể
            if job.can_retry():
                job.retry_count += 1
                job.status = JobStatus.SCHEDULED
                backoff_minutes = 2 ** job.retry_count
                job.scheduled_time = datetime.now() + timedelta(minutes=backoff_minutes)
                error_formatted = format_exception(e)
                job.status_message = f"Lỗi exception, sẽ thử lại sau {backoff_minutes} phút (lần thử {job.retry_count}/{job.max_retries}) - {error_formatted}"
                
                self.logger.log_step(
                    step="RUN_JOB",
                    result="RETRY_SCHEDULED",
                    job_id=job.job_id,
                    retry_count=job.retry_count,
                    next_run=job.scheduled_time.isoformat(),
                    error=safe_get_exception_message(e),
                    error_type=safe_get_exception_type_name(e),
                    status_message=job.status_message
                )
            else:
                job.status = JobStatus.FAILED
                error_formatted = format_exception(e)
                job.error = error_formatted
                job.status_message = f"Lỗi không thể retry sau {job.retry_count} lần thử - {error_formatted}"

                # Log job error via WebSocket
                try:
                    if hasattr(ws_logger, 'log_error'):
                        await ws_logger.log_error(
                            operation="run_job",
                            error=safe_get_exception_message(e),
                            error_type=safe_get_exception_type_name(e),
                            account_id=job.account_id,
                            job_id=job.job_id
                        )
                except Exception:
                    pass

                # Ghi nhận lỗi exception cho SafetyGuard
                try:
                    self.safety_guard.record_post_error(
                        job.account_id,
                        error_type=safe_get_exception_type_name(e),
                        error_message=safe_get_exception_message(e)
                    )
                except Exception:
                    pass
                self.logger.log_step(
                    step="RUN_JOB",
                    result="ERROR",
                    job_id=job.job_id,
                    error=safe_get_exception_message(e),
                    error_type=safe_get_exception_type_name(e),
                    retry_count=job.retry_count,
                    status_message=job.status_message
                )
        
        finally:
            # Save jobs với error handling
            try:
                self.save_jobs()
                # Track save time để tránh reload ngay sau save
                self._last_save_time = datetime.now()
            except StorageError as e:
                # Log warning nhưng không raise
                self.logger.log_step(
                    step="RUN_JOB",
                    result="WARNING",
                    job_id=job.job_id,
                    error=f"Failed to save job in finally block: {str(e)}",
                    error_type="StorageError"
                )
            except Exception as e:
                # Log error nhưng không raise (để đảm bảo job state được update)
                self.logger.log_step(
                    step="RUN_JOB",
                    result="ERROR",
                    job_id=job.job_id,
                    error=f"Unexpected error saving job in finally block: {safe_get_exception_message(e)}",
                    error_type=safe_get_exception_type_name(e)
                )
    
    async def scheduler_loop(
        self,
        post_callback_factory: Callable[[Platform], Callable[[str, str], Any]],
        running_flag_getter: Callable[[], bool],
        running_flag_setter: Callable[[bool], None],
        get_ready_jobs: Callable[[], list],
        cleanup_expired_jobs: Callable[[], int],
        recover_stuck_jobs: Callable[[], int],
        reload_jobs_callback: Callable[[], None] | None = None,
        get_last_save_time: Callable[[], datetime] | None = None
    ) -> None:
        """
        Vòng lặp scheduler chính.
        
        Args:
            post_callback_factory: Factory function để lấy callback dựa trên platform
            running_flag_getter: Function để check running flag
            running_flag_setter: Function để set running flag
            get_ready_jobs: Function để lấy ready jobs
            cleanup_expired_jobs: Function để cleanup expired jobs
            recover_stuck_jobs: Function để recover stuck jobs
            reload_jobs_callback: Optional callback để reload jobs từ storage (để pick up jobs mới)
        """
        while running_flag_getter():
            try:
                # Check running flag ngay đầu loop để có thể exit nhanh
                if not running_flag_getter():
                    self.logger.log_step(
                        step="SCHEDULER_LOOP",
                        result="INFO",
                        note="Scheduler running flag set to False, exiting loop"
                    )
                    break
                
                # Cleanup expired jobs với error handling
                try:
                    cleanup_expired_jobs()
                    # Track save time nếu cleanup có save jobs
                    if hasattr(cleanup_expired_jobs, '__self__') and hasattr(cleanup_expired_jobs.__self__, '_last_save_time'):
                        self._last_save_time = cleanup_expired_jobs.__self__._last_save_time
                except Exception as e:
                    self.logger.log_step(
                        step="SCHEDULER_LOOP",
                        result="WARNING",
                        error=f"Error in cleanup_expired_jobs: {safe_get_exception_message(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
                
                # Recover stuck jobs (jobs RUNNING quá lâu do crash/mất mạng) với error handling
                try:
                    recover_stuck_jobs()
                except Exception as e:
                    self.logger.log_step(
                        step="SCHEDULER_LOOP",
                        result="WARNING",
                        error=f"Error in recover_stuck_jobs: {safe_get_exception_message(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
                
                # Kiểm tra xem có job nào đang RUNNING không
                # Scheduler chỉ nên chạy 1 job tại một thời điểm
                try:
                    running_jobs = [j for j in self.jobs.values() if j.status == JobStatus.RUNNING]
                except (AttributeError, TypeError) as e:
                    # Nếu jobs dict có vấn đề, log và continue
                    self.logger.log_step(
                        step="SCHEDULER_LOOP",
                        result="WARNING",
                        error=f"Error checking running jobs: {safe_get_exception_message(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
                    running_jobs = []
                
                if running_jobs:
                    # Có job đang chạy, không chạy job mới
                    # Chờ job hiện tại hoàn thành hoặc bị recover
                    self.logger.log_step(
                        step="SCHEDULER_LOOP",
                        result="INFO",
                        note=f"Job đang chạy, chờ hoàn thành. Running jobs: {len(running_jobs)}",
                        running_job_ids=[j.job_id for j in running_jobs]
                    )
                    await asyncio.sleep(10)  # Chờ ngắn trước khi check lại
                    continue
                
                # Check running flag lại trước khi chạy job
                if not running_flag_getter():
                    self.logger.log_step(
                        step="SCHEDULER_LOOP",
                        result="INFO",
                        note="Scheduler running flag set to False, exiting loop before running job"
                    )
                    break
                
                # Reload jobs từ storage để pick up jobs mới (mỗi 30 giây)
                # BẢO VỆ: Không reload ngay sau khi save để tránh race condition
                if reload_jobs_callback:
                    try:
                        # Check if we need to reload (every 30 seconds)
                        if not hasattr(self, '_last_reload_time'):
                            self._last_reload_time = datetime.now()
                        
                        # Check if we just saved jobs (avoid reload immediately after save)
                        # Lấy _last_save_time từ scheduler hoặc từ executor
                        if get_last_save_time:
                            last_save_time = get_last_save_time()
                        else:
                            last_save_time = getattr(self, '_last_save_time', datetime.min)
                        
                        elapsed = (datetime.now() - self._last_reload_time).total_seconds()
                        time_since_save = (datetime.now() - last_save_time).total_seconds()
                        
                        # Reload every 30 seconds, but NOT within 2 seconds after save
                        # Tránh race condition: save → reload ngay lập tức → overwrite COMPLETED
                        if elapsed >= 30 and time_since_save >= 2:
                            reload_jobs_callback()  # Reload jobs từ storage
                            self._last_reload_time = datetime.now()
                            self.logger.log_step(
                                step="SCHEDULER_LOOP",
                                result="INFO",
                                note="Reloaded jobs from storage to pick up new jobs"
                            )
                    except Exception as e:
                        # Log nhưng không block
                        self.logger.log_step(
                            step="SCHEDULER_LOOP",
                            result="WARNING",
                            error=f"Error reloading jobs: {safe_get_exception_message(e)}",
                            error_type=safe_get_exception_type_name(e)
                        )
                
                # Lấy jobs sẵn sàng chạy với error handling
                try:
                    ready_jobs = get_ready_jobs()
                    # #region agent log - Debug scheduler_loop get_ready_jobs
                    import json
                    import os
                    log_path = os.path.join(os.path.expanduser("~"), "threads", ".cursor", "debug.log")
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"location":"execution.py:scheduler_loop","message":"get_ready_jobs result","data":{"ready_jobs_count":len(ready_jobs) if ready_jobs else 0,"ready_job_ids":[getattr(j,'job_id','unknown')[:8] for j in ready_jobs[:3]] if ready_jobs else [],"running":running_flag_getter()},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"F"})+'\n')
                    # #endregion
                except Exception as e:
                    self.logger.log_step(
                        step="SCHEDULER_LOOP",
                        result="WARNING",
                        error=f"Error in get_ready_jobs: {safe_get_exception_message(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
                    ready_jobs = []
                
                if ready_jobs:
                    # Chạy job có priority cao nhất
                    try:
                        job = ready_jobs[0]
                        job_status_before = job.status if hasattr(job, 'status') else None
                        await self.run_job(job, post_callback_factory)
                        
                        # Nếu job thành công, thêm delay để đảm bảo action spacing
                        # Delay này giúp tránh bị SafetyGuard chặn khi có nhiều jobs cùng ready
                        job_status_after = job.status if hasattr(job, 'status') else None
                        if job_status_after == JobStatus.COMPLETED:
                            # Lấy min_delay từ SafetyGuard config
                            min_delay_seconds = 5.0  # Default
                            try:
                                from services.safety_guard import SafetyConfig
                                safety_config = SafetyConfig()
                                min_delay_seconds = safety_config.min_delay_between_posts_seconds
                            except Exception:
                                pass
                            
                            # Delay với safety buffer (1.5x để đảm bảo an toàn)
                            delay_seconds = min_delay_seconds * 1.5
                            
                            # Chỉ delay nếu có jobs khác cùng ready cho cùng account
                            has_more_ready_jobs_same_account = False
                            if len(ready_jobs) > 1:
                                for other_job in ready_jobs[1:]:
                                    if (hasattr(other_job, 'account_id') and 
                                        hasattr(job, 'account_id') and 
                                        other_job.account_id == job.account_id):
                                        has_more_ready_jobs_same_account = True
                                        break
                            
                            if has_more_ready_jobs_same_account:
                                self.logger.log_step(
                                    step="SCHEDULER_LOOP",
                                    result="INFO",
                                    note=f"Job completed successfully. Delaying {delay_seconds:.1f}s before next job to ensure action spacing.",
                                    account_id=job.account_id if hasattr(job, 'account_id') else None,
                                    delay_seconds=delay_seconds
                                )
                                await asyncio.sleep(delay_seconds)
                    except Exception as e:
                        # Log error nhưng continue loop
                        self.logger.log_step(
                            step="SCHEDULER_LOOP",
                            result="ERROR",
                            error=f"Error running job {job.job_id if hasattr(job, 'job_id') else 'unknown'}: {safe_get_exception_message(e)}",
                            error_type=safe_get_exception_type_name(e)
                        )
                else:
                    # Không có job nào sẵn sàng
                    # Kiểm tra xem có jobs nào còn active (pending, scheduled, running) không
                    has_active_jobs = False
                    try:
                        active_statuses = [JobStatus.PENDING, JobStatus.SCHEDULED, JobStatus.RUNNING]
                        for job in self.jobs.values():
                            try:
                                if hasattr(job, 'status') and job.status in active_statuses:
                                    has_active_jobs = True
                                    break
                            except (AttributeError, TypeError):
                                continue
                    except (AttributeError, TypeError):
                        # Nếu không thể check, giả định có active jobs để an toàn
                        has_active_jobs = True
                    
                    if has_active_jobs:
                        # Có jobs active, chờ ngắn (30s) rồi check lại
                        self.logger.log_step(
                            step="SCHEDULER_LOOP",
                            result="INFO",
                            note="Không có job nào sẵn sàng, nhưng vẫn còn jobs active. Chờ 30s..."
                        )
                        for _ in range(30):
                            if not running_flag_getter():
                                break
                            await asyncio.sleep(1)
                    else:
                        # Không còn jobs active nào, chờ lâu hơn (5 phút) để tiết kiệm tài nguyên
                        self.logger.log_step(
                            step="SCHEDULER_LOOP",
                            result="INFO",
                            note="Không còn jobs active nào. Chờ 5 phút trước khi check lại..."
                        )
                        for _ in range(300):  # 5 phút = 300 giây
                            if not running_flag_getter():
                                break
                            await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                # Scheduler đang được stop, log và re-raise
                self.logger.log_step(
                    step="SCHEDULER_LOOP",
                    result="INFO",
                    note="Scheduler loop cancelled"
                )
                # Set running = False để đảm bảo loop không tiếp tục
                running_flag_setter(False)
                # Log STOP_SCHEDULER ngay tại đây để đảm bảo log được ghi
                # (vì stop() có thể không được gọi nếu exception được raise trước)
                self.logger.log_step(
                    step="STOP_SCHEDULER",
                    result="INFO",
                    note="Scheduler loop cancelled, will be stopped"
                )
                # Force flush log handlers để đảm bảo log được ghi ngay
                try:
                    for handler in self.logger.logger.handlers:
                        handler.flush()
                except Exception as e:
                    # Log error nhưng không raise
                    print(f"WARNING: Error flushing log handlers: {str(e)}")
                
                # Save jobs trước khi exit với error handling
                try:
                    self.save_jobs()
                    # Track save time để tránh reload ngay sau save
                    self._last_save_time = datetime.now()
                except Exception as e:
                    # Log error nhưng không raise (để đảm bảo loop có thể exit)
                    self.logger.log_step(
                        step="STOP_SCHEDULER",
                        result="WARNING",
                        error=f"Failed to save jobs on cancel: {safe_get_exception_message(e)}",
                        error_type=safe_get_exception_type_name(e)
                    )
                raise
            except Exception as e:
                self.logger.log_step(
                    step="SCHEDULER_LOOP",
                    result="ERROR",
                    error=safe_get_exception_message(e),
                    error_type=safe_get_exception_type_name(e)
                )
                # Chờ 10s trước khi tiếp tục để tránh loop lỗi liên tục
                await asyncio.sleep(10)

