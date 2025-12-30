"""add_topic_ownership_and_auto_gen

Revision ID: 8da9b938e2d4
Revises: 94cb9b1ab7ed
Create Date: 2025-12-31 01:26:10.692243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8da9b938e2d4'
down_revision: Union[str, Sequence[str], None] = '94cb9b1ab7ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns if they don't exist
    # (Altering columns to nullable=True first, then populated, then final state if needed)
    op.add_column('topics', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('topics', sa.Column('is_auto_generated', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('topics', sa.Column('cluster_id', sa.String(length=100), nullable=True))
    
    # Create foreign key
    op.create_foreign_key('fk_topics_user', 'topics', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    # Create indexes with IF NOT EXISTS to avoid crashes
    op.execute('CREATE INDEX IF NOT EXISTS idx_topics_user ON topics (user_id)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_topics_slug ON topics (slug)')


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_topics_slug', table_name='topics')
    op.drop_index('idx_topics_user', table_name='topics')
    
    # Remove foreign key
    op.drop_constraint('fk_topics_user', 'topics', type_='foreignkey')
    
    # Remove columns
    op.drop_column('topics', 'cluster_id')
    op.drop_column('topics', 'is_auto_generated')
    op.drop_column('topics', 'user_id')
