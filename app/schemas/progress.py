"""Progress and achievement schemas"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any


class WeakDomainInfo(BaseModel):
    """Weak domain information"""
    name: str
    accuracy: int


class ProgressResponse(BaseModel):
    """User progress response"""
    id: UUID
    user_id: UUID
    certification_id: UUID
    total_xp: int
    total_quizzes: int
    total_questions_answered: int
    correct_answers: int
    accuracy: float
    current_difficulty: str
    domain_difficulties: Dict[str, str] = {}
    weak_domains: List[WeakDomainInfo] = []
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AchievementResponse(BaseModel):
    """Achievement response"""
    id: UUID
    achievement_type: str
    achievement_name: str
    achievement_description: Optional[str] = None
    earned_at: datetime
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_xp: int
    level: int
    current_streak: int
    total_quizzes: int
    total_questions: int
    average_accuracy: float
    recent_achievements: List[AchievementResponse] = []
    progresses: List[ProgressResponse] = []
