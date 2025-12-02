import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import Certification, User
from app.schemas.certification import CertificationResponse, CertificationCreate
from app.schemas.user import UserResponse
from app.routers.auth import get_current_user_dep
from app.database.models import CertificationDocument
from app.utils.s3 import upload_file
from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from datetime import datetime
import os
import time
from io import BytesIO # Moved to top for consistency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/certifications", tags=["certifications"])


def process_document_background(document_id: str, certification_id: str, db: Session):
    """Background task to process a single document"""
    try:
        # NOTE: Be careful with DB session handling in background tasks. 
        # A new session is often required if the original session closes before the task runs.
        # For simplicity, keeping original logic, but be aware of potential issues if the 
        # parent request's session closes too quickly.
        doc = db.query(CertificationDocument).filter(
            CertificationDocument.id == document_id
        ).first()
        
        if not doc:
            logger.error(f"Document {document_id} not found for background processing")
            return
        
        # Update status to processing
        doc.processing_status = "processing"
        db.commit()
        
        logger.info(f"Background processing document {doc.filename} (ID: {doc.id})")
        
        # Step 1: Process document (download, extract, chunk)
        chunks = document_processor.process_document(
            url=doc.uri,
            certification_id=certification_id,
            document_id=document_id
        )
        
        # Step 2: Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)
        
        # Step 3: Store in vector database
        chunk_data = [
            {
                "text": chunk.text,
                "metadata": chunk.metadata
            }
            for chunk in chunks
        ]
        vector_store.upsert_chunks(certification_id, chunk_data, embeddings)
        
        # Update status to completed
        doc.processing_status = "completed"
        doc.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully processed document {doc.filename} in background")
        
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")
        doc = db.query(CertificationDocument).filter( # Re-fetch/check if doc exists
             CertificationDocument.id == document_id
        ).first()
        if doc:
            doc.processing_status = "failed"
            db.commit()


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
    # NON-DEFAULT ARGUMENTS FIRST
    
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    # DEFAULT ARGUMENTS NEXT
    description: str | None = Form(None),
    documents: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep),
):
    """
    Create a new certification (admin only)
    """
    # Check if user is admin
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create certifications"
        )
    
    # Check if certification already exists
    existing = db.query(Certification).filter(
        Certification.name == name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Certification already exists"
        )
    
    certification = Certification(
        name=name,
        description=description
    )

    try:
        db.add(certification)
        db.commit()
        db.refresh(certification)

        # If documents provided at creation, upload and save them
        if documents:
            # from io import BytesIO # Already moved to top

            for file in documents:
                contents = await file.read()
                bio = BytesIO(contents)
                key, url = upload_file(bio, file.filename)
                doc = CertificationDocument(
                    certification_id=certification.id,
                    filename=file.filename,
                    s3_key=key,
                    uri=url
                )
                db.add(doc)
                db.flush()  # Get doc.id before background task
                
                # Queue background processing
                # NOTE: For background task DB usage, passing a DB session 
                # (which is scoped to the request) is risky. A better pattern 
                # is to initialize a new session inside the background task 
                # using a session maker/factory. I am leaving the original 
                # implementation for minimal changes, but be aware of this.
                background_tasks.add_task(
                    process_document_background,
                    str(doc.id),
                    str(certification.id),
                    db
                )

            # commit document records
            try:
                db.commit()
            except Exception:
                db.rollback()

        logger.info(f"Created certification: {certification.name}")
        return certification
    except Exception as e:
        logger.error(f"Error creating certification: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create certification"
        )


@router.post("/{certification_id}/documents", status_code=201)
async def upload_certification_document(
    # NON-DEFAULT ARGUMENTS FIRST
    background_tasks: BackgroundTasks,
    certification_id: UUID,
    # DEFAULT ARGUMENTS NEXT
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep),  
):
    """Upload a document (PDF/training guide) for a certification (admin only)."""
    # Admin check
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can upload documents")

    cert = db.query(Certification).filter(Certification.id == certification_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")

    # Save to S3 or local
    contents = await file.read()
    # from io import BytesIO # Already moved to top
    bio = BytesIO(contents)
    key, url = upload_file(bio, file.filename)

    doc = CertificationDocument(
        certification_id=certification_id,
        filename=file.filename,
        s3_key=key,
        uri=url
    )
    try:
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"Uploaded document {file.filename} for cert {cert.name}")
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            str(doc.id),
            str(certification_id),
            db
        )
        
        return {
            "id": str(doc.id),
            "filename": doc.filename,
            "uri": doc.uri,
            "processing_status": "queued"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save document record: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save document")


@router.delete("/{certification_id}")
async def delete_certification(
    certification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Delete a certification and its documents (admin only)."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can delete certifications")

    cert = db.query(Certification).filter(Certification.id == certification_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")

    try:
        # Delete vector collection first
        vector_store.delete_collection(certification_id)
        
        # Documents will be cascade-deleted if configured in SQLAlchemy/DB.
        # If not, you might need to manually delete documents first.
        db.delete(cert)
        db.commit()
        logger.info(f"Deleted certification {cert.name} and related documents")
        return {"detail": "Certification deleted"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete certification: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete certification")


@router.post("/{certification_id}/process-documents")
async def process_certification_documents(
    certification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Process all documents for a certification: extract, chunk, embed, and index (admin only)."""
    # Admin check
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can process documents")

    cert = db.query(Certification).filter(Certification.id == certification_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")

    # Get all documents for this certification
    documents = db.query(CertificationDocument).filter(
        CertificationDocument.certification_id == certification_id
    ).all()

    if not documents:
        # Changed 404 to 200/409 since the certification exists, but has no documents
        return {
             "certification_id": str(certification_id),
             "total_documents": 0,
             "processed": 0,
             "failed": 0,
             "status": "skipped",
             "detail": "No documents found for this certification to process"
        }

    start_time = time.time()
    
    try:
        processed_count = 0
        failed_count = 0

        # Note: This is synchronous processing inside an async route. 
        # For a large number of documents, this will block the event loop.
        # Consider using BackgroundTasks or a dedicated process pool (e.g., in `document_processor`)
        # for true background or non-blocking execution.
        for doc in documents:
            try:
                # Update status to processing
                doc.processing_status = "processing"
                db.commit()

                logger.info(f"Processing document {doc.filename} (ID: {doc.id})")

                # Step 1: Process document (download, extract, chunk)
                chunks = document_processor.process_document(
                    url=doc.uri,
                    certification_id=str(certification_id),
                    document_id=str(doc.id)
                )
                
                # Step 2: Generate embeddings
                chunk_texts = [chunk.text for chunk in chunks]
                embeddings = embedding_service.embed_texts(chunk_texts)

                # Step 3: Store in vector database
                chunk_data = [
                    {
                        "text": chunk.text,
                        "metadata": chunk.metadata
                    }
                    for chunk in chunks
                ]
                # It's better to ensure certification_id is a string here if vector_store expects it
                vector_store.upsert_chunks(str(certification_id), chunk_data, embeddings)

                # Update status to completed
                doc.processing_status = "completed"
                doc.processed_at = datetime.utcnow()
                db.commit()

                processed_count += 1
                logger.info(f"Successfully processed document {doc.filename}")

            except Exception as e:
                logger.error(f"Failed to process document {doc.filename}: {e}")
                doc.processing_status = "failed"
                db.commit()
                failed_count += 1

        elapsed_time = time.time() - start_time
        
        return {
            "certification_id": str(certification_id),
            "total_documents": len(documents),
            "processed": processed_count,
            "failed": failed_count,
            "status": "completed" if failed_count == 0 else "partial",
            "processing_time_seconds": round(elapsed_time, 2)
        }

    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        # Note: If an error happens before the loop, all documents might still be stuck in 'processing'
        # The failed documents in the loop are already marked as 'failed'
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process documents: {str(e)}"
        )