"""
Unit tests for Metrics Service.

Tests for orchestration of metrics fetching and saving.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Optional, Dict, Any, List

from services.analytics.service import MetricsService
from services.analytics.storage import MetricsStorage
from browser.manager import BrowserManager
from services.logger import StructuredLogger
from config import Config


class TestMetricsService:
    """Test MetricsService operations."""
    
    @pytest.fixture
    def mock_storage(self) -> Mock:
        """Mock MetricsStorage."""
        storage = Mock(spec=MetricsStorage)
        storage.has_recent_metrics = Mock(return_value=False)
        storage.get_latest_metrics = Mock(return_value=None)
        storage.save_metrics = Mock(return_value=True)
        return storage
    
    @pytest.fixture
    def mock_browser_manager(self) -> Mock:
        """Mock BrowserManager."""
        manager = Mock(spec=BrowserManager)
        manager.account_id = "account_01"
        manager.profile_path = Mock()
        manager.start = AsyncMock()
        manager.close = AsyncMock()
        manager.context = Mock()
        manager.browser = Mock()
        return manager
    
    @pytest.fixture
    def mock_config(self) -> Config:
        """Mock Config object."""
        config = Mock(spec=Config)
        config.analytics = Mock()
        config.analytics.recent_metrics_hours = 1
        config.analytics.fetch_metrics_timeout_seconds = 30
        config.analytics.page_load_delay_seconds = 1.0
        config.analytics.page_load_alt_delay_seconds = 0.5
        config.analytics.username_extraction_timeout_seconds = 10
        config.analytics.delay_between_fetches_seconds = 0.1  # Short delay for testing
        config.platform = Mock()
        config.platform.threads_post_url_template = "https://www.threads.com/@{username}/post/{thread_id}"
        config.platform.threads_post_fallback_template = "https://www.threads.net/post/{thread_id}"
        return config
    
    @pytest.fixture
    def mock_logger(self) -> Mock:
        """Mock structured logger."""
        logger = Mock(spec=StructuredLogger)
        logger.log_step = Mock()
        return logger
    
    @pytest.fixture
    def mock_page(self) -> Mock:
        """Mock Playwright Page."""
        page = Mock()
        page.close = AsyncMock()
        page.goto = AsyncMock()
        page.url = "https://www.threads.com/@testuser/post/123456789"
        page.query_selector = AsyncMock()
        page.content = AsyncMock(return_value="<html>Test</html>")
        return page
    
    @pytest.fixture
    def service(
        self,
        mock_storage: Mock,
        mock_config: Config,
        mock_logger: Mock
    ) -> MetricsService:
        """Create MetricsService instance without browser manager."""
        return MetricsService(
            browser_manager=None,
            storage=mock_storage,
            config=mock_config,
            logger=mock_logger
        )
    
    @pytest.fixture
    def service_with_browser(
        self,
        mock_browser_manager: Mock,
        mock_storage: Mock,
        mock_config: Config,
        mock_logger: Mock
    ) -> MetricsService:
        """Create MetricsService instance with browser manager."""
        return MetricsService(
            browser_manager=mock_browser_manager,
            storage=mock_storage,
            config=mock_config,
            logger=mock_logger
        )
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_success(
        self,
        service: MetricsService,
        mock_page: Mock,
        mock_storage: Mock
    ):
        """Test successful fetch and save metrics."""
        # Setup mock scraper result
        mock_metrics_result = {
            "success": True,
            "thread_id": "123456789",
            "account_id": "account_01",
            "views": 1000,
            "likes": 100,
            "replies": 50,
            "reposts": 20,
            "shares": 10,
            "fetched_at": datetime.now(),
            "error": None
        }
        
        # Mock scraper
        with patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.fetch_metrics = AsyncMock(return_value=mock_metrics_result)
            mock_scraper_class.return_value = mock_scraper
            
            # Execute
            result = await service.fetch_and_save_metrics(
                thread_id="123456789",
                account_id="account_01",
                username="testuser",
                page=mock_page
            )
        
        # Assertions
        assert result["success"] is True
        assert result["thread_id"] == "123456789"
        assert result["metrics"]["views"] == 1000
        assert result["metrics"]["likes"] == 100
        assert result["error"] is None
        
        # Verify storage was called
        mock_storage.save_metrics.assert_called_once()
        save_call = mock_storage.save_metrics.call_args
        assert save_call[1]["thread_id"] == "123456789"
        assert save_call[1]["likes"] == 100
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_cached(
        self,
        service: MetricsService,
        mock_storage: Mock
    ):
        """Test fetch metrics returns cached result when recent metrics exist."""
        # Setup: has recent metrics
        mock_storage.has_recent_metrics = Mock(return_value=True)
        mock_latest_metrics = {
            "thread_id": "123456789",
            "views": 500,
            "likes": 50,
            "replies": 25,
            "reposts": 10,
            "shares": 5,
            "fetched_at": datetime.now()
        }
        mock_storage.get_latest_metrics = Mock(return_value=mock_latest_metrics)
        
        # Execute
        result = await service.fetch_and_save_metrics(
            thread_id="123456789",
            account_id="account_01"
        )
        
        # Assertions
        assert result["success"] is True
        assert result["cached"] is True
        assert result["metrics"] == mock_latest_metrics
        
        # Verify scraper was NOT called (cached)
        # Storage save should NOT be called
        mock_storage.save_metrics.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_create_browser(
        self,
        service: MetricsService,
        mock_storage: Mock
    ):
        """Test metrics fetch creates browser when page is not provided."""
        # Setup mock browser manager
        mock_browser_manager = Mock(spec=BrowserManager)
        mock_browser_manager.account_id = "account_01"
        mock_browser_manager.profile_path = Mock()
        mock_browser_manager.start = AsyncMock()
        mock_browser_manager.close = AsyncMock()
        mock_browser_manager.context = Mock()
        mock_browser_manager.browser = Mock()
        
        # Setup mock page
        mock_page = Mock()
        mock_page.close = AsyncMock()
        mock_browser_manager.context.new_page = AsyncMock(return_value=mock_page)
        
        # Setup mock scraper result
        mock_metrics_result = {
            "success": True,
            "thread_id": "123456789",
            "account_id": "account_01",
            "likes": 100,
            "replies": 50,
            "reposts": 20,
            "shares": 10,
            "fetched_at": datetime.now(),
            "error": None
        }
        
        with patch('services.analytics.service.BrowserManager') as mock_bm_class, \
             patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            
            mock_bm_class.return_value = mock_browser_manager
            mock_scraper = Mock()
            mock_scraper.fetch_metrics = AsyncMock(return_value=mock_metrics_result)
            mock_scraper_class.return_value = mock_scraper
            
            # Execute without page
            result = await service.fetch_and_save_metrics(
                thread_id="123456789",
                account_id="account_01",
                username="testuser"
            )
        
        # Assertions
        assert result["success"] is True
        mock_browser_manager.start.assert_called_once()
        mock_browser_manager.close.assert_called_once()
        mock_page.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_scraper_fails(
        self,
        service: MetricsService,
        mock_page: Mock,
        mock_storage: Mock
    ):
        """Test fetch and save when scraper fails."""
        # Setup mock scraper failure
        mock_metrics_result = {
            "success": False,
            "thread_id": "123456789",
            "account_id": "account_01",
            "error": "Navigation timeout"
        }
        
        with patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.fetch_metrics = AsyncMock(return_value=mock_metrics_result)
            mock_scraper_class.return_value = mock_scraper
            
            # Execute
            result = await service.fetch_and_save_metrics(
                thread_id="123456789",
                account_id="account_01",
                username="testuser",
                page=mock_page
            )
        
        # Assertions
        assert result["success"] is False
        assert "error" in result
        assert "timeout" in result["error"].lower()
        
        # Verify storage was NOT called (scraper failed)
        mock_storage.save_metrics.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_storage_fails(
        self,
        service: MetricsService,
        mock_page: Mock,
        mock_storage: Mock
    ):
        """Test fetch and save when storage save fails."""
        # Setup mock scraper success but storage fails
        mock_metrics_result = {
            "success": True,
            "thread_id": "123456789",
            "account_id": "account_01",
            "likes": 100,
            "replies": 50,
            "fetched_at": datetime.now(),
            "error": None
        }
        
        mock_storage.save_metrics = Mock(return_value=False)
        
        with patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.fetch_metrics = AsyncMock(return_value=mock_metrics_result)
            mock_scraper_class.return_value = mock_scraper
            
            # Execute
            result = await service.fetch_and_save_metrics(
                thread_id="123456789",
                account_id="account_01",
                username="testuser",
                page=mock_page
            )
        
        # Assertions
        assert result["success"] is False
        assert "save" in result["error"].lower() or "database" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_get_username_from_metadata(
        self,
        service: MetricsService,
        mock_page: Mock,
        mock_storage: Mock
    ):
        """Test username retrieval from account metadata."""
        # Setup mock account storage
        mock_account = {
            "account_id": "account_01",
            "metadata": {
                "username": "testuser",
                "threads_username": "testuser"
            }
        }
        
        mock_metrics_result = {
            "success": True,
            "thread_id": "123456789",
            "account_id": "account_01",
            "likes": 100,
            "fetched_at": datetime.now(),
            "error": None
        }
        
        with patch('services.storage.accounts_storage.AccountStorage') as mock_account_storage_class, \
             patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            
            mock_account_storage = Mock()
            mock_account_storage.get_account = Mock(return_value=mock_account)
            mock_account_storage_class.return_value = mock_account_storage
            
            mock_scraper = Mock()
            mock_scraper.fetch_metrics = AsyncMock(return_value=mock_metrics_result)
            mock_scraper_class.return_value = mock_scraper
            
            # Execute without username (should get from metadata)
            result = await service.fetch_and_save_metrics(
                thread_id="123456789",
                account_id="account_01",
                username=None,  # Will be fetched from metadata
                page=mock_page
            )
        
        # Assertions
        assert result["success"] is True
        # Verify scraper was called with username from metadata
        mock_scraper.fetch_metrics.assert_called_once()
        call_args = mock_scraper.fetch_metrics.call_args
        assert call_args[1]["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_account_id_mismatch(
        self,
        service_with_browser: MetricsService,
        mock_browser_manager: Mock,
        mock_page: Mock
    ):
        """Test browser manager recreation when account_id changes."""
        # Setup: browser manager has different account_id
        mock_browser_manager.account_id = "account_02"  # Different from request
        
        # Setup new browser manager for account_01
        new_browser_manager = Mock(spec=BrowserManager)
        new_browser_manager.account_id = "account_01"
        new_browser_manager.profile_path = Mock()
        new_browser_manager.start = AsyncMock()
        new_browser_manager.close = AsyncMock()
        new_browser_manager.context = Mock()
        new_browser_manager.context.new_page = AsyncMock(return_value=mock_page)
        
        mock_metrics_result = {
            "success": True,
            "thread_id": "123456789",
            "account_id": "account_01",
            "likes": 100,
            "fetched_at": datetime.now(),
            "error": None
        }
        
        with patch('services.analytics.service.BrowserManager') as mock_bm_class, \
             patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            
            mock_bm_class.return_value = new_browser_manager
            mock_scraper = Mock()
            mock_scraper.fetch_metrics = AsyncMock(return_value=mock_metrics_result)
            mock_scraper_class.return_value = mock_scraper
            
            # Execute with different account_id
            result = await service_with_browser.fetch_and_save_metrics(
                thread_id="123456789",
                account_id="account_01",  # Different from browser_manager.account_id
                username="testuser"
            )
        
        # Assertions
        assert result["success"] is True
        # Old browser manager should be closed
        mock_browser_manager.close.assert_called_once()
        # New browser manager should be created and started
        new_browser_manager.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_metrics(
        self,
        service: MetricsService,
        mock_page: Mock,
        mock_storage: Mock
    ):
        """Test fetching metrics for multiple threads."""
        thread_ids = ["123456789", "987654321", "111222333"]
        
        # Setup mock scraper results
        mock_results = []
        for thread_id in thread_ids:
            mock_results.append({
                "success": True,
                "thread_id": thread_id,
                "account_id": "account_01",
                "likes": 100,
                "replies": 50,
                "fetched_at": datetime.now(),
                "error": None
            })
        
        with patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.fetch_metrics = AsyncMock(side_effect=mock_results)
            mock_scraper_class.return_value = mock_scraper
            
            # Execute
            results = await service.fetch_multiple_metrics(
                thread_ids=thread_ids,
                account_id="account_01",
                username="testuser",
                page=mock_page
            )
        
        # Assertions
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["success"] is True
            assert result["thread_id"] == thread_ids[i]
        
        # Verify delay between fetches (via asyncio.sleep)
        # Note: Actual delay testing requires mocking asyncio.sleep
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_metrics_exception_handling(
        self,
        service: MetricsService,
        mock_page: Mock
    ):
        """Test exception handling in fetch_and_save_metrics."""
        # Setup: scraper raises exception
        with patch('services.analytics.service.ThreadMetricsScraper') as mock_scraper_class:
            mock_scraper_class.side_effect = Exception("Unexpected error")
            
            # Execute
            result = await service.fetch_and_save_metrics(
                thread_id="123456789",
                account_id="account_01",
                username="testuser",
                page=mock_page
            )
        
        # Assertions
        assert result["success"] is False
        assert "error" in result
        assert "unexpected" in result["error"].lower() or "failed" in result["error"].lower()
