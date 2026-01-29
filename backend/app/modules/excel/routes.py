"""
Excel API routes.

FastAPI routes for Excel operations.
"""

# Standard library
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form

# Local
from backend.app.modules.excel.controllers import ExcelController

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        _controller = ExcelController()
    return _controller


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    account_id: Optional[str] = Form(None, description="Account ID")
):
    """Upload and process Excel file."""
    controller = _get_controller()
    result = await controller.upload_file(file=file, account_id=account_id)
    return result


@router.get("/template")
async def download_template():
    """Download Excel template."""
    controller = _get_controller()
    return controller.get_template()
