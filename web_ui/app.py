"""
Main FastAPI Application
Clean, focused entry point for the web UI
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-First Web Interface for Intelligent Crawling",
        debug=settings.debug
    )
    
    # Add middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # Import and include API routers
    try:
        from .api import chat, jobs, tools, streaming, system
        app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
        app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
        app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
        app.include_router(streaming.router, prefix="/api/streaming", tags=["Streaming"])
        app.include_router(system.router, prefix="/api/system", tags=["System"])
    except ImportError as e:
        logger.warning(f"Some API modules not available: {e}")
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="web_ui/static"), name="static")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {"message": f"Welcome to {settings.app_name} v{settings.app_version}"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    logger.info(f"✅ {settings.app_name} v{settings.app_version} created successfully")
    return app


# Create app instance
app = create_app()