"""
API wrapper cho metrics operations.
"""

# Standard library
from typing import List, Dict, Optional
import asyncio

# Local
from services.analytics.service import MetricsService
from services.analytics.storage import MetricsStorage
from services.logger import StructuredLogger


class MetricsAPI:
    """
    API wrapper cho metrics operations.
    """
    
    def __init__(self):
        """Initialize MetricsAPI."""
        self.logger = StructuredLogger(name="metrics_api")
        self.storage = MetricsStorage()
        self.service = MetricsService(storage=self.storage, logger=self.logger)
    
    def fetch_metrics_for_job(
        self,
        thread_id: str,
        account_id: str,
        username: Optional[str] = None,
        page=None
    ) -> Dict:
        """
        Fetch metrics cho một thread.
        
        Args:
            thread_id: Thread ID
            account_id: Account ID
            page: Optional Playwright page (for reuse)
        
        Returns:
            Dict với result
        """
        try:
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.service.fetch_and_save_metrics(thread_id, account_id, username=username, page=page)
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.log_step(
                step="FETCH_METRICS_FOR_JOB",
                result="ERROR",
                error=f"Failed to fetch metrics: {str(e)}",
                error_type=type(e).__name__,
                thread_id=thread_id
            )
            return {
                "success": False,
                "thread_id": thread_id,
                "metrics": None,
                "error": str(e)
            }
    
    def fetch_metrics_for_jobs(
        self,
        jobs: List[Dict]
    ) -> List[Dict]:
        """
        Fetch metrics cho multiple jobs.
        
        ⚠️ CRITICAL: `jobs` PHẢI đến từ database (jobs table).
        `thread_id` PHẢI được lấy từ database, không được lấy từ nguồn khác.
        
        Args:
            jobs: List of job dicts với thread_id và account_id (từ database)
        
        Returns:
            List of results
        """
        results = []
        
        # Filter completed jobs with thread_id
        jobs_to_fetch = self._filter_completed_jobs_with_thread_id(jobs)
        
        if not jobs_to_fetch:
            return results
        
        try:
            # Group by account_id
            by_account = self._group_jobs_by_account(jobs_to_fetch)
            
            # Fetch for each account
            for account_id, account_jobs in by_account.items():
                account_results = self._fetch_metrics_for_account(account_id, account_jobs)
                results.extend(account_results)
            
            return results
            
        except Exception as e:
            self.logger.log_step(
                step="FETCH_METRICS_FOR_JOBS",
                result="ERROR",
                error=f"Failed to fetch metrics for jobs: {str(e)}",
                error_type=type(e).__name__
            )
            return results
    
    def _filter_completed_jobs_with_thread_id(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter completed jobs with thread_id from database.
        
        Args:
            jobs: List of job dicts
        
        Returns:
            Filtered list of completed jobs with thread_id
        """
        jobs_to_fetch = [
            j for j in jobs
            if j.get('status') == 'completed' and j.get('thread_id')
        ]
        
        # Log verification
        if jobs_to_fetch:
            thread_ids = [j.get('thread_id') for j in jobs_to_fetch]
            self.logger.log_step(
                step="FETCH_METRICS_FOR_JOBS",
                result="IN_PROGRESS",
                note="Fetching metrics for jobs with thread_ids from DATABASE",
                job_count=len(jobs_to_fetch),
                thread_ids_sample=thread_ids[:5],
                account_ids=list(set(j.get('account_id') for j in jobs_to_fetch))
            )
        
        return jobs_to_fetch
    
    def _group_jobs_by_account(self, jobs: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group jobs by account_id.
        
        Args:
            jobs: List of job dicts
        
        Returns:
            Dict mapping account_id -> list of jobs
        """
        from collections import defaultdict
        by_account = defaultdict(list)
        
        for job in jobs:
            account_id = job.get('account_id')
            by_account[account_id].append(job)
        
        return dict(by_account)
    
    def _get_account_username(self, account_id: str) -> Optional[str]:
        """
        Get username from account metadata.
        
        Args:
            account_id: Account ID
        
        Returns:
            Username or None
        """
        try:
            from services.storage.accounts_storage import AccountStorage
            account_storage = AccountStorage()
            account = account_storage.get_account(account_id)
            if account and account.get('metadata'):
                metadata = account.get('metadata', {})
                if isinstance(metadata, dict):
                    return metadata.get('username') or metadata.get('threads_username')
        except Exception:
            pass  # Username will be extracted from page if not available
        
        return None
    
    def _fetch_metrics_for_account(
        self,
        account_id: str,
        account_jobs: List[Dict]
    ) -> List[Dict]:
        """
        Fetch metrics for one account.
        
        Args:
            account_id: Account ID
            account_jobs: List of jobs for this account
        
        Returns:
            List of metric results
        """
        thread_ids = [j.get('thread_id') for j in account_jobs if j.get('thread_id')]
        if not thread_ids:
            return []
        
        # Create new MetricsService for this account
        service = MetricsService()
        
        # Run async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get username from account metadata
            username = self._get_account_username(account_id)
            
            # Fetch metrics
            account_results = loop.run_until_complete(
                service.fetch_multiple_metrics(
                    thread_ids,
                    account_id,
                    username=username,
                    page=None
                )
            )
            return account_results
        finally:
            # Close browser manager after done with this account
            try:
                if service.browser_manager:
                    loop.run_until_complete(service.browser_manager.close())
            except Exception:
                pass  # Ignore close errors
            loop.close()
    
    def get_latest_metrics(self, thread_id: str) -> Optional[Dict]:
        """
        Get latest metrics for a thread.
        
        Args:
            thread_id: Thread ID
        
        Returns:
            Metrics dict or None
        """
        return self.storage.get_latest_metrics(thread_id)
