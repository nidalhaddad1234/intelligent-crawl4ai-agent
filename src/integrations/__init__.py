"""
AI Core Integrations - Replacing hardcoded logic with AI planning
"""

from .web_ui_integration import (
    AIFirstScrapingAgent,
    create_ai_first_chat_handler,
    transform_existing_methods
)

__all__ = [
    'AIFirstScrapingAgent',
    'create_ai_first_chat_handler',
    'transform_existing_methods'
]
