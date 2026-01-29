"""
Dashboard API routes.

REST API endpoints cho dashboard data.

LEGACY ROUTES - Using adapter pattern to call new services when available.
"""

# Standard library
from typing import Optional, Dict, List
from datetime import datetime
from fastapi import APIRouter, Query

# Local
from backend.api.adapters.jobs_adapter import JobsAPI
from backend.api.adapters.analytics_adapter import AnalyticsAPI
from backend.api.dependencies import get_jobs_api, get_analytics_api
from backend.app.core.responses import success_response
from backend.app.core.exceptions import InternalError
from backend.app.core.migration_flags import is_module_enabled

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        try:
            from backend.app.modules.dashboard.controllers import DashboardController
            _controller = DashboardController()
        except ImportError:
            _controller = None
    return _controller


def _calculate_jobs_by_status(jobs: List[Dict]) -> Dict[str, int]:
    """
    Calculate jobs count by status.
    
    Args:
        jobs: List of job dicts
    
    Returns:
        Dict mapping status -> count
    """
    jobs_by_status = {}
    for job in jobs:
        status = job.get("status", "unknown")
        jobs_by_status[status] = jobs_by_status.get(status, 0) + 1
    return jobs_by_status


def _calculate_jobs_by_platform(jobs: List[Dict]) -> Dict[str, int]:
    """
    Calculate jobs count by platform.
    
    Args:
        jobs: List of job dicts
    
    Returns:
        Dict mapping platform -> count
    """
    jobs_by_platform = {}
    for job in jobs:
        platform = job.get("platform", "unknown")
        jobs_by_platform[platform] = jobs_by_platform.get(platform, 0) + 1
    return jobs_by_platform


def _parse_created_at(created_at) -> Optional[datetime]:
    """
    Parse created_at from job dict.
    
    Args:
        created_at: Created at value (string or datetime)
    
    Returns:
        Parsed datetime or None
    """
    if not created_at:
        return None
    
    try:
        if isinstance(created_at, str):
            return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif isinstance(created_at, datetime):
            return created_at
    except Exception:
        pass
    
    return None


def _build_timeline_data(jobs: List[Dict]) -> List[Dict]:
    """
    Build posts timeline data.
    
    Args:
        jobs: List of job dicts
    
    Returns:
        List of timeline items
    """
    timeline = []
    
    for job in jobs:
        created_at = job.get("created_at")
        if not created_at:
            continue
        
        date_obj = _parse_created_at(created_at)
        if not date_obj:
            continue
        
        date_str = date_obj.strftime("%Y-%m-%d")
        platform = job.get("platform", "unknown")
        
        # Find or create timeline item for this date
        found = False
        for item in timeline:
            if item.get("date") == date_str:
                item[platform] = item.get(platform, 0) + 1
                found = True
                break
        
        if not found:
            timeline.append({
                "date": date_str,
                platform: 1
            })
    
    return timeline


def _calculate_hourly_distribution(jobs: List[Dict]) -> Dict[str, int]:
    """
    Calculate hourly distribution of posts.
    
    Args:
        jobs: List of job dicts
    
    Returns:
        Dict mapping hour (string) -> count
    """
    hourly_distribution = {}
    
    for job in jobs:
        created_at = job.get("created_at")
        if not created_at:
            continue
        
        date_obj = _parse_created_at(created_at)
        if not date_obj:
            continue
        
        hour = str(date_obj.hour)
        hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
    
    return hourly_distribution


@router.get("/stats")
async def get_dashboard_stats(
    account_id: Optional[str] = Query(None, description="Filter by account ID")
):
    """Get dashboard statistics."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("dashboard"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_stats(account_id=account_id)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        jobs_api = get_jobs_api()
        jobs = jobs_api.get_all_jobs(account_id=account_id, reload=False)
        
        # Calculate stats
        total_jobs = len(jobs)
        pending_jobs = len([j for j in jobs if j.get("status") == "pending"])
        completed_jobs = len([j for j in jobs if j.get("status") == "completed"])
        failed_jobs = len([j for j in jobs if j.get("status") == "failed"])
        
        stats = {
            "total_jobs": total_jobs,
            "pending_jobs": pending_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        }
        
        return success_response(data=stats, message="Dashboard stats retrieved successfully")
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve dashboard stats: {str(e)}")


@router.get("/metrics")
async def get_dashboard_metrics(
    account_id: Optional[str] = Query(None, description="Filter by account ID")
):
    """Get dashboard metrics."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("dashboard"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_metrics(account_id=account_id)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        jobs_api = get_jobs_api()
        jobs = jobs_api.get_all_jobs(account_id=account_id, reload=False)
        
        # Calculate metrics using helper functions
        metrics = {
            "jobs_by_status": _calculate_jobs_by_status(jobs),
            "jobs_by_platform": _calculate_jobs_by_platform(jobs),
            "posts_timeline": _build_timeline_data(jobs),
            "hourly_distribution": _calculate_hourly_distribution(jobs)
        }
        
        # Add analytics data if account_id provided
        if account_id:
            try:
                analytics_api = get_analytics_api()
                analytics_data = analytics_api.get_account_dashboard_data(account_id=account_id, days=30)
                metrics["analytics"] = analytics_data
            except Exception:
                # Fallback if analytics not available
                pass
        
        return success_response(data=metrics, message="Dashboard metrics retrieved successfully")
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve dashboard metrics: {str(e)}")


@router.get("/activity")
async def get_recent_activity(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    limit: int = Query(10, description="Number of activities to return")
):
    """Get recent activity."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("dashboard"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_activity(account_id=account_id, limit=limit)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        jobs_api = get_jobs_api()
        jobs = jobs_api.get_all_jobs(account_id=account_id, reload=False)
        
        # Sort by created_at and limit
        sorted_jobs = sorted(
            jobs,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:limit]
        
        return success_response(
            data=sorted_jobs,
            message="Recent activity retrieved successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve recent activity: {str(e)}")
