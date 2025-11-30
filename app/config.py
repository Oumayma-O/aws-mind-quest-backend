"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://admin:password@localhost:5432/aws_mind_quest"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:4200"]
    
    # Application
    APP_TITLE: str = "AWS Mind Quest API"
    APP_DESCRIPTION: str = "FastAPI backend for AWS certification quiz platform"
    APP_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
