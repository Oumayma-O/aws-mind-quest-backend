"""User profile routes"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import Profile, Certification
from app.schemas.user import ProfileResponse, ProfileUpdate
from app.routers.auth import get_current_user_dep
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get current user's profile"""
    
    profile = db.query(Profile).filter(
        Profile.user_id == UUID(current_user.id)
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ProfileResponse.model_validate(profile)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    update_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Update user profile"""
    
    profile = db.query(Profile).filter(
        Profile.user_id == UUID(current_user.id)
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Validate certification if provided
    if update_data.selected_certification_id:
        cert = db.query(Certification).filter(
            Certification.id == update_data.selected_certification_id
        ).first()
        
        if not cert:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid certification ID"
            )
    
    # Update profile
    if update_data.selected_certification_id:
        profile.selected_certification_id = update_data.selected_certification_id
    
    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return ProfileResponse.model_validate(profile)
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )
