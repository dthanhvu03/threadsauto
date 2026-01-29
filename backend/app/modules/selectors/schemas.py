"""
Selectors schemas.

Pydantic models for request/response validation and serialization.
"""

# Standard library
from typing import Dict, List, Optional, Any

# Third-party
from pydantic import BaseModel, Field


class SelectorsResponse(BaseModel):
    """Schema for selectors response."""
    
    platform: str
    version: str
    selectors: Dict[str, List[str]]
    
    class Config:
        """Pydantic config."""
        orm_mode = True


class SelectorsUpdate(BaseModel):
    """Schema for updating selectors."""
    
    platform: str = Field(default="threads")
    version: str = Field(default="v1")
    selectors: Dict[str, List[str]] = Field(..., description="Selectors data is required")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "platform": "threads",
                "version": "v1",
                "selectors": {
                    "compose_input": ["div[contenteditable='true']"],
                    "post_button": ["button[type='submit']"]
                }
            }
        }
