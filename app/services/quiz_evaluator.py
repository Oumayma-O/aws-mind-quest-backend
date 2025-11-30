"""Quiz evaluation service - migrated from Supabase functions"""

import logging
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import (
    Quiz, Question, UserProgress, Profile, Achievement, User
)

logger = logging.getLogger(__name__)


class QuizEvaluatorService:
    """Service for evaluating quizzes and scoring"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def evaluate_quiz(
        self,
        user_id: UUID,
        quiz_id: UUID,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate quiz answers and update user progress
        
        Migrated from: supabase/functions/evaluate-quiz/index.ts
        
        Args:
            user_id: User ID
            quiz_id: Quiz ID
            answers: Dict of question_id -> user_answer
            
        Returns:
            Dictionary with evaluation results
        """
        
        # Get quiz with questions
        quiz = self.db.query(Quiz).filter(
            Quiz.id == quiz_id,
            Quiz.user_id == user_id
        ).first()
        if not quiz:
            raise ValueError("Quiz not found")
        
        # Evaluate each question
        score = 0
        total_xp = 0
        domain_performance: Dict[str, Dict[str, int]] = {}
        question_updates = []
        
        for question in quiz.questions:
            user_answer = answers.get(str(question.id))
            is_correct = self._check_answer(question, user_answer)
            
            # Update question
            question.user_answer = user_answer
            question.is_correct = is_correct
            
            # Calculate XP
            xp_earned = 0
            if is_correct:
                score += 1
                if question.difficulty == "easy":
                    xp_earned = 5
                elif question.difficulty == "medium":
                    xp_earned = 10
                else:  # hard
                    xp_earned = 20
            
            question.xp_earned = xp_earned
            total_xp += xp_earned
            
            # Track domain performance
            if question.domain not in domain_performance:
                domain_performance[question.domain] = {"correct": 0, "total": 0}
            domain_performance[question.domain]["total"] += 1
            if is_correct:
                domain_performance[question.domain]["correct"] += 1
            
            question_updates.append(question)
        
        # Save question updates
        for question in question_updates:
            self.db.add(question)
        
        # Update quiz
        quiz.score = score
        quiz.xp_earned = total_xp
        self.db.add(quiz)
        
        # Get user profile
        profile = self.db.query(Profile).filter(
            Profile.user_id == user_id
        ).first()
        if not profile:
            raise ValueError("User profile not found")
        
        # Update user profile
        new_xp = profile.xp + total_xp
        new_level = (new_xp // 100) + 1
        
        # Update streak
        today = datetime.utcnow().strftime("%Y-%m-%d")
        last_quiz_date = profile.last_quiz_date
        new_streak = profile.current_streak or 0
        
        if last_quiz_date:
            last_date = datetime.strptime(last_quiz_date, "%Y-%m-%d")
            current_date = datetime.strptime(today, "%Y-%m-%d")
            days_diff = (current_date - last_date).days
            
            if days_diff == 1:
                new_streak += 1
            elif days_diff > 1:
                new_streak = 1
        else:
            new_streak = 1
        
        profile.xp = new_xp
        profile.level = new_level
        profile.current_streak = new_streak
        profile.last_quiz_date = today
        self.db.add(profile)
        
        # Calculate accuracy
        accuracy = (score / len(quiz.questions)) * 100 if quiz.questions else 0
        
        # Identify weak domains
        weak_domains = []
        for domain, perf in domain_performance.items():
            domain_accuracy = (perf["correct"] / perf["total"]) * 100
            if domain_accuracy < 60:
                weak_domains.append({
                    "name": domain,
                    "accuracy": int(domain_accuracy)
                })
        
        # Determine next difficulty
        next_difficulty = quiz.difficulty
        if accuracy >= 80:
            if quiz.difficulty == "easy":
                next_difficulty = "medium"
            elif quiz.difficulty == "medium":
                next_difficulty = "hard"
        elif accuracy < 50:
            if quiz.difficulty == "hard":
                next_difficulty = "medium"
            elif quiz.difficulty == "medium":
                next_difficulty = "easy"
        
        # Update or create user progress
        user_progress = self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.certification_id == quiz.certification_id
        ).first()
        
        if user_progress:
            new_total_quizzes = (user_progress.total_quizzes or 0) + 1
            new_total_questions = (user_progress.total_questions_answered or 0) + len(quiz.questions)
            new_correct_answers = (user_progress.correct_answers or 0) + score
            new_accuracy = (new_correct_answers / new_total_questions) * 100
            
            user_progress.total_xp = (user_progress.total_xp or 0) + total_xp
            user_progress.total_quizzes = new_total_quizzes
            user_progress.total_questions_answered = new_total_questions
            user_progress.correct_answers = new_correct_answers
            user_progress.accuracy = new_accuracy
            user_progress.current_difficulty = next_difficulty
            user_progress.weak_domains = weak_domains
        else:
            user_progress = UserProgress(
                user_id=user_id,
                certification_id=quiz.certification_id,
                total_xp=total_xp,
                total_quizzes=1,
                total_questions_answered=len(quiz.questions),
                correct_answers=score,
                accuracy=accuracy,
                current_difficulty=next_difficulty,
                weak_domains=weak_domains
            )
        
        self.db.add(user_progress)
        
        # Check for achievements
        achievements = []
        
        # 7-day streak
        if new_streak == 7:
            achievement = Achievement(
                user_id=user_id,
                achievement_type="streak",
                achievement_name="7-Day Streak",
                achievement_description="Completed quizzes for 7 consecutive days"
            )
            self.db.add(achievement)
            achievements.append("7-Day Streak")
        
        # 90%+ accuracy
        if accuracy >= 90:
            achievement = Achievement(
                user_id=user_id,
                achievement_type="accuracy",
                achievement_name="Perfect Score",
                achievement_description="Achieved 90% or higher accuracy on a quiz"
            )
            self.db.add(achievement)
            achievements.append("Perfect Score")
        
        # 100 questions milestone
        if user_progress.total_questions_answered >= 100:
            existing = self.db.query(Achievement).filter(
                Achievement.user_id == user_id,
                Achievement.achievement_name == "100 Questions"
            ).first()
            if not existing:
                achievement = Achievement(
                    user_id=user_id,
                    achievement_type="milestone",
                    achievement_name="100 Questions",
                    achievement_description="Answered 100 questions"
                )
                self.db.add(achievement)
                achievements.append("100 Questions")
        
        self.db.commit()
        
        logger.info(f"Quiz {quiz_id} evaluated: score={score}/{len(quiz.questions)}, xp={total_xp}, accuracy={accuracy:.1f}%")
        
        return {
            "success": True,
            "score": score,
            "total_questions": len(quiz.questions),
            "accuracy": accuracy,
            "xp_earned": total_xp,
            "new_level": new_level,
            "new_streak": new_streak,
            "achievements": achievements,
            "weak_domains": weak_domains,
            "next_difficulty": next_difficulty
        }
    
    def _check_answer(self, question: Question, user_answer: Any) -> bool:
        """Check if user answer is correct"""
        if not user_answer:
            return False
        
        if question.question_type == "multi_select":
            # For multi-select, order doesn't matter
            correct_answers = sorted(question.correct_answer) if isinstance(question.correct_answer, list) else []
            user_answers = sorted(user_answer) if isinstance(user_answer, list) else []
            return correct_answers == user_answers
        else:
            # For single choice and true/false
            return user_answer == question.correct_answer
