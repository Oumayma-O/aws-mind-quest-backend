"""Business logic for user profile management"""

import logging
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.models import Profile, Certification

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_profile(self, user_id: UUID) -> Profile:
        """Get user profile by user ID"""
        profile = self.db.query(Profile).filter(
            Profile.user_id == user_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return profile
    
    def update_profile(
        self,
        user_id: UUID,
        selected_certification_id: UUID = None
    ) -> Profile:
        """
        Update user profile
        
        Args:
            user_id: User ID
            selected_certification_id: Optional certification to select
            
        Returns:
            Updated profile
        """
        profile = self.db.query(Profile).filter(
            Profile.user_id == user_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Validate certification if provided
        if selected_certification_id:
            cert = self.db.query(Certification).filter(
                Certification.id == selected_certification_id
            ).first()
            
            if not cert:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid certification ID"
                )
            
            profile.selected_certification_id = selected_certification_id
        
        try:
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
