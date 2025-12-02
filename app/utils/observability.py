"""
Observability utilities for tracing LLM calls with Langfuse.
"""
import os
from typing import Optional
from langfuse.callback import CallbackHandler


def get_langfuse_handler() -> Optional[CallbackHandler]:
    """
    Returns a Langfuse callback handler if env vars are configured.
    
    Required env vars:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_HOST (defaults to https://cloud.langfuse.com)
    
    Returns:
        CallbackHandler if configured, None otherwise
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if not public_key or not secret_key:
        return None
    
    return CallbackHandler(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )


# Global handler instance (lazy-initialized)
langfuse_handler = get_langfuse_handler()
