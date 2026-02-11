# 📋 Enhanced Logger Documentation

## Overview

Enhanced structured logging system cho Threads Automation Tool với nhiều tính năng nâng cao.

## Features

### ✨ Core Features

1. **Log Rotation**
   - Time-based rotation (midnight, hourly, daily, weekly)
   - Size-based rotation (configurable max file size)
   - Automatic backup management

2. **Multiple Formats**
   - Text format (key-value pairs) - default
   - JSON format (structured, machine-readable)

3. **Context Management**
   - Request ID tracking
   - Correlation ID for distributed tracing
   - Session ID tracking
   - Account/Thread context

4. **Performance Metrics**
   - Automatic timing tracking
   - Memory usage monitoring
   - Performance context managers

5. **Error Tracking**
   - Stack trace capture
   - Error type tracking
   - Exception chaining support

6. **Log Sampling**
   - Configurable sampling rate
   - Useful for high-volume scenarios

7. **Thread Safety**
   - Thread-safe operations
   - Lock-based synchronization

## Usage

### Basic Usage (Backward Compatible)

```python
from services.logger import StructuredLogger

# Create logger (same as before)
logger = StructuredLogger(name="my_service")

# Log step (same API)
logger.log_step(
    step="CLICK_POST_BTN",
    result="SUCCESS",
    time_ms=1200.5,
    account_id="account_001"
)
```

### Enhanced Usage

```python
from services.logger import EnhancedLogger, LoggerConfig, LogFormat

# Create enhanced logger với custom config
config = LoggerConfig(
    name="my_service",
    level=logging.INFO,
    format=LogFormat.JSON,  # Use JSON format
    enable_rotation=True,
    track_performance=True,
    track_memory=True,
    include_stack_trace=True
)

logger = EnhancedLogger(config=config)

# Log với context
logger.set_context(
    request_id="req_123",
    account_id="account_001",
    session_id="session_456"
)

logger.log_step(
    step="PROCESS_REQUEST",
    result="SUCCESS",
    time_ms=500.0
)

# Clear context
logger.clear_context()
```

### Context Manager

```python
# Context manager cho temporary context
with logger.context(request_id="req_123", account_id="acc_001"):
    logger.info("Processing request")
    # Context automatically cleared after block
```

### Performance Tracking

```python
# Automatic performance tracking
with logger.performance_tracking("DATABASE_QUERY"):
    # Do database operation
    result = db.query("SELECT * FROM jobs")
    # Automatically logs timing and memory usage
```

### Error Tracking

```python
try:
    result = await action()
except Exception as e:
    # Automatic stack trace capture
    logger.error(
        "Action failed",
        error=e,
        account_id="account_001"
    )
```

### JSON Format

```python
# Create logger với JSON format
config = LoggerConfig(
    name="api_service",
    format=LogFormat.JSON
)
logger = EnhancedLogger(config=config)

# Logs will be in JSON format
logger.log_step(
    step="API_CALL",
    result="SUCCESS",
    time_ms=100.0
)

# Output:
# {"timestamp": "2026-01-20T10:30:45", "level": "INFO", "logger": "api_service", "message": "API_CALL: SUCCESS", "step": "API_CALL", "result": "SUCCESS", "time_ms": 100.0, ...}
```

### Log Sampling

```python
# Enable sampling for high-volume scenarios
config = LoggerConfig(
    name="high_volume_service",
    enable_sampling=True,
    sampling_rate=0.1  # Log only 10% of events
)
logger = EnhancedLogger(config=config)
```

## Configuration

### LoggerConfig Options

```python
@dataclass
class LoggerConfig:
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
    
    # Sampling
    enable_sampling: bool = False
    sampling_rate: float = 1.0  # 1.0 = 100%
    
    # Thread safety
    thread_safe: bool = True
```

## Migration Guide

### From Old StructuredLogger

Old code:
```python
logger = StructuredLogger(name="my_service")
logger.log_step(step="ACTION", result="SUCCESS")
```

New code (backward compatible):
```python
# Same code works!
logger = StructuredLogger(name="my_service")
logger.log_step(step="ACTION", result="SUCCESS")
```

### To EnhancedLogger

```python
# Option 1: Use EnhancedLogger với default config
from services.logger import EnhancedLogger
logger = EnhancedLogger(name="my_service")

# Option 2: Use EnhancedLogger với custom config
from services.logger import EnhancedLogger, LoggerConfig, LogFormat
config = LoggerConfig(
    name="my_service",
    format=LogFormat.JSON,
    enable_rotation=True
)
logger = EnhancedLogger(config=config)
```

## Best Practices

### 1. Use Context for Request Tracking

```python
# Set context at request start
logger.set_context(
    request_id=generate_request_id(),
    account_id=account_id
)

try:
    # Process request
    result = process()
    logger.log_step(step="PROCESS", result="SUCCESS")
except Exception as e:
    logger.error("Process failed", error=e)
finally:
    # Clear context after request
    logger.clear_context()
```

### 2. Use Performance Tracking for Critical Operations

```python
# Track performance for database queries, API calls, etc.
with logger.performance_tracking("DATABASE_QUERY"):
    result = db.query(sql)
```

### 3. Use JSON Format for Log Aggregation

```python
# Use JSON format when integrating with log aggregation tools
config = LoggerConfig(
    format=LogFormat.JSON,
    enable_rotation=True
)
logger = EnhancedLogger(config=config)
```

### 4. Enable Sampling for High-Volume Services

```python
# Enable sampling for services that log frequently
config = LoggerConfig(
    enable_sampling=True,
    sampling_rate=0.1  # Log 10% of events
)
logger = EnhancedLogger(config=config)
```

### 5. Use Context Manager for Temporary Context

```python
# Use context manager for temporary context
with logger.context(request_id="req_123"):
    logger.info("Processing")
    # Context automatically cleared
```

## Log Format Examples

### Text Format (Default)

```
2026-01-20 10:30:45 - INFO - my_service - STEP=CLICK_POST_BTN RESULT=SUCCESS TIME_MS=1200.5 ACCOUNT_ID=account_001 THREAD_ID=thread_123
```

### JSON Format

```json
{
  "timestamp": "2026-01-20T10:30:45.123456",
  "level": "INFO",
  "logger": "my_service",
  "message": "CLICK_POST_BTN: SUCCESS",
  "step": "CLICK_POST_BTN",
  "result": "SUCCESS",
  "time_ms": 1200.5,
  "time_s": 1.2005,
  "account_id": "account_001",
  "thread_id": "thread_123"
}
```

## Troubleshooting

### Logs Not Rotating

- Check `enable_rotation` is `True`
- Check file permissions on log directory
- Check disk space

### Memory Tracking Not Working

- Ensure `psutil` is installed: `pip install psutil`
- Check `track_memory` is `True` in config

### JSON Format Not Working

- Ensure `format=LogFormat.JSON` in config
- Check that complex objects are JSON-serializable

### Context Not Persisting

- Use `set_context()` for persistent context
- Use `context()` context manager for temporary context
- Check thread safety if using in multi-threaded environment

## Performance Considerations

- **JSON format**: Slightly slower than text format due to JSON serialization
- **Stack traces**: Can be expensive, use `include_stack_trace=False` for high-volume scenarios
- **Memory tracking**: Requires `psutil`, adds minimal overhead
- **Sampling**: Reduces log volume, useful for high-frequency events

## Examples

See `services/logger.py` for complete implementation and more examples.
