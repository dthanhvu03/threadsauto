"""
Accounts API routes.

FastAPI routes for account operations.
"""

# Standard library
from typing import Dict
from fastapi import APIRouter, Body

# Local
from backend.app.modules.accounts.controllers import AccountsController

router = APIRouter()

# Import controller at module scope (NOT in request handler)
_controller = None


def _get_controller():
    """Get controller instance (singleton pattern)."""
    global _controller
    if _controller is None:
        _controller = AccountsController()
    return _controller


@router.get("")
async def list_accounts():
    """List all accounts."""
    controller = _get_controller()
    return await controller.list_accounts()


@router.get("/{account_id}")
async def get_account(account_id: str):
    """Get account by ID."""
    controller = _get_controller()
    return await controller.get_account(account_id)


@router.post("")
async def create_account(account_data: Dict = Body(...)):
    """Create a new account."""
    controller = _get_controller()
    return await controller.create_account(account_data)


@router.delete("/{account_id}")
async def delete_account(account_id: str):
    """Delete an account."""
    controller = _get_controller()
    return await controller.delete_account(account_id)


@router.get("/{account_id}/stats")
async def get_account_stats(account_id: str):
    """Get account statistics."""
    controller = _get_controller()
    return await controller.get_account_stats(account_id)
