"""Application configuration using pydantic-settings."""

import os
from pathlib import Path
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GEMINI_API_KEY: str = ""

    ENCRYPTION_KEY: str = "auto_generated_on_first_run"

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = ""
    PAGES_DIR: str = ""
    CHROMA_DIR: str = ""
    DATABASE_URL: str = ""

    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/tiff",
        "text/plain",
    ]

    CORS_ORIGINS: str = "http://localhost:3000"

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    GEMINI_MODEL: str = "gemini-2.0-flash"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.UPLOAD_DIR:
            self.UPLOAD_DIR = os.path.join(self.BASE_DIR, "storage", "uploads")
        if not self.PAGES_DIR:
            self.PAGES_DIR = os.path.join(self.BASE_DIR, "storage", "pages")
        if not self.CHROMA_DIR:
            self.CHROMA_DIR = os.path.join(self.BASE_DIR, "storage", "chroma")
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"sqlite:///{os.path.join(self.BASE_DIR, 'storage', 'app.db')}"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS as a comma-separated list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create all required storage directories if they don't exist."""
        for dir_path in [self.UPLOAD_DIR, self.PAGES_DIR, self.CHROMA_DIR]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
