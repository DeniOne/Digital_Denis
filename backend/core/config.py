"""
Digital Den — Core Configuration
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
    database_url: str = "postgresql://denis:denis_dev_2024@127.0.0.1:5434/digital_denis"
    redis_url: str = "redis://127.0.0.1:6379/0"
    
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
    
    # ElevenLabs for TTS
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "pMsXg9Y9C95gIn6ycYid"  # Recommended default voice
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    
    # ─────────────────────────────────────────────────────────────────────────
    # Telegram
    # ─────────────────────────────────────────────────────────────────────────
    telegram_bot_token: Optional[str] = None
    allowed_telegram_ids: Optional[str] = None  # Comma-separated list of allowed IDs
    
    # ─────────────────────────────────────────────────────────────────────────
    # Security
    # ─────────────────────────────────────────────────────────────────────────
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    
    # Encryption
    encryption_key: str = "change-this-in-production-must-be-32-bytes-base64"
    
    # Push Notifications (VAPID)
    vapid_private_key: str = "private_key.pem"
    vapid_public_key: str = "BJZfDd76XxBDteP3n5ZjPCDz4-SJHeg9N174hPS6m6Q8Iz_bxXSHrduSItz-OHaK2dLglvjkY8GJjoV_EFZcat4"
    vapid_claims_sub: str = "mailto:admin@digitaldenis.local"
    
    # Google OAuth2
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # Frontend URL for redirects
    frontend_url: str = "http://localhost:3000"
    
    # ─────────────────────────────────────────────────────────────────────────
    # System
    # ─────────────────────────────────────────────────────────────────────────
    system_language: str = "ru"
    debug: bool = True
    log_level: str = "INFO"
    json_logs: bool = False
    log_level: str = "INFO"
    json_logs: bool = False
    
    # Profile path (relative to project root)
    profile_path: str = "ai/profiles/den.yaml"
    
    class Config:
        # Load .env from project root (parent of backend/)
        from pathlib import Path
        # Try to find .env by looking up from current file
        @staticmethod
        def find_env_file():
            base = Path(__file__).resolve().parent
            for _ in range(4):
                if (base / ".env").exists():
                    return base / ".env"
                if base.parent == base:
                    break
                base = base.parent
            return Path(__file__).resolve().parent.parent.parent / ".env" # Fallback

        env_file = find_env_file()
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
