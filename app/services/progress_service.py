"""Business logic for progress tracking and dashboard"""

import logging
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.models import UserProgress, Profile, Achievement

logger = logging.getLogger(__name__)


class ProgressService:
    """Service for managing user progress and stats"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self, user_id: UUID) -> dict:
        """
        Get comprehensive dashboard statistics
        
        Returns:
            Dictionary with profile, progress, and achievement data
        """
        # Get profile
        profile = self.db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Get all progresses
        progresses = self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).all()
        
        # Calculate aggregates
        total_questions = sum(p.total_questions_answered or 0 for p in progresses)
        total_correct = sum(p.correct_answers or 0 for p in progresses)
        average_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        # Get recent achievements
        recent_achievements = (
            self.db.query(Achievement)
            .filter(Achievement.user_id == user_id)
            .order_by(Achievement.earned_at.desc())
            .limit(5)
            .all()
        )
        
        return {
            "total_xp": profile.xp,
            "level": profile.level,
            "current_streak": profile.current_streak,
            "total_quizzes": sum(p.total_quizzes or 0 for p in progresses),
            "total_questions": total_questions,
            "average_accuracy": average_accuracy,
            "recent_achievements": recent_achievements,
            "progresses": progresses
        }
    
    def get_certification_progress(self, user_id: UUID, certification_id: UUID) -> UserProgress:
        """Get progress for a specific certification, creating it if it doesn't exist"""
        progress = self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.certification_id == certification_id
        ).first()
        
        # Cold start: Create initial progress record if it doesn't exist
        if not progress:
            # Verify certification exists
            from app.database.models import Certification
            certification = self.db.query(Certification).filter(
                Certification.id == certification_id
            ).first()
            
            if not certification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Certification not found"
                )
            
            # Create initial progress
            progress = UserProgress(
                user_id=user_id,
                certification_id=certification_id,
                total_xp=0,
                total_quizzes=0,
                total_questions_answered=0,
                correct_answers=0,
                accuracy=0,
                domain_difficulties={},
                weak_domains=[]
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)
            logger.info(f"Created initial progress for user {user_id} on certification {certification_id}")
        
        return progress
    
    def get_all_progress(self, user_id: UUID) -> List[UserProgress]:
        """Get progress across all certifications"""
        return self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).all()
    
    def get_achievements(self, user_id: UUID) -> List[Achievement]:
        """Get all user achievements"""
        return (
            self.db.query(Achievement)
            .filter(Achievement.user_id == user_id)
            .order_by(Achievement.earned_at.desc())
            .all()
        )
