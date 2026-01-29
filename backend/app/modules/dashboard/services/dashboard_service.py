"""
Dashboard service.

Business logic layer for dashboard operations.
Handles stats calculation, metrics aggregation, and timeline processing.
"""

# Standard library
from typing import Dict, List, Optional
from datetime import datetime

# Local
from services.logger import StructuredLogger
from backend.app.shared.base_service import BaseService
from backend.app.modules.jobs.services.jobs_service import JobsService
from backend.app.core.exceptions import InternalError


class DashboardService(BaseService):
    """
    Service for dashboard business logic.
    
    Handles:
    - Stats calculation
    - Metrics aggregation
    - Timeline processing
    - Analytics integration
    """
    
    def __init__(self, jobs_service: Optional[JobsService] = None):
        """
        Initialize dashboard service.
        
        Args:
            jobs_service: JobsService instance. If None, creates new instance.
        """
        super().__init__("dashboard_service")
        self.jobs_service = jobs_service or JobsService()
    
    def get_stats(self, account_id: Optional[str] = None) -> Dict:
        """
        Get dashboard statistics.
        
        Args:
            account_id: Optional account ID filter
        
        Returns:
            Dictionary with stats (total_jobs, pending_jobs, completed_jobs, failed_jobs, success_rate)
        """
        try:
            # Get jobs using JobsService (not JobsAPI)
            jobs = self.jobs_service.get_all_jobs(
                account_id=account_id,
                reload=False
            )
            
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
            
            return stats
        except Exception as e:
            self.logger.log_step(
                step="GET_DASHBOARD_STATS",
                result="ERROR",
                error=f"Failed to get dashboard stats: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to retrieve dashboard stats: {str(e)}")
    
    def get_metrics(self, account_id: Optional[str] = None) -> Dict:
        """
        Get dashboard metrics.
        
        Args:
            account_id: Optional account ID filter
        
        Returns:
            Dictionary with metrics (jobs_by_status, jobs_by_platform, posts_timeline, hourly_distribution, analytics)
        """
        try:
            # Get jobs using JobsService
            jobs = self.jobs_service.get_all_jobs(
                account_id=account_id,
                reload=False
            )
            
            # Calculate basic metrics from jobs
            metrics = {
                "jobs_by_status": {},
                "jobs_by_platform": {},
                "posts_timeline": [],
                "hourly_distribution": {}
            }
            
            for job in jobs:
                status = job.get("status", "unknown")
                platform = job.get("platform", "unknown")
                
                metrics["jobs_by_status"][status] = metrics["jobs_by_status"].get(status, 0) + 1
                metrics["jobs_by_platform"][platform] = metrics["jobs_by_platform"].get(platform, 0) + 1
                
                # Timeline data
                created_at = job.get("created_at")
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            date_obj = created_at
                        date_str = date_obj.strftime("%Y-%m-%d")
                        hour = date_obj.hour
                        
                        # Add to timeline
                        found = False
                        for item in metrics["posts_timeline"]:
                            if item.get("date") == date_str:
                                item[platform] = item.get(platform, 0) + 1
                                found = True
                                break
                        if not found:
                            metrics["posts_timeline"].append({
                                "date": date_str,
                                platform: 1
                            })
                        
                        # Hourly distribution
                        metrics["hourly_distribution"][str(hour)] = metrics["hourly_distribution"].get(str(hour), 0) + 1
                    except Exception:
                        pass
            
            # If account_id provided, try to get analytics data
            if account_id:
                try:
                    from backend.api.dependencies import get_analytics_api
                    analytics_api = get_analytics_api()
                    analytics_data = analytics_api.get_account_dashboard_data(account_id=account_id, days=30)
                    metrics["analytics"] = analytics_data
                except Exception as e:
                    # Fallback if analytics not available
                    self.logger.log_step(
                        step="GET_DASHBOARD_METRICS_ANALYTICS",
                        result="WARNING",
                        error=f"Analytics not available: {str(e)}",
                        account_id=account_id,
                        error_type=type(e).__name__
                    )
                    pass
            
            return metrics
        except Exception as e:
            self.logger.log_step(
                step="GET_DASHBOARD_METRICS",
                result="ERROR",
                error=f"Failed to get dashboard metrics: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to retrieve dashboard metrics: {str(e)}")
    
    def get_activity(self, account_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get recent activity.
        
        Args:
            account_id: Optional account ID filter
            limit: Number of activities to return
        
        Returns:
            List of recent jobs sorted by created_at
        """
        try:
            # Get jobs using JobsService
            jobs = self.jobs_service.get_all_jobs(
                account_id=account_id,
                reload=False
            )
            
            # Sort by created_at and limit
            sorted_jobs = sorted(
                jobs,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )[:limit]
            
            return sorted_jobs
        except Exception as e:
            self.logger.log_step(
                step="GET_DASHBOARD_ACTIVITY",
                result="ERROR",
                error=f"Failed to get dashboard activity: {str(e)}",
                account_id=account_id,
                limit=limit,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to retrieve recent activity: {str(e)}")
