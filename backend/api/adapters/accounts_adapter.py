"""
API để quản lý accounts.

API wrapper cho account operations (orchestration layer giữa UI ↔ Scheduler ↔ Storage).
"""

# Standard library
from pathlib import Path
from typing import List, Dict, Optional

# Local
from services.logger import StructuredLogger
from services.storage.accounts_storage import AccountStorage
from config.storage_config_loader import get_storage_config_from_env


class AccountsAPI:
    """
    API để quản lý accounts.
    
    Quản lý profiles và cung cấp thông tin về accounts.
    
    NOTE: Giống JobsAPI, AccountsAPI không own scheduler instance mà resolve active scheduler
    mỗi lần cần dùng để đảm bảo consistency với Scheduler đang chạy.
    """
    
    def __init__(self, use_mysql: bool = True):
        """
        Khởi tạo AccountsAPI.
        
        Args:
            use_mysql: If True, use MySQL storage. If False, use file system.
        """
        # Initialize logger
        self.logger = StructuredLogger(name="accounts_api")
        
        self.use_mysql = use_mysql
        
        # Initialize MySQL storage if enabled
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
                    step="INIT_ACCOUNTS_API",
                    result="WARNING",
                    error=f"Failed to initialize MySQL storage, falling back to file system: {str(e)}",
                    error_type=type(e).__name__
                )
                self.use_mysql = False
                self.account_storage = None
        
        # FIX: Dùng absolute path thay vì relative path (for file system fallback)
        _base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.profiles_dir = _base_dir / "profiles"
        
        # Ensure profiles directory exists (for file system fallback)
        if not self.use_mysql:
            try:
                self.profiles_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                self.logger.log_step(
                    step="INIT_ACCOUNTS_API",
                    result="WARNING",
                    error=f"Could not create profiles directory: {str(e)}",
                    error_type=type(e).__name__,
                    profiles_dir=str(self.profiles_dir)
                )
            except OSError as e:
                self.logger.log_step(
                    step="INIT_ACCOUNTS_API",
                    result="WARNING",
                    error=f"Could not create profiles directory: {str(e)}",
                    error_type=type(e).__name__,
                    profiles_dir=str(self.profiles_dir)
                )
    
    def _get_active_scheduler(self):
        """
        Get active scheduler instance (giống JobsAPI pattern).
        
        Returns:
            Active scheduler instance hoặc None
        """
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
        """
        Get jobs count from MySQL directly (source of truth).
        
        Args:
            account_id: Account ID
        
        Returns:
            Jobs count
        """
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
                # Use DictCursor to get named results
                import pymysql.cursors
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    # Query all jobs for this account (all statuses)
                    query = "SELECT COUNT(*) as count FROM jobs WHERE account_id = %s"
                    cursor.execute(query, (account_id,))
                    result = cursor.fetchone()
                    
                    # pymysql DictCursor returns dict with column names as keys
                    if result and isinstance(result, dict):
                        count = result.get('count', 0)
                    elif result and isinstance(result, (list, tuple)):
                        # Fallback for tuple cursor
                        count = result[0] if len(result) > 0 else 0
                    else:
                        count = 0
                    
                    # Also verify with a direct query to debug
                    cursor.execute("SELECT COUNT(*) as total FROM jobs")
                    total_jobs = cursor.fetchone()
                    total_count = total_jobs.get('count', 0) if isinstance(total_jobs, dict) else (total_jobs[0] if total_jobs else 0)
                    
                    self.logger.log_step(
                        step="GET_JOBS_COUNT_FROM_MYSQL",
                        result="SUCCESS",
                        account_id=account_id,
                        jobs_count=count,
                        total_jobs_in_db=total_count
                    )
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
    
    def list_accounts(self) -> List[Dict]:
        """
        List tất cả accounts.
        
        Uses MySQL nếu enabled, otherwise falls back to file system.
        
        Returns:
            List of account dicts với jobs_count
        """
        # Try MySQL first if available
        if self.use_mysql and self.account_storage:
            try:
                return self._list_accounts_from_mysql()
            except Exception as e:
                self.logger.log_step(
                    step="LIST_ACCOUNTS",
                    result="WARNING",
                    error=f"Failed to load from MySQL, falling back to file system: {str(e)}",
                    error_type=type(e).__name__
                )
                # Fall through to file system
        
        # Fallback to file system
        try:
            return self._list_accounts_from_filesystem()
        except Exception as e:
            self.logger.log_step(
                step="LIST_ACCOUNTS",
                result="ERROR",
                error=f"Failed to list accounts: {str(e)}",
                error_type=type(e).__name__
            )
            import traceback
            traceback.print_exc()
            return []
    
    def _list_accounts_from_mysql(self) -> List[Dict]:
        """
        List accounts from MySQL.
        
        Returns:
            List of account dicts with jobs_count
        """
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
            
            self.logger.debug(f"Account {account_id}: jobs_count={jobs_count}")
            accounts.append(account_dict)
        
        self.logger.log_step(
            step="LIST_ACCOUNTS",
            result="SUCCESS",
            note=f"Listed {len(accounts)} accounts from MySQL",
            accounts_count=len(accounts)
        )
        return accounts
    
    def _get_account_jobs_count(self, account_id: str, scheduler) -> int:
        """
        Get jobs count for account (MySQL or scheduler fallback).
        
        Args:
            account_id: Account ID
            scheduler: Scheduler instance (may be None)
        
        Returns:
            Jobs count
        """
        if self.use_mysql and self.account_storage:
            # Use MySQL as source of truth
            return self._get_jobs_count_from_mysql(account_id)
        elif scheduler:
            # Fallback to scheduler
            try:
                return len(scheduler.list_jobs(account_id=account_id))
            except Exception as e:
                self.logger.log_step(
                    step="LIST_ACCOUNTS_GET_JOBS_COUNT",
                    result="WARNING",
                    error=f"Could not get jobs count: {str(e)}",
                    error_type=type(e).__name__,
                    account_id=account_id
                )
                return 0
        return 0
    
    def _get_account_metadata(self, account_id: str) -> Optional[Dict]:
        """
        Get account metadata from MySQL if available.
        
        Args:
            account_id: Account ID
        
        Returns:
            Metadata dict or None
        """
        if not (self.use_mysql and self.account_storage):
            return None
        
        try:
            account_from_db = self.account_storage.get_account(account_id)
            if account_from_db:
                return account_from_db.get("metadata")
        except Exception:
            # Ignore errors, continue without metadata
            pass
        
        return None
    
    def _build_account_dict(
        self,
        account_id: str,
        profile_path: str,
        jobs_count: int,
        metadata: Optional[Dict]
    ) -> Dict:
        """
        Build account dictionary.
        
        Args:
            account_id: Account ID
            profile_path: Profile directory path
            jobs_count: Jobs count
            metadata: Optional metadata
        
        Returns:
            Account dict
        """
        return {
            "account_id": account_id,
            "jobs_count": jobs_count,
            "profile_path": profile_path,
            "metadata": metadata
        }
    
    def _list_accounts_from_filesystem(self) -> List[Dict]:
        """
        List accounts from file system.
        
        Returns:
            List of account dicts
        """
        accounts = []
        
        if not self.profiles_dir.exists():
            return accounts
        
        scheduler = self._get_active_scheduler()
        
        for profile_dir in self.profiles_dir.iterdir():
            try:
                if not (profile_dir.is_dir() and not profile_dir.name.startswith('.')):
                    continue
                
                account_id = profile_dir.name
                
                # Get jobs count
                jobs_count = self._get_account_jobs_count(account_id, scheduler)
                
                # Get metadata
                metadata = self._get_account_metadata(account_id)
                
                # Build account dict
                account_dict = self._build_account_dict(
                    account_id=account_id,
                    profile_path=str(profile_dir),
                    jobs_count=jobs_count,
                    metadata=metadata
                )
                
                self.logger.debug(
                    f"Account {account_id}: jobs_count={jobs_count} "
                    f"(from {'MySQL' if self.use_mysql and self.account_storage else 'scheduler'})"
                )
                accounts.append(account_dict)
                
            except PermissionError as e:
                self.logger.log_step(
                    step="LIST_ACCOUNTS",
                    result="WARNING",
                    error=f"Permission denied accessing directory: {str(e)}",
                    error_type=type(e).__name__,
                    profile_dir=str(profile_dir)
                )
                continue
            except OSError as e:
                self.logger.log_step(
                    step="LIST_ACCOUNTS",
                    result="WARNING",
                    error=f"OS error accessing directory: {str(e)}",
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
        
        # Sort accounts safely
        try:
            sorted_accounts = sorted(accounts, key=lambda x: x.get('account_id', ''))
            self.logger.debug(f"Listed {len(sorted_accounts)} accounts")
            return sorted_accounts
        except Exception as e:
            self.logger.log_step(
                step="LIST_ACCOUNTS_SORT",
                result="WARNING",
                error=f"Could not sort accounts: {str(e)}",
                error_type=type(e).__name__
            )
            return accounts
    
    def create_account(self, account_id: str) -> bool:
        """
        Create new account profile.
        
        Args:
            account_id: Account ID to create
        
        Returns:
            True if successful, False otherwise
        """
        # Validate account_id
        if not account_id or not isinstance(account_id, str):
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"Invalid account_id: {account_id}",
                account_id=account_id
            )
            return False
        
        account_id = account_id.strip()
        if not account_id:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error="account_id cannot be empty or only spaces",
                account_id=account_id
            )
            return False
        
        # Validate account_id format (no invalid characters for directory name)
        import re
        if re.search(r'[<>:"/\\|?*]', account_id):
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"account_id contains invalid characters: {account_id}",
                account_id=account_id
            )
            return False
        
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
                    return True
                else:
                    # Exists but not a directory
                    self.logger.log_step(
                        step="CREATE_ACCOUNT",
                        result="ERROR",
                        error=f"Path exists but is not a directory: {profile_path}",
                        account_id=account_id,
                        profile_path=str(profile_path)
                    )
                    return False
            
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
                return True
            else:
                self.logger.log_step(
                    step="CREATE_ACCOUNT",
                    result="ERROR",
                    error=f"Failed to verify directory creation: {profile_path}",
                    account_id=account_id,
                    profile_path=str(profile_path)
                )
                return False
        except PermissionError as e:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"Permission denied: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return False
        except OSError as e:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"OS error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return False
        except Exception as e:
            self.logger.log_step(
                step="CREATE_ACCOUNT",
                result="ERROR",
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            import traceback
            traceback.print_exc()
            return False
    
    def _validate_account_id_for_deletion(self, account_id: str) -> bool:
        """
        Validate account_id for deletion.
        
        Args:
            account_id: Account ID to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not account_id or not isinstance(account_id, str):
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Invalid account_id: {account_id}",
                account_id=account_id
            )
            return False
        
        account_id = account_id.strip()
        if not account_id:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error="account_id cannot be empty or only spaces",
                account_id=account_id
            )
            return False
        
        return True
    
    def _check_deletion_security(self, account_id: str) -> bool:
        """
        Check security constraints for deletion.
        
        Args:
            account_id: Account ID to check
        
        Returns:
            True if safe to delete, False otherwise
        """
        # Prevent deleting system paths
        if account_id in ['..', '.', '']:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Cannot delete system path: {account_id}",
                account_id=account_id
            )
            return False
        
        # Ensure we're not deleting outside profiles directory
        profile_path = self.profiles_dir / account_id
        try:
            profile_path.resolve().relative_to(self.profiles_dir.resolve())
        except ValueError:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Invalid path, outside profiles directory: {account_id}",
                account_id=account_id,
                profile_path=str(profile_path),
                profiles_dir=str(self.profiles_dir)
            )
            return False
        
        return True
    
    def _delete_profile_directory(self, account_id: str) -> bool:
        """
        Delete profile directory.
        
        Args:
            account_id: Account ID
        
        Returns:
            True if successful, False otherwise
        """
        import shutil
        profile_path = self.profiles_dir / account_id
        
        if not profile_path.exists():
            # Path doesn't exist, consider it deleted (idempotent)
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="SUCCESS",
                note="Account does not exist (already deleted)",
                account_id=account_id
            )
            return True
        
        if not profile_path.is_dir():
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Path exists but is not a directory: {profile_path}",
                account_id=account_id,
                profile_path=str(profile_path)
            )
            return False
        
        # Delete directory
        shutil.rmtree(profile_path)
        
        # Verify deletion
        if not profile_path.exists():
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="SUCCESS",
                account_id=account_id,
                profile_path=str(profile_path)
            )
            return True
        else:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Directory still exists after deletion: {profile_path}",
                account_id=account_id,
                profile_path=str(profile_path)
            )
            return False
    
    def _delete_account_from_mysql(self, account_id: str) -> None:
        """
        Delete account from MySQL if enabled.
        
        Args:
            account_id: Account ID
        """
        if self.use_mysql and self.account_storage:
            try:
                self.account_storage.delete_account(account_id)
                self.logger.log_step(
                    step="DELETE_ACCOUNT_MYSQL",
                    result="SUCCESS",
                    account_id=account_id
                )
            except Exception as e:
                # Log but don't fail deletion
                self.logger.log_step(
                    step="DELETE_ACCOUNT_MYSQL",
                    result="WARNING",
                    error=f"Failed to delete from MySQL: {str(e)}",
                    error_type=type(e).__name__,
                    account_id=account_id
                )
    
    def delete_account(self, account_id: str) -> bool:
        """
        Delete account profile.
        
        Args:
            account_id: Account ID to delete
        
        Returns:
            True if successful, False otherwise
        """
        # Validate account_id
        if not self._validate_account_id_for_deletion(account_id):
            return False
        
        account_id = account_id.strip()
        
        # Security checks
        if not self._check_deletion_security(account_id):
            return False
        
        try:
            # Delete from MySQL if enabled
            self._delete_account_from_mysql(account_id)
            
            # Delete profile directory
            return self._delete_profile_directory(account_id)
            
        except PermissionError as e:
            self.logger.log_step(
                step="DELETE_ACCOUNT",
                result="ERROR",
                error=f"Permission denied: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return False
        except OSError as e:
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
            import traceback
            traceback.print_exc()
            return False
