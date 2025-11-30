"""Create initial admin user on startup if none exists"""

import logging
from uuid import uuid4
from sqlalchemy.orm import Session
from app.database.models import User
from app.utils.security import get_password_hash

logger = logging.getLogger(__name__)


def create_initial_admin(db: Session) -> None:
    """
    Create an initial admin user if no admin exists.
    
    This runs on application startup to ensure at least one admin exists
    for managing certifications and other admin tasks.
    """
    try:
        # Check if any admin user already exists
        admin_exists = db.query(User).filter(User.is_admin == True).first()
        
        if admin_exists:
            logger.info(f"Admin user already exists: {admin_exists.email}")
            return
        
        # Create initial admin
        admin = User(
            id=uuid4(),
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("AdminPass123!"),
            is_admin=True,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        logger.info(f"✅ Initial admin created: {admin.email} (username: {admin.username})")
        logger.info("⚠️  Change the default password immediately!")
        
    except Exception as e:
        logger.error(f"Failed to create initial admin: {e}")
        db.rollback()
