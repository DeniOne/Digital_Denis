#!/usr/bin/env python3
"""Fix duplicate mama Evgeniya and check timezone."""
import asyncio
from db.database import async_session_maker
from sqlalchemy import text

async def fix():
    async with async_session_maker() as db:
        # 1. Удаляем дубликат "День рождения мамы Евгении" (оставляем первый)
        print("=== Removing duplicate 'День рождения мамы Евгении' ===")
        result = await db.execute(text("""
            SELECT id FROM reminder_schedules 
            WHERE title = 'День рождения мамы Евгении' 
            ORDER BY created_at ASC
            OFFSET 1
        """))
        duplicate_ids = [row[0] for row in result.fetchall()]
        
        if duplicate_ids:
            for dup_id in duplicate_ids:
                await db.execute(text(f"DELETE FROM reminder_instances WHERE schedule_id = '{dup_id}'"))
                await db.execute(text(f"DELETE FROM reminder_schedules WHERE id = '{dup_id}'"))
            print(f"Deleted {len(duplicate_ids)} duplicate(s)")
        else:
            print("No duplicates found")
        
        await db.commit()
        
        # 2. Проверяем timezone в reminder_schedules
        print("\n=== Checking timezone settings ===")
        result = await db.execute(text("SELECT title, timezone FROM reminder_schedules WHERE title LIKE '%рождения%' LIMIT 5"))
        for row in result.fetchall():
            print(f"  {row[0]}: timezone = {row[1]}")
        
        print("\n=== DONE ===")

if __name__ == "__main__":
    asyncio.run(fix())
