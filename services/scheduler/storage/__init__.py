"""
Storage module cho scheduler.

Provides storage implementations:
- JobStorage (JSON files) - Original implementation
- MySQLJobStorage (MySQL database) - New implementation
- JobStorageBase - Abstract base class
- Factory function for creating storage instances

All implementations follow same interface via JobStorageBase.
"""

# Import for backward compatibility
from services.scheduler.storage.json_storage import JobStorage

# Import base class for implementations
from services.scheduler.storage.base import JobStorageBase

# Import factory
from services.scheduler.storage.factory import create_job_storage

__all__ = [
    "JobStorage",  # JSON storage (backward compatible)
    "JobStorageBase",  # Abstract base class
    "create_job_storage",  # Factory function
]
