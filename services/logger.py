"""
Module: services/logger.py

Enhanced structured logging cho Threads automation.

Features:
- Log rotation (size-based và time-based)
- JSON format support
- Context management (request ID, correlation ID)
- Performance metrics (auto timing, memory tracking)
- Error tracking với stack traces
- Log sampling cho high-volume scenarios
- Thread-safe operations
- Multiple output formats (text, JSON)
"""

# Standard library
import logging
import json
import sys
import traceback
import threading
import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
import os
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from enum import Enum
from contextlib import contextmanager
from dataclasses import dataclass, field

# Local
from utils.sanitize import (
    sanitize_data, 
    sanitize_error, 
    sanitize_kwargs,
    sanitize_status_message,
    sanitize_value
)


class LogFormat(Enum):
    """Log format enumeration."""
    TEXT = "text"
    JSON = "json"


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogContext:
    """Log context for correlation tracking."""
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    account_id: Optional[str] = None
    thread_id: Optional[str] = None
    user_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggerConfig:
    """Logger configuration."""
    # Basic settings
    name: str = "threads_automation"
    level: int = logging.INFO
    log_dir: str = "./logs"
    
    # Format settings
    format: LogFormat = LogFormat.TEXT
    include_timestamp: bool = True
    include_level: bool = True
    include_logger_name: bool = True
    
    # Rotation settings
    enable_rotation: bool = True
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    rotation_when: str = "midnight"  # midnight, H, D, W0
    rotation_interval: int = 1
    
    # Performance tracking
    track_performance: bool = True
    track_memory: bool = True
    
    # Error tracking
    include_stack_trace: bool = True
    max_stack_depth: int = 10
    
    # Sampling (for high-volume scenarios)
    enable_sampling: bool = False
    sampling_rate: float = 1.0  # 1.0 = 100%, 0.1 = 10%
    
    # Thread safety
    thread_safe: bool = True


class EnhancedLogger:
    """
    Enhanced structured logger cho Threads automation.
    
    Features:
    - Log rotation (size và time-based)
    - JSON format support
    - Context management
    - Performance metrics
    - Error tracking với stack traces
    - Log sampling
    - Thread-safe operations
    """
    
    def __init__(
        self,
        name: str = "threads_automation",
        level: int = logging.INFO,
        log_dir: str = "./logs",
        config: Optional[LoggerConfig] = None
    ):
        """
        Khởi tạo enhanced logger.
        
        Args:
            name: Tên logger
            level: Mức log
            log_dir: Thư mục cho file log
            config: Logger configuration (optional)
        """
        self.name = name
        self.config = config or LoggerConfig(
            name=name,
            level=level,
            log_dir=log_dir
        )
        self.log_dir = Path(self.config.log_dir)
        self._lock = threading.Lock() if self.config.thread_safe else None
        self._context = LogContext()
        self._performance_stack: List[Dict[str, Any]] = []
        
        # Create log directory với error handling
        self._setup_log_directory()
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.config.level)
        
        # Clear existing handlers để tránh duplicate
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_log_directory(self) -> None:
        """Setup log directory với error handling."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            print(f"WARNING: Could not create log directory {self.log_dir}: {str(e)}, using current directory")
            self.log_dir = Path(".")
    
    def _setup_handlers(self) -> None:
        """Setup file và console handlers."""
        # File handler với rotation
        if self.config.enable_rotation:
            try:
                log_file = self.log_dir / f"{self.name}.log"
                
                # Use TimedRotatingFileHandler for time-based rotation
                file_handler = TimedRotatingFileHandler(
                    filename=str(log_file),
                    when=self.config.rotation_when,
                    interval=self.config.rotation_interval,
                    backupCount=self.config.backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(self.config.level)
                
                # Also add size-based rotation as secondary
                # Note: Python's logging doesn't support both simultaneously,
                # so we prioritize time-based rotation
                
            except (PermissionError, OSError) as e:
                print(f"WARNING: Could not create file handler: {str(e)}, using console handler only")
                file_handler = None
        else:
            try:
                log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
                file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
                file_handler.setLevel(self.config.level)
            except (PermissionError, OSError) as e:
                print(f"WARNING: Could not create file handler: {str(e)}, using console handler only")
                file_handler = None
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.config.level)
        
        # Formatter
        if self.config.format == LogFormat.JSON:
            formatter = self._create_json_formatter()
        else:
            formatter = self._create_text_formatter()
        
        # Add formatter và handlers
        if file_handler:
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _create_text_formatter(self) -> logging.Formatter:
        """Tạo text formatter."""
        format_parts = []
        if self.config.include_timestamp:
            format_parts.append("%(asctime)s")
        if self.config.include_level:
            format_parts.append("%(levelname)s")
        if self.config.include_logger_name:
            format_parts.append("%(name)s")
        format_parts.append("%(message)s")
        
        format_str = " - ".join(format_parts)
        return logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
    
    def _create_json_formatter(self) -> logging.Formatter:
        """Tạo JSON formatter (custom formatter sẽ format message as JSON)."""
        # We'll handle JSON formatting in _format_log method
        return logging.Formatter('%(message)s')
    
    def _acquire_lock(self) -> None:
        """Acquire lock nếu thread-safe enabled."""
        if self._lock:
            self._lock.acquire()
    
    def _release_lock(self) -> None:
        """Release lock nếu thread-safe enabled."""
        if self._lock:
            self._lock.release()
    
    def set_context(self, **kwargs) -> None:
        """
        Set log context.
        
        Args:
            **kwargs: Context fields (request_id, correlation_id, session_id, etc.)
        """
        self._acquire_lock()
        try:
            for key, value in kwargs.items():
                if hasattr(self._context, key):
                    setattr(self._context, key, value)
                else:
                    self._context.extra[key] = value
        finally:
            self._release_lock()
    
    def clear_context(self) -> None:
        """Clear log context."""
        self._acquire_lock()
        try:
            self._context = LogContext()
        finally:
            self._release_lock()
    
    @contextmanager
    def context(self, **kwargs):
        """
        Context manager cho log context.
        
        Usage:
            with logger.context(request_id="req123", account_id="acc001"):
                logger.info("Processing request")
        """
        old_context = LogContext(
            request_id=self._context.request_id,
            correlation_id=self._context.correlation_id,
            session_id=self._context.session_id,
            account_id=self._context.account_id,
            thread_id=self._context.thread_id,
            user_id=self._context.user_id,
            extra=self._context.extra.copy()
        )
        
        self.set_context(**kwargs)
        try:
            yield
        finally:
            self._context = old_context
    
    @contextmanager
    def performance_tracking(self, operation: str):
        """
        Context manager để track performance.
        
        Usage:
            with logger.performance_tracking("DATABASE_QUERY"):
                # Do operation
                pass
        """
        start_time = time.time()
        start_memory = self._get_memory_usage() if self.config.track_memory else None
        
        try:
            yield
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage() if self.config.track_memory else None
            
            memory_delta = None
            if start_memory is not None and end_memory is not None:
                memory_delta = end_memory - start_memory
            
            self.log_step(
                step=operation,
                result="SUCCESS",
                time_ms=elapsed_ms,
                memory_mb=end_memory,
                memory_delta_mb=memory_delta
            )
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        if not PSUTIL_AVAILABLE:
            return None
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except Exception:
            return None
    
    def _should_log(self) -> bool:
        """Check if should log based on sampling rate."""
        if not self.config.enable_sampling:
            return True
        
        import random
        return random.random() < self.config.sampling_rate
    
    def _format_log(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> str:
        """
        Định dạng log message.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields
        
        Returns:
            Formatted log string
        """
        # Build log data
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message
        }
        
        # Add context
        if self._context.request_id:
            log_data["request_id"] = self._context.request_id
        if self._context.correlation_id:
            log_data["correlation_id"] = self._context.correlation_id
        if self._context.session_id:
            log_data["session_id"] = self._context.session_id
        if self._context.account_id:
            log_data["account_id"] = self._context.account_id
        if self._context.thread_id:
            log_data["thread_id"] = self._context.thread_id
        if self._context.user_id:
            log_data["user_id"] = self._context.user_id
        if self._context.extra:
            # Sanitize extra context
            log_data["extra"] = sanitize_data(self._context.extra) if isinstance(self._context.extra, dict) else self._context.extra
        
        # Sanitize kwargs trước khi thêm vào log_data
        sanitized_kwargs = sanitize_kwargs(kwargs) if kwargs else {}
        
        # Add additional fields với sanitized values
        for key, value in sanitized_kwargs.items():
            if value is not None:
                try:
                    # Special handling for status_message
                    if key == "status_message" and isinstance(value, str):
                        log_data[key] = sanitize_status_message(value)
                    # Special handling for metadata (recursive sanitize)
                    elif key == "metadata" and isinstance(value, dict):
                        log_data[key] = sanitize_data(value)
                    # Serialize complex types
                    elif isinstance(value, (dict, list)):
                        log_data[key] = value
                    elif isinstance(value, Exception):
                        log_data[key] = sanitize_error(value)
                        if self.config.include_stack_trace:
                            log_data[f"{key}_traceback"] = sanitize_error(self._format_traceback(value))
                    else:
                        log_data[key] = value
                except Exception:
                    log_data[key] = f"<unserializable:{type(value).__name__}>"
        
        # Sanitize toàn bộ log_data trước khi format
        log_data = sanitize_data(log_data)
        
        # Format based on config
        if self.config.format == LogFormat.JSON:
            try:
                return json.dumps(log_data, default=str, ensure_ascii=False)
            except Exception:
                # Fallback to text format if JSON serialization fails
                return self._format_text_log(log_data)
        else:
            return self._format_text_log(log_data)
    
    def _format_text_log(self, log_data: Dict[str, Any]) -> str:
        """Format log as text (key-value pairs)."""
        parts = []
        
        # Core fields
        if "step" in log_data:
            parts.append(f"STEP={log_data['step']}")
        if "result" in log_data:
            parts.append(f"RESULT={log_data['result']}")
        
        # Context fields
        for field in ["request_id", "correlation_id", "session_id", "account_id", "thread_id", "user_id"]:
            if field in log_data and log_data[field]:
                parts.append(f"{field.upper()}={log_data[field]}")
        
        # Additional fields
        for key, value in log_data.items():
            if key not in ["step", "result", "timestamp", "level", "logger", "message",
                          "request_id", "correlation_id", "session_id", "account_id",
                          "thread_id", "user_id", "extra"]:
                try:
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, default=str)
                    else:
                        value = str(value)
                    # Escape special characters
                    value = value.replace('\n', ' ').replace('\r', ' ')
                    parts.append(f"{key.upper()}={value}")
                except Exception:
                    parts.append(f"{key.upper()}=<format_error>")
        
        # Message
        if "message" in log_data:
            parts.append(f"MSG={log_data['message']}")
        
        return " ".join(parts)
    
    def _format_traceback(self, exception: Exception) -> str:
        """Format exception traceback."""
        try:
            tb_lines = traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__
            )
            tb_str = "".join(tb_lines)
            # Limit stack depth
            lines = tb_str.split('\n')
            if len(lines) > self.config.max_stack_depth * 2:
                lines = lines[:self.config.max_stack_depth * 2] + ['... (truncated)']
            return '\n'.join(lines)
        except Exception:
            return str(exception)
    
    def log_step(
        self,
        step: str,
        result: str,
        time_ms: Optional[float] = None,
        error: Optional[Union[str, Exception]] = None,
        account_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        content_hash: Optional[Union[int, str]] = None,
        risk_level: Optional[str] = None,
        error_type: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log một bước với định dạng structured.
        
        Args:
            step: Tên hành động (ví dụ: "CLICK_POST_BTN")
            result: Kết quả (SUCCESS, FAILED, ERROR, IN_PROGRESS, WARNING)
            time_ms: Thời gian thực thi tính bằng milliseconds
            error: Thông báo lỗi hoặc Exception object
            account_id: Mã định danh tài khoản
            thread_id: Thread ID nếu có
            content_hash: Hash của content nếu có
            risk_level: Mức rủi ro (low, medium, high, critical)
            error_type: Loại lỗi
            **kwargs: Các trường bổ sung
        """
        if not self._should_log():
            return
        
        # Sanitize kwargs trước khi thêm vào log_data
        sanitized_kwargs = sanitize_kwargs(kwargs) if kwargs else {}
        
        # Special sanitization for sensitive fields
        if "status_message" in sanitized_kwargs and isinstance(sanitized_kwargs["status_message"], str):
            sanitized_kwargs["status_message"] = sanitize_status_message(sanitized_kwargs["status_message"])
        if "metadata" in sanitized_kwargs and isinstance(sanitized_kwargs["metadata"], dict):
            sanitized_kwargs["metadata"] = sanitize_data(sanitized_kwargs["metadata"])
        
        # Build log data với sanitized kwargs
        log_data = {
            "step": step,
            "result": result,
            **sanitized_kwargs
        }
        
        # Time formatting
        if time_ms is not None:
            try:
                log_data["time_ms"] = float(time_ms)
                log_data["time_s"] = float(time_ms) / 1000.0
            except (TypeError, ValueError):
                log_data["time_ms"] = str(time_ms)
                log_data["time_s"] = "N/A"
        
        # Error handling - sanitize error messages
        if error is not None:
            if isinstance(error, Exception):
                log_data["error"] = sanitize_error(error)
                log_data["error_type"] = error_type or type(error).__name__
                if self.config.include_stack_trace:
                    log_data["error_traceback"] = sanitize_error(self._format_traceback(error))
            else:
                log_data["error"] = sanitize_error(str(error))
                if error_type:
                    log_data["error_type"] = error_type
        
        # Context fields (override với explicit params)
        if account_id:
            log_data["account_id"] = account_id
        if thread_id:
            log_data["thread_id"] = thread_id
        
        # Content hash
        if content_hash is not None:
            log_data["content_hash"] = str(content_hash)
        
        # Risk level
        if risk_level:
            log_data["risk_level"] = risk_level
        
        # Format và log
        try:
            level = "ERROR" if result in ["ERROR", "FAILED"] else "INFO"
            if result == "WARNING":
                level = "WARNING"
            
            log_message = self._format_log(level=level, message=f"{step}: {result}", **log_data)
            
            # Log với appropriate level
            if level == "ERROR":
                self.logger.error(log_message)
            elif level == "WARNING":
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
        except Exception as e:
            # Fallback nếu format fails
            fallback_msg = f"STEP={step} RESULT={result} ERROR=Log formatting failed: {str(e)}"
            try:
                self.logger.error(fallback_msg)
            except Exception:
                print(f"ERROR: Logger completely failed: {str(e)}")
                print(f"Log message: {fallback_msg}")
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        if not self._should_log():
            return
        try:
            log_message = self._format_log(level="DEBUG", message=message, **kwargs)
            self.logger.debug(log_message)
        except Exception:
            self.logger.debug(message)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        if not self._should_log():
            return
        try:
            log_message = self._format_log(level="INFO", message=message, **kwargs)
            self.logger.info(log_message)
        except Exception:
            self.logger.info(message)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        if not self._should_log():
            return
        try:
            log_message = self._format_log(level="WARNING", message=message, **kwargs)
            self.logger.warning(log_message)
        except Exception:
            self.logger.warning(message)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message với optional exception."""
        if not self._should_log():
            return
        try:
            log_data = {"error": str(error)} if error else {}
            if error and self.config.include_stack_trace:
                log_data["error_traceback"] = self._format_traceback(error)
            log_message = self._format_log(level="ERROR", message=message, **log_data, **kwargs)
            self.logger.error(log_message)
        except Exception:
            self.logger.error(message)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message với optional exception."""
        if not self._should_log():
            return
        try:
            log_data = {"error": str(error)} if error else {}
            if error and self.config.include_stack_trace:
                log_data["error_traceback"] = self._format_traceback(error)
            log_message = self._format_log(level="CRITICAL", message=message, **log_data, **kwargs)
            self.logger.critical(log_message)
        except Exception:
            self.logger.critical(message)


# Backward compatibility: StructuredLogger wraps EnhancedLogger
class StructuredLogger(EnhancedLogger):
    """
    Structured logger cho Threads automation (backward compatibility).
    
    Wrapper around EnhancedLogger với default settings cho compatibility.
    """
    
    def __init__(
        self,
        name: str = "threads_automation",
        level: int = logging.INFO,
        log_dir: str = "./logs"
    ):
        """
        Khởi tạo structured logger.
        
        Args:
            name: Tên logger
            level: Mức log
            log_dir: Thư mục cho file log
        """
        config = LoggerConfig(
            name=name,
            level=level,
            log_dir=log_dir,
            format=LogFormat.TEXT,
            enable_rotation=False,  # Disable rotation for backward compatibility
            track_performance=False,  # Disable performance tracking by default
            track_memory=False,
            include_stack_trace=False  # Disable stack traces by default
        )
        super().__init__(name=name, level=level, log_dir=log_dir, config=config)
