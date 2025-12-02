"""Progress and user stats routes"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.progress import ProgressResponse, AchievementResponse, DashboardStats
from app.routers.auth import get_current_user_dep
from app.schemas.user import UserResponse
from app.services.progress_service import ProgressService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user dashboard statistics"""
    service = ProgressService(db)
    stats = service.get_dashboard_stats(UUID(current_user.id))
    
    return DashboardStats(
        total_xp=stats["total_xp"],
        level=stats["level"],
        current_streak=stats["current_streak"],
        total_quizzes=stats["total_quizzes"],
        total_questions=stats["total_questions"],
        average_accuracy=stats["average_accuracy"],
        recent_achievements=[
            AchievementResponse.model_validate(a) for a in stats["recent_achievements"]
        ],
        progresses=[
            ProgressResponse.model_validate(p) for p in stats["progresses"]
        ]
    )


@router.get("/certifications/{certification_id}", response_model=ProgressResponse)
async def get_certification_progress(
    certification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user progress for specific certification"""
    service = ProgressService(db)
    progress = service.get_certification_progress(UUID(current_user.id), certification_id)
    return ProgressResponse.model_validate(progress)


@router.get("/certifications", response_model=list[ProgressResponse])
async def get_all_progress(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user progress for all certifications"""
    service = ProgressService(db)
    progresses = service.get_all_progress(UUID(current_user.id))
    return [ProgressResponse.model_validate(p) for p in progresses]


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get all user achievements"""
    service = ProgressService(db)
    achievements = service.get_achievements(UUID(current_user.id))
    return [AchievementResponse.model_validate(a) for a in achievements]


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
