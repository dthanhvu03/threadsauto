"""
Accounts service.

Business logic layer for account operations.
Handles validation, orchestration, and business rules.
"""

# Standard library
from typing import List, Dict, Optional

# Local
from services.logger import StructuredLogger
from backend.app.shared.base_service import BaseService
from backend.app.modules.accounts.repositories.accounts_repository import AccountsRepository
from backend.app.core.exceptions import ValidationError, NotFoundError, InternalError


class AccountsService(BaseService):
    """
    Service for account business logic.
    
    Handles:
    - Validation
    - Business rules
    - Orchestration
    - Safety checks
    """
    
    def __init__(self, repository: Optional[AccountsRepository] = None):
        """
        Initialize accounts service.
        
        Args:
            repository: AccountsRepository instance. If None, creates new instance.
        """
        super().__init__("accounts_service")
        self.repository = repository or AccountsRepository()
    
    def list_accounts(self) -> List[Dict]:
        """
        List all accounts.
        
        Returns:
            List of account dictionaries with jobs_count
        """
        try:
            accounts = self.repository.list_all()
            return accounts
        except Exception as e:
            self.logger.log_step(
                step="LIST_ACCOUNTS",
                result="ERROR",
                error=f"Failed to list accounts: {str(e)}",
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to list accounts: {str(e)}")
    
    def get_account(self, account_id: str) -> Dict:
        """
        Get account by ID.
        
        Args:
            account_id: Account ID
        
        Returns:
            Account dictionary
        
        Raises:
            NotFoundError: If account not found
        """
        try:
            account = self.repository.get_by_id(account_id)
            if not account:
                raise NotFoundError(
                    resource="Account",
                    details={"account_id": account_id}
                )
            return account
        except (NotFoundError, InternalError):
            raise
        except Exception as e:
            self.logger.log_step(
                step="GET_ACCOUNT",
                result="ERROR",
                error=f"Failed to get account: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to get account: {str(e)}")
    
    def create_account(self, account_id: str) -> Dict:
        """
        Create new account.
        
        Args:
            account_id: Account ID to create
        
        Returns:
            Dictionary with account_id
        
        Raises:
            ValidationError: If account_id is invalid
            InternalError: If creation fails
        """
        # Validate account_id
        if not account_id or not isinstance(account_id, str):
            raise ValidationError(
                message="account_id is required and must be a string",
                details={"field": "account_id"}
            )
        
        account_id = account_id.strip()
        if not account_id:
            raise ValidationError(
                message="account_id cannot be empty or only spaces",
                details={"field": "account_id"}
            )
        
        try:
            result = self.repository.create({"account_id": account_id})
            return result
        except (ValidationError, InternalError):
            raise
        except Exception as e:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"Failed to create account: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to create account: {str(e)}")
    
    def delete_account(self, account_id: str) -> Dict:
        """
        Delete account.
        
        Args:
            account_id: Account ID to delete
        
        Returns:
            Dictionary with account_id
        
        Raises:
            NotFoundError: If account not found
            InternalError: If deletion fails
        """
        # Check if account exists
        account = self.repository.get_by_id(account_id)
        if not account:
            raise NotFoundError(
                resource="Account",
                details={"account_id": account_id}
            )
        
        try:
            success = self.repository.delete(account_id)
            if not success:
                raise InternalError(
                    message="Failed to delete account",
                    details={"account_id": account_id}
                )
            
            return {"account_id": account_id}
        except (NotFoundError, InternalError):
            raise
        except Exception as e:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Failed to delete account: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to delete account: {str(e)}")
    
    def get_account_stats(self, account_id: str) -> Dict:
        """
        Get account statistics.
        
        Args:
            account_id: Account ID
        
        Returns:
            Account statistics dictionary
        
        Raises:
            NotFoundError: If account not found
        """
        try:
            account = self.get_account(account_id)
            
            # Build stats from account data
            stats = {
                "account_id": account_id,
                "jobs_count": account.get("jobs_count", 0),
                "profile_path": account.get("profile_path"),
                "metadata": account.get("metadata")
            }
            
            return stats
        except (NotFoundError, InternalError):
            raise
        except Exception as e:
            self.logger.log_step(
                step="GET_ACCOUNT_STATS",
                result="ERROR",
                error=f"Failed to get account stats: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to get account stats: {str(e)}")
