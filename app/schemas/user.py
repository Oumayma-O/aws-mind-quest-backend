"""User request/response schemas"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str
    password: str
    selected_certification_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "securepassword123",
                "selected_certification_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class UserResponse(BaseModel):
    """User response (public data)"""
    id: UUID
    email: EmailStr
    username: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """JWT token payload data"""
    sub: str  # user_id
    email: str


class ProfileResponse(BaseModel):
    """User profile response"""
    id: UUID
    user_id: UUID
    username: str
    selected_certification_id: Optional[UUID] = None
    xp: int
    level: int
    current_streak: int
    last_quiz_date: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    """Update user profile"""
    selected_certification_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "selected_certification_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
