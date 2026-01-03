"""
Digital Den — Test Configuration
═══════════════════════════════════════════════════════════════════════════

Pytest configuration and fixtures for backend tests.
"""

import sys
from pathlib import Path
import os

# Add backend to Python path for imports
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Also add project root for ai/profiles access
project_root = backend_path.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set test environment variables BEFORE importing anything else
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-for-testing")
os.environ.setdefault("OPENROUTER_API_KEY", "test-api-key")

# Set profile path to test profile or the real one if it exists
real_profile = project_root / "ai" / "profiles" / "denis.yaml"
os.environ["PROFILE_PATH"] = str(real_profile) if real_profile.exists() else ""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ─────────────────────────────────────────────────────────────────────────────
# Mock Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for unit tests."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mock response"))]
    ))
    return client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "telegram_id": "123456789",
    }


@pytest.fixture
def sample_memory_data():
    """Sample memory/fact data for testing."""
    return {
        "id": 1,
        "user_id": 1,
        "content": "Test memory content",
        "memory_type": "fact",
        "importance": 0.8,
        "topics": ["test", "memory"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Profile Mock (to avoid file loading during tests)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_profile():
    """Auto-mock the profile to avoid file loading errors."""
    mock_profile_data = {
        "profile": {
            "name": "Test User",
            "role": "Developer",
            "cognitive_type": "analytical",
            "principles": ["Test principle"],
            "thinking_style": {"good": [], "bad": []},
            "decision_style": [],
            "rules": [],
            "terminology": {},
            "forbidden_patterns": [],
            "ai_expected": [],
            "ai_forbidden": [],
            "ai_must": [],
            "response_format": {"language": "ru"}
        }
    }
    
    with patch('orchestrator.profile.get_profile') as mock_get:
        from orchestrator.profile import DigitalProfile
        mock_get.return_value = DigitalProfile(mock_profile_data)
        yield mock_get
