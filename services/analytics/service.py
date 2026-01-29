"""
Module: services/analytics/service.py

Metrics service để orchestrate fetch và save metrics.
"""

# Standard library
from typing import Optional, Dict, Any, List
from datetime import datetime

# Third-party
from playwright.async_api import Page

# Local
from services.logger import StructuredLogger
from services.analytics.storage import MetricsStorage
from threads.metrics_scraper import ThreadMetricsScraper
from browser.manager import BrowserManager
from config import Config


class MetricsService:
    """
    Service để fetch và save thread metrics.
    
    Orchestrates:
    - Fetching metrics từ Threads
    - Saving to database
    - Browser management
    """
    
    def __init__(
        self,
        browser_manager: Optional[BrowserManager] = None,
        storage: Optional[MetricsStorage] = None,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize metrics service.
        
        Args:
            browser_manager: Browser manager instance (optional)
            storage: Metrics storage instance (optional)
            config: Config object (optional)
            logger: Structured logger (optional)
        """
        self.browser_manager = browser_manager
        self.storage = storage or MetricsStorage()
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="metrics_service")
        self._own_browser = browser_manager is None
    
    async def fetch_and_save_metrics(
        self,
        thread_id: str,
        account_id: str,
        username: Optional[str] = None,
        page: Optional[Page] = None
    ) -> Dict[str, Any]:
        """
        Fetch metrics từ Threads và save vào database.
        
        Args:
            thread_id: Thread ID
            account_id: Account ID
            username: Threads username (optional - sẽ extract từ page nếu không có)
            page: Optional Playwright page (if None, will create browser)
        
        Returns:
            Dict với result:
            {
                "success": bool,
                "thread_id": str,
                "metrics": Optional[Dict],
                "error": Optional[str]
            }
        """
        try:
            self.logger.log_step(
                step="FETCH_AND_SAVE_METRICS",
                result="IN_PROGRESS",
                thread_id=thread_id,
                account_id=account_id
            )
            
            # Check if we have recent metrics (avoid duplicate fetches)
            recent_hours = self.config.analytics.recent_metrics_hours
            if self.storage.has_recent_metrics(thread_id, hours=recent_hours):
                latest = self.storage.get_latest_metrics(thread_id)
                if latest:
                    self.logger.log_step(
                        step="FETCH_AND_SAVE_METRICS",
                        result="SKIPPED",
                        note="Recent metrics already exist",
                        thread_id=thread_id
                    )
                    return {
                        "success": True,
                        "thread_id": thread_id,
                        "metrics": latest,
                        "error": None,
                        "cached": True
                    }
            
            # Use provided page or create browser
            if page is None:
                # ⚠️ FIX: Check nếu browser_manager account_id khác với account_id hiện tại
                # Nếu khác, cần tạo browser_manager mới với account_id đúng
                if self.browser_manager is None or self.browser_manager.account_id != account_id:
                    # Close old browser manager nếu có và account_id khác
                    if self.browser_manager and self.browser_manager.account_id != account_id:
                        try:
                            await self.browser_manager.close()
                            self.logger.log_step(
                                step="FETCH_AND_SAVE_METRICS_CLOSE_OLD_BROWSER",
                                result="SUCCESS",
                                old_account_id=self.browser_manager.account_id,
                                new_account_id=account_id,
                                note="Closing browser manager for previous account"
                            )
                        except Exception as e:
                            self.logger.log_step(
                                step="FETCH_AND_SAVE_METRICS_CLOSE_OLD_BROWSER",
                                result="WARNING",
                                error=str(e),
                                old_account_id=self.browser_manager.account_id if self.browser_manager else None,
                                new_account_id=account_id
                            )
                    
                    # Create new browser manager với account_id đúng
                    self.browser_manager = BrowserManager(account_id=account_id)
                    await self.browser_manager.start()
                    
                    # Verify context was created
                    if not self.browser_manager.context:
                        raise RuntimeError(
                            f"Browser context is None after start() for account {account_id}. "
                            f"Browser may not have started correctly."
                        )
                    
                    self.logger.log_step(
                        step="FETCH_AND_SAVE_METRICS_CREATE_BROWSER",
                        result="SUCCESS",
                        account_id=account_id,
                        profile_path=str(self.browser_manager.profile_path),
                        has_context=bool(self.browser_manager.context)
                    )
                
                # Use existing context from browser manager (has login session)
                # launch_persistent_context returns context directly, not browser
                if self.browser_manager.context:
                    page = await self.browser_manager.context.new_page()
                else:
                    # This should not happen if browser_manager.start() succeeded
                    raise RuntimeError(
                        f"Browser context is None for account {account_id}. "
                        f"Browser may not have started correctly."
                    )
                close_page = True
            else:
                close_page = False
            
            try:
                # Lấy username từ account metadata nếu không có
                if not username:
                    try:
                        from services.storage.accounts_storage import AccountStorage
                        account_storage = AccountStorage()
                        account = account_storage.get_account(account_id)
                        if account and account.get('metadata'):
                            metadata = account.get('metadata', {})
                            if isinstance(metadata, dict):
                                username = metadata.get('username') or metadata.get('threads_username')
                                if username:
                                    self.logger.log_step(
                                        step="FETCH_AND_SAVE_METRICS_GET_USERNAME",
                                        result="SUCCESS",
                                        username=username,
                                        account_id=account_id,
                                        source="metadata"
                                    )
                                else:
                                    self.logger.log_step(
                                        step="FETCH_AND_SAVE_METRICS_GET_USERNAME",
                                        result="WARNING",
                                        account_id=account_id,
                                        note="No username found in metadata. Will try to extract from page (may get wrong username if browser logged into different account)"
                                    )
                    except Exception as e:
                        self.logger.log_step(
                            step="FETCH_AND_SAVE_METRICS_GET_USERNAME",
                            result="WARNING",
                            error=f"Could not get username from account metadata: {str(e)}",
                            error_type=type(e).__name__,
                            account_id=account_id
                        )
                
                # Nếu vẫn không có username, thử extract từ profile page
                # ⚠️ WARNING: Extract username từ page có thể lấy username của account đang login,
                # không phải account_id được truyền vào. Cần đảm bảo browser profile đang login đúng account.
                if not username and page:
                    try:
                        from services.analytics.username_service import UsernameService
                        username_service = UsernameService(config=self.config, logger=self.logger)
                        extraction_timeout = self.config.analytics.username_extraction_timeout_seconds
                        extracted_username = await username_service.extract_and_save_username(
                            page=page,
                            account_id=account_id,
                            timeout=extraction_timeout,
                            save_to_metadata=True
                        )
                        if extracted_username:
                            # ⚠️ WARNING: Validate extracted username matches account
                            # Nếu browser profile đang login account khác, extracted_username sẽ sai
                            self.logger.log_step(
                                step="FETCH_AND_SAVE_METRICS_EXTRACT_USERNAME",
                                result="SUCCESS",
                                username=extracted_username,
                                account_id=account_id,
                                warning="Extracted username from page - ensure browser profile matches account_id"
                            )
                            username = extracted_username
                        else:
                            self.logger.log_step(
                                step="FETCH_AND_SAVE_METRICS_EXTRACT_USERNAME",
                                result="WARNING",
                                error="Could not extract username from profile page",
                                account_id=account_id,
                                note="Browser profile may not be logged in or may be logged into different account"
                            )
                    except Exception as e:
                        self.logger.log_step(
                            step="FETCH_AND_SAVE_METRICS_EXTRACT_USERNAME",
                            result="WARNING",
                            error=f"Could not extract username from profile page: {str(e)}",
                            error_type=type(e).__name__,
                            account_id=account_id,
                            note="Browser profile may not be logged in or may be logged into different account"
                        )
                
                # Create scraper and fetch metrics
                scraper = ThreadMetricsScraper(page, config=self.config, logger=self.logger)
                metrics_result = await scraper.fetch_metrics(thread_id, account_id, username=username)
                
                # Check if thread was skipped (username mismatch)
                if metrics_result.get("skipped"):
                    # Thread belongs to different account - skip it
                    return {
                        "success": False,
                        "thread_id": thread_id,
                        "metrics": None,
                        "error": metrics_result.get("error", "Thread skipped"),
                        "skipped": True
                    }
                
                if metrics_result.get("success"):
                    # Save to database
                    saved = self.storage.save_metrics(
                        thread_id=metrics_result["thread_id"],
                        account_id=metrics_result["account_id"],
                        views=metrics_result.get("views"),
                        likes=metrics_result.get("likes", 0),
                        replies=metrics_result.get("replies", 0),
                        reposts=metrics_result.get("reposts", 0),
                        shares=metrics_result.get("shares", 0),
                        fetched_at=metrics_result.get("fetched_at", datetime.now())
                    )
                    
                    if saved:
                        return {
                            "success": True,
                            "thread_id": thread_id,
                            "metrics": {
                                "views": metrics_result.get("views"),
                                "likes": metrics_result.get("likes", 0),
                                "replies": metrics_result.get("replies", 0),
                                "reposts": metrics_result.get("reposts", 0),
                                "shares": metrics_result.get("shares", 0),
                                "fetched_at": metrics_result.get("fetched_at")
                            },
                            "error": None
                        }
                    else:
                        return {
                            "success": False,
                            "thread_id": thread_id,
                            "metrics": None,
                            "error": "Failed to save metrics to database"
                        }
                else:
                    return {
                        "success": False,
                        "thread_id": thread_id,
                        "metrics": None,
                        "error": metrics_result.get("error", "Unknown error")
                    }
                    
            finally:
                if close_page and page:
                    await page.close()
                    # ⚠️ CRITICAL: Don't close browser_manager here if we're in fetch_multiple_metrics
                    # Browser manager should be reused for multiple fetches
                    # Only close if this is a single fetch (not part of batch)
                    # We'll close browser_manager in fetch_multiple_metrics finally block instead
                    # if self._own_browser and self.browser_manager:
                    #     await self.browser_manager.close()
                        
        except Exception as e:
            self.logger.log_step(
                step="FETCH_AND_SAVE_METRICS",
                result="ERROR",
                error=f"Failed to fetch and save metrics: {str(e)}",
                error_type=type(e).__name__,
                thread_id=thread_id
            )
            
            return {
                "success": False,
                "thread_id": thread_id,
                "metrics": None,
                "error": str(e)
            }
    
    async def fetch_multiple_metrics(
        self,
        thread_ids: List[str],
        account_id: str,
        username: Optional[str] = None,
        page: Optional[Page] = None,
        parallel: Optional[bool] = None,
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch metrics for multiple threads.
        
        Args:
            thread_ids: List of thread IDs
            account_id: Account ID
            username: Threads username (optional)
            page: Optional Playwright page (if None, will create and reuse browser)
            parallel: Enable parallel fetching (None = use config default)
            max_concurrent: Max concurrent fetches (None = use config default)
        
        Returns:
            List of results
        """
        # Use config defaults if not specified
        parallel_mode = parallel if parallel is not None else self.config.analytics.parallel_fetch_enabled
        max_workers = max_concurrent if max_concurrent is not None else self.config.analytics.max_concurrent_fetches
        
        # If no page provided, create browser manager once and reuse for all threads
        # This ensures browser context stays alive across multiple fetches
        if page is None:
            # Ensure browser manager exists and is for correct account
            if self.browser_manager is None or self.browser_manager.account_id != account_id:
                if self.browser_manager and self.browser_manager.account_id != account_id:
                    await self.browser_manager.close()
                
                self.browser_manager = BrowserManager(account_id=account_id)
                await self.browser_manager.start()
                
                if not self.browser_manager.context:
                    raise RuntimeError(
                        f"Browser context is None after start() for account {account_id}. "
                        f"Browser may not have started correctly."
                    )
        
        try:
            if parallel_mode and len(thread_ids) > 1:
                # Parallel mode: fetch multiple threads concurrently with limit
                results = await self._fetch_parallel(
                    thread_ids, 
                    account_id, 
                    username=username, 
                    max_concurrent=max_workers
                )
            else:
                # Sequential mode: fetch one by one (original implementation)
                results = await self._fetch_sequential(
                    thread_ids, 
                    account_id, 
                    username=username
                )
        finally:
            # Close browser manager if we created it (when page was None initially)
            if page is None and self.browser_manager and self._own_browser:
                try:
                    await self.browser_manager.close()
                    self.browser_manager = None
                except Exception as e:
                    self.logger.log_step(
                        step="FETCH_MULTIPLE_METRICS_CLOSE_BROWSER",
                        result="WARNING",
                        error=str(e),
                        account_id=account_id
                    )
        
        return results
    
    async def _fetch_sequential(
        self,
        thread_ids: List[str],
        account_id: str,
        username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch metrics sequentially (one by one)."""
        results = []
        import asyncio
        
        for thread_id in thread_ids:
            # Pass page=None to reuse browser manager's context
            # fetch_and_save_metrics will create new page from context each time
            result = await self.fetch_and_save_metrics(
                thread_id, 
                account_id, 
                username=username, 
                page=None  # Let it create page from browser_manager.context
            )
            results.append(result)
            
            # Delay between fetches từ config
            delay = self.config.analytics.delay_between_fetches_seconds
            await asyncio.sleep(delay)
        
        return results
    
    async def _fetch_parallel(
        self,
        thread_ids: List[str],
        account_id: str,
        username: Optional[str] = None,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Fetch metrics in parallel với limit (semaphore).
        
        Performance: Nhanh hơn 3-4 lần so với sequential.
        Với 10 threads, max_concurrent=3: ~20s thay vì ~70s.
        """
        import asyncio
        
        # Semaphore để limit số lượng concurrent fetches
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_one(thread_id: str) -> Dict[str, Any]:
            """Fetch metrics cho một thread với semaphore protection."""
            async with semaphore:
                try:
                    result = await self.fetch_and_save_metrics(
                        thread_id,
                        account_id,
                        username=username,
                        page=None  # Let it create page from browser_manager.context
                    )
                    return result
                except Exception as exc:
                    error_msg = str(exc)
                    self.logger.log_step(
                        step="FETCH_PARALLEL_ONE",
                        result="ERROR",
                        error=f"Failed to fetch metrics for thread {thread_id}: {error_msg}",
                        error_type=type(exc).__name__,
                        thread_id=thread_id,
                        account_id=account_id
                    )
                    return {
                        "success": False,
                        "thread_id": thread_id,
                        "metrics": None,
                        "error": error_msg
                    }
        
        # Create tasks for all threads
        tasks = [fetch_one(tid) for tid in thread_ids]
        
        # Execute all tasks in parallel với return_exceptions=True
        # để không fail cả batch nếu một task fail
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions (already handled in fetch_one)
        final_results = []
        for r in results:
            if isinstance(r, Exception):
                self.logger.log_step(
                    step="FETCH_PARALLEL_GATHER",
                    result="ERROR",
                    error=f"Unexpected exception: {str(r)}",
                    error_type=type(r).__name__
                )
            else:
                final_results.append(r)
        
        self.logger.log_step(
            step="FETCH_PARALLEL_COMPLETE",
            result="SUCCESS",
            account_id=account_id,
            total_threads=len(thread_ids),
            completed=len(final_results),
            max_concurrent=max_concurrent
        )
        
        return final_results
