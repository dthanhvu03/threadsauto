"""
Dashboard schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Optional, Dict, Any, List

# Third-party
from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    
    total_jobs: int
    pending_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    
    class Config:
        """Pydantic config."""
        orm_mode = True


class DashboardMetrics(BaseModel):
    """Schema for dashboard metrics."""
    
    jobs_by_status: Dict[str, int]
    jobs_by_platform: Dict[str, int]
    posts_timeline: List[Dict[str, Any]]
    hourly_distribution: Dict[str, int]
    analytics: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic config."""
        orm_mode = True


class ActivityQuery(BaseModel):
    """Schema for activity query parameters."""
    
    account_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "account_id": "account_001",
                "limit": 10
            }
        }
