"""
Helpers for JobsAPI.

Mục tiêu:
- Giảm trách nhiệm của `JobsAPI` (orchestration layer) bằng cách tách các phần
  lặp lại/độc lập như: resolve active scheduler, safe reload, convert jobs to dict.
- KHÔNG thay đổi behavior public của JobsAPI.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Protocol

from services.logger import StructuredLogger


class SchedulerLike(Protocol):
    """Protocol for minimal scheduler methods used by JobsAPI helpers."""

    jobs: Dict[str, Any]

    def reload_jobs(self, force: bool = False) -> None: ...

    def list_jobs(self, account_id: Optional[str] = None) -> List[Any]: ...


def resolve_target_scheduler(fallback_scheduler: SchedulerLike) -> SchedulerLike:
    """
    Resolve active scheduler if available, otherwise use fallback_scheduler.

    Note: ui.utils.get_active_scheduler is an optional dependency (UI runtime).
    """
    try:
        from ui.utils import get_active_scheduler

        active_scheduler = get_active_scheduler()
        return active_scheduler if active_scheduler else fallback_scheduler
    except Exception:
        return fallback_scheduler


def safe_reload_jobs(
    scheduler: SchedulerLike,
    logger: StructuredLogger,
    force: bool = False
) -> None:
    """Reload jobs with error handling and logging, without raising."""
    try:
        scheduler.reload_jobs(force=force)
        logger.debug(
            f"Reloaded jobs from storage, count: {len(getattr(scheduler, 'jobs', {}))} "
            f"(target_scheduler_id={id(scheduler)})"
        )
    except Exception as reload_error:
        logger.log_step(
            step="GET_ALL_JOBS_RELOAD",
            result="WARNING",
            error=f"Failed to reload jobs: {str(reload_error)}",
            error_type=type(reload_error).__name__,
        )


def convert_jobs_to_dicts(
    jobs: List[Any],
    to_dict: Callable[[Any], Dict],
    logger: StructuredLogger
) -> List[Dict]:
    """
    Convert list of ScheduledJob-like objects to list of dicts.

    Keeps the same logging behavior as JobsAPI.get_all_jobs():
    - warn per conversion error
    - warn summary if any errors
    """
    result: List[Dict] = []
    conversion_errors = 0

    for job in jobs:
        try:
            result.append(to_dict(job))
        except Exception as e:
            conversion_errors += 1
            job_id = getattr(job, "job_id", "unknown")
            logger.log_step(
                step="GET_ALL_JOBS_CONVERT",
                result="WARNING",
                error=f"Error converting job to dict: {str(e)}",
                error_type=type(e).__name__,
                job_id=job_id,
            )
            continue

    if conversion_errors > 0:
        logger.warning(
            f"Converted {len(result)}/{len(jobs)} jobs successfully "
            f"({conversion_errors} errors)"
        )

    return result
