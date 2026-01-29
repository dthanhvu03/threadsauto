"""
Accounts API routes.

REST API endpoints cho account operations.

LEGACY ROUTES - Using adapter pattern to call new services when available.
"""

# Standard library
from typing import List, Optional, Dict
from fastapi import APIRouter, Query, Body

# Local
from backend.api.adapters.accounts_adapter import AccountsAPI
from backend.api.dependencies import get_accounts_api
from backend.app.core.responses import success_response
from backend.app.core.exceptions import NotFoundError, InternalError, ValidationError
from backend.app.core.migration_flags import is_module_enabled
from backend.app.core.validation import validate_account_id
from utils.sanitize import sanitize_user_input

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        try:
            from backend.app.modules.accounts.controllers import AccountsController
            _controller = AccountsController()
        except ImportError:
            _controller = None
    return _controller


@router.get("")
async def list_accounts():
    """List all accounts."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("accounts"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.list_accounts()
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        accounts_api = get_accounts_api()
        accounts = accounts_api.list_accounts()
        
        # Debug: Log accounts data
        import logging
        logger = logging.getLogger("fastapi_backend")
        logger.info(f"List accounts: Found {len(accounts)} accounts")
        for acc in accounts:
            logger.info(f"  - {acc.get('account_id')}: jobs_count={acc.get('jobs_count', 'N/A')}")
        
        return success_response(data=accounts, message="Accounts retrieved successfully")
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve accounts: {str(e)}")


@router.get("/{account_id}")
async def get_account(account_id: str):
    """Get account by ID."""
    # Validate account_id format
    is_valid, error_message = validate_account_id(account_id)
    if not is_valid:
        raise ValidationError(message=error_message or "Invalid account_id", details={"field": "account_id"})
    
    # Sanitize account_id
    sanitized_account_id = sanitize_user_input(account_id, input_type="account_id")
    
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("accounts"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_account(sanitized_account_id)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        accounts_api = get_accounts_api()
        # Get account from list_accounts and filter by account_id
        accounts = accounts_api.list_accounts()
        account = next((acc for acc in accounts if acc.get("account_id") == sanitized_account_id), None)
        if not account:
            raise NotFoundError(resource="Account", details={"account_id": sanitized_account_id})
        return success_response(data=account, message="Account retrieved successfully")
    except (NotFoundError, InternalError, ValidationError):
        raise
    except Exception as e:
        raise InternalError(message="Failed to retrieve account")


@router.post("")
async def create_account(account_data: Dict = Body(...)):
    """Create a new account."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("accounts"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.create_account(account_data)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        accounts_api = get_accounts_api()
        account_id = account_data.get("account_id")
        if not account_id:
            raise ValidationError(message="account_id is required", details={"field": "account_id"})
        
        # Validate account_id format
        is_valid, error_message = validate_account_id(account_id)
        if not is_valid:
            raise ValidationError(message=error_message or "Invalid account_id", details={"field": "account_id"})
        
        # Sanitize account_id
        sanitized_account_id = sanitize_user_input(account_id, input_type="account_id")
        
        # Create account using AccountsAPI
        success = accounts_api.create_account(sanitized_account_id)
        if not success:
            raise InternalError(message="Failed to create account")
        
        return success_response(
            data={"account_id": sanitized_account_id},
            message="Account created successfully"
        )
    except (ValidationError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message="Failed to create account")


@router.delete("/{account_id}")
async def delete_account(account_id: str):
    """Delete an account."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("accounts"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.delete_account(account_id)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        accounts_api = get_accounts_api()
        # Delete account using AccountsAPI
        success = accounts_api.delete_account(account_id)
        if not success:
            raise InternalError(message="Failed to delete account", details={"account_id": account_id})
        
        return success_response(
            data={"account_id": account_id},
            message="Account deleted successfully"
        )
    except (NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to delete account: {str(e)}")


@router.get("/{account_id}/stats")
async def get_account_stats(account_id: str):
    """Get account statistics."""
    # Adapter pattern: Use new controller if available, else fallback to legacy
    if is_module_enabled("accounts"):
        controller = _get_controller()
        if controller:
            try:
                return await controller.get_account_stats(account_id)
            except Exception as e:
                # Fallback to legacy if new controller fails
                pass
    
    # Legacy implementation
    try:
        accounts_api = get_accounts_api()
        # Get account info first
        accounts = accounts_api.list_accounts()
        account = next((acc for acc in accounts if acc.get("account_id") == account_id), None)
        if not account:
            raise NotFoundError(resource="Account", details={"account_id": account_id})
        
        # Build stats from account data
        stats = {
            "account_id": account_id,
            "jobs_count": account.get("jobs_count", 0),
            "profile_path": account.get("profile_path"),
            "metadata": account.get("metadata")
        }
        
        return success_response(data=stats, message="Account stats retrieved successfully")
    except (NotFoundError, InternalError):
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve account stats: {str(e)}")
