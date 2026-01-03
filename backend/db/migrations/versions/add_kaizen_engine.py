"""
Add Kaizen Engine tables

Revision ID: add_kaizen_engine
Revises: c67bdc05acb6
Create Date: 2026-01-03

Tables:
- kaizen_snapshots: Daily Kaizen metrics snapshots
- kaizen_contour_metrics: Detailed contour metrics
- kaizen_state_transitions: State change history
- kaizen_observations: AI-generated observations
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic
revision = 'add_kaizen_engine'
down_revision = '7967b79d11d8'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════
    # Kaizen Snapshots - Daily state capture
    # ═══════════════════════════════════════════════════════════════════════
    op.create_table(
        'kaizen_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        
        # Kaizen Index
        sa.Column('kaizen_index', sa.Float(), default=0.0),
        sa.Column('kaizen_index_7d', sa.Float(), default=0.0),
        sa.Column('kaizen_index_14d', sa.Float(), default=0.0),
        sa.Column('kaizen_index_30d', sa.Float(), default=0.0),
        
        # User state
        sa.Column('user_state', sa.String(20), default='plateau'),
        
        # Cognitive Contour
        sa.Column('cognitive_score', sa.Float(), default=0.5),
        sa.Column('cognitive_trend', sa.String(20), default='stable'),
        sa.Column('cognitive_change_pct', sa.Float(), default=0.0),
        
        # Decision Contour
        sa.Column('decision_score', sa.Float(), default=0.5),
        sa.Column('decision_trend', sa.String(20), default='stable'),
        sa.Column('decision_change_pct', sa.Float(), default=0.0),
        
        # Management Contour
        sa.Column('management_score', sa.Float(), default=0.5),
        sa.Column('management_trend', sa.String(20), default='stable'),
        sa.Column('management_change_pct', sa.Float(), default=0.0),
        
        # Stability Contour
        sa.Column('stability_score', sa.Float(), default=0.5),
        sa.Column('stability_trend', sa.String(20), default='stable'),
        sa.Column('stability_change_pct', sa.Float(), default=0.0),
        
        # Raw metrics
        sa.Column('avg_message_length', sa.Float(), default=0.0),
        sa.Column('formulation_precision', sa.Float(), default=0.0),
        sa.Column('abstraction_level', sa.Float(), default=0.0),
        sa.Column('topic_switches', sa.Integer(), default=0),
        sa.Column('decision_completion_rate', sa.Float(), default=0.0),
        sa.Column('revisit_rate', sa.Float(), default=0.0),
        sa.Column('messages_count', sa.Integer(), default=0),
        sa.Column('decisions_count', sa.Integer(), default=0),
        sa.Column('insights_count', sa.Integer(), default=0),
        
        # Mirror observation
        sa.Column('mirror_observation', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('metadata', JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_kaizen_snapshot_user_date', 'kaizen_snapshots', ['user_id', 'snapshot_date'])
    op.create_index('idx_kaizen_snapshot_date', 'kaizen_snapshots', ['snapshot_date'])
    op.create_index('idx_kaizen_snapshot_state', 'kaizen_snapshots', ['user_state'])
    
    # ═══════════════════════════════════════════════════════════════════════
    # Kaizen Contour Metrics - Detailed per-contour tracking
    # ═══════════════════════════════════════════════════════════════════════
    op.create_table(
        'kaizen_contour_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('snapshot_id', UUID(as_uuid=True), sa.ForeignKey('kaizen_snapshots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contour', sa.String(20), nullable=False),
        sa.Column('score', sa.Float(), default=0.5),
        sa.Column('trend', sa.String(20), default='stable'),
        sa.Column('change_pct', sa.Float(), default=0.0),
        sa.Column('sub_metrics', JSONB(), default={}),
        sa.Column('influence_factors', JSONB(), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_kaizen_contour_snapshot', 'kaizen_contour_metrics', ['snapshot_id'])
    op.create_index('idx_kaizen_contour_type', 'kaizen_contour_metrics', ['contour'])
    
    # ═══════════════════════════════════════════════════════════════════════
    # Kaizen State Transitions - State change history
    # ═══════════════════════════════════════════════════════════════════════
    op.create_table(
        'kaizen_state_transitions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_state', sa.String(20), nullable=False),
        sa.Column('to_state', sa.String(20), nullable=False),
        sa.Column('transition_date', sa.Date(), nullable=False),
        sa.Column('probable_factors', JSONB(), default=[]),
        sa.Column('previous_state_duration', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_kaizen_transition_user', 'kaizen_state_transitions', ['user_id'])
    op.create_index('idx_kaizen_transition_date', 'kaizen_state_transitions', ['transition_date'])
    
    # ═══════════════════════════════════════════════════════════════════════
    # Kaizen Observations - AI-generated neutral observations
    # ═══════════════════════════════════════════════════════════════════════
    op.create_table(
        'kaizen_observations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('observation_date', sa.Date(), nullable=False),
        sa.Column('contour', sa.String(20), nullable=True),
        sa.Column('observation_text', sa.Text(), nullable=False),
        sa.Column('observation_type', sa.String(30), default='pattern'),
        sa.Column('confidence', sa.Float(), default=0.7),
        sa.Column('snapshot_id', UUID(as_uuid=True), sa.ForeignKey('kaizen_snapshots.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_mirror_worthy', sa.Boolean(), default=False),
        sa.Column('is_viewed', sa.Boolean(), default=False),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_kaizen_obs_user', 'kaizen_observations', ['user_id'])
    op.create_index('idx_kaizen_obs_date', 'kaizen_observations', ['observation_date'])
    op.create_index('idx_kaizen_obs_mirror', 'kaizen_observations', ['is_mirror_worthy'])


def downgrade():
    op.drop_table('kaizen_observations')
    op.drop_table('kaizen_state_transitions')
    op.drop_table('kaizen_contour_metrics')
    op.drop_table('kaizen_snapshots')
