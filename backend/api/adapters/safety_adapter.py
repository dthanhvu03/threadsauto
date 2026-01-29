"""
Safety API wrapper.

Interface để UI tương tác với Safety Guard.
"""

from typing import Dict, Optional, Tuple
from services.safety_guard import SafetyConfig, get_shared_safety_guard


class SafetyAPI:
    """
    API wrapper cho Safety Guard operations.
    
    Cung cấp interface đơn giản cho UI.
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """
        Initialize Safety API.
        
        Args:
            config: Optional safety configuration
        """
        # Dùng shared SafetyGuard singleton ở tầng services để đồng bộ với scheduler
        self.safety_guard = get_shared_safety_guard(config=config)
    
    def check_can_post(
        self,
        account_id: str,
        content: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check if account can post.
        
        Args:
            account_id: Account ID
            content: Content to post
        
        Returns:
            Tuple of (allowed, error_message, risk_level)
        """
        allowed, error, risk_level = self.safety_guard.can_post(account_id, content)
        return allowed, error, risk_level.value
    
    def get_account_stats(self, account_id: str) -> Dict:
        """
        Get account safety statistics.
        
        Args:
            account_id: Account ID
        
        Returns:
            Dict with stats
        """
        return self.safety_guard.get_account_stats(account_id)
    
    def record_post_success(self, account_id: str, content: str) -> None:
        """Record successful post."""
        self.safety_guard.record_post_success(account_id, content)
    
    def record_post_error(
        self,
        account_id: str,
        error_type: str,
        error_message: str
    ) -> None:
        """Record post error."""
        self.safety_guard.record_post_error(account_id, error_type, error_message)
    
    def record_high_risk_event(self, account_id: str, event_type: str) -> None:
        """Record high-risk event."""
        self.safety_guard.record_high_risk_event(account_id, event_type)
