"""Configuration management for MemNexus."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # App
    APP_NAME: str = "MemNexus"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, validation_alias="MEMNEXUS_DEBUG")
    ENV: str = Field(default="development", validation_alias="MEMNEXUS_ENV")
    
    # Paths
    DATA_DIR: Path = Field(
        default=Path.home() / ".memnexus",
        validation_alias="MEMNEXUS_DATA_DIR",
    )
    
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
    HOST: str = Field(default="127.0.0.1", validation_alias="MEMNEXUS_HOST")
    PORT: int = Field(default=8080, validation_alias="MEMNEXUS_PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/memnexus",
        validation_alias="MEMNEXUS_DATABASE_URL",
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="MEMNEXUS_REDIS_URL",
    )
    
    # LanceDB
    LANCEDB_URI: str = Field(
        default="~/.memnexus/memory.lance",
        validation_alias="MEMNEXUS_LANCEDB_URI",
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        validation_alias="MEMNEXUS_SECRET_KEY",
    )
    
    # Agent settings
    AGENT_TIMEOUT: int = Field(
        default=300,
        validation_alias="MEMNEXUS_AGENT_TIMEOUT",
    )
    AGENT_MAX_RETRIES: int = Field(
        default=3,
        validation_alias="MEMNEXUS_AGENT_MAX_RETRIES",
    )
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
