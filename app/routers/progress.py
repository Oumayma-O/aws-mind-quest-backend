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


def get_progress_service(db: Session = Depends(get_db)) -> ProgressService:
    """Provide ProgressService via DI per request."""
    return ProgressService(db)

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    service: ProgressService = Depends(get_progress_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user dashboard statistics"""
    stats = service.get_dashboard_stats(current_user.id)
    
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
    service: ProgressService = Depends(get_progress_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user progress for specific certification"""
    progress = service.get_certification_progress(current_user.id, certification_id)
    return ProgressResponse.model_validate(progress)


@router.get("/certifications", response_model=list[ProgressResponse])
async def get_all_progress(
    db: Session = Depends(get_db),
    service: ProgressService = Depends(get_progress_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get user progress for all certifications"""
    progresses = service.get_all_progress(current_user.id)
    return [ProgressResponse.model_validate(p) for p in progresses]


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    db: Session = Depends(get_db),
    service: ProgressService = Depends(get_progress_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get all user achievements"""
    achievements = service.get_achievements(current_user.id)
    return [AchievementResponse.model_validate(a) for a in achievements]

