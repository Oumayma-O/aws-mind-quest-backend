"""Business logic for certification management"""

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from datetime import datetime

from app.database.models import Certification, CertificationDocument, User
from app.schemas.certification import CertificationCreate
from app.utils.s3 import upload_file
from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class CertificationService:
    """Service for managing certifications and their documents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_all(self) -> List[Certification]:
        """Get all certifications"""
        return self.db.query(Certification).all()
    
    def get_by_id(self, certification_id: UUID) -> Optional[Certification]:
        """Get certification by ID"""
        return self.db.query(Certification).filter(
            Certification.id == certification_id
        ).first()
    
    def create(
        self,
        name: str,
        description: Optional[str],
        user_id: UUID,
        documents: Optional[List[UploadFile]] = None
    ) -> Certification:
        """
        Create a new certification (admin only)
        
        Args:
            name: Certification name
            description: Optional description
            user_id: User creating the certification (must be admin)
            documents: Optional list of PDF documents to upload
            
        Returns:
            Created certification
            
        Raises:
            HTTPException: If user is not admin or certification exists
        """
        # Check admin status
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create certifications"
            )
        
        # Check for duplicates
        existing = self.db.query(Certification).filter(
            Certification.name == name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Certification already exists"
            )
        
        # Create certification
        certification = Certification(name=name, description=description)
        self.db.add(certification)
        self.db.flush()
        
        # Handle document uploads
        if documents:
            for file in documents:
                # Persist each document immediately so background tasks can find it
                self.add_document(certification.id, file)
        
        self.db.commit()
        self.db.refresh(certification)
        
        logger.info(f"Created certification: {certification.name} (ID: {certification.id})")
        return certification
    
    def add_document(self, certification_id: UUID, file: UploadFile) -> CertificationDocument:
        """Upload and register a document for a certification. Commits the record."""
        if not file.filename or not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Upload to S3
        s3_key = f"certifications/{certification_id}/{file.filename}"
        uri = upload_file(file.file, s3_key)
        
        # Create document record
        doc = CertificationDocument(
            certification_id=certification_id,
            filename=file.filename,
            s3_key=s3_key,
            uri=uri,
            processing_status="pending"
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        logger.info(f"Uploaded document: {file.filename} for certification {certification_id}")
        return doc
    
    def process_document_sync(self, document_id: str, certification_id: str):
        """
        Synchronously process a document (extract, chunk, embed, store)
        
        Args:
            document_id: Document ID to process
            certification_id: Parent certification ID
        """
        doc = self.db.query(CertificationDocument).filter(
            CertificationDocument.id == document_id
        ).first()
        
        if not doc:
            logger.error(f"Document {document_id} not found")
            return
        
        try:
            # Update status
            doc.processing_status = "processing"
            self.db.commit()
            
            logger.info(f"Processing document {doc.filename} (ID: {doc.id})")
            
            # Step 1: Extract and chunk
            chunks = document_processor.process_document(
                url=doc.uri,
                certification_id=certification_id,
                document_id=document_id
            )
            
            # Step 2: Generate embeddings
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = embedding_service.embed_texts(chunk_texts)
            
            # Step 3: Store in vector DB
            chunk_data = [
                {"text": chunk.text, "metadata": chunk.metadata}
                for chunk in chunks
            ]
            vector_store.upsert_chunks(certification_id, chunk_data, embeddings)
            
            # Mark as completed
            doc.processing_status = "completed"
            doc.processed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Successfully processed {doc.filename}")
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            doc.processing_status = "failed"
            self.db.commit()
    
    def get_documents(self, certification_id: UUID) -> List[CertificationDocument]:
        """Get all documents for a certification"""
        return self.db.query(CertificationDocument).filter(
            CertificationDocument.certification_id == certification_id
        ).all()
    
    def delete_document(self, document_id: UUID, user_id: UUID):
        """Delete a document (admin only)"""
        # Check admin
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete documents"
            )
        
        doc = self.db.query(CertificationDocument).filter(
            CertificationDocument.id == document_id
        ).first()
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete from vector store if processed
        if doc.processing_status == "completed":
            try:
                vector_store.delete_document(str(doc.certification_id), str(document_id))
            except Exception as e:
                logger.warning(f"Failed to delete from vector store: {e}")
        
        # Delete from DB
        self.db.delete(doc)
        self.db.commit()
        
        logger.info(f"Deleted document {doc.filename}")
