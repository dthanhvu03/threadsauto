"""
Module: config/storage.py

Configuration storage and loading utilities.
"""

# Standard library
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Local
from config.config import Config, RunMode
from config.storage_config_loader import get_storage_config_from_env
from services.storage.config_storage import ConfigStorage
from services.logger import StructuredLogger


CONFIG_FILE = Path("./config.json")
_USE_MYSQL_CONFIG = True  # Use MySQL by default


def load_config(use_mysql: Optional[bool] = None) -> Config:
    """
    Load configuration từ MySQL (if enabled) hoặc JSON file.
    
    Priority:
    1. MySQL (if use_mysql=True and available)
    2. JSON file (config.json)
    3. Defaults
    
    Args:
        use_mysql: If True, use MySQL. If None, use default (MySQL).
    
    Returns:
        Config instance
    """
    if use_mysql is None:
        use_mysql = _USE_MYSQL_CONFIG
    
    # Try MySQL first
    if use_mysql:
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            config_storage = ConfigStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                charset=mysql_config.charset,
                logger=StructuredLogger(name="config_storage")
            )
            config = config_storage.load_config()
            if config:
                return config
        except Exception:
            # Fall through to JSON file
            pass
    
    # Fallback to JSON file
    if not CONFIG_FILE.exists():
        return Config()
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return _dict_to_config(data)
    except Exception as e:
        # Return defaults if loading fails
        print(f"Warning: Failed to load config: {e}, using defaults")
        return Config()


def save_config(config: Config, use_mysql: Optional[bool] = None) -> None:
    """
    Save configuration to MySQL (if enabled) và JSON file.
    
    Args:
        config: Config instance to save
        use_mysql: If True, save to MySQL. If None, use default (MySQL).
    """
    if use_mysql is None:
        use_mysql = _USE_MYSQL_CONFIG
    
    # Save to MySQL if enabled
    if use_mysql:
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            config_storage = ConfigStorage(
                host=mysql_config.host,
                port=mysql_config.port,
                user=mysql_config.user,
                password=mysql_config.password,
                database=mysql_config.database,
                charset=mysql_config.charset,
                logger=StructuredLogger(name="config_storage")
            )
            config_storage.save_config(config)
        except Exception as e:
            # Log warning but continue to save to JSON file
            print(f"Warning: Failed to save config to MySQL: {e}, saving to JSON file")
    
    # Also save to JSON file (for backup/backward compatibility)
    try:
        data = _config_to_dict(config)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Failed to save config: {e}") from e


def _config_to_dict(config: Config) -> Dict[str, Any]:
    """Convert Config instance to dictionary."""
    return {
        "mode": config.mode.value,
        "browser": {
            "headless": config.browser.headless,
            "slow_mo": config.browser.slow_mo,
            "timeout": config.browser.timeout,
            "debug": config.browser.debug,
            "navigation_timeout": config.browser.navigation_timeout,
            "element_wait_timeout": config.browser.element_wait_timeout,
            "short_timeout": config.browser.short_timeout,
            "very_short_timeout": config.browser.very_short_timeout,
            "long_wait_timeout": config.browser.long_wait_timeout,
        },
        "selectors": {
            "version": config.selectors.version,
            "use_custom": config.selectors.use_custom,
            "platform": config.selectors.platform,
        },
        "anti_detection": {
            "min_delay": config.anti_detection.min_delay,
            "max_delay": config.anti_detection.max_delay,
            "typing_chunk_size": config.anti_detection.typing_chunk_size,
            "typing_delay_min": config.anti_detection.typing_delay_min,
            "typing_delay_max": config.anti_detection.typing_delay_max,
        },
        "safety": {
            "max_posts_per_day": config.safety.max_posts_per_day,
            "min_delay_between_posts": config.safety.min_delay_between_posts,
            "rate_limit_window": config.safety.rate_limit_window,
            "rate_limit_max_actions": config.safety.rate_limit_max_actions,
            "auto_pause_on_high_risk": config.safety.auto_pause_on_high_risk,
            "high_risk_threshold": config.safety.high_risk_threshold,
            "consecutive_error_threshold": config.safety.consecutive_error_threshold,
        },
        "scheduler": {
            "max_retries": config.scheduler.max_retries,
            "max_running_minutes": config.scheduler.max_running_minutes,
            "check_interval_seconds": config.scheduler.check_interval_seconds,
            "reload_interval_seconds": config.scheduler.reload_interval_seconds,
            "reload_check_delay_seconds": config.scheduler.reload_check_delay_seconds,
            "processing_delay_seconds": config.scheduler.processing_delay_seconds,
        },
        "storage": {
            "jobs_dir": config.storage.jobs_dir,
            "logs_dir": config.storage.logs_dir,
            "profiles_dir": config.storage.profiles_dir,
        },
        "platform": {
            "threads_base_url": config.platform.threads_base_url,
            "threads_compose_url": config.platform.threads_compose_url,
            "threads_login_url": config.platform.threads_login_url,
            "threads_profile_url": config.platform.threads_profile_url,
            "threads_post_url_template": config.platform.threads_post_url_template,
            "threads_post_fallback_template": config.platform.threads_post_fallback_template,
            "facebook_url": config.platform.facebook_url,
        },
        "analytics": {
            "fetch_metrics_timeout_seconds": config.analytics.fetch_metrics_timeout_seconds,
            "page_load_delay_seconds": config.analytics.page_load_delay_seconds,
            "page_load_alt_delay_seconds": config.analytics.page_load_alt_delay_seconds,
            "username_extraction_timeout_seconds": config.analytics.username_extraction_timeout_seconds,
            "username_page_load_delay_seconds": config.analytics.username_page_load_delay_seconds,
            "username_element_wait_timeout_ms": config.analytics.username_element_wait_timeout_ms,
            "username_click_timeout_ms": config.analytics.username_click_timeout_ms,
            "username_navigation_delay_seconds": config.analytics.username_navigation_delay_seconds,
            "delay_between_fetches_seconds": config.analytics.delay_between_fetches_seconds,
            "parallel_fetch_enabled": config.analytics.parallel_fetch_enabled,
            "max_concurrent_fetches": config.analytics.max_concurrent_fetches,
            "recent_metrics_hours": config.analytics.recent_metrics_hours,
        },
    }


def _dict_to_config(data: Dict[str, Any]) -> Config:
    """Convert dictionary to Config instance."""
    from config.config import (
        BrowserConfig,
        SelectorConfig,
        AntiDetectionConfig,
        SafetyConfig,
        SchedulerConfig,
        StorageConfig,
        PlatformConfig
    )
    
    browser_data = data.get("browser", {})
    browser = BrowserConfig(
        headless=browser_data.get("headless", False),
        slow_mo=browser_data.get("slow_mo", 100),
        timeout=browser_data.get("timeout", 30000),
        debug=browser_data.get("debug", False),
        navigation_timeout=browser_data.get("navigation_timeout", 30000),
        element_wait_timeout=browser_data.get("element_wait_timeout", 10000),
        short_timeout=browser_data.get("short_timeout", 5000),
        very_short_timeout=browser_data.get("very_short_timeout", 3000),
        long_wait_timeout=browser_data.get("long_wait_timeout", 15000),
    )
    
    selectors_data = data.get("selectors", {})
    selectors = SelectorConfig(
        version=selectors_data.get("version", "v1"),
        use_custom=selectors_data.get("use_custom", False),
        platform=selectors_data.get("platform", "threads"),
    )
    
    anti_detection_data = data.get("anti_detection", {})
    anti_detection = AntiDetectionConfig(
        min_delay=anti_detection_data.get("min_delay", 0.5),
        max_delay=anti_detection_data.get("max_delay", 2.0),
        typing_chunk_size=anti_detection_data.get("typing_chunk_size", 4),
        typing_delay_min=anti_detection_data.get("typing_delay_min", 0.05),
        typing_delay_max=anti_detection_data.get("typing_delay_max", 0.15),
    )
    
    safety_data = data.get("safety", {})
    safety = SafetyConfig(
        max_posts_per_day=safety_data.get("max_posts_per_day", 10),
        min_delay_between_posts=safety_data.get("min_delay_between_posts", 5),
        rate_limit_window=safety_data.get("rate_limit_window", 60),
        rate_limit_max_actions=safety_data.get("rate_limit_max_actions", 10),
        auto_pause_on_high_risk=safety_data.get("auto_pause_on_high_risk", True),
        high_risk_threshold=safety_data.get("high_risk_threshold", 3),
        consecutive_error_threshold=safety_data.get("consecutive_error_threshold", 5),
    )
    
    scheduler_data = data.get("scheduler", {})
    scheduler = SchedulerConfig(
        max_retries=scheduler_data.get("max_retries", 3),
        max_running_minutes=scheduler_data.get("max_running_minutes", 30),
        check_interval_seconds=scheduler_data.get("check_interval_seconds", 10),
        reload_interval_seconds=scheduler_data.get("reload_interval_seconds", 30),
        reload_check_delay_seconds=scheduler_data.get("reload_check_delay_seconds", 2),
        processing_delay_seconds=scheduler_data.get("processing_delay_seconds", 4.0),
        overdue_threshold_hours=scheduler_data.get("overdue_threshold_hours", None),
    )
    
    storage_data = data.get("storage", {})
    storage = StorageConfig(
        jobs_dir=storage_data.get("jobs_dir", "./jobs"),
        logs_dir=storage_data.get("logs_dir", "./logs"),
        profiles_dir=storage_data.get("profiles_dir", "./profiles"),
    )
    
    platform_data = data.get("platform", {})
    platform = PlatformConfig(
        threads_base_url=platform_data.get("threads_base_url", "https://www.threads.com/?hl=vi"),
        threads_compose_url=platform_data.get("threads_compose_url", "https://www.threads.com/?hl=vi/compose"),
        threads_login_url=platform_data.get("threads_login_url", "https://threads.net/login"),
        threads_profile_url=platform_data.get("threads_profile_url", "https://www.threads.com/"),
        threads_post_url_template=platform_data.get("threads_post_url_template", "https://www.threads.com/@{username}/post/{thread_id}"),
        threads_post_fallback_template=platform_data.get("threads_post_fallback_template", "https://www.threads.com/post/{thread_id}"),
        facebook_url=platform_data.get("facebook_url", "https://www.facebook.com"),
    )
    
    analytics_data = data.get("analytics", {})
    from config.config import AnalyticsConfig
    analytics = AnalyticsConfig(
        fetch_metrics_timeout_seconds=analytics_data.get("fetch_metrics_timeout_seconds", 30),
        page_load_delay_seconds=analytics_data.get("page_load_delay_seconds", 2.0),
        page_load_alt_delay_seconds=analytics_data.get("page_load_alt_delay_seconds", 3.0),
        username_extraction_timeout_seconds=analytics_data.get("username_extraction_timeout_seconds", 30),
        username_page_load_delay_seconds=analytics_data.get("username_page_load_delay_seconds", 3.0),
        username_element_wait_timeout_ms=analytics_data.get("username_element_wait_timeout_ms", 5000),
        username_click_timeout_ms=analytics_data.get("username_click_timeout_ms", 10000),
        username_navigation_delay_seconds=analytics_data.get("username_navigation_delay_seconds", 2.0),
        delay_between_fetches_seconds=analytics_data.get("delay_between_fetches_seconds", 2.0),
        parallel_fetch_enabled=analytics_data.get("parallel_fetch_enabled", True),
        max_concurrent_fetches=analytics_data.get("max_concurrent_fetches", 3),
        recent_metrics_hours=analytics_data.get("recent_metrics_hours", 1),
    )
    
    mode = RunMode(data.get("mode", data.get("run_mode", "SAFE")))
    
    return Config(
        mode=mode,
        browser=browser,
        selectors=selectors,
        anti_detection=anti_detection,
        safety=safety,
        scheduler=scheduler,
        storage=storage,
        platform=platform,
        analytics=analytics
    )

