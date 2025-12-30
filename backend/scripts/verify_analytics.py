import asyncio
from uuid import UUID
from db.database import async_session
from analytics.service import analytics_service
from memory.models import User

async def verify_analytics():
    async with async_session() as db:
        from sqlalchemy import select
        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        
        if not user:
            print("No user found. Run verify_search.py first.")
            return

        print(f"Testing analytics for user: {user.username} ({user.id})")
        
        # Debug: Check columns in users table
        from sqlalchemy import text
        col_res = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
        columns = [row[0] for row in col_res.fetchall()]
        print(f"Columns in 'users' table: {columns}")
        
        if 'notification_settings' not in columns:
            print("CRITICAL: notification_settings column is STILL MISSING in database!")
            return
        print("\n--- Summary (30 days) ---")
        summary = await analytics_service.get_summary(db, user.id, days=30)
        print(f"Total Memories: {summary['total_memories']}")
        print(f"Types: {summary['by_type']}")
        print(f"Top Topics: {[t['name'] for t in summary['top_topics']]}")
        print(f"Streak: {summary['streak']} days")
        
        # 2. Test Activity
        print("\n--- Activity (7 days) ---")
        activity = await analytics_service.get_activity_timeline(db, user.id, days=7)
        for point in activity:
            print(f"- {point['date']}: {point['count']} items")
            
        # 3. Test Heatmap
        print("\n--- Heatmap Data ---")
        heatmap = await analytics_service.get_heatmap_data(db, user.id)
        print(f"Data points: {len(heatmap)}")

if __name__ == "__main__":
    asyncio.run(verify_analytics())
