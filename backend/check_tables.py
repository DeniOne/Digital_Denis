import asyncio
from sqlalchemy import text
from db.database import async_session

async def check_tables():
    async with async_session() as db:
        result = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
        tables = [row[0] for row in result.fetchall()]
        print('Tables:', tables)
        print('user_settings exists:', 'user_settings' in tables)
        print('rules exists:', 'rules' in tables)

asyncio.run(check_tables())
