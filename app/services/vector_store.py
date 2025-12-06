"""Vector store manager using Qdrant"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from app.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manage vector embeddings in Qdrant"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.embedding_dimension = settings.EMBEDDING_DIMENSIONS
    
    def _get_collection_name(self, certification_id: UUID) -> str:
        """Generate collection name for a certification"""
        return f"cert_{str(certification_id).replace('-', '_')}"
    
    def create_collection(self, certification_id: UUID) -> None:
        """Create a new collection for a certification"""
        collection_name = self._get_collection_name(certification_id)
        
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection {collection_name} already exists")
                return
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {collection_name}")
        
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    def upsert_chunks(
        self,
        certification_id: UUID,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> None:
        """Insert or update chunk embeddings"""
        collection_name = self._get_collection_name(certification_id)
        
        # Ensure collection exists
        self.create_collection(certification_id)
        
        # Prepare points
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=idx,  # Use chunk index as ID (or generate UUID)
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "certification_id": str(certification_id),
                    "document_id": chunk["metadata"]["document_id"],
                    "page_number": chunk["metadata"]["page_number"],
                    "chunk_index": chunk["metadata"]["chunk_index"]
                }
            )
            points.append(point)
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch
            )
        
        logger.info(f"Upserted {len(points)} points to {collection_name}")
    
    def search(
        self,
        certification_id: UUID,
        query_embedding: List[float],
        top_k: int = 30,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        collection_name = self._get_collection_name(certification_id)
        
        # Build filter
        query_filter = None
        if document_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter
            )
            
            chunks = []
            for result in results:
                chunks.append({
                    "text": result.payload["text"],
                    "score": result.score,
                    "metadata": {
                        "document_id": result.payload["document_id"],
                        "page_number": result.payload["page_number"],
                        "chunk_index": result.payload["chunk_index"]
                    }
                })
            
            logger.info(f"Found {len(chunks)} similar chunks")
            return chunks
        
        except Exception as e:
            logger.error(f"Search failed in {collection_name}: {e}")
            raise
    
    def delete_collection(self, certification_id: UUID) -> None:
        """Delete a collection"""
        collection_name = self._get_collection_name(certification_id)
        
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")
    
    def collection_exists(self, certification_id: UUID) -> bool:
        """Check if collection exists"""
        collection_name = self._get_collection_name(certification_id)
        collections = self.client.get_collections().collections
        return any(c.name == collection_name for c in collections)


# Singleton instance
vector_store = VectorStore()
