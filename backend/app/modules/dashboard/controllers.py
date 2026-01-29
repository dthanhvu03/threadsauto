"""
Dashboard controller.

Request/response handling layer.
Transforms service responses to API responses.
"""

# Standard library
from typing import Dict, List, Optional

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import InternalError
from backend.app.modules.dashboard.services.dashboard_service import DashboardService


class DashboardController:
    """
    Controller for dashboard endpoints.
    
    Handles:
    - Request validation
    - Calling service layer
    - Transforming service response to API response
    """
    
    def __init__(self, service: Optional[DashboardService] = None):
        """
        Initialize dashboard controller.
        
        Args:
            service: DashboardService instance. If None, creates new instance.
        """
        self.service = service or DashboardService()
    
    async def get_stats(self, account_id: Optional[str] = None) -> Dict:
        """
        Get dashboard statistics endpoint.
        
        Args:
            account_id: Optional account ID filter
        
        Returns:
            API response with dashboard stats
        """
        stats = self.service.get_stats(account_id=account_id)
        return success_response(
            data=stats,
            message="Dashboard stats retrieved successfully"
        )
    
    async def get_metrics(self, account_id: Optional[str] = None) -> Dict:
        """
        Get dashboard metrics endpoint.
        
        Args:
            account_id: Optional account ID filter
        
        Returns:
            API response with dashboard metrics
        """
        metrics = self.service.get_metrics(account_id=account_id)
        return success_response(
            data=metrics,
            message="Dashboard metrics retrieved successfully"
        )
    
    async def get_activity(
        self,
        account_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        """
        Get recent activity endpoint.
        
        Args:
            account_id: Optional account ID filter
            limit: Number of activities to return
        
        Returns:
            API response with recent activity
        """
        activity = self.service.get_activity(account_id=account_id, limit=limit)
        return success_response(
            data=activity,
            message="Recent activity retrieved successfully"
        )
