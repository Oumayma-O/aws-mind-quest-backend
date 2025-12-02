"""Embedding service: Generate vector embeddings using OpenAI"""

import logging
from typing import List
from openai import OpenAI
from app.config import settings
import time

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using OpenAI API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batched)"""
        if not texts:
            return []
        
        # OpenAI allows up to 2048 texts per request, but we'll be conservative
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self._embed_batch_with_retry(batch)
            all_embeddings.extend(embeddings)
        
        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def _embed_batch_with_retry(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                
                embeddings = [item.embedding for item in response.data]
                return embeddings
            
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Failed to generate embeddings after {self.max_retries} attempts")
                    raise


# Singleton instance
embedding_service = EmbeddingService()
