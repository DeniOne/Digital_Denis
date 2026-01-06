#!/usr/bin/env python3
"""Fix schedule bugs."""
import asyncio
from db.database import async_session_maker
from sqlalchemy import text

async def fix():
    async with async_session_maker() as db:
        # 1. Исправляем schedule_type для дней рождения (DAILY -> YEARLY)
        print("=== Fixing schedule_type DAILY -> YEARLY for birthdays ===")
        await db.execute(text("""
            UPDATE reminder_schedules 
            SET schedule_type = 'YEARLY' 
            WHERE title LIKE '%рождения%' AND schedule_type = 'DAILY'
        """))
        
        # 2. Удаляем дубликаты "День рождения Ромы" (оставляем только один)
        print("=== Removing duplicate 'День рождения Ромы' ===")
        # Находим все ID кроме первого
        result = await db.execute(text("""
            SELECT id FROM reminder_schedules 
            WHERE title = 'День рождения Ромы' 
            ORDER BY created_at ASC
            OFFSET 1
        """))
        duplicate_ids = [row[0] for row in result.fetchall()]
        
        if duplicate_ids:
            # Удаляем связанные reminder_instances
            for dup_id in duplicate_ids:
                await db.execute(text(f"DELETE FROM reminder_instances WHERE schedule_id = '{dup_id}'"))
                await db.execute(text(f"DELETE FROM reminder_schedules WHERE id = '{dup_id}'"))
            print(f"Deleted {len(duplicate_ids)} duplicates")
        
        # 3. Удаляем старую таблетку (на вчера)
        print("=== Removing old tablet reminder ===")
        await db.execute(text("""
            DELETE FROM schedule_items WHERE title = 'Выпить таблетку'
        """))
        
        await db.commit()
        print("=== DONE ===")
        
        # Проверяем результат
        print("\n=== Updated REMINDER_SCHEDULES ===")
        result = await db.execute(text("SELECT id, title, schedule_type, start_date FROM reminder_schedules WHERE title LIKE '%рождения%' ORDER BY title"))
        for row in result.fetchall():
            print(row)

if __name__ == "__main__":
    asyncio.run(fix())
