"""
Initial migration: Create all tables including PGVector extension
═══════════════════════════════════════════════════════════════════════════

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PGVector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create topics table
    op.create_table(
        'topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id'), nullable=True),
        sa.Column('level', sa.Integer, default=0),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('item_count', sa.Integer, default=0),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_topics_parent', 'topics', ['parent_id'])
    op.create_index('idx_topics_slug', 'topics', ['slug'])
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(50), default='telegram'),
        sa.Column('metadata_json', postgresql.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
    )
    
    # Create memory_items table
    op.create_table(
        'memory_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('structured_data', postgresql.JSON, nullable=True),
        sa.Column('source_agent', sa.String(50), nullable=True),
        sa.Column('source_session', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confidence', sa.Float, default=0.5),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('accessed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_memory_items_user', 'memory_items', ['user_id'])
    op.create_index('idx_memory_items_type', 'memory_items', ['item_type'])
    op.create_index('idx_memory_items_status', 'memory_items', ['status'])
    op.create_index('idx_memory_items_created', 'memory_items', ['created_at'])
    
    # Create memory_topics (M2M)
    op.create_table(
        'memory_topics',
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('memory_items.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('topics.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('confidence', sa.Float, default=0.5),
        sa.Column('assigned_by', sa.String(50), default='llm'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_memory_topics_topic', 'memory_topics', ['topic_id'])
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('agent', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_messages_session', 'messages', ['session_id'])
    op.create_index('idx_messages_created', 'messages', ['created_at'])
    
    # Create memory_embeddings table (PGVector)
    op.execute('''
        CREATE TABLE memory_embeddings (
            memory_id UUID PRIMARY KEY REFERENCES memory_items(id) ON DELETE CASCADE,
            embedding vector(1536) NOT NULL,
            model TEXT DEFAULT 'text-embedding-ada-002'
        )
    ''')
    
    # Create HNSW index for fast similarity search
    op.execute('''
        CREATE INDEX idx_memory_embeddings_vector 
        ON memory_embeddings 
        USING hnsw (embedding vector_cosine_ops)
    ''')
    
    # Create memory_relations table (for graph)
    op.create_table(
        'memory_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('memory_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('memory_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float, default=0.5),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_memory_relations_source', 'memory_relations', ['source_id'])
    op.create_index('idx_memory_relations_target', 'memory_relations', ['target_id'])


def downgrade() -> None:
    op.drop_table('memory_relations')
    op.execute('DROP TABLE memory_embeddings')
    op.drop_table('messages')
    op.drop_table('memory_topics')
    op.drop_table('memory_items')
    op.drop_table('sessions')
    op.drop_table('topics')
    op.execute('DROP EXTENSION IF EXISTS vector')
