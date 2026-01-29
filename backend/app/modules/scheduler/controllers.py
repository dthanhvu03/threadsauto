"""
Scheduler controller.

Request/response handling layer.
Transforms service responses to API responses.
"""

# Standard library
from typing import Dict, Optional

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import InternalError
from backend.app.modules.scheduler.services.scheduler_service import SchedulerService


class SchedulerController:
    """
    Controller for scheduler endpoints.
    
    Handles:
    - Request validation
    - Calling service layer
    - Transforming service response to API response
    """
    
    def __init__(self, service: Optional[SchedulerService] = None):
        """
        Initialize scheduler controller.
        
        Args:
            service: SchedulerService instance. If None, creates new instance (singleton).
        """
        self.service = service or SchedulerService()
    
    async def start(self, account_id: Optional[str] = None) -> Dict:
        """
        Start scheduler endpoint.
        
        Args:
            account_id: Optional account ID filter
        
        Returns:
            API response with scheduler status
        """
        result = self.service.start(account_id=account_id)
        return success_response(
            data=result,
            message=result.get("message", "Scheduler started successfully")
        )
    
    async def stop(self) -> Dict:
        """
        Stop scheduler endpoint.
        
        Returns:
            API response with scheduler status
        """
        result = await self.service.stop()
        
        return success_response(
            data=result,
            message=result.get("message", "Scheduler stopped successfully")
        )
    
    async def get_status(self) -> Dict:
        """
        Get scheduler status endpoint.
        
        Returns:
            API response with scheduler status
        """
        status_data = self.service.get_status()
        return success_response(
            data=status_data,
            message="Scheduler status retrieved successfully"
        )
    
    async def get_active_jobs(self) -> Dict:
        """
        Get active jobs endpoint.
        
        Returns:
            API response with list of active jobs
        """
        active_jobs = self.service.get_active_jobs()
        return success_response(
            data=active_jobs,
            message="Active jobs retrieved successfully"
        )
