"""
Selectors API routes.

FastAPI routes for selectors operations.
"""

# Standard library
from typing import Dict
from fastapi import APIRouter, Query, Body

# Local
from backend.app.modules.selectors.controllers import SelectorsController

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        _controller = SelectorsController()
    return _controller


@router.get("")
async def get_selectors(
    platform: str = Query(default="threads", description="Platform name"),
    version: str = Query(default="v1", description="Selector version")
):
    """Get selectors for a platform and version."""
    controller = _get_controller()
    return await controller.get_selectors(platform=platform, version=version)


@router.put("")
async def update_selectors(selectors_data: Dict = Body(...)):
    """Update selectors."""
    controller = _get_controller()
    return await controller.update_selectors(selectors_data)


@router.get("/versions")
async def get_versions(
    platform: str = Query(default="threads", description="Platform name")
):
    """Get all available versions for a platform."""
    controller = _get_controller()
    return await controller.get_versions(platform=platform)


@router.get("/metadata")
async def get_metadata(
    platform: str = Query(default="threads", description="Platform name"),
    version: str = Query(default="v1", description="Selector version")
):
    """Get metadata for a selector version."""
    controller = _get_controller()
    return await controller.get_metadata(platform=platform, version=version)


@router.delete("/{version}")
async def delete_version(
    version: str,
    platform: str = Query(default="threads", description="Platform name")
):
    """Delete a selector version."""
    controller = _get_controller()
    return await controller.delete_version(platform=platform, version=version)
