"""
Module: services/scheduler/models.py

Models cho scheduler: JobStatus, JobPriority, ScheduledJob.
"""

# Standard library
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict

# Local
from services.utils.datetime_utils import normalize_to_utc


class JobStatus(Enum):
    """Trạng thái của job."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class JobPriority(Enum):
    """Độ ưu tiên của job."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Platform(Enum):
    """Platform được hỗ trợ."""
    THREADS = "threads"
    FACEBOOK = "facebook"


@dataclass
class ScheduledJob:
    """Job được lên lịch."""
    job_id: str
    account_id: str
    content: str
    scheduled_time: datetime
    priority: JobPriority
    status: JobStatus
    platform: Platform = Platform.THREADS  # Platform mặc định là THREADS để backward compatible
    max_retries: int = 3
    retry_count: int = 0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None  # Thời gian job bắt đầu chạy (khi status = RUNNING)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    thread_id: Optional[str] = None
    status_message: Optional[str] = None  # Thông điệp trạng thái chi tiết
    link_aff: Optional[str] = None  # Link affiliate để đăng trong comment (optional)
    
    def __post_init__(self):
        """Khởi tạo sau khi tạo object."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển job thành dict để lưu."""
        try:
            data = asdict(self)
        except Exception:
            # Fallback nếu asdict fails
            data = {
                'job_id': self.job_id,
                'account_id': self.account_id,
                'content': self.content,
                'scheduled_time': self.scheduled_time,
                'priority': self.priority,
                'status': self.status,
                'max_retries': self.max_retries,
                'retry_count': self.retry_count,
                'created_at': self.created_at,
                'started_at': self.started_at,
                'completed_at': self.completed_at,
                'error': self.error,
                'thread_id': self.thread_id,
                'status_message': self.status_message,
                'link_aff': self.link_aff
            }
        
        # Convert datetime to ISO string với error handling
        try:
            if isinstance(data.get('scheduled_time'), datetime):
                data['scheduled_time'] = data['scheduled_time'].isoformat()
        except (AttributeError, TypeError):
            pass
        
        try:
            if isinstance(data.get('created_at'), datetime):
                data['created_at'] = data['created_at'].isoformat()
        except (AttributeError, TypeError):
            pass
        
        try:
            if isinstance(data.get('completed_at'), datetime):
                data['completed_at'] = data['completed_at'].isoformat()
        except (AttributeError, TypeError):
            pass
        
        try:
            if isinstance(data.get('started_at'), datetime):
                data['started_at'] = data['started_at'].isoformat()
        except (AttributeError, TypeError):
            pass
        
        # Convert enums to values với error handling
        try:
            if hasattr(self.priority, 'value'):
                data['priority'] = self.priority.value
            else:
                data['priority'] = str(self.priority)
        except (AttributeError, TypeError):
            data['priority'] = str(self.priority) if self.priority else None
        
        try:
            if hasattr(self.status, 'value'):
                data['status'] = self.status.value
            else:
                data['status'] = str(self.status)
        except (AttributeError, TypeError):
            data['status'] = str(self.status) if self.status else None
        
        try:
            if hasattr(self, 'platform') and self.platform:
                if hasattr(self.platform, 'value'):
                    data['platform'] = self.platform.value
                else:
                    data['platform'] = str(self.platform)
            else:
                # Default to THREADS nếu không có platform
                data['platform'] = Platform.THREADS.value
        except (AttributeError, TypeError):
            # Default to THREADS nếu có lỗi
            data['platform'] = Platform.THREADS.value
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledJob':
        """
        Tạo job từ dict.
        
        Note: scheduled_time từ database đã là UTC, không cần normalize lại.
        Chỉ normalize khi parse từ user input (Excel, form).
        """
        # Make a copy để không modify original dict
        job_data = data.copy()
        
        # Convert ISO string to datetime với error handling
        # Note: datetime từ database đã có timezone info (UTC), không cần normalize
        try:
            if isinstance(job_data.get('scheduled_time'), str):
                job_data['scheduled_time'] = datetime.fromisoformat(job_data['scheduled_time'])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid scheduled_time format: {job_data.get('scheduled_time')}") from e
        
        try:
            if isinstance(job_data.get('created_at'), str):
                job_data['created_at'] = datetime.fromisoformat(job_data['created_at'])
        except (ValueError, TypeError):
            # created_at có thể None hoặc invalid, set to None
            job_data['created_at'] = None
        
        try:
            if isinstance(job_data.get('completed_at'), str):
                job_data['completed_at'] = datetime.fromisoformat(job_data['completed_at'])
        except (ValueError, TypeError):
            # completed_at có thể None hoặc invalid, set to None
            job_data['completed_at'] = None
        
        try:
            if isinstance(job_data.get('started_at'), str):
                job_data['started_at'] = datetime.fromisoformat(job_data['started_at'])
        except (ValueError, TypeError):
            # started_at có thể None hoặc invalid, set to None
            job_data['started_at'] = None
        
        # Convert values to enums với error handling
        try:
            priority_value = job_data.get('priority')
            if isinstance(priority_value, JobPriority):
                job_data['priority'] = priority_value
            elif isinstance(priority_value, (int, str)):
                job_data['priority'] = JobPriority(priority_value)
            else:
                # Default to NORMAL nếu không parse được
                job_data['priority'] = JobPriority.NORMAL
        except (ValueError, KeyError, TypeError):
            # Default to NORMAL nếu không parse được
            job_data['priority'] = JobPriority.NORMAL
        
        try:
            status_value = job_data.get('status')
            if isinstance(status_value, JobStatus):
                job_data['status'] = status_value
            elif isinstance(status_value, str):
                job_data['status'] = JobStatus(status_value)
            else:
                # Default to SCHEDULED nếu không parse được
                job_data['status'] = JobStatus.SCHEDULED
        except (ValueError, KeyError, TypeError):
            # Default to SCHEDULED nếu không parse được
            job_data['status'] = JobStatus.SCHEDULED
        
        # Convert platform value to enum với error handling (backward compatible)
        try:
            platform_value = job_data.get('platform')
            if isinstance(platform_value, Platform):
                job_data['platform'] = platform_value
            elif isinstance(platform_value, str):
                job_data['platform'] = Platform(platform_value)
            else:
                # Default to THREADS nếu không có platform (backward compatible)
                job_data['platform'] = Platform.THREADS
        except (ValueError, KeyError, TypeError):
            # Default to THREADS nếu không parse được (backward compatible)
            job_data['platform'] = Platform.THREADS
        
        try:
            return cls(**job_data)
        except TypeError as e:
            # Missing required fields
            raise ValueError(f"Invalid job data: missing required fields. Error: {str(e)}") from e
    
    def is_expired(self) -> bool:
        """
        Kiểm tra job đã hết hạn chưa.
        
        Job được coi là expired nếu:
        - Đã quá 24 giờ kể từ scheduled_time
        - VÀ job chưa được completed
        """
        try:
            # Chỉ coi là expired nếu đã quá 24h từ scheduled_time
            # Và job chưa completed
            if self.status == JobStatus.COMPLETED:
                return False
            
            if not hasattr(self, 'scheduled_time') or self.scheduled_time is None:
                return False
            
            # Normalize to UTC for consistent comparison
            scheduled_time_utc = normalize_to_utc(self.scheduled_time)
            now_utc = datetime.now(timezone.utc)
            return now_utc > scheduled_time_utc + timedelta(hours=24)
        except (AttributeError, TypeError):
            # Nếu có lỗi khi check, return False (không coi là expired)
            return False
    
    def is_ready(self) -> bool:
        """
        Kiểm tra job đã sẵn sàng chạy chưa.
        
        CHẶN CHẶT: Jobs COMPLETED, RUNNING, FAILED, CANCELLED, EXPIRED 
        KHÔNG BAO GIỜ được coi là ready.
        """
        try:
            # Validate required fields
            if not hasattr(self, 'status') or self.status is None:
                return False
            
            if not hasattr(self, 'scheduled_time') or self.scheduled_time is None:
                return False
            
            # BẢO VỆ: Chặn các jobs đã hoàn thành hoặc không thể chạy
            if self.status in [
                JobStatus.COMPLETED,  # Đã chạy xong - KHÔNG BAO GIỜ chạy lại
                JobStatus.RUNNING,    # Đang chạy - không thể chạy lại
                JobStatus.FAILED,     # Đã fail hết retry - không chạy lại
                JobStatus.CANCELLED,  # Đã bị hủy - không chạy
                JobStatus.EXPIRED     # Đã hết hạn - không chạy
            ]:
                return False
            
            # Chỉ jobs SCHEDULED hoặc PENDING mới có thể ready
            # Normalize to UTC for consistent comparison
            scheduled_time_utc = normalize_to_utc(self.scheduled_time)
            now_utc = datetime.now(timezone.utc)
            time_diff_seconds = (now_utc - scheduled_time_utc).total_seconds()
            is_ready = (
                self.status in [JobStatus.SCHEDULED, JobStatus.PENDING] and
                now_utc >= scheduled_time_utc and
                not self.is_expired()
            )
            
            # #region agent log - Debug is_ready check
            import json
            import os
            log_path = os.path.join(os.path.expanduser("~"), "threads", ".cursor", "debug.log")
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location":"models.py:is_ready","message":"is_ready check","data":{"job_id":getattr(self,'job_id','unknown')[:8] if hasattr(self,'job_id') else 'unknown',"status":str(self.status),"scheduled_time_utc":scheduled_time_utc.isoformat() if hasattr(scheduled_time_utc,'isoformat') else str(scheduled_time_utc),"now_utc":now_utc.isoformat(),"time_diff_seconds":time_diff_seconds,"time_diff_hours":time_diff_seconds/3600,"is_ready":is_ready,"is_expired":self.is_expired()},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"F"})+'\n')
            # #endregion
            
            # Cập nhật status message với error handling
            try:
                if is_ready:
                    scheduled_str = self.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.scheduled_time, 'strftime') else str(self.scheduled_time)
                    self.status_message = f"Sẵn sàng chạy - đã đến thời gian đăng ({scheduled_str})"
                elif self.status == JobStatus.SCHEDULED:
                    try:
                        # Normalize to UTC for consistent comparison
                        scheduled_time_utc = normalize_to_utc(self.scheduled_time)
                        now_utc = datetime.now(timezone.utc)
                        time_until = (scheduled_time_utc - now_utc).total_seconds()
                        if time_until > 0:
                            minutes = int(time_until / 60)
                            scheduled_str = self.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.scheduled_time, 'strftime') else str(self.scheduled_time)
                            self.status_message = f"Đang chờ - sẽ chạy sau {minutes} phút ({scheduled_str})"
                        else:
                            self.status_message = "Đã quá thời gian nhưng chưa được chạy"
                    except (TypeError, AttributeError):
                        self.status_message = "Đang chờ - scheduled time invalid"
                elif self.status == JobStatus.RUNNING:
                    self.status_message = "Đang chạy - đang đăng bài"
                elif self.status == JobStatus.COMPLETED:
                    thread_id = getattr(self, 'thread_id', None)
                    self.status_message = f"Hoàn thành - Thread ID: {thread_id or 'N/A'}"
                elif self.status == JobStatus.FAILED:
                    error = getattr(self, 'error', None)
                    self.status_message = f"Thất bại - {error or 'Không rõ lỗi'}"
                elif self.status == JobStatus.EXPIRED:
                    self.status_message = "Hết hạn - đã quá 24h từ thời gian lên lịch"
            except Exception:
                # Nếu update status_message fails, không fail is_ready check
                pass
            
            return is_ready
        except Exception:
            # Nếu có lỗi khi check, return False
            return False
    
    def can_retry(self) -> bool:
        """Kiểm tra job có thể retry không."""
        return self.retry_count < self.max_retries
    
    def is_stuck(self, max_running_minutes: int = 30) -> bool:
        """
        Kiểm tra job có bị stuck không (đang RUNNING quá lâu).
        
        Args:
            max_running_minutes: Số phút tối đa job có thể ở trạng thái RUNNING (mặc định: 30 phút)
        
        Returns:
            True nếu job bị stuck (RUNNING quá lâu), False nếu không
        """
        try:
            if not hasattr(self, 'status') or self.status != JobStatus.RUNNING:
                return False
            
            # Nếu không có started_at, coi như stuck ngay lập tức
            # (có thể là job cũ từ trước khi có field này, hoặc job bị crash ngay sau khi set RUNNING)
            started_at = getattr(self, 'started_at', None)
            if not started_at:
                # Nếu job RUNNING nhưng không có started_at, coi như stuck
                # Vì không biết khi nào nó bắt đầu chạy
                return True
            
            # Kiểm tra thời gian đã chạy với error handling
            try:
                # Normalize to UTC for consistent comparison
                started_at_utc = normalize_to_utc(started_at)
                now_utc = datetime.now(timezone.utc)
                running_duration = now_utc - started_at_utc
                return running_duration > timedelta(minutes=max_running_minutes)
            except (TypeError, AttributeError):
                # Nếu không thể tính duration, coi như stuck
                return True
        except Exception:
            # Nếu có lỗi khi check, return False (không coi là stuck)
            return False

