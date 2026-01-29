"""
Scheduler module cho Threads automation.

Module này quản lý job queue với:
- Priority-based scheduling
- Datetime-based execution
- Retry policy với exponential backoff
- Dead job handling
- Expired job skipping
"""

import sys
from pathlib import Path

# Add parent directory to path để các sub-modules có thể import utils modules
# CRITICAL: Phải setup TRƯỚC KHI import bất kỳ sub-module nào
_parent_dir = Path(__file__).resolve().parent.parent.parent
_parent_dir_str = str(_parent_dir)
if _parent_dir_str not in sys.path:
    sys.path.insert(0, _parent_dir_str)
elif sys.path[0] != _parent_dir_str:
    sys.path.remove(_parent_dir_str)
    sys.path.insert(0, _parent_dir_str)

from services.scheduler.models import (
    JobStatus,
    JobPriority,
    ScheduledJob
)
from services.scheduler.scheduler import Scheduler

__all__ = [
    "JobStatus",
    "JobPriority",
    "ScheduledJob",
    "Scheduler"
]

