import asyncio
import os
import sys
from sqlalchemy import select

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.db.database import SessionLocal
from backend.memory.models import User
from backend.core.auth import get_current_user_optional

async def test_auth():
    async with SessionLocal() as db:
        print("Testing get_current_user_optional...")
        try:
            user = await get_current_user_optional(credentials=None, db=db)
            print(f"Success: {user}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # OS env for DB
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://denis:denis_dev_2024@localhost:5434/digital_denis"
    asyncio.run(test_auth())
