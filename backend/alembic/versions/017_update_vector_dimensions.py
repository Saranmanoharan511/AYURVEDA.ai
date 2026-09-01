"""
update vector dimensions for Titan V2 embeddings

Revision ID: 017
Revises: 016_add_processing_status_to_reports
Create Date: 2026-08-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_vector_dims'
down_revision = '016_processing_status'
branch_labels = None
depends_on = None


def upgrade():
    # Update vector dimensions from 1536 (OpenAI) to 1024 (Titan V2)
    # This requires dropping and recreating the vector column and index
    
    # Drop existing HNSW index if it exists
    try:
        op.drop_index('ix_document_chunks_embedding_vector', table_name='document_chunks')
    except Exception:
        # Index might not exist if pgvector wasn't available
        pass
    
    # Drop existing vector column if it exists
    try:
        op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding_vector")
    except Exception:
        # Column might not exist
        pass
    
    # Add vector column with new dimensions (1024 for Titan V2)
    try:
        op.execute("ALTER TABLE document_chunks ADD COLUMN embedding_vector vector(1024)")
        # Create HNSW index for efficient vector similarity search
        op.execute("CREATE INDEX ix_document_chunks_embedding_vector ON document_chunks USING hnsw (embedding_vector vector_cosine_ops)")
    except Exception:
        # If pgvector is not available, we'll use the FLOAT[] fallback
        pass


def downgrade():
    # Revert back to 1536 dimensions (OpenAI)
    
    # Drop existing HNSW index if it exists
    try:
        op.drop_index('ix_document_chunks_embedding_vector', table_name='document_chunks')
    except Exception:
        pass
    
    # Drop existing vector column if it exists
    try:
        op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding_vector")
    except Exception:
        pass
    
    # Add vector column with original dimensions (1536 for OpenAI)
    try:
        op.execute("ALTER TABLE document_chunks ADD COLUMN embedding_vector vector(1536)")
        op.execute("CREATE INDEX ix_document_chunks_embedding_vector ON document_chunks USING hnsw (embedding_vector vector_cosine_ops)")
    except Exception:
        # If pgvector is not available, we'll use the FLOAT[] fallback
        pass
