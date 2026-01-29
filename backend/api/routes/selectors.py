"""
Selectors API routes.

REST API endpoints cho selector management.

LEGACY ROUTES - Using adapter pattern to call new services when available.
"""

# Standard library
from typing import Dict
from fastapi import APIRouter, Query, Body

# Local
from backend.api.adapters.selectors_adapter import SelectorsAPI
from backend.api.dependencies import get_selectors_api
from backend.app.core.responses import success_response
from backend.app.core.exceptions import NotFoundError, InternalError, ValidationError
from backend.app.core.migration_flags import is_module_enabled

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        try:
            from backend.app.modules.selectors.controllers import SelectorsController
            _controller = SelectorsController()
        except ImportError:
            _controller = None
    return _controller


@router.get("")
async def get_selectors(
    platform: str = Query(default="threads", description="Platform name"),
    version: str = Query(default="v1", description="Selector version")
):
    """Get selectors for a platform and version."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("selectors"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_selectors(platform=platform, version=version)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        selectors_api = get_selectors_api()
        selectors = selectors_api.get_selectors(platform=platform, version=version)
        
        return success_response(
            data={
                "platform": platform,
                "version": version,
                "selectors": selectors
            },
            message="Selectors retrieved successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve selectors: {str(e)}")


@router.put("")
async def update_selectors(selectors_data: Dict = Body(...)):
    """Update selectors."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("selectors"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.update_selectors(selectors_data)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        selectors_api = get_selectors_api()
        platform = selectors_data.get("platform", "threads")
        version = selectors_data.get("version", "v1")
        selectors = selectors_data.get("selectors", {})
        
        if not selectors:
            raise ValidationError(message="Selectors data is required", details={"field": "selectors"})
        
        # Save selectors using API
        success = selectors_api.save_selectors(
            platform=platform,
            version=version,
            selectors=selectors
        )
        
        if not success:
            raise InternalError(message="Failed to save selectors", details={"platform": platform, "version": version})
        
        return success_response(
            data={
                "platform": platform,
                "version": version,
                "selectors": selectors
            },
            message="Selectors updated successfully"
        )
    except (ValidationError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to update selectors: {str(e)}")


@router.get("/versions")
async def get_versions(
    platform: str = Query(default="threads", description="Platform name")
):
    """Get all available versions for a platform."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("selectors"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_versions(platform=platform)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        selectors_api = get_selectors_api()
        versions = selectors_api.get_versions(platform=platform)
        
        return success_response(
            data={
                "platform": platform,
                "versions": versions
            },
            message="Versions retrieved successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve versions: {str(e)}")


@router.get("/metadata")
async def get_metadata(
    platform: str = Query(default="threads", description="Platform name"),
    version: str = Query(default="v1", description="Selector version")
):
    """Get metadata for a selector version."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("selectors"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_metadata(platform=platform, version=version)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        selectors_api = get_selectors_api()
        metadata = selectors_api.get_metadata(platform=platform, version=version)
        
        return success_response(
            data={
                "platform": platform,
                "version": version,
                "metadata": metadata
            },
            message="Metadata retrieved successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve metadata: {str(e)}")


@router.delete("/{version}")
async def delete_version(
    version: str,
    platform: str = Query(default="threads", description="Platform name")
):
    """Delete a selector version."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("selectors"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.delete_version(platform=platform, version=version)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        selectors_api = get_selectors_api()
        deleted = selectors_api.delete_version(platform=platform, version=version)
        
        if not deleted:
            raise NotFoundError(
                resource="Selector version",
                details={"platform": platform, "version": version}
            )
        
        return success_response(
            data={
                "platform": platform,
                "version": version,
                "deleted": True
            },
            message="Version deleted successfully"
        )
    except (NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to delete version: {str(e)}")
