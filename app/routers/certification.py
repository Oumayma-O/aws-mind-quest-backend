"""Certification routes"""

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import Certification, User
from app.schemas.certification import CertificationResponse, CertificationCreate
from app.routers.auth import get_current_user_dep
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/certifications", tags=["certifications"])


@router.get("", response_model=List[CertificationResponse])
async def list_certifications(db: Session = Depends(get_db)):
    """
    Get all available AWS certifications
    """
    certifications = db.query(Certification).all()
    return certifications


@router.get("/{certification_id}", response_model=CertificationResponse)
async def get_certification(
    certification_id: UUID,
    db: Session = Depends(get_db)
):
    """Get specific certification by ID"""
    certification = db.query(Certification).filter(
        Certification.id == certification_id
    ).first()
    
    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    return certification


@router.post("", response_model=CertificationResponse, status_code=201)
async def create_certification(
    cert_data: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """
    Create a new certification (admin only)
    
    Note: In production, add role-based access control
    """
    
    # Check if certification already exists
    existing = db.query(Certification).filter(
        Certification.name == cert_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Certification already exists"
        )
    
    certification = Certification(
        name=cert_data.name,
        description=cert_data.description
    )
    
    try:
        db.add(certification)
        db.commit()
        db.refresh(certification)
        logger.info(f"Created certification: {certification.name}")
        return certification
    except Exception as e:
        logger.error(f"Error creating certification: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create certification"
        )
