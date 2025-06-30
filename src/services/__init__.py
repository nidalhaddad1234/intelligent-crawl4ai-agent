"""
Services Layer - Intelligent Crawl4AI Agent

This module provides clean service abstractions for:
- LLM operations (Ollama integration)
- Vector storage (ChromaDB management)
- URL processing and validation
- External API integrations

Each service is designed to be:
- Self-contained and focused
- Easily testable and mockable
- Configuration-driven
- Production-ready with proper error handling
"""

from .llm_service import LLMService
from .vector_service import VectorService
from .url_service import URLService
from .external_apis import ExternalAPIService

__all__ = [
    'LLMService',
    'VectorService', 
    'URLService',
    'ExternalAPIService'
]

# Service version for compatibility tracking
__version__ = "1.0.0"
