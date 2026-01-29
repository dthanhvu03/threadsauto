"""
Accounts repository.

Data access layer for accounts. Wraps AccountStorage.
"""

# Standard library
from typing import List, Dict, Optional
from pathlib import Path

# Local
from services.logger import StructuredLogger
from services.storage.accounts_storage import AccountStorage
from config.storage_config_loader import get_storage_config_from_env
from backend.app.shared.base_repository import BaseRepository


class AccountsRepository(BaseRepository):
    """
    Repository for account data access.
    
    Handles all interactions with AccountStorage.
    No business logic - only data access.
    """
    
    def __init__(self, use_mysql: bool = True):
        """
        Initialize accounts repository.
        
        Args:
            use_mysql: If True, use MySQL storage. If False, use file system.
        """
        self.logger = StructuredLogger(name="accounts_repository")
        self.use_mysql = use_mysql
        
        # Initialize AccountStorage
        self.account_storage = None
        if use_mysql:
            try:
                storage_config = get_storage_config_from_env()
                mysql_config = storage_config.mysql
                self.account_storage = AccountStorage(
                    host=mysql_config.host,
                    port=mysql_config.port,
                    user=mysql_config.user,
                    password=mysql_config.password,
                    database=mysql_config.database,
                    charset=mysql_config.charset,
                    logger=self.logger
                )
            except Exception as e:
                self.logger.log_step(
                    step="INIT_ACCOUNTS_REPOSITORY",
                    result="WARNING",
                    error=f"Failed to initialize MySQL storage, falling back to file system: {str(e)}",
                    error_type=type(e).__name__
                )
                self.use_mysql = False
                self.account_storage = None
        
        # Setup profiles directory (for file system fallback)
        _base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.profiles_dir = _base_dir / "profiles"
        
        if not self.use_mysql:
            try:
                self.profiles_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                self.logger.log_step(
                    step="INIT_ACCOUNTS_REPOSITORY",
                    result="WARNING",
                    error=f"Could not create profiles directory: {str(e)}",
                    error_type=type(e).__name__,
                    profiles_dir=str(self.profiles_dir)
                )
    
    def _get_active_scheduler(self):
        """Get active scheduler instance."""
        try:
            from ui.utils import get_active_scheduler
            return get_active_scheduler()
        except Exception as e:
            self.logger.log_step(
                step="GET_ACTIVE_SCHEDULER",
                result="WARNING",
                error=f"Could not get active scheduler: {str(e)}",
                error_type=type(e).__name__
            )
            return None
    
    def _get_jobs_count_from_mysql(self, account_id: str) -> int:
        """Get jobs count from MySQL directly."""
        if not self.account_storage:
            return 0
        
        try:
            import pymysql
            from services.storage.connection_pool import get_connection_pool
            from config.storage_config_loader import get_storage_config_from_env
            
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            
            pool = get_connection_pool(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database
            )
            
            with pool.get_connection() as conn:
                import pymysql.cursors
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    query = "SELECT COUNT(*) as count FROM jobs WHERE account_id = %s"
                    cursor.execute(query, (account_id,))
                    result = cursor.fetchone()
                    
                    if result and isinstance(result, dict):
                        count = result.get('count', 0)
                    elif result and isinstance(result, (list, tuple)):
                        count = result[0] if len(result) > 0 else 0
                    else:
                        count = 0
                    
                    return int(count) if count else 0
        except Exception as e:
            self.logger.log_step(
                step="GET_JOBS_COUNT_FROM_MYSQL",
                result="WARNING",
                error=f"Failed to get jobs count from MySQL: {str(e)}",
                account_id=account_id,
                error_type=type(e).__name__
            )
            return 0
    
    def get_all(
        self,
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all accounts, optionally filtered.
        
        Args:
            filters: Optional filter criteria (not used for accounts)
            limit: Optional limit on number of results
            offset: Optional offset for pagination
        
        Returns:
            List of account dictionaries
        """
        accounts = self.list_all()
        
        # Apply pagination if specified
        if offset is not None:
            accounts = accounts[offset:]
        if limit is not None:
            accounts = accounts[:limit]
        
        return accounts
    
    def list_all(self) -> List[Dict]:
        """
        List all accounts.
        
        Returns:
            List of account dictionaries with jobs_count
        """
        # Use MySQL if available
        if self.use_mysql and self.account_storage:
            try:
                mysql_accounts = self.account_storage.list_accounts()
                
                accounts = []
                for account in mysql_accounts:
                    account_id = account["account_id"]
                    jobs_count = self._get_jobs_count_from_mysql(account_id)
                    
                    account_dict = {
                        "account_id": account_id,
                        "jobs_count": jobs_count,
                        "profile_path": account.get("profile_path"),
                        "metadata": account.get("metadata")
                    }
                    accounts.append(account_dict)
                
                self.logger.log_step(
                    step="LIST_ACCOUNTS",
                    result="SUCCESS",
                    note=f"Listed {len(accounts)} accounts from MySQL",
                    accounts_count=len(accounts)
                )
                return accounts
            except Exception as e:
                self.logger.log_step(
                    step="LIST_ACCOUNTS",
                    result="WARNING",
                    error=f"Failed to load from MySQL, falling back to file system: {str(e)}",
                    error_type=type(e).__name__
                )
                # Fall through to file system
        
        # Fallback to file system
        accounts = []
        try:
            if not self.profiles_dir.exists():
                return accounts
            
            scheduler = self._get_active_scheduler()
            
            for profile_dir in self.profiles_dir.iterdir():
                try:
                    if profile_dir.is_dir() and not profile_dir.name.startswith('.'):
                        account_id = profile_dir.name
                        
                        # Get jobs count
                        jobs_count = 0
                        if self.use_mysql and self.account_storage:
                            jobs_count = self._get_jobs_count_from_mysql(account_id)
                        elif scheduler:
                            try:
                                jobs_count = len(scheduler.list_jobs(account_id=account_id))
                            except Exception:
                                jobs_count = 0
                        
                        # Get metadata from MySQL if available
                        metadata = None
                        if self.use_mysql and self.account_storage:
                            try:
                                account_from_db = self.account_storage.get_account(account_id)
                                if account_from_db:
                                    metadata = account_from_db.get("metadata")
                            except Exception:
                                pass
                        
                        account_dict = {
                            "account_id": account_id,
                            "jobs_count": jobs_count,
                            "profile_path": str(profile_dir),
                            "metadata": metadata
                        }
                        accounts.append(account_dict)
                except (PermissionError, OSError) as e:
                    self.logger.log_step(
                        step="LIST_ACCOUNTS",
                        result="WARNING",
                        error=f"Error accessing directory: {str(e)}",
                        error_type=type(e).__name__,
                        profile_dir=str(profile_dir)
                    )
                    continue
                except Exception as e:
                    self.logger.log_step(
                        step="LIST_ACCOUNTS",
                        result="WARNING",
                        error=f"Error processing directory: {str(e)}",
                        error_type=type(e).__name__,
                        profile_dir=str(profile_dir)
                    )
                    continue
            
            # Sort accounts
            try:
                sorted_accounts = sorted(accounts, key=lambda x: x.get('account_id', ''))
                return sorted_accounts
            except Exception:
                return accounts
        except Exception as e:
            self.logger.log_step(
                step="LIST_ACCOUNTS",
                result="ERROR",
                error=f"Failed to list accounts: {str(e)}",
                error_type=type(e).__name__
            )
            return []
    
    def get_by_id(self, account_id: str) -> Optional[Dict]:
        """
        Get account by ID.
        
        Args:
            account_id: Account ID
        
        Returns:
            Account dictionary if found, None otherwise
        """
        accounts = self.list_all()
        return next((acc for acc in accounts if acc.get("account_id") == account_id), None)
    
    def create(self, entity_data: Dict) -> Dict:
        """
        Create new account profile.
        
        Args:
            entity_data: Dictionary containing account_id
        
        Returns:
            Created account dictionary
        """
        account_id = entity_data.get("account_id") if isinstance(entity_data, dict) else str(entity_data)
        
        # Validate account_id
        if not account_id or not isinstance(account_id, str):
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"Invalid account_id: {account_id}",
                account_id=account_id
            )
            raise ValueError(f"Invalid account_id: {account_id}")
        
        account_id = account_id.strip()
        if not account_id:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error="account_id cannot be empty or only spaces",
                account_id=account_id
            )
            raise ValueError("account_id cannot be empty or only spaces")
        
        # Validate account_id format
        import re
        if re.search(r'[<>:"/\\|?*]', account_id):
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"account_id contains invalid characters: {account_id}",
                account_id=account_id
            )
            raise ValueError(f"account_id contains invalid characters: {account_id}")
        
        try:
            profile_path = self.profiles_dir / account_id
            
            # Check if already exists
            if profile_path.exists():
                if profile_path.is_dir():
                    # Already exists, return True (idempotent)
                self.logger.log_step(
                    step="CREATE_ACCOUNT",
                    result="SUCCESS",
                    note="Account already exists",
                    account_id=account_id
                )
                return {"account_id": account_id, "profile_path": str(profile_path)}
                else:
                self.logger.log_step(
                    step="CREATE_ACCOUNT",
                    result="ERROR",
                    error=f"Path exists but is not a directory: {profile_path}",
                    account_id=account_id
                )
                raise ValueError(f"Path exists but is not a directory: {profile_path}")
            
            # Create directory
            profile_path.mkdir(parents=True, exist_ok=True)
            
            # Verify creation
            if profile_path.exists() and profile_path.is_dir():
                self.logger.log_step(
                    step="CREATE_ACCOUNT",
                    result="SUCCESS",
                    account_id=account_id,
                    profile_path=str(profile_path)
                )
                return {"account_id": account_id, "profile_path": str(profile_path)}
            else:
                self.logger.log_step(
                    step="CREATE_ACCOUNT",
                    result="ERROR",
                    error=f"Failed to verify directory creation: {profile_path}",
                    account_id=account_id
                )
                raise RuntimeError(f"Failed to verify directory creation: {profile_path}")
        except (PermissionError, OSError) as e:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"OS error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            raise
        except Exception as e:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            raise
    
    def update(self, account_id: str, entity_data: Dict) -> Optional[Dict]:
        """
        Update account (not supported for accounts - accounts are immutable).
        
        Args:
            account_id: Account ID
            entity_data: Updated account data (not used)
        
        Returns:
            None (accounts cannot be updated)
        """
        # Accounts are immutable - cannot be updated
        # This method exists to satisfy BaseRepository interface
        return None
    
    def delete(self, account_id: str) -> bool:
        """
        Delete account profile.
        
        Args:
            account_id: Account ID to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            profile_path = self.profiles_dir / account_id
            
            if not profile_path.exists():
                self.logger.log_step(
                    step="DELETE_ACCOUNT",
                    result="WARNING",
                    error="Account does not exist",
                    account_id=account_id
                )
                return False
            
            if not profile_path.is_dir():
                self.logger.log_step(
                    step="DELETE_ACCOUNT",
                    result="ERROR",
                    error=f"Path exists but is not a directory: {profile_path}",
                    account_id=account_id
                )
                return False
            
            # Delete directory
            import shutil
            shutil.rmtree(profile_path)
            
            # Verify deletion
            if not profile_path.exists():
                self.logger.log_step(
                    step="DELETE_ACCOUNT",
                    result="SUCCESS",
                    account_id=account_id
                )
                return True
            else:
                self.logger.log_step(
                    step="DELETE_ACCOUNT",
                    result="ERROR",
                    error="Failed to verify directory deletion",
                    account_id=account_id
                )
                return False
        except (PermissionError, OSError) as e:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"OS error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return False
        except Exception as e:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return False
