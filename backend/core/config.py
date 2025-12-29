"""
Digital Denis — Core Configuration
═══════════════════════════════════════════════════════════════════════════

Конфигурация из переменных окружения.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # ─────────────────────────────────────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────────────────────────────────────
    database_url: str = "postgresql://denis:denis_dev_2024@localhost:5432/digital_denis"
    redis_url: str = "redis://localhost:6379/0"
    
    # ─────────────────────────────────────────────────────────────────────────
    # LLM Providers
    # ─────────────────────────────────────────────────────────────────────────
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Default model for main tasks
    default_model: str = "anthropic/claude-3.5-sonnet"
    
    # Cheap model for classification, topic extraction
    cheap_model: str = "meta-llama/llama-3.1-70b-instruct"
    
    # Groq for cheap tasks and voice
    groq_api_key: Optional[str] = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.1-70b-versatile"
    groq_whisper_model: str = "whisper-large-v3"
    
    # Fallback providers (optional)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Telegram
    # ─────────────────────────────────────────────────────────────────────────
    telegram_bot_token: Optional[str] = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Security
    # ─────────────────────────────────────────────────────────────────────────
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    
    # ─────────────────────────────────────────────────────────────────────────
    # System
    # ─────────────────────────────────────────────────────────────────────────
    system_language: str = "ru"
    debug: bool = True
    
    # Profile path (relative to project root)
    profile_path: str = "../ai/profiles/denis.yaml"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
