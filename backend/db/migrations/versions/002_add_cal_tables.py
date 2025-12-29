"""
Add CAL tables migration
═══════════════════════════════════════════════════════════════════════════

Revision ID: 002_add_cal_tables
Revises: 001_initial
Create Date: 2024-12-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_cal_tables'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CAL Topic Stats
    op.create_table(
        'cal_topic_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('topics.id'), nullable=False),
        sa.Column('period_date', sa.Date, nullable=False),
        sa.Column('item_count', sa.Integer, default=0),
        sa.Column('decision_count', sa.Integer, default=0),
        sa.Column('insight_count', sa.Integer, default=0),
        sa.Column('fact_count', sa.Integer, default=0),
        sa.Column('avg_confidence', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cal_topic_stats_topic_date', 'cal_topic_stats', ['topic_id', 'period_date'])
    
    # CAL Graph Nodes
    op.create_table(
        'cal_graph_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('memory_items.id'), nullable=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('topics.id'), nullable=True),
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('label', sa.Text, nullable=False),
        sa.Column('x_pos', sa.Float, nullable=True),
        sa.Column('y_pos', sa.Float, nullable=True),
        sa.Column('cluster_id', sa.Integer, nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('importance_score', sa.Float, default=0.5),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cal_nodes_memory', 'cal_graph_nodes', ['memory_id'])
    op.create_index('idx_cal_nodes_type', 'cal_graph_nodes', ['node_type'])
    
    # CAL Graph Edges
    op.create_table(
        'cal_graph_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('cal_graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('cal_graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('edge_type', sa.String(50), nullable=False),
        sa.Column('weight', sa.Float, default=1.0),
        sa.Column('confidence', sa.Float, default=0.5),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cal_edges_source', 'cal_graph_edges', ['source_id'])
    op.create_index('idx_cal_edges_target', 'cal_graph_edges', ['target_id'])
    op.create_index('idx_cal_edges_type', 'cal_graph_edges', ['edge_type'])
    
    # CAL Decision Analysis
    op.create_table(
        'cal_decision_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('memory_items.id'), nullable=False),
        sa.Column('strong_points', postgresql.JSONB, default=[]),
        sa.Column('weak_points', postgresql.JSONB, default=[]),
        sa.Column('risks', postgresql.JSONB, default=[]),
        sa.Column('missing_info', postgresql.JSONB, default=[]),
        sa.Column('overall_score', sa.Float),
        sa.Column('clarity_score', sa.Float),
        sa.Column('completeness_score', sa.Float),
        sa.Column('risk_level', sa.String(20)),
        sa.Column('interpretation', sa.Text),
        sa.Column('recommendations', postgresql.JSONB, default=[]),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cal_decision_analysis_decision', 'cal_decision_analysis', ['decision_id'])
    
    # CAL Anomalies
    op.create_table(
        'cal_anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('anomaly_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('baseline_value', sa.Float),
        sa.Column('current_value', sa.Float),
        sa.Column('deviation_percent', sa.Float),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('topics.id'), nullable=True),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('memory_items.id'), nullable=True),
        sa.Column('title', sa.String(255)),
        sa.Column('interpretation', sa.Text),
        sa.Column('suggested_action', sa.Text),
        sa.Column('status', sa.String(20), default='new'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_cal_anomalies_type', 'cal_anomalies', ['anomaly_type'])
    op.create_index('idx_cal_anomalies_severity', 'cal_anomalies', ['severity'])
    op.create_index('idx_cal_anomalies_status', 'cal_anomalies', ['status'])
    op.create_index('idx_cal_anomalies_detected', 'cal_anomalies', ['detected_at'])
    
    # CAL Health Snapshots
    op.create_table(
        'cal_health_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('snapshot_date', sa.Date, nullable=False),
        sa.Column('total_memories', sa.Integer, default=0),
        sa.Column('active_topics', sa.Integer, default=0),
        sa.Column('decisions_made', sa.Integer, default=0),
        sa.Column('insights_captured', sa.Integer, default=0),
        sa.Column('decision_quality_avg', sa.Float),
        sa.Column('memory_diversity_score', sa.Float),
        sa.Column('thinking_consistency_score', sa.Float),
        sa.Column('overall_health_score', sa.Float),
        sa.Column('anomalies_count', sa.Integer, default=0),
        sa.Column('unresolved_anomalies', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cal_health_date', 'cal_health_snapshots', ['snapshot_date'])


def downgrade() -> None:
    op.drop_table('cal_health_snapshots')
    op.drop_table('cal_anomalies')
    op.drop_table('cal_decision_analysis')
    op.drop_table('cal_graph_edges')
    op.drop_table('cal_graph_nodes')
    op.drop_table('cal_topic_stats')
