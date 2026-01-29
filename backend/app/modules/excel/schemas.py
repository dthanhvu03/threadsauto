"""
Excel schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Optional

# Third-party
from pydantic import BaseModel, Field


class ExcelUploadResponse(BaseModel):
    """Schema for Excel upload response."""
    
    filename: str
    account_id: Optional[str] = None
    jobs_created: Optional[int] = None
    
    class Config:
        """Pydantic config."""
        orm_mode = True
