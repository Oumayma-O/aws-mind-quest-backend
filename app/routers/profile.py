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


def get_profile_service(db: Session = Depends(get_db)) -> ProfileService:
    """Provide ProfileService via DI per request."""
    return ProfileService(db)

@router.get("", response_model=ProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get current user's profile"""
    profile = service.get_profile(current_user.id)
    return profile


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    update_data: ProfileUpdate,
    db: Session = Depends(get_db),
    service: ProfileService = Depends(get_profile_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Update user profile"""
    profile = service.update_profile(
        user_id=current_user.id,
        selected_certification_id=update_data.selected_certification_id
    )
    return ProfileResponse.model_validate(profile)
