"""
Config API routes.

REST API endpoints cho configuration management.

LEGACY ROUTES - Using adapter pattern to call new services when available.
"""

# Standard library
from typing import Dict
from fastapi import APIRouter, Body

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import InternalError
from backend.app.core.migration_flags import is_module_enabled
from config.config import Config, RunMode
from config.storage import load_config, save_config, _config_to_dict, _dict_to_config

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        try:
            from backend.app.modules.config.controllers import ConfigController
            _controller = ConfigController()
        except ImportError:
            _controller = None
    return _controller


@router.get("")
async def get_config():
    """Get current configuration from database."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("config"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_config()
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        # Load config from database (falls back to defaults if not found)
        config = load_config()
        
        # Convert to dict for API response
        config_dict = _config_to_dict(config)
        
        # Add run_mode as top-level (for backward compatibility)
        config_dict["run_mode"] = config.mode.value
        
        return success_response(
            data=config_dict,
            message="Configuration retrieved successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve configuration: {str(e)}")


@router.put("")
async def update_config(config_data: Dict = Body(...)):
    """Update configuration and save to database."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("config"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.update_config(config_data)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        # Load current config (or create new with defaults)
        current_config = load_config()
        
        # Convert dict to Config object
        updated_config = _dict_to_config(config_data)
        
        # Handle run_mode separately (it's top-level in dict but mode in Config)
        if "run_mode" in config_data:
            try:
                updated_config.mode = RunMode(config_data["run_mode"])
            except (ValueError, KeyError):
                pass  # Keep current mode if invalid
        
        # Save to database
        save_config(updated_config)
        
        # Return updated config as dict
        config_dict = _config_to_dict(updated_config)
        config_dict["run_mode"] = updated_config.mode.value
        
        return success_response(
            data=config_dict,
            message="Configuration updated successfully"
        )
    except Exception as e:
        raise InternalError(message=f"Failed to update configuration: {str(e)}")
