"""
Excel controller.

Request/response handling layer.
Transforms service responses to API responses.
"""

# Standard library
from typing import Dict, Optional
from pathlib import Path
from fastapi import UploadFile
from fastapi.responses import FileResponse

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import NotFoundError, InternalError
from backend.app.modules.excel.services.excel_service import ExcelService


class ExcelController:
    """
    Controller for Excel endpoints.
    
    Handles:
    - Request validation
    - Calling service layer
    - Transforming service response to API response
    """
    
    def __init__(self, service: Optional[ExcelService] = None):
        """
        Initialize Excel controller.
        
        Args:
            service: ExcelService instance. If None, creates new instance.
        """
        self.service = service or ExcelService()
    
    async def upload_file(
        self,
        file: UploadFile,
        account_id: Optional[str] = None
    ) -> Dict:
        """
        Upload Excel file endpoint.
        
        Args:
            file: Uploaded file
            account_id: Optional account ID
        
        Returns:
            API response with upload result
        """
        result = await self.service.upload_file(file=file, account_id=account_id)
        
        # Build success message with job creation summary
        if result.get("jobs_created", 0) > 0:
            message = (
                f"Excel file uploaded successfully. "
                f"Created {result['jobs_created']} job(s) from {result.get('scheduled_posts', 0)} scheduled post(s)."
            )
            if result.get("jobs_failed", 0) > 0:
                message += f" {result['jobs_failed']} job(s) failed to create."
        else:
            message = (
                f"Excel file uploaded successfully. "
                f"Found {result.get('total_posts', 0)} post(s), "
                f"but no scheduled posts to create jobs. "
                f"({result.get('immediate_posts', 0)} immediate post(s) require manual posting)"
            )
        
        return success_response(
            data=result,
            message=message
        )
    
    def get_template(self) -> FileResponse:
        """
        Get template file endpoint.
        
        Returns:
            FileResponse with template file
        
        Raises:
            NotFoundError: If template file does not exist
        """
        template_path = self.service.get_template_path()
        
        return FileResponse(
            template_path,
            filename="job_template.json",
            media_type="application/json"
        )
