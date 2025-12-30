import asyncio
from uuid import UUID
from db.database import async_session
from memory.models import User, MemoryItem
from analytics.topic_orchestrator import topic_orchestrator

async def verify_clustering():
    async with async_session() as db:
        # 1. Get user
        from sqlalchemy import select
        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            print("No user found. Run verify_search.py first.")
            return

        print(f"Testing clustering for user: {user.username} ({user.id})")
        
        # 2. Add some specific clusterable memories if needed
        # (Assuming verify_search.py already added some, but let's add more for a distinct cluster)
        more_memories = [
            "Нужно изучить теорию графов для алгоритмов кластеризации.",
            "Библиотека HDBSCAN очень мощная для поиска плотных групп точек.",
            "Математика в основе машинного обучения важна для анализа данных.",
            "Алгоритмы на графах помогают визуализировать связи в памяти.",
            "Плотность распределения данных в векторном пространстве определяет кластеры."
        ]
        
        for content in more_memories:
            mem = MemoryItem(user_id=user.id, content=content, item_type="insight")
            db.add(mem)
        
        await db.commit()
        print(f"Added {len(more_memories)} more memories for clustering.")
        
        # 3. Ensure they are indexed (reindex_all is easiest)
        from memory.semantic import semantic_memory
        await semantic_memory.reindex_all(db)
        print("Indexed all memories.")
        
        # 4. Run Clustering
        print("🚀 Running topic auto-clustering...")
        result = await topic_orchestrator.run_auto_clustering(db, user.id)
        
        print("\n--- Clustering Result ---")
        print(f"Status: {result.get('status')}")
        print(f"Topics Created: {result.get('topics_created')}")
        for topic in result.get('details', []):
            print(f"- Topic: {topic['name']} (Items: {topic['count']})")

if __name__ == "__main__":
    asyncio.run(verify_clustering())
