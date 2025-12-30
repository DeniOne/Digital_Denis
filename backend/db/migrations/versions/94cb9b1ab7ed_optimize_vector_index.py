"""optimize_vector_index

Revision ID: 94cb9b1ab7ed
Revises: 6fe1a9061346
Create Date: 2025-12-31 01:18:06.081579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94cb9b1ab7ed'
down_revision: Union[str, Sequence[str], None] = '6fe1a9061346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing index if any (it might be named idx_memory_embeddings_vector from 001_initial)
    op.execute("DROP INDEX IF EXISTS idx_memory_embeddings_vector")
    
    # Create HNSW index (better for recall and speed)
    # Cosine distance is used because it's standard for OpenAI embeddings
    op.execute("""
        CREATE INDEX idx_memory_embeddings_hnsw 
        ON memory_embeddings 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    
    # Analyze table for query planner
    op.execute("ANALYZE memory_embeddings;")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_memory_embeddings_hnsw")
    # Restore basic index if needed (though 001_initial had hnsw too, 
    # but we might want to go back to exactly what was there)
    op.execute("""
        CREATE INDEX idx_memory_embeddings_vector 
        ON memory_embeddings 
        USING hnsw (embedding vector_cosine_ops)
    """)
