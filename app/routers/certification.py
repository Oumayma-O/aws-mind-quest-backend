import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.certification import CertificationResponse
from app.schemas.user import UserResponse
from app.routers.auth import get_current_user_dep
from app.services.certification_service import CertificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/certifications", tags=["certifications"])


@router.get("", response_model=List[CertificationResponse])
async def list_certifications(db: Session = Depends(get_db)):
    """Get all available AWS certifications"""
    service = CertificationService(db)
    return service.list_all()


@router.get("/{certification_id}", response_model=CertificationResponse)
async def get_certification(
    certification_id: UUID,
    db: Session = Depends(get_db)
):
    """Get specific certification by ID"""
    service = CertificationService(db)
    certification = service.get_by_id(certification_id)
    
    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    return certification


@router.post("", response_model=CertificationResponse, status_code=201)
async def create_certification(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    description: str | None = Form(None),
    documents: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep),
):
    """Create a new certification (admin only)"""
    service = CertificationService(db)
    
    # Convert UploadFile to list if needed
    doc_list = documents if documents else None
    
    certification = service.create(
        name=name,
        description=description,
        user_id=current_user.id,
        documents=doc_list
    )
    
    # Queue background processing for uploaded documents
    if doc_list:
        for doc in service.get_documents(certification.id):
            if doc.processing_status == "pending":
                background_tasks.add_task(
                    service.process_document_sync,
                    str(doc.id),
                    str(certification.id)
                )
    
    return certification


@router.post("/{certification_id}/documents", status_code=201)
async def upload_certification_document(
    background_tasks: BackgroundTasks,
    certification_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep),
):
    """Upload a document for a certification (admin only)"""
    service = CertificationService(db)
    
    # Verify certification exists
    if not service.get_by_id(certification_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    # Upload document
    doc = service._upload_document(certification_id, file)
    db.commit()
    
    # Queue background processing
    background_tasks.add_task(
        service.process_document_sync,
        str(doc.id),
        str(certification_id)
    )
    
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "uri": doc.uri,
        "processing_status": "queued"
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Delete a certification document (admin only)"""
    service = CertificationService(db)
    service.delete_document(document_id, current_user.id)
    return {"detail": "Document deleted"}


@router.get("/{certification_id}/documents")
async def get_certification_documents(
    certification_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all documents for a certification"""
    service = CertificationService(db)
    documents = service.get_documents(certification_id)
    
    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "processing_status": doc.processing_status,
            "processed_at": doc.processed_at,
            "created_at": doc.created_at
        }
        for doc in documents
    ]