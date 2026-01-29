"""
Excel API routes.

REST API endpoints cho Excel upload operations.

LEGACY ROUTES - Using adapter pattern to call new services when available.
"""

# Standard library
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse

# Third-party
import aiofiles

# Local
from backend.api.adapters.accounts_adapter import AccountsAPI
from backend.api.adapters.jobs_adapter import JobsAPI
from backend.api.dependencies import get_accounts_api, get_jobs_api
from backend.app.core.responses import success_response
from backend.app.core.exceptions import NotFoundError, InternalError
from backend.app.core.migration_flags import is_module_enabled

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        try:
            from backend.app.modules.excel.controllers import ExcelController
            _controller = ExcelController()
        except ImportError:
            _controller = None
    return _controller


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    account_id: Optional[str] = Form(None, description="Account ID")
):
    """Upload and process Excel file."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("excel"):
        controller = _get_controller()
        if controller:
            try:
                result = await controller.upload_file(file=file, account_id=account_id)
                return result
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation - Use ExcelService directly
    try:
        # Try to use ExcelService directly (even if module not enabled)
        try:
            from backend.app.modules.excel.services.excel_service import ExcelService
            service = ExcelService()
            result = await service.upload_file(file=file, account_id=account_id)
            return success_response(
                data=result,
                message=(
                    f"Excel file uploaded successfully. "
                    f"Created {result.get('jobs_created', 0)} job(s) from {result.get('scheduled_posts', 0)} scheduled post(s)."
                    if result.get("jobs_created", 0) > 0
                    else f"Excel file uploaded successfully. Found {result.get('total_posts', 0)} post(s), but no scheduled posts to create jobs."
                )
            )
        except ImportError as e:
            # Fallback to basic response if ExcelService not available
            return success_response(
                data={"filename": file.filename, "account_id": account_id},
                message="Excel file uploaded successfully (processing not available)"
            )
    except Exception as e:
        raise InternalError(message=f"Failed to upload Excel file: {str(e)}")


@router.get("/template")
async def download_template():
    """Download Excel template."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("excel"):
        controller = _get_controller()
        if controller:
            try:
                return controller.get_template()
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        # Get template file path
        template_path = Path("schemas/job_template.json")
        if not template_path.exists():
            raise NotFoundError(resource="Template", details={"path": str(template_path)})
        
        # Return template file
        return FileResponse(
            template_path,
            filename="job_template.json",
            media_type="application/json"
        )
    except (NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to download template: {str(e)}")
