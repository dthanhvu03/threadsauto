"""
Module: config/config.py

Configuration management for Threads automation.
"""

# Standard library
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RunMode(Enum):
    """Run mode enumeration."""
    SAFE = "SAFE"
    FAST = "FAST"


@dataclass
class BrowserConfig:
    """Browser configuration."""
    headless: bool = False
    slow_mo: int = 100
    timeout: int = 30000  # Default timeout (ms)
    debug: bool = False
    
    # Timeouts (in milliseconds)
    navigation_timeout: int = 30000  # Navigation timeout
    element_wait_timeout: int = 10000  # Element wait timeout
    short_timeout: int = 5000  # Short timeout
    very_short_timeout: int = 3000  # Very short timeout
    long_wait_timeout: int = 15000  # Long wait timeout


@dataclass
class SelectorConfig:
    """Selector configuration."""
    version: str = "v1"
    use_custom: bool = False  # Use custom selectors from storage instead of hardcoded
    platform: str = "threads"  # Platform name for selector loading


@dataclass
class AntiDetectionConfig:
    """Anti-detection configuration."""
    min_delay: float = 0.5
    max_delay: float = 2.0
    typing_chunk_size: int = 4
    typing_delay_min: float = 0.05
    typing_delay_max: float = 0.15


@dataclass
class SafetyConfig:
    """Safety configuration."""
    max_posts_per_day: int = 10
    min_delay_between_posts: int = 5
    rate_limit_window: int = 60
    rate_limit_max_actions: int = 10
    auto_pause_on_high_risk: bool = True
    high_risk_threshold: int = 3
    consecutive_error_threshold: int = 5


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    max_retries: int = 3
    max_running_minutes: int = 30
    check_interval_seconds: int = 10  # Interval between job checks
    reload_interval_seconds: int = 30  # Interval to reload jobs from storage
    reload_check_delay_seconds: int = 2  # Delay before reload after save
    processing_delay_seconds: float = 4.0  # Delay after processing
    overdue_threshold_hours: Optional[int] = None  # Skip jobs overdue by more than this (None = catch-up all overdue jobs)


@dataclass
class ConnectionPoolConfig:
    """MySQL connection pool configuration."""
    pool_size: int = 10
    max_overflow: int = 20
    read_timeout_seconds: int = 30
    write_timeout_seconds: int = 30
    pool_recycle_seconds: int = 3600  # Recycle connections after 1 hour


@dataclass
class MySQLStorageConfig:
    """MySQL storage configuration."""
    host: str = "localhost"
    port: int = 3306
    user: str = "threads_user"
    password: str = ""
    database: str = "threads_analytics"
    charset: str = "utf8mb4"
    pool: Optional[ConnectionPoolConfig] = None
    
    def __post_init__(self):
        """Initialize connection pool config if not provided."""
        if self.pool is None:
            self.pool = ConnectionPoolConfig()


@dataclass
class StorageConfig:
    """
    Storage configuration.
    
    Supports both JSON and MySQL storage backends.
    """
    # Storage type: "json" or "mysql"
    # Default: "mysql" (after migration)
    storage_type: str = "mysql"
    
    # JSON storage config
    jobs_dir: str = "./jobs"
    logs_dir: str = "./logs"
    profiles_dir: str = "./profiles"
    
    # MySQL storage config
    mysql: Optional[MySQLStorageConfig] = None
    
    def __post_init__(self):
        """Initialize MySQL config if not provided."""
        if self.mysql is None:
            self.mysql = MySQLStorageConfig()


@dataclass
class ConnectionPoolConfig:
    """MySQL connection pool configuration."""
    pool_size: int = 10
    max_overflow: int = 20
    read_timeout_seconds: int = 30
    write_timeout_seconds: int = 30
    pool_recycle_seconds: int = 3600  # Recycle connections after 1 hour


@dataclass
class AnalyticsConfig:
    """Analytics and metrics fetching configuration."""
    # Metrics scraper
    fetch_metrics_timeout_seconds: int = 30
    page_load_delay_seconds: float = 2.0
    page_load_alt_delay_seconds: float = 3.0
    
    # Username extractor
    username_extraction_timeout_seconds: int = 30
    username_page_load_delay_seconds: float = 3.0
    username_element_wait_timeout_ms: int = 5000
    username_click_timeout_ms: int = 10000
    username_navigation_delay_seconds: float = 2.0
    
    # Fetch multiple metrics
    delay_between_fetches_seconds: float = 2.0
    
    # Parallel fetching (tăng tốc fetch metrics)
    parallel_fetch_enabled: bool = True  # Bật parallel mode
    max_concurrent_fetches: int = 3  # Số lượng threads fetch cùng lúc (3-5 recommended)
    
    # Recent metrics check (skip if metrics fetched within this time)
    recent_metrics_hours: int = 1


@dataclass
class PlatformConfig:
    """Platform URLs configuration."""
    threads_base_url: str = "https://www.threads.com/?hl=vi"
    threads_compose_url: str = "https://www.threads.com/?hl=vi/compose"
    threads_login_url: str = "https://threads.net/login"
    threads_profile_url: str = "https://www.threads.com/"  # For username extraction
    threads_post_url_template: str = "https://www.threads.com/@{username}/post/{thread_id}"
    threads_post_fallback_template: str = "https://www.threads.com/post/{thread_id}"
    facebook_url: str = "https://www.facebook.com"


@dataclass
class Config:
    """
    Main configuration class.
    
    Loads configuration from config.yaml or uses defaults.
    """
    
    mode: RunMode = RunMode.SAFE
    browser: Optional[BrowserConfig] = None
    selectors: Optional[SelectorConfig] = None
    anti_detection: Optional[AntiDetectionConfig] = None
    safety: Optional[SafetyConfig] = None
    scheduler: Optional[SchedulerConfig] = None
    storage: Optional[StorageConfig] = None
    platform: Optional[PlatformConfig] = None
    analytics: Optional[AnalyticsConfig] = None
    
    def __post_init__(self):
        """Initialize default configs if not provided."""
        if self.browser is None:
            self.browser = BrowserConfig()
        
        if self.selectors is None:
            self.selectors = SelectorConfig()
        
        if self.anti_detection is None:
            self.anti_detection = AntiDetectionConfig()
        
        if self.safety is None:
            self.safety = SafetyConfig()
        
        if self.scheduler is None:
            self.scheduler = SchedulerConfig()
        
        if self.storage is None:
            self.storage = StorageConfig()
        
        if self.platform is None:
            self.platform = PlatformConfig()
        
        if self.analytics is None:
            self.analytics = AnalyticsConfig()
        
        # Adjust based on mode
        if self.mode == RunMode.FAST:
            self.anti_detection.min_delay = 0.3
            self.anti_detection.max_delay = 1.0
            self.browser.slow_mo = 50
        elif self.mode == RunMode.SAFE:
            self.anti_detection.min_delay = 0.5
            self.anti_detection.max_delay = 2.0
            self.browser.slow_mo = 100

