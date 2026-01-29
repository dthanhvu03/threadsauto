"""
Scheduler schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Optional, List, Dict, Any

# Third-party
from pydantic import BaseModel, Field


class SchedulerStatus(BaseModel):
    """Schema for scheduler status."""
    
    running: bool
    active_jobs_count: int
    
    class Config:
        """Pydantic config."""
        orm_mode = True


class SchedulerStartRequest(BaseModel):
    """Schema for starting scheduler."""
    
    account_id: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "account_id": "account_001"
            }
        }
