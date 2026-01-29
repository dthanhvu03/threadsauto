"""
FastAPI dependencies.

Shared dependencies cho API routes.
"""

# Local
from backend.api.adapters.jobs_adapter import JobsAPI
from backend.api.adapters.accounts_adapter import AccountsAPI
from backend.api.adapters.analytics_adapter import AnalyticsAPI
from backend.api.adapters.metrics_adapter import MetricsAPI
from backend.api.adapters.safety_adapter import SafetyAPI
from backend.api.adapters.selectors_adapter import SelectorsAPI

# Global instances (singleton pattern)
_jobs_api_instance = None
_accounts_api_instance = None
_analytics_api_instance = None
_metrics_api_instance = None
_safety_api_instance = None
_selectors_api_instance = None


def get_jobs_api() -> JobsAPI:
    """Get JobsAPI instance (singleton)."""
    global _jobs_api_instance
    if _jobs_api_instance is None:
        _jobs_api_instance = JobsAPI()
    return _jobs_api_instance


def get_accounts_api() -> AccountsAPI:
    """Get AccountsAPI instance (singleton)."""
    global _accounts_api_instance
    if _accounts_api_instance is None:
        _accounts_api_instance = AccountsAPI()
    return _accounts_api_instance


def get_analytics_api() -> AnalyticsAPI:
    """Get AnalyticsAPI instance (singleton)."""
    global _analytics_api_instance
    if _analytics_api_instance is None:
        _analytics_api_instance = AnalyticsAPI()
    return _analytics_api_instance


def get_metrics_api() -> MetricsAPI:
    """Get MetricsAPI instance (singleton)."""
    global _metrics_api_instance
    if _metrics_api_instance is None:
        _metrics_api_instance = MetricsAPI()
    return _metrics_api_instance


def get_safety_api() -> SafetyAPI:
    """Get SafetyAPI instance (singleton)."""
    global _safety_api_instance
    if _safety_api_instance is None:
        _safety_api_instance = SafetyAPI()
    return _safety_api_instance


def get_selectors_api() -> SelectorsAPI:
    """Get SelectorsAPI instance (singleton)."""
    global _selectors_api_instance
    if _selectors_api_instance is None:
        _selectors_api_instance = SelectorsAPI()
    return _selectors_api_instance
