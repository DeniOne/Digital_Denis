#!/usr/bin/env python3
"""Check reminder instance for debugging."""
import asyncio
from db.database import async_session_maker
from sqlalchemy import text
from datetime import datetime

async def check():
    async with async_session_maker() as db:
        # Проверяем reminder на 15:55
        print("=== Reminder instances for 'Выпить чай' ===")
        result = await db.execute(text("""
            SELECT 
                ri.id,
                rs.title,
                ri.remind_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Moscow' as remind_at_msk,
                ri.status,
                ri.sent_at,
                u.telegram_id
            FROM reminder_instances ri
            JOIN reminder_schedules rs ON ri.schedule_id = rs.id
            JOIN users u ON rs.user_id = u.id
            WHERE rs.title LIKE '%чай%' OR rs.title LIKE '%табл%'
            ORDER BY ri.remind_at DESC
            LIMIT 5
        """))
        
        for row in result.fetchall():
            print(f"  ID: {row[0]}")
            print(f"  Title: {row[1]}")
            print(f"  Remind at (MSK): {row[2]}")
            print(f"  Status: {row[3]}")
            print(f"  Sent at: {row[4]}")
            print(f"  Telegram ID: {row[5]}")
            print()
        
        print("\n=== Schedule items for 'чай' ===")
        result2 = await db.execute(text("""
            SELECT 
                si.id,
                si.title,
                si.start_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Moscow' as start_msk,
                si.status
            FROM schedule_items si
            WHERE si.title LIKE '%чай%' OR si.title LIKE '%табл%'
            ORDER BY si.start_at DESC
            LIMIT 5
        """))
        
        for row in result2.fetchall():
            print(f"  Title: {row[1]}")
            print(f"  Start at (MSK): {row[2]}")
            print(f"  Status: {row[3]}")
            print()

if __name__ == "__main__":
    asyncio.run(check())
