"""
Digital Den — Topic Orchestrator
═══════════════════════════════════════════════════════════════════════════

Orchestrates clustering, naming, and topic creation.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import slugify
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from memory.models import Topic, MemoryTopic, MemoryItem
from analytics.clustering import clustering_service
from analytics.topic_generator import topic_naming_service

class TopicOrchestrator:
    """
    Ties together clustering and naming to create/update auto-generated topics.
    """
    
    async def run_auto_clustering(
        self, 
        db: AsyncSession, 
        user_id: UUID,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        1. Find clusters
        2. Name them
        3. Create/Update topics
        4. Link memories
        """
        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M")
        
        # 1. Cluster discovery
        clusters = await clustering_service.cluster_user_memories(db, user_id)
        if not clusters:
            return {"status": "no_clusters_found", "count": 0}
            
        # 2. Cleanup old auto-generated topics for this user (optional or incremental?)
        # For now, let's keep it clean or just append? 
        # Requirement 10.2 says "Merge похожих топиков", but simpler is to re-run and re-link.
        
        results = []
        for cluster in clusters:
            memory_ids = cluster["memory_ids"]
            
            # 3. Generate name & metadata
            metadata = await topic_naming_service.generate_topic_metadata(db, memory_ids)
            
            # 4. Create topic
            topic_name = metadata["name"]
            base_slug = slugify.slugify(topic_name)
            slug = f"auto_{user_id.hex[:8]}_{base_slug}"
            
            # Check if exists (unlikely with this slug, but good practice)
            stmt = select(Topic).where(Topic.slug == slug)
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if existing:
                topic = existing
                topic.name = topic_name
                topic.description = metadata["description"]
                topic.keywords = metadata["keywords"]
                topic.cluster_id = run_id
            else:
                topic = Topic(
                    id=uuid4(),
                    name=topic_name,
                    slug=slug,
                    description=metadata["description"],
                    keywords=metadata["keywords"],
                    user_id=user_id,
                    is_auto_generated=True,
                    cluster_id=run_id,
                    is_system=False
                )
                db.add(topic)
                await db.flush()
                
            # 5. Link memories (clear old auto-links for these memories if any?)
            # Actually, memories can have multiple topics. 
            # We'll just add assignments.
            
            for mid in memory_ids:
                # Check if link exists
                link_stmt = select(MemoryTopic).where(
                    MemoryTopic.memory_id == mid,
                    MemoryTopic.topic_id == topic.id
                )
                link_res = await db.execute(link_stmt)
                if not link_res.scalar_one_or_none():
                    db.add(MemoryTopic(
                        memory_id=mid,
                        topic_id=topic.id,
                        confidence=0.9, # High confidence since it's a cluster
                        assigned_by="clustering"
                    ))
            
            results.append({
                "topic_id": topic.id,
                "name": topic_name,
                "count": len(memory_ids)
            })
            
        await db.commit()
        return {
            "status": "success",
            "run_id": run_id,
            "topics_created": len(results),
            "details": results
        }

from datetime import datetime
topic_orchestrator = TopicOrchestrator()
