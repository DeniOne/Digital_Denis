"""
Digital Denis — CAL Database Models
═══════════════════════════════════════════════════════════════════════════

SQLAlchemy models for Cognitive Analytics Layer.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Float, Boolean, DateTime, ForeignKey,
    Integer, JSON, Date, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from memory.models import Base


# ═══════════════════════════════════════════════════════════════════════════
# Topic Statistics (Time-series)
# ═══════════════════════════════════════════════════════════════════════════

class CALTopicStats(Base):
    """Daily topic statistics for trend analysis."""
    __tablename__ = "cal_topic_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)
    
    # Time period
    period_date = Column(Date, nullable=False)
    
    # Metrics
    item_count = Column(Integer, default=0)
    decision_count = Column(Integer, default=0)
    insight_count = Column(Integer, default=0)
    fact_count = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_cal_topic_stats_topic_date", "topic_id", "period_date"),
        {"schema": None},
    )


# ═══════════════════════════════════════════════════════════════════════════
# Graph Nodes and Edges (Mind Map)
# ═══════════════════════════════════════════════════════════════════════════

class CALGraphNode(Base):
    """Node in the mind map graph."""
    __tablename__ = "cal_graph_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to source
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id"), nullable=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    
    # Node info
    node_type = Column(String(50), nullable=False)  # idea, decision, insight, topic, concept
    label = Column(Text, nullable=False)
    
    # Positioning (for visualization)
    x_pos = Column(Float, nullable=True)
    y_pos = Column(Float, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    
    # Metadata
    meta_data = Column("metadata", JSONB, default={})
    importance_score = Column(Float, default=0.5)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    outgoing_edges = relationship("CALGraphEdge", foreign_keys="CALGraphEdge.source_id", back_populates="source")
    incoming_edges = relationship("CALGraphEdge", foreign_keys="CALGraphEdge.target_id", back_populates="target")
    
    __table_args__ = (
        Index("idx_cal_nodes_memory", "memory_id"),
        Index("idx_cal_nodes_type", "node_type"),
    )


class CALGraphEdge(Base):
    """Edge connecting nodes in the mind map."""
    __tablename__ = "cal_graph_edges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Nodes
    source_id = Column(UUID(as_uuid=True), ForeignKey("cal_graph_nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("cal_graph_nodes.id", ondelete="CASCADE"), nullable=False)
    
    # Edge properties
    edge_type = Column(String(50), nullable=False)  # depends_on, contradicts, evolves_from, reinforces, relates_to
    weight = Column(Float, default=1.0)
    confidence = Column(Float, default=0.5)
    
    # Metadata
    meta_data = Column("metadata", JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source = relationship("CALGraphNode", foreign_keys=[source_id], back_populates="outgoing_edges")
    target = relationship("CALGraphNode", foreign_keys=[target_id], back_populates="incoming_edges")
    
    __table_args__ = (
        Index("idx_cal_edges_source", "source_id"),
        Index("idx_cal_edges_target", "target_id"),
        Index("idx_cal_edges_type", "edge_type"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Decision Analysis
# ═══════════════════════════════════════════════════════════════════════════

class CALDecisionAnalysis(Base):
    """Analysis results for decisions."""
    __tablename__ = "cal_decision_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id"), nullable=False)
    
    # Analysis results
    strong_points = Column(JSONB, default=[])
    weak_points = Column(JSONB, default=[])
    risks = Column(JSONB, default=[])
    missing_info = Column(JSONB, default=[])
    
    # Scores
    overall_score = Column(Float)  # 0-1
    clarity_score = Column(Float)
    completeness_score = Column(Float)
    risk_level = Column(String(20))  # low, medium, high
    
    # LLM explanation
    interpretation = Column(Text)
    recommendations = Column(JSONB, default=[])
    
    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_cal_decision_analysis_decision", "decision_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Anomalies
# ═══════════════════════════════════════════════════════════════════════════

class CALAnomaly(Base):
    """Detected anomalies in thinking patterns."""
    __tablename__ = "cal_anomalies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Anomaly classification
    anomaly_type = Column(String(50), nullable=False)
    # Types: topic_spike, topic_drop, decision_quality_drop, unusual_pattern, 
    #        high_risk_decision, contradiction_detected
    
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Detection context
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    baseline_value = Column(Float)
    current_value = Column(Float)
    deviation_percent = Column(Float)
    
    # Related entities
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memory_items.id"), nullable=True)
    
    # Description
    title = Column(String(255))
    interpretation = Column(Text)
    suggested_action = Column(Text)
    
    # Status
    status = Column(String(20), default="new")  # new, acknowledged, in_review, resolved, dismissed
    
    # Timestamps
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("idx_cal_anomalies_type", "anomaly_type"),
        Index("idx_cal_anomalies_severity", "severity"),
        Index("idx_cal_anomalies_status", "status"),
        Index("idx_cal_anomalies_detected", "detected_at"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Cognitive Health Snapshots
# ═══════════════════════════════════════════════════════════════════════════

class CALHealthSnapshot(Base):
    """Periodic cognitive health snapshots."""
    __tablename__ = "cal_health_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Snapshot time
    snapshot_date = Column(Date, nullable=False)
    
    # Metrics
    total_memories = Column(Integer, default=0)
    active_topics = Column(Integer, default=0)
    decisions_made = Column(Integer, default=0)
    insights_captured = Column(Integer, default=0)
    
    # Quality scores (0-100)
    decision_quality_avg = Column(Float)
    memory_diversity_score = Column(Float)
    thinking_consistency_score = Column(Float)
    overall_health_score = Column(Float)
    
    # Anomaly counts
    anomalies_count = Column(Integer, default=0)
    unresolved_anomalies = Column(Integer, default=0)
    
    # Created at
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_cal_health_date", "snapshot_date"),
    )
