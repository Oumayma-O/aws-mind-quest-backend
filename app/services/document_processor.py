"""Document processing: PDF extraction and text chunking"""

import logging
from typing import List, Dict, Any
from io import BytesIO
import requests
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None


class DocumentChunk:
    """Represents a chunk of text from a document"""
    def __init__(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_index: int
    ):
        self.text = text
        self.metadata = metadata
        self.chunk_index = chunk_index


class DocumentProcessor:
    """Process PDF documents: download, extract text, and chunk"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def download_file(self, url: str) -> BytesIO:
        """Download file from URL (S3 or local path)"""
        try:
            # Check if it's an S3 URL (both s3:// and https://bucket.s3.amazonaws.com)
            if url and (url.startswith("s3://") or "s3.amazonaws.com" in url or f"{settings.AWS_S3_BUCKET}/" in url):
                logger.info(f"Detected S3 URL, using authenticated download: {url}")
                return self._download_from_s3(url)
            elif url.startswith("http"):
                logger.warning(f"Using public HTTP download (not S3): {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return BytesIO(response.content)
            else:
                # Local file path
                with open(url, 'rb') as f:
                    return BytesIO(f.read())
        except Exception as e:
            logger.error(f"Failed to download file from {url}: {e}")
            raise
    
    def _download_from_s3(self, url: str) -> BytesIO:
        """Download file from S3 using AWS credentials"""
        if not boto3:
            raise ImportError("boto3 is required to download from S3")
        
        # Extract key (file path) from S3 URL
        # s3://bucket/certifications/file.pdf -> certifications/file.pdf
        # https://bucket.s3.region.amazonaws.com/certifications/file.pdf -> certifications/file.pdf
        key = url.split(f"{settings.AWS_S3_BUCKET}/", 1)[-1]
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Download file into BytesIO object
        try:
            logger.info(f"Downloading from S3: s3://{settings.AWS_S3_BUCKET}/{key}")
            file_obj = BytesIO()
            s3_client.download_fileobj(settings.AWS_S3_BUCKET, key, file_obj)
            file_obj.seek(0)  # Reset to beginning
            return file_obj
        except ClientError as e:
            logger.error(f"S3 download failed for s3://{settings.AWS_S3_BUCKET}/{key}: {e}")
            raise
    
    def extract_text_from_pdf(self, file_obj: BytesIO) -> List[Dict[str, Any]]:
        """Extract text from PDF with pdfplumber, preserving page numbers and layout."""
        try:
            pages: List[Dict[str, Any]] = []
            with pdfplumber.open(file_obj) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text(layout=True) or ""
                    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
                    if cleaned:
                        pages.append({
                            "page_number": page_num,
                            "text": cleaned
                        })
            logger.info(f"Extracted {len(pages)} pages from PDF")
            return pages
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise
    
    def chunk_document(
        self,
        pages: List[Dict[str, Any]],
        certification_id: str,
        document_id: str
    ) -> List[DocumentChunk]:
        """Chunk document text with metadata"""
        chunks = []
        chunk_index = 0
        
        for page_data in pages:
            page_number = page_data["page_number"]
            text = page_data["text"]
            
            # Split text into chunks
            text_chunks = self.text_splitter.split_text(text)
            
            for text_chunk in text_chunks:
                metadata = {
                    "certification_id": str(certification_id),
                    "document_id": str(document_id),
                    "page_number": page_number,
                    "chunk_index": chunk_index
                }
                
                chunks.append(DocumentChunk(
                    text=text_chunk,
                    metadata=metadata,
                    chunk_index=chunk_index
                ))
                chunk_index += 1
        
        logger.info(f"Created {len(chunks)} chunks from document {document_id}")
        return chunks
    
    def process_document(
        self,
        url: str,
        certification_id: str,
        document_id: str
    ) -> List[DocumentChunk]:
        """Full pipeline: download → extract → chunk"""
        try:
            logger.info(f"Processing document {document_id} from {url}")
            
            # Download
            file_obj = self.download_file(url)
            
            # Extract text
            pages = self.extract_text_from_pdf(file_obj)
            
            # Chunk
            chunks = self.chunk_document(pages, certification_id, document_id)
            
            return chunks
        except Exception as e:
            logger.error(f"Document processing failed for {document_id}: {e}")
            raise


# Singleton instance
document_processor = DocumentProcessor()
