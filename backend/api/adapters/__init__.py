"""
API adapters for backend.

These adapters provide orchestration layer between API routes and services.
Moved from ui/api/ to backend/api/adapters/ for better architecture.
"""

from backend.api.adapters.jobs_adapter import JobsAPI
from backend.api.adapters.accounts_adapter import AccountsAPI
from backend.api.adapters.analytics_adapter import AnalyticsAPI
from backend.api.adapters.metrics_adapter import MetricsAPI
from backend.api.adapters.safety_adapter import SafetyAPI
from backend.api.adapters.selectors_adapter import SelectorsAPI

__all__ = [
    "JobsAPI",
    "AccountsAPI",
    "AnalyticsAPI",
    "MetricsAPI",
    "SafetyAPI",
    "SelectorsAPI",
]
