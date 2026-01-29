"""
Config schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Dict, Any

# Third-party
from pydantic import BaseModel


class ConfigResponse(BaseModel):
    """Schema for config response."""
    
    run_mode: str
    selectors: Dict[str, Any] = {}
    browser: Dict[str, Any] = {}
    anti_detection: Dict[str, Any] = {}
    
    class Config:
        """Pydantic config."""
        orm_mode = True
        extra = "allow"  # Allow additional fields
