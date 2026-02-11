"""
Jobs module.

Handles job operations: creation, retrieval, update, deletion.
"""

# Export main components for easy importing
from backend.app.modules.jobs.routes import router
from backend.app.modules.jobs.controllers import JobsController
from backend.app.modules.jobs.services.jobs_service import JobsService
from backend.app.modules.jobs.repositories.jobs_repository import JobsRepository

__all__ = [
    "router",
    "JobsController",
    "JobsService",
    "JobsRepository"
]
