"""
Enhanced Safety Guard Service.

Xử lý rate limiting, duplicate detection, action spacing, và account health monitoring.
"""

import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum

from services.logger import StructuredLogger


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyConfig:
    """Safety guard configuration."""
    # Rate limiting
    rate_limit_window_seconds: int = 60
    rate_limit_max_actions: int = 10
    
    # Daily limits
    daily_posts_max: int = 10
    daily_posts_reset_hour: int = 0  # Midnight
    
    # Action spacing
    min_delay_between_posts_seconds: float = 5.0
    max_delay_between_posts_seconds: float = 30.0
    
    # Duplicate detection
    duplicate_check_history_size: int = 100
    duplicate_similarity_threshold: float = 0.9  # 90% similarity
    
    # Cooldown periods
    cooldown_after_error_seconds: int = 60
    cooldown_after_high_risk_seconds: int = 300
    
    # Auto-pause thresholds
    auto_pause_high_risk_events: int = 3
    auto_pause_consecutive_errors: int = 5
    auto_pause_rate_limit_violations: int = 3


@dataclass
class AccountHealth:
    """Account health tracking."""
    account_id: str
    risk_level: RiskLevel = RiskLevel.LOW
    daily_posts_count: int = 0
    last_post_time: Optional[datetime] = None
    consecutive_errors: int = 0
    high_risk_events: int = 0
    rate_limit_violations: int = 0
    is_paused: bool = False
    paused_until: Optional[datetime] = None
    content_history: deque = field(default_factory=lambda: deque(maxlen=100))
    action_timestamps: deque = field(default_factory=lambda: deque(maxlen=100))


# Shared singleton để toàn bộ hệ thống (UI, scheduler) dùng chung state SafetyGuard
_SHARED_SAFETY_GUARD: Optional['SafetyGuard'] = None


class SafetyGuard:
    """
    Enhanced Safety Guard for account protection.
    
    Features:
    - Rate limiting (sliding window)
    - Duplicate content detection
    - Action spacing enforcement
    - Account health monitoring
    - Auto-pause on high risk
    """
    
    def __init__(
        self,
        config: Optional[SafetyConfig] = None,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize Safety Guard.
        
        Args:
            config: Safety configuration (default: SafetyConfig())
            logger: Logger instance (optional)
        """
        self.config = config or SafetyConfig()
        self.logger = logger
        
        # Account health tracking
        self.account_health: Dict[str, AccountHealth] = {}
        
        # Content hash tracking (for duplicate detection)
        self.content_hashes: Dict[str, set] = defaultdict(set)  # account_id -> set of hashes
        
        # Thread lock for rate limit checks to prevent race conditions
        self._rate_limit_lock = threading.Lock()
        
        # Maximum size for content hashes per account (prevent memory leak)
        self._max_content_hashes_per_account = 1000
    
    def get_account_health(self, account_id: str) -> AccountHealth:
        """
        Get or create account health tracking.
        
        Args:
            account_id: Account ID
        
        Returns:
            AccountHealth instance
        """
        if account_id not in self.account_health:
            self.account_health[account_id] = AccountHealth(account_id=account_id)
        
        health = self.account_health[account_id]
        
        # Reset daily count if new day (more robust handling)
        now = datetime.now()
        if health.last_post_time is not None:
            # Check if it's a new day
            if now.date() > health.last_post_time.date():
                health.daily_posts_count = 0
        # If last_post_time is None, daily_posts_count should already be 0 (default)
        # No need to reset in this case
        
        return health
    
    def check_rate_limit(self, account_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if account is within rate limit.
        
        Thread-safe: Uses lock to prevent race conditions.
        
        Args:
            account_id: Account ID
        
        Returns:
            Tuple of (allowed, error_message)
        """
        # Thread-safe access to prevent race conditions
        with self._rate_limit_lock:
            health = self.get_account_health(account_id)
            
            # Check if paused
            if health.is_paused:
                if health.paused_until and datetime.now() < health.paused_until:
                    return False, f"Account is paused until {health.paused_until}"
                else:
                    # Auto-unpause if cooldown expired
                    health.is_paused = False
                    health.paused_until = None
            
            # Check rate limit (sliding window)
            now = datetime.now()
            window_start = now - timedelta(seconds=self.config.rate_limit_window_seconds)
            
            # Count actions in window
            actions_in_window = sum(
                1 for ts in health.action_timestamps
                if ts >= window_start
            )
            
            if actions_in_window >= self.config.rate_limit_max_actions:
                health.rate_limit_violations += 1
                health.risk_level = RiskLevel.MEDIUM
                
                # Auto-pause if too many violations
                if health.rate_limit_violations >= self.config.auto_pause_rate_limit_violations:
                    self._pause_account(health, self.config.cooldown_after_high_risk_seconds)
                    return False, f"Rate limit exceeded. Account auto-paused due to {health.rate_limit_violations} violations."
                
                return False, f"Rate limit exceeded: {actions_in_window}/{self.config.rate_limit_max_actions} actions in last {self.config.rate_limit_window_seconds}s"
            
            return True, None
    
    def check_daily_limit(self, account_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if account is within daily post limit.
        
        Args:
            account_id: Account ID
        
        Returns:
            Tuple of (allowed, error_message)
        """
        health = self.get_account_health(account_id)
        
        if health.daily_posts_count >= self.config.daily_posts_max:
            return False, f"Daily post limit reached: {health.daily_posts_count}/{self.config.daily_posts_max}"
        
        return True, None
    
    def check_action_spacing(self, account_id: str) -> Tuple[bool, Optional[str], float]:
        """
        Check if enough time has passed since last action.
        
        Args:
            account_id: Account ID
        
        Returns:
            Tuple of (allowed, error_message, required_delay_seconds)
        """
        health = self.get_account_health(account_id)
        
        if health.last_post_time is None:
            return True, None, 0.0
        
        now = datetime.now()
        elapsed = (now - health.last_post_time).total_seconds()
        required_delay = self.config.min_delay_between_posts_seconds
        
        if elapsed < required_delay:
            remaining = required_delay - elapsed
            return False, f"Action spacing required: {remaining:.1f}s remaining", remaining
        
        return True, None, 0.0
    
    def check_duplicate_content(self, account_id: str, content: str) -> Tuple[bool, Optional[str]]:
        """
        Check if content is duplicate.
        
        Args:
            account_id: Account ID
            content: Content to check
        
        Returns:
            Tuple of (allowed, error_message)
        """
        # Normalize content for comparison
        normalized = self._normalize_content(content)
        content_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        
        # Check against history
        if content_hash in self.content_hashes[account_id]:
            return False, "Duplicate content detected (exact match)"
        
        # Check similarity against recent content
        health = self.get_account_health(account_id)
        for recent_content in health.content_history:
            similarity = self._calculate_similarity(normalized, recent_content)
            if similarity >= self.config.duplicate_similarity_threshold:
                return False, f"Duplicate content detected ({similarity*100:.1f}% similarity)"
        
        return True, None
    
    def can_post(
        self,
        account_id: str,
        content: str
    ) -> Tuple[bool, Optional[str], RiskLevel]:
        """
        Comprehensive check if account can post.
        
        Args:
            account_id: Account ID
            content: Content to post
        
        Returns:
            Tuple of (allowed, error_message, risk_level)
        """
        health = self.get_account_health(account_id)
        
        # Check if paused
        if health.is_paused:
            if health.paused_until and datetime.now() < health.paused_until:
                return False, f"Account is paused until {health.paused_until}", health.risk_level
            else:
                health.is_paused = False
                health.paused_until = None
        
        # Check rate limit
        allowed, error = self.check_rate_limit(account_id)
        if not allowed:
            return False, error, health.risk_level
        
        # Check daily limit
        allowed, error = self.check_daily_limit(account_id)
        if not allowed:
            return False, error, health.risk_level
        
        # Check action spacing
        allowed, error, _ = self.check_action_spacing(account_id)
        if not allowed:
            return False, error, health.risk_level
        
        # Check duplicate content
        allowed, error = self.check_duplicate_content(account_id, content)
        if not allowed:
            health.risk_level = RiskLevel.MEDIUM
            return False, error, health.risk_level
        
        return True, None, health.risk_level
    
    def record_post_success(self, account_id: str, content: str) -> None:
        """
        Record successful post.
        
        Args:
            account_id: Account ID
            content: Posted content
        """
        health = self.get_account_health(account_id)
        
        now = datetime.now()
        health.last_post_time = now
        health.daily_posts_count += 1
        health.action_timestamps.append(now)
        
        # Add to content history
        normalized = self._normalize_content(content)
        content_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        
        # Cleanup old hashes to prevent memory leak
        self._cleanup_content_hashes(account_id)
        
        self.content_hashes[account_id].add(content_hash)
        health.content_history.append(normalized)
        
        # Reset consecutive errors on success
        health.consecutive_errors = 0
        
        # Lower risk level on success
        if health.risk_level == RiskLevel.HIGH and health.consecutive_errors == 0:
            health.risk_level = RiskLevel.MEDIUM
        
        if self.logger:
            self.logger.log_step(
                step="SAFETY_GUARD_RECORD_SUCCESS",
                result="SUCCESS",
                account_id=account_id,
                risk_level=health.risk_level.value,
                daily_posts=health.daily_posts_count
            )
    
    def record_post_error(
        self,
        account_id: str,
        error_type: str,
        error_message: str
    ) -> None:
        """
        Record post error.
        
        Args:
            account_id: Account ID
            error_type: Type of error
            error_message: Error message
        """
        health = self.get_account_health(account_id)
        
        health.consecutive_errors += 1
        
        # Increase risk level based on errors
        if health.consecutive_errors >= self.config.auto_pause_consecutive_errors:
            health.risk_level = RiskLevel.CRITICAL
            self._pause_account(health, self.config.cooldown_after_error_seconds)
        elif health.consecutive_errors >= 3:
            health.risk_level = RiskLevel.HIGH
        elif health.consecutive_errors >= 1:
            health.risk_level = RiskLevel.MEDIUM
        
        if self.logger:
            self.logger.log_step(
                step="SAFETY_GUARD_RECORD_ERROR",
                result="ERROR",
                account_id=account_id,
                error=error_message,
                error_type=error_type,
                consecutive_errors=health.consecutive_errors,
                risk_level=health.risk_level.value
            )
    
    def record_high_risk_event(self, account_id: str, event_type: str) -> None:
        """
        Record high-risk event.
        
        Args:
            account_id: Account ID
            event_type: Type of event
        """
        health = self.get_account_health(account_id)
        
        health.high_risk_events += 1
        health.risk_level = RiskLevel.HIGH
        
        # Auto-pause if too many high-risk events
        if health.high_risk_events >= self.config.auto_pause_high_risk_events:
            health.risk_level = RiskLevel.CRITICAL
            self._pause_account(health, self.config.cooldown_after_high_risk_seconds)
        
        if self.logger:
            self.logger.log_step(
                step="SAFETY_GUARD_HIGH_RISK",
                result="WARNING",
                account_id=account_id,
                event_type=event_type,
                high_risk_events=health.high_risk_events,
                risk_level=health.risk_level.value
            )
    
    def _pause_account(self, health: AccountHealth, cooldown_seconds: int) -> None:
        """Pause account for cooldown period."""
        health.is_paused = True
        health.paused_until = datetime.now() + timedelta(seconds=cooldown_seconds)
        
        if self.logger:
            self.logger.log_step(
                step="SAFETY_GUARD_AUTO_PAUSE",
                result="PAUSED",
                account_id=health.account_id,
                paused_until=health.paused_until.isoformat(),
                risk_level=health.risk_level.value
            )
    
    def _normalize_content(self, content: str) -> str:
        """
        Normalize content for duplicate detection.
        
        Note: Uses shared utility function from utils.content
        """
        from utils.content import normalize_content
        return normalize_content(content)
    
    def _cleanup_content_hashes(self, account_id: str) -> None:
        """
        Cleanup old content hashes to prevent memory leak.
        
        Args:
            account_id: Account ID
        """
        if account_id in self.content_hashes:
            hash_set = self.content_hashes[account_id]
            if len(hash_set) > self._max_content_hashes_per_account:
                # Keep only recent hashes (convert to list, keep last N, convert back to set)
                # Note: sets are unordered, so we keep a subset
                # In practice, we could use a deque or LRU cache for better control
                hash_list = list(hash_set)
                # Keep last N hashes
                recent_hashes = hash_list[-self._max_content_hashes_per_account:]
                self.content_hashes[account_id] = set(recent_hashes)
    
    def cleanup_inactive_accounts(self, max_inactive_days: int = 30) -> int:
        """
        Cleanup AccountHealth objects for inactive accounts.
        
        Args:
            max_inactive_days: Maximum days of inactivity before cleanup
        
        Returns:
            Number of accounts cleaned up
        """
        now = datetime.now()
        cutoff_date = now - timedelta(days=max_inactive_days)
        
        accounts_to_remove = []
        for account_id, health in self.account_health.items():
            if health.last_post_time is None:
                # Never posted, check created_at if available
                # For now, skip accounts that never posted
                continue
            
            if health.last_post_time < cutoff_date:
                accounts_to_remove.append(account_id)
        
        # Remove inactive accounts
        for account_id in accounts_to_remove:
            del self.account_health[account_id]
            # Also cleanup content hashes
            if account_id in self.content_hashes:
                del self.content_hashes[account_id]
        
        return len(accounts_to_remove)
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two content strings.
        
        Uses simple word overlap ratio.
        """
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0


def get_shared_safety_guard(
    config: Optional[SafetyConfig] = None,
    logger: Optional[StructuredLogger] = None
) -> SafetyGuard:
    """
    Get global SafetyGuard instance (singleton) để share state giữa UI và Scheduler.

    Args:
        config: SafetyConfig (optional, only used on first creation)
        logger: StructuredLogger (optional)

    Returns:
        SafetyGuard singleton
    """
    global _SHARED_SAFETY_GUARD
    if _SHARED_SAFETY_GUARD is None:
        _SHARED_SAFETY_GUARD = SafetyGuard(config=config, logger=logger)
    return _SHARED_SAFETY_GUARD

