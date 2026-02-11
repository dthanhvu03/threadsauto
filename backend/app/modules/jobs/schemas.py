"""
Jobs schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Optional
from datetime import datetime

# Third-party
from pydantic import BaseModel, Field, validator


class JobCreate(BaseModel):
    """Schema for creating a job."""
    
    account_id: str = Field(..., description="Account ID")
    content: str = Field(..., description="Job content", min_length=1)
    scheduled_time: str = Field(..., description="Scheduled time in ISO format")
    priority: str = Field(default="NORMAL", description="Job priority (NORMAL, HIGH, URGENT)")
    platform: str = Field(default="THREADS", description="Platform (THREADS, FACEBOOK)")
    link_aff: Optional[str] = Field(None, description="Optional affiliate link")
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority value."""
        valid_priorities = ['NORMAL', 'HIGH', 'URGENT']
        if v.upper() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.upper()
    
    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform value."""
        valid_platforms = ['THREADS', 'FACEBOOK']
        if v.upper() not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return v.upper()
    
    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        """Validate scheduled_time format."""
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError("scheduled_time must be in ISO format")
        return v
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "account_id": "account_001",
                "content": "Hello Threads!",
                "scheduled_time": "2026-01-25T10:00:00",
                "priority": "NORMAL",
                "platform": "THREADS",
                "link_aff": None
            }
        }


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    
    content: Optional[str] = Field(None, description="Job content", min_length=1)
    account_id: Optional[str] = Field(None, description="Account ID")
    scheduled_time: Optional[str] = Field(None, description="Scheduled time in ISO format")
    priority: Optional[str] = Field(None, description="Job priority")
    platform: Optional[str] = Field(None, description="Platform")
    max_retries: Optional[int] = Field(None, description="Maximum retries", ge=0, le=10)
    link_aff: Optional[str] = Field(None, description="Optional affiliate link")
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority value."""
        if v is None:
            return v
        valid_priorities = ['NORMAL', 'HIGH', 'URGENT']
        if v.upper() not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v.upper()
    
    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform value."""
        if v is None:
            return v
        valid_platforms = ['THREADS', 'FACEBOOK']
        if v.upper() not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return v.upper()
    
    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        """Validate scheduled_time format."""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError("scheduled_time must be in ISO format")
        return v


class JobResponse(BaseModel):
    """Schema for job response."""
    
    job_id: str
    account_id: str
    content: str
    scheduled_time: Optional[str]
    status: str
    priority: Optional[str]
    platform: Optional[str]
    thread_id: Optional[str]
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    
    class Config:
        """Pydantic config."""
        orm_mode = True
