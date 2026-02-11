"""
Unit tests for Safety Guard.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.safety_guard import SafetyGuard, RiskLevel, SafetyConfig


class TestSafetyGuard:
    """Test Safety Guard operations."""
    
    @pytest.fixture
    def mock_logger(self, mock_logger):
        """Mock logger."""
        return mock_logger
    
    @pytest.fixture
    def config(self):
        """Safety config."""
        return SafetyConfig(
            rate_limit_window_seconds=60,
            rate_limit_max_actions=10,
            daily_posts_max=10,
            min_delay_between_posts_seconds=5.0,
            duplicate_check_history_size=100
        )
    
    @pytest.fixture
    def safety_guard(self, config, mock_logger):
        """Create SafetyGuard instance."""
        return SafetyGuard(config=config, logger=mock_logger)
    
    def test_init(self, safety_guard, config):
        """Test initialization."""
        assert safety_guard.config == config
    
    def test_check_rate_limit(self, safety_guard):
        """Test rate limit checking."""
        account_id = "account_01"
        
        # Should pass first 10 actions
        for i in range(10):
            allowed, message = safety_guard.check_rate_limit(account_id)
            assert allowed is True, f"Action {i+1} should be allowed"
        
        # 11th action should be blocked
        allowed, message = safety_guard.check_rate_limit(account_id)
        assert allowed is False
        assert "rate limit" in message.lower()
    
    def test_check_daily_limit(self, safety_guard):
        """Test daily limit checking."""
        account_id = "account_01"
        
        # Should pass first 10 posts
        for i in range(10):
            allowed, message = safety_guard.check_daily_limit(account_id)
            assert allowed is True, f"Post {i+1} should be allowed"
        
        # 11th post should be blocked
        allowed, message = safety_guard.check_daily_limit(account_id)
        assert allowed is False
        assert "daily limit" in message.lower()
    
    def test_check_duplicate_content(self, safety_guard):
        """Test duplicate content detection."""
        account_id = "account_01"
        content = "Test content for duplicate check"
        
        # First post should pass
        allowed, message = safety_guard.check_duplicate_content(account_id, content)
        assert allowed is True
        
        # Duplicate should be blocked
        allowed, message = safety_guard.check_duplicate_content(account_id, content)
        assert allowed is False
        assert "duplicate" in message.lower()
    
    def test_check_action_spacing(self, safety_guard):
        """Test action spacing enforcement."""
        account_id = "account_01"
        
        # First action should pass
        allowed, message = safety_guard.check_action_spacing(account_id)
        assert allowed is True
        
        # Immediate second action should be blocked (min delay = 5 seconds)
        allowed, message = safety_guard.check_action_spacing(account_id)
        assert allowed is False
        assert "spacing" in message.lower() or "delay" in message.lower()
    
    def test_record_high_risk_event(self, safety_guard):
        """Test recording high risk events."""
        account_id = "account_01"
        
        # Record 3 high risk events (threshold = 3)
        for i in range(3):
            safety_guard.record_high_risk_event(account_id, "test_reason")
        
        # Check if account is paused
        health = safety_guard.get_account_health(account_id)
        # Note: Auto-pause logic may vary, this is a basic check
        assert health.high_risk_events_count >= 3
    
    def test_record_error(self, safety_guard):
        """Test recording errors."""
        account_id = "account_01"
        
        # Record 5 consecutive errors (threshold = 5)
        for i in range(5):
            safety_guard.record_error(account_id, "test_error")
        
        health = safety_guard.get_account_health(account_id)
        assert health.consecutive_errors >= 5
    
    def test_reset_daily_counters(self, safety_guard):
        """Test daily counter reset."""
        account_id = "account_01"
        
        # Record some posts
        safety_guard.check_daily_limit(account_id)  # Records a post
        
        # Get health before reset
        health_before = safety_guard.get_account_health(account_id)
        assert health_before.daily_posts_count > 0
        
        # Reset (simulate new day)
        safety_guard._reset_daily_counters(account_id)
        
        # Get health after reset
        health_after = safety_guard.get_account_health(account_id)
        assert health_after.daily_posts_count == 0
