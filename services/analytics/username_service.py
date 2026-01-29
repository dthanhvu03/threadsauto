"""
Module: services/analytics/username_service.py

Service để extract và lưu username từ Threads profile page vào account metadata.
"""

# Standard library
import json
from typing import Optional, Dict, Any

# Third-party
from playwright.async_api import Page

# Local
from threads.username_extractor import UsernameExtractor
from services.storage.accounts_storage import AccountStorage
from services.logger import StructuredLogger
from config import Config


class UsernameService:
    """
    Service để extract và lưu username vào account metadata.
    
    Flow:
    1. Extract username từ Threads profile page
    2. Lưu username vào account metadata trong MySQL
    3. Return username
    """
    
    def __init__(
        self,
        account_storage: Optional[AccountStorage] = None,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize username service.
        
        Args:
            account_storage: Account storage instance
            config: Config object
            logger: Structured logger instance
        """
        self.config = config or Config()
        if account_storage is None:
            # Load MySQL config từ environment
            try:
                from config.storage_config_loader import get_storage_config_from_env
                storage_config = get_storage_config_from_env()
                mysql_config = storage_config.mysql
                
                self.account_storage = AccountStorage(
                    host=mysql_config.host,
                    port=mysql_config.port,
                    user=mysql_config.user,
                    password=mysql_config.password,
                    database=mysql_config.database,
                    logger=logger
                )
            except Exception:
                # Fallback to default (might fail later, but allows extraction to work)
                self.account_storage = AccountStorage(logger=logger)
        else:
            self.account_storage = account_storage
        
        self.logger = logger or StructuredLogger(name="username_service")
    
    async def extract_and_save_username(
        self,
        page: Page,
        account_id: str,
        timeout: int = 30,
        save_to_metadata: bool = True
    ) -> Optional[str]:
        """
        Extract username từ Threads profile page và lưu vào account metadata.
        
        Args:
            page: Playwright page instance (đã login)
            account_id: Account ID
            timeout: Timeout cho extraction (seconds)
            save_to_metadata: Có lưu vào metadata không (default: True)
        
        Returns:
            Username string (không có @ prefix) hoặc None nếu không extract được
        
        Flow:
        1. Extract username từ profile page
        2. Nếu extract thành công và save_to_metadata=True:
           - Get current account metadata
           - Update metadata với username
           - Save to MySQL
        3. Return username
        """
        try:
            # Step 1: Extract username
            extractor = UsernameExtractor(page, config=self.config, logger=self.logger)
            # Use timeout từ parameter hoặc config
            if timeout is None:
                timeout = self.config.analytics.username_extraction_timeout_seconds
            username = await extractor.extract_username(account_id, timeout=timeout)
            
            if not username:
                self.logger.log_step(
                    step="EXTRACT_AND_SAVE_USERNAME",
                    result="FAILED",
                    error="Could not extract username from profile page",
                    account_id=account_id
                )
                return None
            
            # Step 2: Save to account metadata nếu cần
            if save_to_metadata:
                try:
                    # Get current account
                    account = self.account_storage.get_account(account_id)
                    current_metadata = account.get("metadata", {}) if account else {}
                    
                    if not isinstance(current_metadata, dict):
                        current_metadata = {}
                    
                    # Update metadata với username
                    current_metadata["username"] = username
                    current_metadata["threads_username"] = username  # Alternative key
                    
                    # Save to MySQL
                    updated = self.account_storage.update_account(
                        account_id=account_id,
                        metadata=current_metadata
                    )
                    
                    if updated:
                        self.logger.log_step(
                            step="EXTRACT_AND_SAVE_USERNAME",
                            result="SUCCESS",
                            username=username,
                            account_id=account_id,
                            saved_to_metadata=True
                        )
                    else:
                        self.logger.log_step(
                            step="EXTRACT_AND_SAVE_USERNAME",
                            result="WARNING",
                            username=username,
                            account_id=account_id,
                            error="Username extracted but failed to save to metadata",
                            saved_to_metadata=False
                        )
                except Exception as e:
                    self.logger.log_step(
                        step="EXTRACT_AND_SAVE_USERNAME",
                        result="WARNING",
                        username=username,
                        account_id=account_id,
                        error=f"Failed to save username to metadata: {str(e)}",
                        error_type=type(e).__name__,
                        saved_to_metadata=False
                    )
                    # Vẫn return username dù không save được
            else:
                self.logger.log_step(
                    step="EXTRACT_AND_SAVE_USERNAME",
                    result="SUCCESS",
                    username=username,
                    account_id=account_id,
                    saved_to_metadata=False
                )
            
            return username
            
        except Exception as e:
            self.logger.log_step(
                step="EXTRACT_AND_SAVE_USERNAME",
                result="ERROR",
                error=f"Unexpected error: {str(e)}",
                error_type=type(e).__name__,
                account_id=account_id
            )
            return None
