"""
Config API routes.

FastAPI routes for config operations.
"""

# Standard library
from typing import Dict
from fastapi import APIRouter, Body

# Local
from backend.app.modules.config.controllers import ConfigController

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        _controller = ConfigController()
    return _controller


@router.get("")
async def get_config():
    """Get current configuration."""
    controller = _get_controller()
    return await controller.get_config()


@router.put("")
async def update_config(config_data: Dict = Body(...)):
    """Update configuration."""
    controller = _get_controller()
    return await controller.update_config(config_data)
