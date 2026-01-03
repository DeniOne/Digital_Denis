"""Add Kaizen Settings to UserSettings

Revision ID: add_kaizen_settings
Revises: add_kaizen_engine
Create Date: 2026-01-03
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'add_kaizen_settings'
down_revision = 'add_kaizen_engine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Kaizen Engine settings columns to user_settings table."""
    
    # Add Kaizen Engine settings columns
    op.add_column(
        'user_settings',
        sa.Column('kaizen_adaptive_ai_enabled', sa.Boolean(), nullable=True, server_default='true')
    )
    op.add_column(
        'user_settings',
        sa.Column('kaizen_show_mirror', sa.Boolean(), nullable=True, server_default='true')
    )
    op.add_column(
        'user_settings',
        sa.Column('kaizen_comparison_period', sa.String(20), nullable=True, server_default='month')
    )


def downgrade() -> None:
    """Remove Kaizen Engine settings columns."""
    
    op.drop_column('user_settings', 'kaizen_comparison_period')
    op.drop_column('user_settings', 'kaizen_show_mirror')
    op.drop_column('user_settings', 'kaizen_adaptive_ai_enabled')
