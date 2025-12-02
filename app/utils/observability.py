"""
Observability utilities for tracing LLM calls with Langfuse.
"""
from typing import Optional
from langfuse.callback import CallbackHandler
from app.config import settings


def get_langfuse_handler() -> Optional[CallbackHandler]:
    """
    Returns a Langfuse callback handler if settings are configured.
    
    Required settings:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_HOST (defaults to https://cloud.langfuse.com)
    
    Returns:
        CallbackHandler if configured, None otherwise
    """
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        return None
    
    return CallbackHandler(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST or "https://cloud.langfuse.com",
    )


# Global handler instance (lazy-initialized)
langfuse_handler = get_langfuse_handler()
