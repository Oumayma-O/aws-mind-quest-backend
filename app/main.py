"""Main FastAPI application"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.db import engine, get_db
from app.database.models import Base
from app.routers import auth, certification, quiz, progress, profile
from app.utils.create_initial_admin import create_initial_admin
from app.utils.seed_certifications import seed_certifications
from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.database.models import CertificationDocument
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_seed_documents_background(documents_to_process):
    """Process seed documents in background thread"""
    logger.info(f"Starting background processing of {len(documents_to_process)} seed documents")
    
    db = next(get_db())
    try:
        for doc_id, cert_id in documents_to_process:
            try:
                doc = db.query(CertificationDocument).filter(
                    CertificationDocument.id == doc_id
                ).first()
                
                if not doc or doc.processing_status == "completed":
                    continue
                
                # Update status
                doc.processing_status = "processing"
                db.commit()
                
                logger.info(f"Processing seed document {doc.filename}")
                
                # Process document
                chunks = document_processor.process_document(
                    url=doc.uri,
                    certification_id=cert_id,
                    document_id=doc_id
                )
                
                # Generate embeddings
                chunk_texts = [chunk.text for chunk in chunks]
                embeddings = embedding_service.embed_texts(chunk_texts)
                
                # Store in vector database
                chunk_data = [
                    {"text": chunk.text, "metadata": chunk.metadata}
                    for chunk in chunks
                ]
                vector_store.upsert_chunks(cert_id, chunk_data, embeddings)
                
                # Update status
                doc.processing_status = "completed"
                doc.processed_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Successfully processed seed document {doc.filename}")
                
            except Exception as e:
                logger.error(f"Failed to process seed document {doc_id}: {e}")
                if doc:
                    doc.processing_status = "failed"
                    db.commit()
    finally:
        db.close()


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    logger.info("Starting AWS Mind Quest API...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Create initial admin user if none exists
    try:
        db = next(get_db())
        create_initial_admin(db)
        # Seed predefined certifications and get documents to process
        try:
            documents_to_process = seed_certifications(db)
            
            # Process seed documents in background thread
            if documents_to_process:
                thread = threading.Thread(
                    target=process_seed_documents_background,
                    args=(documents_to_process,),
                    daemon=True
                )
                thread.start()
                logger.info(f"Started background thread to process {len(documents_to_process)} seed documents")
        except Exception as e:
            logger.error(f"Error seeding certifications: {e}")
    except Exception as e:
        logger.error(f"Error creating initial admin: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AWS Mind Quest API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "version": settings.APP_VERSION
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AWS Mind Quest API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


# Include routers
app.include_router(auth.router)
app.include_router(certification.router)
app.include_router(quiz.router)
app.include_router(progress.router)
app.include_router(profile.router)


# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
