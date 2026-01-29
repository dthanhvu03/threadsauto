"""
Accounts schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Optional, Dict, Any

# Third-party
from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    """Schema for creating an account."""
    
    account_id: str = Field(..., description="Account ID", min_length=1)
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "account_id": "account_001"
            }
        }


class AccountResponse(BaseModel):
    """Schema for account response."""
    
    account_id: str
    jobs_count: int
    profile_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic config."""
        orm_mode = True


class AccountStats(BaseModel):
    """Schema for account statistics."""
    
    account_id: str
    jobs_count: int
    profile_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic config."""
        orm_mode = True
