"""Enhanced retrieval service with randomization for diversity"""

import logging
import random
from typing import List, Dict, Any
from uuid import UUID
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class EnhancedRetrievalService:
    """Retrieval service with randomization to ensure content diversity across quizzes"""
    
    def retrieve_with_randomization(
        self,
        certification_id: UUID,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks and randomize selection for diversity
        
        Prevents repeated questions on consecutive quizzes by randomly selecting
        from a larger pool of relevant chunks instead of always using the top-k.
        
        Args:
            certification_id: Certification to search in
            query: Search query
            top_k: Number of chunks to return (randomly selected)
            
        Returns:
            List of randomly selected relevant chunks with metadata
        """
        try:
            # Step 1: Get query embedding
            query_embedding = embedding_service.embed_text(query)
            
            # Step 2: Retrieve larger pool (retrieve 2x to randomize from)
            pool_size = top_k * 3  # Retrieve 30 to select 10 from
            chunks = vector_store.search(
                certification_id=certification_id,
                query_embedding=query_embedding,
                top_k=pool_size
            )
            
            if not chunks:
                logger.warning(f"No chunks found for query: {query}")
                return []
            
            # Step 3: Randomly select from pool for diversity
            if len(chunks) > top_k:
                selected_chunks = random.sample(chunks, top_k)
            else:
                selected_chunks = chunks
            
            logger.info(
                f"Randomized retrieval: {len(chunks)} retrieved → {len(selected_chunks)} randomly selected"
            )
            
            return selected_chunks
            
        except Exception as e:
            logger.error(f"Error in randomized retrieval: {e}")
            # Fallback to regular retrieval
            query_embedding = embedding_service.embed_text(query)
            return vector_store.search(
                certification_id=certification_id,
                query_embedding=query_embedding,
                top_k=top_k
            )


# Singleton instance
retrieval_service = EnhancedRetrievalService()
