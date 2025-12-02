import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.quiz import (
    QuizGenerateRequest, QuizGenerateResponse, QuizEvaluateRequest,
    QuizEvaluateResponse, QuizHistoryResponse, QuizDetailResponse
)
from app.services.quiz_service import QuizService
from app.services.quiz_generator import QuizGeneratorService
from app.services.quiz_evaluator import QuizEvaluatorService
from app.routers.auth import get_current_user_dep
from app.schemas.user import UserResponse
from app.utils.timer import timer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


def get_quiz_service(db: Session = Depends(get_db)) -> QuizService:
    """Provide QuizService via DI per request."""
    return QuizService(db)


def get_quiz_generator_service(db: Session = Depends(get_db)) -> QuizGeneratorService:
    """Provide QuizGeneratorService via DI per request."""
    return QuizGeneratorService(db)


def get_quiz_evaluator_service(db: Session = Depends(get_db)) -> QuizEvaluatorService:
    """Provide QuizEvaluatorService via DI per request."""
    return QuizEvaluatorService(db)


@router.post("/generate", response_model=QuizGenerateResponse, status_code=201)
@timer(logger=logger)
async def generate_quiz(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    generator: QuizGeneratorService = Depends(get_quiz_generator_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """
    Generate a new quiz with AI-generated questions
    
    This endpoint migrates the Supabase `generate-quiz` function to FastAPI.
    
    - **certification_id**: The AWS certification to quiz on
    - **difficulty**: Quiz difficulty level (easy, medium, hard)
    - **weak_domains**: Optional list of domains to focus on (from previous results)
    
    The quiz questions are generated using OpenAI API based on the certification
    and difficulty level. If weak_domains are provided, the LLM will prioritize
    those areas to help the user improve.
    """
    
    try:
        # Generate quiz using LLM service
        quiz = await generator.generate_quiz(
            user_id=current_user.id,
            certification_id=request.certification_id,
            difficulty=request.difficulty,
            weak_domains=request.weak_domains
        )
        
        # Build response with questions
        questions = [
            {
                "id": q.id,
                "quiz_id": q.quiz_id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "domain": q.domain,
                "user_answer": q.user_answer,
                "is_correct": q.is_correct,
                "xp_earned": q.xp_earned,
                "created_at": q.created_at
            }
            for q in quiz.questions
        ]
        
        return QuizGenerateResponse(
            quiz_id=quiz.id,
            certification_id=quiz.certification_id,
            difficulty=quiz.difficulty,
            total_questions=quiz.total_questions,
            questions=questions
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz"
        )


@router.post("/{quiz_id}/evaluate", response_model=QuizEvaluateResponse)
@timer(logger=logger)
async def evaluate_quiz(
    quiz_id: UUID,
    request: QuizEvaluateRequest,
    db: Session = Depends(get_db),
    evaluator: QuizEvaluatorService = Depends(get_quiz_evaluator_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """
    Evaluate quiz answers and calculate score
    
    This endpoint migrates the Supabase `evaluate-quiz` function to FastAPI.
    
    - **quiz_id**: The quiz being evaluated
    - **answers**: Dictionary of question_id -> user_answer
    
    This endpoint:
    1. Grades all questions
    2. Calculates XP earned based on difficulty
    3. Updates user profile (XP, level, streak)
    4. Identifies weak domains for targeted improvement
    5. Suggests next difficulty level
    6. Awards achievements (streaks, accuracy milestones)
    
    Returns:
    - Score and accuracy
    - XP earned and new level
    - Streak information
    - Achievements unlocked
    - Weak domains for focused study
    - Recommended next difficulty
    """
    
    try:
        # Evaluate quiz using evaluator service
        result = await evaluator.evaluate_quiz(
            user_id=UUID(current_user.id),
            quiz_id=quiz_id,
            answers=request.answers
        )
        
        return QuizEvaluateResponse(
            success=result["success"],
            score=result["score"],
            total_questions=result["total_questions"],
            accuracy=result["accuracy"],
            xp_earned=result["xp_earned"],
            new_level=result["new_level"],
            new_streak=result["new_streak"],
            achievements=result["achievements"],
            weak_domains=result["weak_domains"],
            next_difficulty=result["next_difficulty"]
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error evaluating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate quiz"
        )


@router.get("", response_model=list[QuizHistoryResponse])
@timer(logger=logger)
async def get_quiz_history(
    certification_id: UUID = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    service: QuizService = Depends(get_quiz_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """
    Get user's quiz history
    """
    quizzes = service.get_quiz_history(
        user_id=UUID(current_user.id),
        certification_id=certification_id,
        limit=limit,
        offset=offset
    )
    
    return [
        QuizHistoryResponse(
            id=q.id,
            certification_id=q.certification_id,
            difficulty=q.difficulty,
            score=q.score,
            total_questions=q.total_questions,
            accuracy=(q.score / q.total_questions * 100) if q.total_questions > 0 else 0,
            xp_earned=q.xp_earned,
            completed_at=q.completed_at
        )
        for q in quizzes
    ]


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
@timer(logger=logger)
async def get_quiz_detail(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    service: QuizService = Depends(get_quiz_service),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get detailed quiz information with all questions"""
    quiz = service.get_quiz_by_id(quiz_id, UUID(current_user.id))
    
    accuracy = (quiz.score / quiz.total_questions * 100) if quiz.total_questions > 0 else 0
    
    return QuizDetailResponse(
        id=quiz.id,
        certification_id=quiz.certification_id,
        difficulty=quiz.difficulty,
        score=quiz.score,
        total_questions=quiz.total_questions,
        accuracy=accuracy,
        xp_earned=quiz.xp_earned,
        questions=[
            {
                "id": q.id,
                "quiz_id": q.quiz_id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "domain": q.domain,
                "user_answer": q.user_answer,
                "is_correct": q.is_correct,
                "xp_earned": q.xp_earned,
                "created_at": q.created_at
            }
            for q in quiz.questions
        ],
        completed_at=quiz.completed_at
    )
