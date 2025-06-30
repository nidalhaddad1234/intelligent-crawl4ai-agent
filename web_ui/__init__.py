"""
Web UI - Clean and organized FastAPI application

Modular web interface for the AI-first intelligent crawling system
"""

from .app import create_app

__version__ = "2.0.0"
__all__ = ['create_app']