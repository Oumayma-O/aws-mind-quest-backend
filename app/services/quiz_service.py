"""Business logic for quiz history and retrieval"""

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.models import Quiz

logger = logging.getLogger(__name__)


class QuizService:
    """Service for quiz history and retrieval operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_quiz_history(
        self,
        user_id: UUID,
        certification_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Quiz]:
        """
        Get user's quiz history
        
        Args:
            user_id: User ID
            certification_id: Optional filter by certification
            limit: Number of quizzes to return
            offset: Pagination offset
            
        Returns:
            List of quizzes
        """
        query = self.db.query(Quiz).filter(Quiz.user_id == user_id)
        
        if certification_id:
            query = query.filter(Quiz.certification_id == certification_id)
        
        return query.order_by(Quiz.created_at.desc()).limit(limit).offset(offset).all()
    
    def get_quiz_by_id(self, quiz_id: UUID, user_id: UUID) -> Quiz:
        """
        Get quiz by ID (user must own it)
        
        Args:
            quiz_id: Quiz ID
            user_id: User ID for ownership validation
            
        Returns:
            Quiz with all questions
            
        Raises:
            HTTPException: If quiz not found or user doesn't own it
        """
        quiz = self.db.query(Quiz).filter(
            Quiz.id == quiz_id,
            Quiz.user_id == user_id
        ).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        return quiz
    
    def get_quiz_stats(self, user_id: UUID) -> dict:
        """
        Get aggregate quiz statistics for a user
        
        Returns:
            Dictionary with total_quizzes, avg_score, total_xp
        """
        quizzes = self.db.query(Quiz).filter(Quiz.user_id == user_id).all()
        
        if not quizzes:
            return {
                "total_quizzes": 0,
                "avg_score": 0,
                "total_xp": 0,
                "avg_accuracy": 0
            }
        
        total_score = sum(q.score for q in quizzes)
        total_questions = sum(q.total_questions for q in quizzes)
        total_xp = sum(q.xp_earned for q in quizzes)
        
        return {
            "total_quizzes": len(quizzes),
            "avg_score": total_score / len(quizzes),
            "total_xp": total_xp,
            "avg_accuracy": (total_score / total_questions * 100) if total_questions > 0 else 0
        }
