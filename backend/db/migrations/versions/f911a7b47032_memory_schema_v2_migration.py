"""
Memory Schema v2 Migration

Revision ID: f911a7b47032
Revises: add_kaizen_engine
Create Date: 2026-01-04

Changes:
1. Extend memory_items table with RAG 2.0 fields
2. Create memory_events table (metapamory)
3. Create kaizen_metrics table
4. Create conversation_states table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


# revision identifiers, used by Alembic
revision = 'f911a7b47032'
down_revision = 'add_kaizen_settings'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════════
    # 1. Extend memory_items table
    # ═══════════════════════════════════════════════════════════════════════
    
    # Add new columns
    op.add_column('memory_items', sa.Column('related_to', ARRAY(UUID(as_uuid=True)), nullable=True))
    op.add_column('memory_items', sa.Column('usage_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('memory_items', sa.Column('positive_outcomes', sa.Integer(), server_default='0', nullable=False))
    op.add_column('memory_items', sa.Column('negative_outcomes', sa.Integer(), server_default='0', nullable=False))
    op.add_column('memory_items', sa.Column('confidence_level', sa.String(16), server_default='medium', nullable=False))
    
    # Remove old confidence FLOAT → convert to confidence_level VARCHAR
    # First, update confidence_level based on old confidence value
    op.execute("""
        UPDATE memory_items 
        SET confidence_level = CASE
            WHEN confidence >= 0.8 THEN 'high'
            WHEN confidence >= 0.5 THEN 'medium'
            ELSE 'low'
        END
    """)
    
    # Drop old item_type constraint
    op.execute("ALTER TABLE memory_items DROP CONSTRAINT IF EXISTS memory_items_item_type_check")
    
    # Add new extended item_type constraint
    op.create_check_constraint(
        'memory_items_item_type_check',
        'memory_items',
        "item_type IN ('decision', 'insight', 'fact', 'thought', 'principle', 'rule', 'hypothesis', 'reflection', 'emotion', 'failure', 'task')"
    )
    
    # Add confidence_level constraint
    op.create_check_constraint(
        'memory_items_confidence_level_check',
        'memory_items',
        "confidence_level IN ('high', 'medium', 'low', 'unknown')"
    )
    
    # Create indexes
    op.create_index('idx_memory_items_confidence', 'memory_items', ['confidence_level'])
    op.create_index('idx_memory_items_usage', 'memory_items', ['usage_count'], postgresql_using='btree')
    op.create_index('idx_memory_items_related', 'memory_items', ['related_to'], postgresql_using='gin')
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. Create memory_events table (metapamory)
    # ═══════════════════════════════════════════════════════════════════════
    
    op.create_table(
        'memory_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('memory_id', UUID(as_uuid=True), sa.ForeignKey('memory_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('event_type', sa.String(32), nullable=False),  # recalled, used, rejected, archived
        sa.Column('outcome', sa.String(16), nullable=True),      # positive, neutral, negative, unknown
        
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Indexes for memory_events
    op.create_index('idx_memory_events_memory', 'memory_events', ['memory_id'])
    op.create_index('idx_memory_events_user', 'memory_events', ['user_id'])
    op.create_index('idx_memory_events_type', 'memory_events', ['event_type'])
    op.create_index('idx_memory_events_created', 'memory_events', ['created_at'])
    
    # Constraints
    op.create_check_constraint(
        'memory_events_event_type_check',
        'memory_events',
        "event_type IN ('recalled', 'used', 'rejected', 'archived')"
    )
    op.create_check_constraint(
        'memory_events_outcome_check',
        'memory_events',
        "outcome IS NULL OR outcome IN ('positive', 'neutral', 'negative', 'unknown')"
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. Create kaizen_metrics table
    # ═══════════════════════════════════════════════════════════════════════
    
    op.create_table(
        'kaizen_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('dimension', sa.String(32), nullable=False),  # decision_quality, consistency, clarity_of_thought, execution, emotional_stability
        sa.Column('score', sa.Float(), nullable=False),         # 0.0 - 100.0
        
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Indexes
    op.create_index('idx_kaizen_metrics_user', 'kaizen_metrics', ['user_id'])
    op.create_index('idx_kaizen_metrics_dimension', 'kaizen_metrics', ['dimension'])
    op.create_index('idx_kaizen_metrics_created', 'kaizen_metrics', ['created_at'])
    
    # Constraints
    op.create_check_constraint(
        'kaizen_metrics_dimension_check',
        'kaizen_metrics',
        "dimension IN ('decision_quality', 'consistency', 'clarity_of_thought', 'execution', 'emotional_stability')"
    )
    op.create_check_constraint(
        'kaizen_metrics_score_check',
        'kaizen_metrics',
        "score >= 0.0 AND score <= 100.0"
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. Create conversation_states table
    # ═══════════════════════════════════════════════════════════════════════
    
    op.create_table(
        'conversation_states',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', sa.String(255), nullable=False),  # chat_id from Telegram
        
        # Core state
        sa.Column('topic', sa.Text(), nullable=True),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('current_step', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(50), nullable=True),
        
        # Entities and objects
        sa.Column('active_entities', ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('active_objects', ARRAY(sa.Text()), server_default='{}', nullable=False),
        
        # Assumptions and constraints
        sa.Column('assumptions', ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('constraints', ARRAY(sa.Text()), server_default='{}', nullable=False),
        
        # Decisions and questions
        sa.Column('decisions_made', JSONB(), server_default='[]', nullable=False),
        sa.Column('open_questions', ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('unresolved_points', ARRAY(sa.Text()), server_default='{}', nullable=False),
        
        # Confidence
        sa.Column('confidence_level', sa.String(16), server_default='unknown', nullable=False),
        
        # TTL
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('ttl_hours', sa.Integer(), server_default='48', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Indexes
    op.create_index('idx_conversation_states_user', 'conversation_states', ['user_id'])
    op.create_index('idx_conversation_states_conv_id', 'conversation_states', ['conversation_id'])
    op.create_index('idx_conversation_states_updated', 'conversation_states', ['last_updated'])
    
    # Unique constraint
    op.create_unique_constraint('uq_user_conversation', 'conversation_states', ['user_id', 'conversation_id'])
    
    # Constraints
    op.create_check_constraint(
        'conversation_states_confidence_level_check',
        'conversation_states',
        "confidence_level IN ('high', 'medium', 'low', 'unknown')"
    )


def downgrade():
    # Drop conversation_states
    op.drop_table('conversation_states')
    
    # Drop kaizen_metrics
    op.drop_table('kaizen_metrics')
    
    # Drop memory_events
    op.drop_table('memory_events')
    
    # Remove new columns from memory_items
    op.drop_index('idx_memory_items_related', table_name='memory_items')
    op.drop_index('idx_memory_items_usage', table_name='memory_items')
    op.drop_index('idx_memory_items_confidence', table_name='memory_items')
    
    op.drop_constraint('memory_items_confidence_level_check', 'memory_items', type_='check')
    
    op.drop_column('memory_items', 'confidence_level')
    op.drop_column('memory_items', 'negative_outcomes')
    op.drop_column('memory_items', 'positive_outcomes')
    op.drop_column('memory_items', 'usage_count')
    op.drop_column('memory_items', 'related_to')
    
    # Restore old item_type constraint
    op.execute("ALTER TABLE memory_items DROP CONSTRAINT IF EXISTS memory_items_item_type_check")
    op.create_check_constraint(
        'memory_items_item_type_check',
        'memory_items',
        "item_type IN ('decision', 'insight', 'fact', 'thought')"
    )
