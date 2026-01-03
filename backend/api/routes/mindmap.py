"""
Digital Den — Mind Map API Routes
═══════════════════════════════════════════════════════════════════════════

REST API endpoints for mind map graph.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from analytics.graphs import mind_map_service, graph_builder
from core.auth import get_current_user_optional
from memory.models import User


router = APIRouter(tags=["Mind Map"])


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class NodeDataSchema(BaseModel):
    memory_id: Optional[str] = None
    importance: Optional[float] = None
    created_at: Optional[str] = None


class GraphNodeSchema(BaseModel):
    id: str
    label: str
    node_type: str
    size: float
    color: str
    x: Optional[float] = None
    y: Optional[float] = None
    cluster: Optional[int] = None
    data: NodeDataSchema


class GraphEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str
    weight: float
    style: str
    color: str


class ClusterSchema(BaseModel):
    id: int
    count: int


class GraphMetadataSchema(BaseModel):
    total_nodes: int
    total_edges: int
    period_days: int


class GraphDataResponse(BaseModel):
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]
    clusters: List[ClusterSchema] = []
    metadata: GraphMetadataSchema


class BuildConnectionsResponse(BaseModel):
    edges_created: int
    memory_ids: List[str]


class AddTopicNodesResponse(BaseModel):
    nodes_created: int


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=GraphDataResponse)
async def get_mind_map(
    topic_id: Optional[UUID] = None,
    node_types: Optional[str] = Query(None, description="Comma-separated node types"),
    days: int = Query(30, ge=7, le=365),
    max_nodes: int = Query(100, ge=10, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Get mind map graph for visualization.
    
    Node types: idea, decision, insight, topic, fact, concept
    """
    types_list = node_types.split(",") if node_types else None
    
    graph = await mind_map_service.get_graph(
        db=db,
        user_id=current_user.id,
        topic_id=topic_id,
        node_types=types_list,
        days=days,
        max_nodes=max_nodes,
    )
    
    return GraphDataResponse(
        nodes=[
            GraphNodeSchema(
                id=n.id,
                label=n.label,
                node_type=n.node_type,
                size=n.size,
                color=n.color,
                x=n.x,
                y=n.y,
                cluster=n.cluster,
                data=NodeDataSchema(**n.data),
            )
            for n in graph.nodes
        ],
        edges=[
            GraphEdgeSchema(
                id=e.id,
                source=e.source,
                target=e.target,
                edge_type=e.edge_type,
                weight=e.weight,
                style=e.style,
                color=e.color,
            )
            for e in graph.edges
        ],
        clusters=[ClusterSchema(**c) for c in graph.clusters],
        metadata=GraphMetadataSchema(**graph.metadata),
    )


@router.get("/node/{node_id}/neighbors", response_model=GraphDataResponse)
async def get_node_neighbors(
    node_id: UUID,
    depth: int = Query(1, ge=1, le=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get neighborhood graph for a specific node."""
    graph = await mind_map_service.get_node_neighbors(db, node_id, depth=depth, user_id=current_user.id)
    
    return GraphDataResponse(
        nodes=[
            GraphNodeSchema(
                id=n.id,
                label=n.label,
                node_type=n.node_type,
                size=n.size,
                color=n.color,
                x=n.x,
                y=n.y,
                cluster=n.cluster,
                data=NodeDataSchema(**n.data),
            )
            for n in graph.nodes
        ],
        edges=[
            GraphEdgeSchema(
                id=e.id,
                source=e.source,
                target=e.target,
                edge_type=e.edge_type,
                weight=e.weight,
                style=e.style,
                color=e.color,
            )
            for e in graph.edges
        ],
        clusters=[],
        metadata=GraphMetadataSchema(
            total_nodes=len(graph.nodes),
            total_edges=len(graph.edges),
            period_days=0,
        ),
    )


@router.post("/build-connections", response_model=BuildConnectionsResponse)
async def build_connections(
    memory_ids: List[UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Build graph connections for specific memory items.
    Useful for manual triggering after batch imports.
    """
    from memory.models import MemoryItem
    from sqlalchemy import select
    
    result = await db.execute(
        select(MemoryItem).where(
            and_(
                MemoryItem.id.in_(memory_ids),
                MemoryItem.user_id == current_user.id
            )
        )
    )
    memories = result.scalars().all()
    
    edges = await graph_builder.find_connections(db, memories)
    
    return BuildConnectionsResponse(
        edges_created=len(edges),
        memory_ids=[str(m.id) for m in memories],
    )


@router.post("/add-topic-nodes", response_model=AddTopicNodesResponse)
async def add_topic_nodes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Add topic nodes to the graph."""
    count = await mind_map_service.add_topic_nodes(db, user_id=current_user.id)
    return AddTopicNodesResponse(nodes_created=count)


@router.get("/stats")
async def get_graph_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """Get graph statistics."""
    from analytics.cal_models import CALGraphNode, CALGraphEdge
    from sqlalchemy import select, func
    
    # Count nodes by type
    # TODO: Add user_id filtering when CALGraphNode model is updated with user_id field
    node_result = await db.execute(
        select(
            CALGraphNode.node_type,
            func.count(CALGraphNode.id).label("count")
        ).group_by(CALGraphNode.node_type)
    )
    node_counts = {row.node_type: row.count for row in node_result.fetchall()}
    
    # Count edges by type
    edge_result = await db.execute(
        select(
            CALGraphEdge.edge_type,
            func.count(CALGraphEdge.id).label("count")
        ).group_by(CALGraphEdge.edge_type)
    )
    edge_counts = {row.edge_type: row.count for row in edge_result.fetchall()}
    
    # Total counts
    total_nodes = sum(node_counts.values())
    total_edges = sum(edge_counts.values())
    
    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "nodes_by_type": node_counts,
        "edges_by_type": edge_counts,
        "avg_degree": total_edges * 2 / max(1, total_nodes),
    }
