"""
Digital Den — Clustering Service
═══════════════════════════════════════════════════════════════════════════

Unsupervised clustering of memory embeddings using HDBSCAN.
"""

import numpy as np
from typing import List, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.cluster import HDBSCAN

from memory.models import MemoryEmbedding

class ClusteringService:
    """
    Groups memory items by semantic similarity.
    """
    
    def __init__(self, min_cluster_size: int = 5, min_samples: int = 3):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
    
    async def cluster_user_memories(
        self, 
        db: AsyncSession, 
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Runs HDBSCAN on user's memory embeddings.
        Returns: [{"cluster_id": int, "memory_ids": [UUID], "center_embedding": [...]}]
        """
        # 1. Fetch all embeddings for user
        # We need to join with memory_items to filter by user_id
        from memory.models import MemoryItem
        
        stmt = (
            select(MemoryEmbedding.memory_id, MemoryEmbedding.embedding)
            .join(MemoryItem, MemoryItem.id == MemoryEmbedding.memory_id)
            .where(MemoryItem.user_id == user_id)
            .where(MemoryItem.status == 'active')
        )
        
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        if len(rows) < self.min_cluster_size:
            return []
            
        memory_ids = [row[0] for row in rows]
        embeddings = np.array([row[1] for row in rows])
        
        # 2. Fit HDBSCAN
        clusterer = HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric='cosine',
            cluster_selection_method='eom'
        )
        
        labels = clusterer.fit_predict(embeddings)
        
        # 3. Group by labels
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:  # Noise
                continue
            
            if label not in clusters:
                clusters[label] = {
                    "cluster_id": int(label),
                    "memory_ids": [],
                    "embeddings": []
                }
            
            clusters[label]["memory_ids"].append(memory_ids[i])
            clusters[label]["embeddings"].append(embeddings[i])
            
        # 4. Calculate centroids and format results
        results = []
        for label, data in clusters.items():
            centroid = np.mean(data["embeddings"], axis=0).tolist()
            results.append({
                "cluster_label": label,
                "memory_ids": data["memory_ids"],
                "centroid": centroid
            })
            
        return results

clustering_service = ClusteringService()
