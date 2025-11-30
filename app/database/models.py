"""SQLAlchemy database models"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, JSON, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()


class Certification(Base):
    """AWS Certification model"""
    __tablename__ = "certifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profiles = relationship("Profile", back_populates="selected_certification")
    quizzes = relationship("Quiz", back_populates="certification")
    user_progresses = relationship("UserProgress", back_populates="certification")
    
    def __repr__(self):
        return f"<Certification {self.name}>"


class User(Base):
    """User model (extends auth table)"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    quizzes = relationship("Quiz", back_populates="user")
    user_progresses = relationship("UserProgress", back_populates="user")
    achievements = relationship("Achievement", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"


class Profile(Base):
    """User profile model"""
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    selected_certification_id = Column(UUID(as_uuid=True), ForeignKey("certifications.id"), nullable=True)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    current_streak = Column(Integer, default=0)
    last_quiz_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    selected_certification = relationship("Certification", back_populates="profiles")
    
    def __repr__(self):
        return f"<Profile {self.user_id}>"


class Quiz(Base):
    """Quiz model"""
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    certification_id = Column(UUID(as_uuid=True), ForeignKey("certifications.id"), nullable=False)
    difficulty = Column(String(20), nullable=False, default="easy")
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="ck_difficulty"),
    )
    
    # Relationships
    user = relationship("User", back_populates="quizzes")
    certification = relationship("Certification", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quiz {self.id}>"


class Question(Base):
    """Question model"""
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # multiple_choice, multi_select, true_false
    options = Column(JSON, nullable=False)  # List of options
    correct_answer = Column(JSON, nullable=False)  # String or List
    user_answer = Column(JSON, nullable=True)  # User's response
    explanation = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    difficulty = Column(String(20), nullable=False)
    domain = Column(String(100), nullable=False)
    xp_earned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("question_type IN ('multiple_choice', 'multi_select', 'true_false')", name="ck_question_type"),
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="ck_question_difficulty"),
    )
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    
    def __repr__(self):
        return f"<Question {self.id}>"


class UserProgress(Base):
    """User progress per certification"""
    __tablename__ = "user_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    certification_id = Column(UUID(as_uuid=True), ForeignKey("certifications.id"), nullable=False)
    total_xp = Column(Integer, default=0)
    total_quizzes = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy = Column(Numeric(5, 2), default=0)
    current_difficulty = Column(String(20), default="easy")
    domain_difficulties = Column(JSON, default={})  # Per-domain difficulty levels
    weak_domains = Column(JSON, default=[])  # List of weak domains
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("user_id", "certification_id", name="uq_user_certification"),
        CheckConstraint("current_difficulty IN ('easy', 'medium', 'hard')", name="ck_progress_difficulty"),
    )
    
    # Relationships
    user = relationship("User", back_populates="user_progresses")
    certification = relationship("Certification", back_populates="user_progresses")
    
    def __repr__(self):
        return f"<UserProgress {self.user_id} - {self.certification_id}>"


class Achievement(Base):
    """Achievement/Badge model"""
    __tablename__ = "achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_type = Column(String(50), nullable=False)  # streak, accuracy, milestone
    achievement_name = Column(String(255), nullable=False)
    achievement_description = Column(Text, nullable=True)
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    
    def __repr__(self):
        return f"<Achievement {self.achievement_name}>"
