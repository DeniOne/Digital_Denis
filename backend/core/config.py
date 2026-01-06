"""
Digital Den — Core Configuration
═══════════════════════════════════════════════════════════════════════════

Конфигурация из переменных окружения.
"""

from functools import lru_cache
from typing import Optional

from pathlib import Path
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
    
    # ─────────────────────────────────────────────────────────────────────────
    # Hybrid AI Architecture — Model Roles
    # ─────────────────────────────────────────────────────────────────────────
    
    # Router/Classifier model (cheap, fast) — диспетчер запросов
    router_model: str = "openai/gpt-4o-mini"
    
    # Default model for main tasks — основная модель
    default_model: str = "anthropic/claude-sonnet-4.5"
    
    # Fast/Routine model — рутинные задачи (80% запросов)
    fast_model: str = "openai/gpt-4o-mini"
    
    # Thinking/Reasoning models — глубокий анализ, философия
    thinking_model: str = "deepseek/deepseek-r1"
    thinking_fallback_model: str = "anthropic/claude-opus-4.5"  # Claude Opus 4.5
    
    # Creative models — творческие задачи
    creative_text_model: str = "openai/gpt-4o"  # Книги, сторителлинг
    creative_multimodal_model: str = "google/gemini-3-flash-preview"  # Gemini 3 Flash
    
    # Reasoning model (Gemini for deep analysis)
    google_api_key: Optional[str] = None
    reasoning_model: str = "gemini-1.5-pro"
    
    # Cheap model for classification, topic extraction
    cheap_model: str = "openai/gpt-4o-mini"
    
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
    vapid_private_key: str = "zbEb2KyvSVvP3L1-FPxwavNv2uBtd83Ph9YsDMggA2k"
    vapid_public_key: str = "BIAZ8zpfTVa2KhuMsr75SZHnIp_QY7HD5xnkPhYCuWT1cYxnXQod_aesOnO8cLaseS5_CQOICK2bzyMsm2xnvE8"
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
        # Multi-level .env file detection
        @staticmethod
        def find_env_file():
            from pathlib import Path
            # 1. Try relative to current working directory
            try:
                cwd_env = Path.cwd() / ".env"
                if cwd_env.exists():
                    return cwd_env
            except Exception:
                pass
                
            # 2. Try walking up from this file
            base = Path(__file__).resolve().parent
            for _ in range(5):
                if (base / ".env").exists():
                    return base / ".env"
                if base.parent == base:
                    break
                base = base.parent
                
            # 3. Explicit Docker fallback
            if Path("/app/.env").exists():
                return Path("/app/.env")
                
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
