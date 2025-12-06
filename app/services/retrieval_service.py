"""Enhanced retrieval service with compression and filtering"""

import logging
from typing import List, Dict, Any
from uuid import UUID
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.config import settings

logger = logging.getLogger(__name__)


class EnhancedRetrievalService:
    """Retrieval service with contextual compression for better relevance"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
    
    def retrieve_with_compression(
        self,
        certification_id: UUID,
        query: str,
        top_k: int = 20,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve and compress documents using embeddings-based filtering
        
        Args:
            certification_id: Certification to search in
            query: Search query
            top_k: Number of initial chunks to retrieve (will be filtered)
            similarity_threshold: Keep chunks with similarity >= this threshold (0.0-1.0)
            
        Returns:
            List of compressed, relevant chunks with metadata
        """
        try:
            # Step 1: Get query embedding
            query_embedding = embedding_service.embed_text(query)
            
            # Step 2: Retrieve initial candidates (more than final top_k)
            initial_top_k = top_k * 2  # Retrieve 20, compress to 10
            chunks = vector_store.search(
                certification_id=certification_id,
                query_embedding=query_embedding,
                top_k=initial_top_k
            )
            
            if not chunks:
                logger.warning(f"No chunks found for query: {query}")
                return []
            
            # Step 3: Convert to LangChain Documents
            documents = [
                Document(
                    page_content=chunk['text'],
                    metadata=chunk['metadata']
                )
                for chunk in chunks
            ]
            
            # Step 4: Apply embeddings-based compression/filtering
            embeddings_filter = EmbeddingsFilter(
                embeddings=self.embeddings,
                similarity_threshold=similarity_threshold
            )
            
            compressed_docs = embeddings_filter.compress_documents(
                documents=documents,
                query=query
            )
            
            # Step 5: Convert back to dict format
            compressed_chunks = [
                {
                    'text': doc.page_content,
                    'metadata': doc.metadata,
                    'score': getattr(doc, 'score', None)
                }
                for doc in compressed_docs[:top_k]  # Limit to final top_k
            ]
            
            logger.info(
                f"Compressed retrieval: {len(chunks)} initial → "
                f"{len(compressed_docs)} filtered → {len(compressed_chunks)} final"
            )
            
            return compressed_chunks
            
        except Exception as e:
            logger.error(f"Error in compressed retrieval: {e}")
            # Fallback to regular retrieval
            query_embedding = embedding_service.embed_text(query)
            return vector_store.search(
                certification_id=certification_id,
                query_embedding=query_embedding,
                top_k=top_k
            )


# Singleton instance
retrieval_service = EnhancedRetrievalService()
