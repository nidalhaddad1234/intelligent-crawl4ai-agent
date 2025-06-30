"""
Web UI Configuration
Centralized configuration management
"""

import os
import json
from typing import Optional, List, Union
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    app_name: str = "AI-First Web UI"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 1
    
    # AI settings
    ai_core_enabled: bool = True
    default_ai_model: str = "deepseek-coder:1.3b"
    ai_timeout: int = 30
    
    # WebSocket settings
    websocket_timeout: int = 300
    max_connections: int = 100
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [".txt", ".csv", ".json", ".xlsx"]
    
    # Background job settings
    max_concurrent_jobs: int = 5
    job_timeout: int = 300
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    @field_validator('cors_origins', 'cors_methods', 'cors_headers', mode='before')
    @classmethod
    def parse_list_from_string(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v.split(',')
        return v
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "WEB_UI_",
        "extra": "allow"  # Allow extra fields from .env file
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings