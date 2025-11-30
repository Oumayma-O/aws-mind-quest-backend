"""Quiz generation service - migrated from Supabase functions"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.database.models import Quiz, Question, UserProgress, Certification, Profile
from app.services.llm_service import LLMService
from app.schemas.quiz import QuestionCreate

logger = logging.getLogger(__name__)

# AWS domains for quiz generation
AWS_DOMAINS = [
    "IAM (Identity and Access Management)",
    "EC2 (Elastic Compute Cloud)",
    "S3 (Simple Storage Service)",
    "VPC (Virtual Private Cloud)",
    "RDS (Relational Database Service)",
    "Lambda",
    "CloudWatch",
    "CloudFormation",
    "Security and Compliance",
    "Pricing and Support"
]


class QuizGeneratorService:
    """Service for generating quizzes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()
    
    async def generate_quiz(
        self,
        user_id: UUID,
        certification_id: UUID,
        difficulty: str,
        weak_domains: Optional[List[Dict[str, Any]]] = None
    ) -> Quiz:
        """
        Generate a new quiz using LLM
        
        Migrated from: supabase/functions/generate-quiz/index.ts
        
        Args:
            user_id: User ID
            certification_id: Certification ID
            difficulty: Difficulty level (easy, medium, hard)
            weak_domains: List of weak domains to focus on
            
        Returns:
            Quiz object with generated questions
        """
        
        # Get certification
        certification = self.db.query(Certification).filter(
            Certification.id == certification_id
        ).first()
        if not certification:
            raise ValueError("Certification not found")
        
        # Determine focus domains
        focus_domains = []
        if weak_domains and len(weak_domains) > 0:
            # Prioritize weak domains
            focus_domains = [d.get("name") for d in weak_domains[:3]]
        else:
            # Use first 3 AWS domains
            focus_domains = [d.split("(")[0].strip() for d in AWS_DOMAINS[:3]]
        
        # Generate quiz using LLM
        logger.info(f"Generating quiz for user {user_id} with focus domains: {focus_domains}")
        quiz_data = await self.llm.generate_quiz(
            certification=certification.name,
            difficulty=difficulty,
            focus_domains=focus_domains
        )
        
        # Create quiz record
        quiz = Quiz(
            user_id=user_id,
            certification_id=certification_id,
            difficulty=difficulty,
            total_questions=len(quiz_data.get("questions", []))
        )
        self.db.add(quiz)
        self.db.flush()  # Get quiz ID
        
        # Create question records
        questions = []
        for q in quiz_data.get("questions", []):
            question = Question(
                quiz_id=quiz.id,
                question_text=q.get("question_text"),
                question_type=q.get("question_type"),
                options=q.get("options"),
                correct_answer=q.get("correct_answer"),
                explanation=q.get("explanation"),
                difficulty=q.get("difficulty"),
                domain=q.get("domain")
            )
            self.db.add(question)
            questions.append(question)
        
        self.db.commit()
        self.db.refresh(quiz)
        
        logger.info(f"Quiz {quiz.id} generated successfully with {len(questions)} questions")
        return quiz
