"""User profile routes"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.user import ProfileResponse, ProfileUpdate, UserResponse
from app.routers.auth import get_current_user_dep
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get current user's profile"""
    service = ProfileService(db)
    profile = service.get_profile(UUID(current_user.id))
    return ProfileResponse.model_validate(profile)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    update_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Update user profile"""
    service = ProfileService(db)
    profile = service.update_profile(
        user_id=UUID(current_user.id),
        selected_certification_id=update_data.selected_certification_id
    )
    return ProfileResponse.model_validate(profile)
