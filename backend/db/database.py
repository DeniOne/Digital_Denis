"""
Digital Denis — Database Connection
═══════════════════════════════════════════════════════════════════════════

Async database connection management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings


# Convert sync URL to async
def get_async_database_url() -> str:
    """Convert postgresql:// to postgresql+asyncpg://"""
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# Async engine
engine = create_async_engine(
    get_async_database_url(),
    echo=settings.debug,
    future=True,
)

# Async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Alias for compatibility
async_session_maker = async_session


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
