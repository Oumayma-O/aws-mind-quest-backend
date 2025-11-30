"""Quiz request/response schemas"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any, Union


class QuestionBase(BaseModel):
    """Base question schema"""
    question_text: str
    question_type: str  # multiple_choice, multi_select, true_false
    options: List[str]
    correct_answer: Union[str, List[str]]
    explanation: str
    difficulty: str
    domain: str


class QuestionCreate(QuestionBase):
    """Question creation schema (from LLM)"""
    pass


class QuestionResponse(QuestionBase):
    """Question response"""
    id: UUID
    quiz_id: UUID
    user_answer: Optional[Union[str, List[str]]] = None
    is_correct: Optional[bool] = None
    xp_earned: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuizGenerateRequest(BaseModel):
    """Generate quiz request"""
    certification_id: UUID
    difficulty: str = "easy"  # easy, medium, hard
    weak_domains: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "certification_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium",
                "weak_domains": ["EC2", "VPC"]
            }
        }


class QuizGenerateResponse(BaseModel):
    """Generate quiz response"""
    quiz_id: UUID
    certification_id: UUID
    difficulty: str
    total_questions: int
    questions: List[QuestionResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "quiz_id": "550e8400-e29b-41d4-a716-446655440001",
                "certification_id": "550e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium",
                "total_questions": 5,
                "questions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "question_text": "What is EC2?",
                        "question_type": "multiple_choice",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                        "explanation": "Explanation here...",
                        "difficulty": "easy",
                        "domain": "EC2",
                        "quiz_id": "550e8400-e29b-41d4-a716-446655440001",
                        "user_answer": None,
                        "is_correct": None,
                        "xp_earned": 0,
                        "created_at": "2025-01-01T00:00:00"
                    }
                ]
            }
        }


class QuizEvaluateRequest(BaseModel):
    """Evaluate quiz request"""
    quiz_id: UUID
    answers: dict[str, Union[str, List[str]]]  # question_id -> answer
    
    class Config:
        json_schema_extra = {
            "example": {
                "quiz_id": "550e8400-e29b-41d4-a716-446655440001",
                "answers": {
                    "550e8400-e29b-41d4-a716-446655440002": "Option A",
                    "550e8400-e29b-41d4-a716-446655440003": ["Option A", "Option C"]
                }
            }
        }


class DomainPerformance(BaseModel):
    """Domain performance info"""
    name: str
    correct: int
    total: int
    accuracy: int = Field(ge=0, le=100)


class WeakDomain(BaseModel):
    """Weak domain info"""
    name: str
    accuracy: int = Field(ge=0, le=100)


class QuizEvaluateResponse(BaseModel):
    """Evaluate quiz response"""
    success: bool
    score: int
    total_questions: int
    accuracy: float = Field(ge=0, le=100)
    xp_earned: int
    new_level: int
    new_streak: int
    achievements: List[str] = []
    weak_domains: List[WeakDomain] = []
    next_difficulty: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "score": 4,
                "total_questions": 5,
                "accuracy": 80.0,
                "xp_earned": 35,
                "new_level": 3,
                "new_streak": 5,
                "achievements": ["Perfect Score"],
                "weak_domains": [
                    {"name": "VPC", "accuracy": 50}
                ],
                "next_difficulty": "hard"
            }
        }


class QuizHistoryResponse(BaseModel):
    """Quiz history response"""
    id: UUID
    certification_id: UUID
    difficulty: str
    score: int
    total_questions: int
    accuracy: float
    xp_earned: int
    completed_at: datetime
    
    class Config:
        from_attributes = True


class QuizDetailResponse(BaseModel):
    """Quiz detail with questions"""
    id: UUID
    certification_id: UUID
    difficulty: str
    score: int
    total_questions: int
    accuracy: float
    xp_earned: int
    questions: List[QuestionResponse]
    completed_at: datetime
    
    class Config:
        from_attributes = True
