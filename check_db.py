#!/usr/bin/env python3
"""Quick DB check script."""
import asyncio
from db.database import async_session_maker
from sqlalchemy import text

async def check():
    async with async_session_maker() as db:
        print("=== SCHEDULE_ITEMS (last 10) ===")
        result = await db.execute(text("SELECT id, title, start_at, status, item_type FROM schedule_items ORDER BY created_at DESC LIMIT 10"))
        for row in result.fetchall():
            print(row)
        
        print("\n=== REMINDER_SCHEDULES ===")
        result = await db.execute(text("SELECT id, title, schedule_type, start_date, is_active FROM reminder_schedules ORDER BY created_at DESC LIMIT 10"))
        for row in result.fetchall():
            print(row)
        
        print("\n=== REMINDER_INSTANCES (pending) ===")
        result = await db.execute(text("SELECT id, remind_at, status, sent_at FROM reminder_instances WHERE status = 'PENDING' ORDER BY remind_at LIMIT 10"))
        for row in result.fetchall():
            print(row)

if __name__ == "__main__":
    asyncio.run(check())
