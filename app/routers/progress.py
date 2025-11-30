"""Progress and user stats routes"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import UserProgress, Profile, Achievement
from app.schemas.progress import ProgressResponse, AchievementResponse, DashboardStats
from app.routers.auth import get_current_user_dep
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user dashboard statistics"""
    
    user_id = UUID(current_user.id)
    
    # Get profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Get all progresses
    progresses = db.query(UserProgress).filter(
        UserProgress.user_id == user_id
    ).all()
    
    # Calculate overall accuracy
    total_questions = sum(p.total_questions_answered or 0 for p in progresses)
    total_correct = sum(p.correct_answers or 0 for p in progresses)
    average_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    # Get recent achievements
    recent_achievements = db.query(Achievement).filter(
        Achievement.user_id == user_id
    ).order_by(Achievement.earned_at.desc()).limit(5).all()
    
    return DashboardStats(
        total_xp=profile.xp,
        level=profile.level,
        current_streak=profile.current_streak,
        total_quizzes=sum(p.total_quizzes or 0 for p in progresses),
        total_questions=total_questions,
        average_accuracy=average_accuracy,
        recent_achievements=[
            AchievementResponse.model_validate(a) for a in recent_achievements
        ],
        progresses=[
            ProgressResponse.model_validate(p) for p in progresses
        ]
    )


@router.get("/certifications/{certification_id}", response_model=ProgressResponse)
async def get_certification_progress(
    certification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user progress for specific certification"""
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == UUID(current_user.id),
        UserProgress.certification_id == certification_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found for this certification"
        )
    
    return ProgressResponse.model_validate(progress)


@router.get("/certifications", response_model=list[ProgressResponse])
async def get_all_progress(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user progress for all certifications"""
    
    progresses = db.query(UserProgress).filter(
        UserProgress.user_id == UUID(current_user.id)
    ).all()
    
    return [ProgressResponse.model_validate(p) for p in progresses]


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get all user achievements"""
    
    achievements = db.query(Achievement).filter(
        Achievement.user_id == UUID(current_user.id)
    ).order_by(Achievement.earned_at.desc()).all()
    
    return [AchievementResponse.model_validate(a) for a in achievements]
