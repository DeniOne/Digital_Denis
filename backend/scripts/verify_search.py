import asyncio
from uuid import uuid4
from db.database import async_session
from memory.models import MemoryItem, User
from memory.semantic import semantic_memory

async def verify():
    async with async_session() as db:
        # 1. Ensure a user exists
        from sqlalchemy import select
        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        
        if not user:
            user = User(username="test_user")
            db.add(user)
            await db.commit()
            print("Created test user.")
            
        # 2. Add some test memories
        test_memories = [
            "Сегодня я купил синие яблоки в магазине 'Морозко'.",
            "Завтра будет солнечно, надо пойти гулять в парк.",
            "Синие фрукты бывают редко, но яблоки из 'Морозко' интересные."
        ]
        
        mem_ids = []
        for content in test_memories:
            mem = MemoryItem(user_id=user.id, content=content, item_type="fact")
            db.add(mem)
            await db.flush()
            mem_ids.append(mem.id)
            
        await db.commit()
        print(f"Added {len(test_memories)} test memories.")
        
        # 3. Index them
        for mid in mem_ids:
            await semantic_memory.index(db, mid)
        print("Indexed test memories.")
        
        # 4. Perform Hybrid Search
        print("\n--- Hybrid Search Results (Query: 'синие яблоки') ---")
        results = await semantic_memory.search(db, "синие яблоки", limit=5)
        for mem, score in results:
            print(f"[{score:.4f}] {mem.content}")
            
        # 5. Cleanup (optional)
        # for mid in mem_ids:
        #    await db.execute(delete(MemoryItem).where(MemoryItem.id == mid))
        # await db.commit()

if __name__ == "__main__":
    asyncio.run(verify())
