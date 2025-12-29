"""
Digital Denis — Mind Map Graph Builder
═══════════════════════════════════════════════════════════════════════════

Graph construction and management for mind map visualization.
"""

import json
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.cal_models import CALGraphNode, CALGraphEdge
from memory.models import MemoryItem, Topic
from memory.semantic import semantic_memory
from llm.groq import groq


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

class NodeType(str, Enum):
    IDEA = "idea"
    DECISION = "decision"
    INSIGHT = "insight"
    TOPIC = "topic"
    FACT = "fact"
    CONCEPT = "concept"


class EdgeType(str, Enum):
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    EVOLVES_FROM = "evolves_from"
    REINFORCES = "reinforces"
    BELONGS_TO = "belongs_to"
    RELATES_TO = "relates_to"


# Visual styles for edge types
EDGE_STYLES = {
    EdgeType.DEPENDS_ON: {"style": "solid", "color": "#4A90A4"},
    EdgeType.CONTRADICTS: {"style": "dashed", "color": "#E74C3C"},
    EdgeType.EVOLVES_FROM: {"style": "solid", "color": "#3498DB"},
    EdgeType.REINFORCES: {"style": "solid", "color": "#27AE60"},
    EdgeType.BELONGS_TO: {"style": "dotted", "color": "#95A5A6"},
    EdgeType.RELATES_TO: {"style": "solid", "color": "#9B59B6"},
}

# Node colors by type
NODE_COLORS = {
    NodeType.IDEA: "#F39C12",
    NodeType.DECISION: "#27AE60",
    NodeType.INSIGHT: "#9B59B6",
    NodeType.TOPIC: "#3498DB",
    NodeType.FACT: "#1ABC9C",
    NodeType.CONCEPT: "#E67E22",
}


# ═══════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class GraphNode:
    """Node for visualization."""
    id: str
    label: str
    node_type: str
    size: float = 1.0
    color: str = "#95A5A6"
    x: Optional[float] = None
    y: Optional[float] = None
    cluster: Optional[int] = None
    data: Dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """Edge for visualization."""
    id: str
    source: str
    target: str
    edge_type: str
    weight: float = 1.0
    style: str = "solid"
    color: str = "#95A5A6"


@dataclass
class GraphData:
    """Complete graph for visualization."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    clusters: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# Graph Builder
# ═══════════════════════════════════════════════════════════════════════════

class GraphBuilder:
    """
    Mind Map graph construction.
    
    Builds graph nodes and edges from memory items,
    using semantic similarity and LLM for relationship detection.
    """
    
    # Thresholds
    MIN_SIMILARITY_FOR_EDGE = 0.7
    MIN_CONFIDENCE_FOR_NODE = 0.5
    
    async def create_node_from_memory(
        self,
        db: AsyncSession,
        memory: MemoryItem,
    ) -> CALGraphNode:
        """Create a graph node from memory item."""
        node_type = self._memory_type_to_node_type(memory.item_type)
        label = memory.summary or memory.content[:100]
        
        # Calculate initial importance based on type and confidence
        importance = self._calculate_importance(memory)
        
        node = CALGraphNode(
            id=uuid4(),
            memory_id=memory.id,
            node_type=node_type,
            label=label,
            importance_score=importance,
            metadata={
                "item_type": memory.item_type,
                "confidence": memory.confidence,
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
            },
        )
        db.add(node)
        return node
    
    def _memory_type_to_node_type(self, memory_type: str) -> str:
        """Map memory type to node type."""
        mapping = {
            "decision": NodeType.DECISION.value,
            "insight": NodeType.INSIGHT.value,
            "fact": NodeType.FACT.value,
            "thought": NodeType.IDEA.value,
            "aggregation": NodeType.CONCEPT.value,
        }
        return mapping.get(memory_type, NodeType.IDEA.value)
    
    def _calculate_importance(self, memory: MemoryItem) -> float:
        """Calculate node importance score."""
        base = 0.5
        
        # Decisions are more important
        if memory.item_type == "decision":
            base += 0.2
        elif memory.item_type == "insight":
            base += 0.1
        
        # Add confidence
        if memory.confidence:
            base += memory.confidence * 0.2
        
        return min(1.0, base)
    
    async def find_connections(
        self,
        db: AsyncSession,
        new_items: List[MemoryItem],
    ) -> List[CALGraphEdge]:
        """
        Find connections between new items and existing graph.
        
        Uses:
        1. Semantic similarity search
        2. LLM-based relationship classification
        3. Contradiction detection for decisions
        """
        edges = []
        
        for item in new_items:
            # Get or create node for this item
            node = await self._get_or_create_node(db, item)
            
            # 1. Find semantically similar items
            similar = await semantic_memory.search(
                db=db,
                query=item.content,
                limit=10,
                similarity_threshold=self.MIN_SIMILARITY_FOR_EDGE,
            )
            
            # 2. Determine relationship type for each
            for sim_item, similarity in similar:
                if sim_item.id == item.id:
                    continue
                
                # Get target node
                target_node = await self._get_or_create_node(db, sim_item)
                
                # Check if edge already exists
                existing = await self._edge_exists(db, node.id, target_node.id)
                if existing:
                    continue
                
                # Determine edge type
                edge_type = await self._determine_edge_type(item, sim_item)
                
                if edge_type:
                    edge = CALGraphEdge(
                        id=uuid4(),
                        source_id=node.id,
                        target_id=target_node.id,
                        edge_type=edge_type,
                        weight=similarity,
                        confidence=similarity,
                        metadata={"method": "semantic_similarity"},
                    )
                    db.add(edge)
                    edges.append(edge)
            
            # 3. Check for contradictions (decisions only)
            if item.item_type == "decision":
                contradictions = await self._find_contradictions(db, item)
                for contra_item, score in contradictions:
                    target_node = await self._get_or_create_node(db, contra_item)
                    
                    existing = await self._edge_exists(db, node.id, target_node.id)
                    if not existing:
                        edge = CALGraphEdge(
                            id=uuid4(),
                            source_id=node.id,
                            target_id=target_node.id,
                            edge_type=EdgeType.CONTRADICTS.value,
                            weight=score,
                            confidence=score,
                            metadata={"method": "contradiction_detection"},
                        )
                        db.add(edge)
                        edges.append(edge)
        
        await db.commit()
        
        # Update node degrees
        await self._update_node_degrees(db, edges)
        
        return edges
    
    async def _get_or_create_node(
        self,
        db: AsyncSession,
        memory: MemoryItem
    ) -> CALGraphNode:
        """Get existing node or create new one."""
        result = await db.execute(
            select(CALGraphNode).where(CALGraphNode.memory_id == memory.id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            node = await self.create_node_from_memory(db, memory)
        
        return node
    
    async def _edge_exists(
        self,
        db: AsyncSession,
        source_id: UUID,
        target_id: UUID
    ) -> bool:
        """Check if edge already exists between nodes."""
        result = await db.execute(
            select(CALGraphEdge).where(
                or_(
                    and_(
                        CALGraphEdge.source_id == source_id,
                        CALGraphEdge.target_id == target_id
                    ),
                    and_(
                        CALGraphEdge.source_id == target_id,
                        CALGraphEdge.target_id == source_id
                    )
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def _determine_edge_type(
        self,
        source: MemoryItem,
        target: MemoryItem
    ) -> Optional[str]:
        """Use LLM to determine relationship type."""
        prompt = f"""Определи тип связи между двумя записями:

Запись A ({source.item_type}): {source.content[:200]}
Запись B ({target.item_type}): {target.content[:200]}

Возможные связи:
- depends_on: A зависит от B / строится на B
- evolves_from: A - развитие/уточнение B
- reinforces: A поддерживает/усиливает B
- contradicts: A противоречит B
- relates_to: A связана с B тематически
- none: нет значимой связи

Ответь одним словом — типом связи:"""
        
        try:
            result = await groq.complete_simple(prompt)
            edge_type = result.strip().lower()
            
            valid_types = [e.value for e in EdgeType]
            if edge_type in valid_types and edge_type != "none":
                return edge_type
            return EdgeType.RELATES_TO.value if "relat" in edge_type else None
            
        except Exception as e:
            print(f"Error determining edge type: {e}")
            return EdgeType.RELATES_TO.value
    
    async def _find_contradictions(
        self,
        db: AsyncSession,
        decision: MemoryItem
    ) -> List[Tuple[MemoryItem, float]]:
        """Find decisions that contradict this one."""
        # Get other decisions
        result = await db.execute(
            select(MemoryItem).where(
                and_(
                    MemoryItem.item_type == "decision",
                    MemoryItem.status == "active",
                    MemoryItem.id != decision.id
                )
            ).limit(20)
        )
        other_decisions = result.scalars().all()
        
        contradictions = []
        
        for other in other_decisions:
            is_contra, score = await self._check_contradiction(decision, other)
            if is_contra:
                contradictions.append((other, score))
        
        return contradictions
    
    async def _check_contradiction(
        self,
        decision_a: MemoryItem,
        decision_b: MemoryItem
    ) -> Tuple[bool, float]:
        """Check if two decisions contradict."""
        prompt = f"""Определи, противоречат ли эти два решения друг другу:

Решение 1: {decision_a.content[:200]}
Решение 2: {decision_b.content[:200]}

Ответь в формате: YES/NO и уверенность (0.0-1.0)
Пример: YES 0.8 или NO 0.9"""
        
        try:
            result = await groq.complete_simple(prompt)
            parts = result.strip().upper().split()
            
            if parts and parts[0] == "YES":
                score = float(parts[1]) if len(parts) > 1 else 0.7
                return True, score
            return False, 0.0
            
        except Exception:
            return False, 0.0
    
    async def _update_node_degrees(
        self,
        db: AsyncSession,
        new_edges: List[CALGraphEdge]
    ) -> None:
        """Update degree counts for affected nodes."""
        node_ids = set()
        for edge in new_edges:
            node_ids.add(edge.source_id)
            node_ids.add(edge.target_id)
        
        for node_id in node_ids:
            # Count edges for this node
            result = await db.execute(
                select(func.count(CALGraphEdge.id)).where(
                    or_(
                        CALGraphEdge.source_id == node_id,
                        CALGraphEdge.target_id == node_id
                    )
                )
            )
            degree = result.scalar() or 0
            
            # Update node
            await db.execute(
                update(CALGraphNode)
                .where(CALGraphNode.id == node_id)
                .values(metadata=func.jsonb_set(
                    CALGraphNode.metadata,
                    '{degree}',
                    str(degree)
                ))
            )


# ═══════════════════════════════════════════════════════════════════════════
# Mind Map Service
# ═══════════════════════════════════════════════════════════════════════════

class MindMapService:
    """
    Service for mind map retrieval and manipulation.
    """
    
    def __init__(self):
        self.builder = GraphBuilder()
    
    async def get_graph(
        self,
        db: AsyncSession,
        topic_id: Optional[UUID] = None,
        node_types: Optional[List[str]] = None,
        days: int = 30,
        max_nodes: int = 100,
    ) -> GraphData:
        """Get graph data for visualization."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Build node query
        query = select(CALGraphNode).where(
            CALGraphNode.created_at > cutoff
        )
        
        if topic_id:
            query = query.where(CALGraphNode.topic_id == topic_id)
        
        if node_types:
            query = query.where(CALGraphNode.node_type.in_(node_types))
        
        query = query.order_by(desc(CALGraphNode.importance_score)).limit(max_nodes)
        
        result = await db.execute(query)
        db_nodes = result.scalars().all()
        node_ids = [n.id for n in db_nodes]
        
        # Get edges between these nodes
        edge_result = await db.execute(
            select(CALGraphEdge).where(
                and_(
                    CALGraphEdge.source_id.in_(node_ids),
                    CALGraphEdge.target_id.in_(node_ids)
                )
            )
        )
        db_edges = edge_result.scalars().all()
        
        # Format for visualization
        nodes = [self._format_node(n) for n in db_nodes]
        edges = [self._format_edge(e) for e in db_edges]
        
        # Get cluster info
        clusters = await self._get_clusters(db, node_ids)
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            clusters=clusters,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "period_days": days,
            },
        )
    
    def _format_node(self, node: CALGraphNode) -> GraphNode:
        """Format node for visualization."""
        node_type = NodeType(node.node_type) if node.node_type in [e.value for e in NodeType] else NodeType.IDEA
        color = NODE_COLORS.get(node_type, "#95A5A6")
        
        return GraphNode(
            id=str(node.id),
            label=node.label[:50] if node.label else "Untitled",
            node_type=node.node_type,
            size=0.5 + node.importance_score * 1.5,
            color=color,
            x=node.x_pos,
            y=node.y_pos,
            cluster=node.cluster_id,
            data={
                "memory_id": str(node.memory_id) if node.memory_id else None,
                "importance": node.importance_score,
                "created_at": node.created_at.isoformat() if node.created_at else None,
            },
        )
    
    def _format_edge(self, edge: CALGraphEdge) -> GraphEdge:
        """Format edge for visualization."""
        edge_type = EdgeType(edge.edge_type) if edge.edge_type in [e.value for e in EdgeType] else EdgeType.RELATES_TO
        style_info = EDGE_STYLES.get(edge_type, {"style": "solid", "color": "#95A5A6"})
        
        return GraphEdge(
            id=str(edge.id),
            source=str(edge.source_id),
            target=str(edge.target_id),
            edge_type=edge.edge_type,
            weight=edge.weight,
            style=style_info["style"],
            color=style_info["color"],
        )
    
    async def _get_clusters(
        self,
        db: AsyncSession,
        node_ids: List[UUID]
    ) -> List[Dict]:
        """Get cluster information for nodes."""
        result = await db.execute(
            select(
                CALGraphNode.cluster_id,
                func.count(CALGraphNode.id).label("count")
            )
            .where(
                and_(
                    CALGraphNode.id.in_(node_ids),
                    CALGraphNode.cluster_id.is_not(None)
                )
            )
            .group_by(CALGraphNode.cluster_id)
        )
        
        return [
            {"id": row.cluster_id, "count": row.count}
            for row in result.fetchall()
        ]
    
    async def get_node_neighbors(
        self,
        db: AsyncSession,
        node_id: UUID,
        depth: int = 1
    ) -> GraphData:
        """Get neighborhood graph for a specific node."""
        # Get edges from/to this node
        edge_result = await db.execute(
            select(CALGraphEdge).where(
                or_(
                    CALGraphEdge.source_id == node_id,
                    CALGraphEdge.target_id == node_id
                )
            )
        )
        edges = edge_result.scalars().all()
        
        # Collect neighbor IDs
        neighbor_ids = set([node_id])
        for edge in edges:
            neighbor_ids.add(edge.source_id)
            neighbor_ids.add(edge.target_id)
        
        # Get nodes
        node_result = await db.execute(
            select(CALGraphNode).where(CALGraphNode.id.in_(neighbor_ids))
        )
        nodes = node_result.scalars().all()
        
        return GraphData(
            nodes=[self._format_node(n) for n in nodes],
            edges=[self._format_edge(e) for e in edges],
        )
    
    async def add_topic_nodes(
        self,
        db: AsyncSession,
    ) -> int:
        """Add topic nodes to graph."""
        result = await db.execute(
            select(Topic).where(Topic.is_active == True)
        )
        topics = result.scalars().all()
        
        count = 0
        for topic in topics:
            # Check if node exists
            existing = await db.execute(
                select(CALGraphNode).where(CALGraphNode.topic_id == topic.id)
            )
            if existing.scalar_one_or_none():
                continue
            
            node = CALGraphNode(
                id=uuid4(),
                topic_id=topic.id,
                node_type=NodeType.TOPIC.value,
                label=topic.name,
                importance_score=0.7 + (topic.item_count or 0) * 0.01,
            )
            db.add(node)
            count += 1
        
        await db.commit()
        return count


# Global instances
graph_builder = GraphBuilder()
mind_map_service = MindMapService()
