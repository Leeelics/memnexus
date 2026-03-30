"""Configuration management for MemNexus."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings.
    
    Uses environment variables with MEMNEXUS_ prefix.
    """
    
    # App
    APP_NAME: str = "MemNexus"
    APP_VERSION: str = "0.3.0"
    DEBUG: bool = Field(default=False)
    ENV: str = Field(default="development")
    
    # Paths
    DATA_DIR: Path = Field(default=Path.home() / ".memnexus")
    
    @property
    def memory_dir(self) -> Path:
        """Directory for memory storage."""
        path = self.DATA_DIR / "memory"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def sessions_dir(self) -> Path:
        """Directory for session data."""
        path = self.DATA_DIR / "sessions"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def logs_dir(self) -> Path:
        """Directory for logs."""
        path = self.DATA_DIR / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    # Server
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8080)
    
    # LanceDB
    LANCEDB_URI: str = Field(default="~/.memnexus/memory.lance")
    
    # Security
    SECRET_KEY: str = Field(default="change-me-in-production")
    
    # Agent settings
    AGENT_TIMEOUT: int = Field(default=300)
    AGENT_MAX_RETRIES: int = Field(default=3)
    
    def __init__(self, **kwargs):
        # Load from environment variables with MEMNEXUS_ prefix
        env_prefix = "MEMNEXUS_"
        env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Remove prefix and convert to setting name
                setting_name = key[len(env_prefix):]
                # Convert to appropriate type
                if value.lower() in ("true", "false"):
                    env_vars[setting_name] = value.lower() == "true"
                elif value.isdigit():
                    env_vars[setting_name] = int(value)
                else:
                    env_vars[setting_name] = value
        
        # Override with kwargs
        env_vars.update(kwargs)
        
        super().__init__(**env_vars)
        
        # Ensure data directory exists
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
