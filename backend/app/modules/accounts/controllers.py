"""
Accounts controller.

Request/response handling layer.
Transforms service responses to API responses.
"""

# Standard library
from typing import Dict, List

# Local
from backend.app.core.responses import success_response
from backend.app.core.exceptions import NotFoundError, ValidationError, InternalError
from backend.app.modules.accounts.services.accounts_service import AccountsService
from backend.app.modules.accounts.schemas import AccountCreate


class AccountsController:
    """
    Controller for accounts endpoints.
    
    Handles:
    - Request validation (using schemas)
    - Calling service layer
    - Transforming service response to API response
    - HTTP status codes
    """
    
    def __init__(self, service: AccountsService = None):
        """
        Initialize accounts controller.
        
        Args:
            service: AccountsService instance. If None, creates new instance.
        """
        self.service = service or AccountsService()
    
    async def list_accounts(self) -> Dict:
        """
        List accounts endpoint.
        
        Returns:
            API response with list of accounts
        """
        accounts = self.service.list_accounts()
        return success_response(
            data=accounts,
            message="Accounts retrieved successfully"
        )
    
    async def get_account(self, account_id: str) -> Dict:
        """
        Get account by ID endpoint.
        
        Args:
            account_id: Account ID
        
        Returns:
            API response with account data
        
        Raises:
            NotFoundError: If account not found
        """
        account = self.service.get_account(account_id)
        return success_response(
            data=account,
            message="Account retrieved successfully"
        )
    
    async def create_account(self, account_data: Dict) -> Dict:
        """
        Create account endpoint.
        
        Args:
            account_data: Account creation data (must include account_id)
        
        Returns:
            API response with created account_id
        
        Raises:
            ValidationError: If account_id is missing or invalid
            InternalError: If creation fails
        """
        # Validate using schema
        try:
            account_create = AccountCreate(**account_data)
            account_id = account_create.account_id
        except Exception as e:
            raise ValidationError(
                message=f"Invalid account data: {str(e)}",
                details={"field": "account_id"}
            )
        
        result = self.service.create_account(account_id)
        return success_response(
            data=result,
            message="Account created successfully"
        )
    
    async def delete_account(self, account_id: str) -> Dict:
        """
        Delete account endpoint.
        
        Args:
            account_id: Account ID to delete
        
        Returns:
            API response with deleted account_id
        
        Raises:
            NotFoundError: If account not found
            InternalError: If deletion fails
        """
        result = self.service.delete_account(account_id)
        return success_response(
            data=result,
            message="Account deleted successfully"
        )
    
    async def get_account_stats(self, account_id: str) -> Dict:
        """
        Get account statistics endpoint.
        
        Args:
            account_id: Account ID
        
        Returns:
            API response with account statistics
        
        Raises:
            NotFoundError: If account not found
        """
        stats = self.service.get_account_stats(account_id)
        return success_response(
            data=stats,
            message="Account stats retrieved successfully"
        )
