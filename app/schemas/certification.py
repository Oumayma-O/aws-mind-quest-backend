"""Certification schemas"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class CertificationCreate(BaseModel):
    """Create certification request"""
    name: str
    description: str = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "AWS Cloud Practitioner",
                "description": "Foundational understanding of AWS Cloud"
            }
        }


class CertificationResponse(BaseModel):
    """Certification response"""
    id: UUID
    name: str
    description: str = None
    created_at: datetime
    
    class Config:
        from_attributes = True
