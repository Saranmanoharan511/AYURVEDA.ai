"""
create document_chunks table with pgvector support

Revision ID: 010
Revises: 009
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_chunks'
down_revision = '009_reports'
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create document_chunks table with proper pgvector support
    # Using vector(1024) for Titan V2 embeddings (configurable via EMBEDDING_DIMENSIONS)
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patient_documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),  # Fallback for environments without pgvector
        sa.Column('chunk_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('source_filename', sa.String(255), nullable=True),
        sa.Column('document_type', sa.String(100), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create indexes for chunk_index and created_at (not automatically indexed)
    op.create_index('ix_document_chunks_chunk_index', 'document_chunks', ['chunk_index'])
    op.create_index('ix_document_chunks_created_at', 'document_chunks', ['created_at'])
    
    # Try to add vector column for pgvector (if extension is available)
    # This provides real vector similarity search capabilities
    try:
        # Using vector(1024) for Titan V2 embeddings
        op.execute("ALTER TABLE document_chunks ADD COLUMN embedding_vector vector(1024)")
        # Create HNSW index for efficient vector similarity search
        op.execute("CREATE INDEX ix_document_chunks_embedding_vector ON document_chunks USING hnsw (embedding_vector vector_cosine_ops)")
    except Exception:
        # If pgvector is not available, we'll use the FLOAT[] fallback
        pass


def downgrade():
    # Drop vector index if it exists
    try:
        op.drop_index('ix_document_chunks_embedding_vector', table_name='document_chunks')
    except Exception:
        pass
    
    # Drop vector column if it exists
    try:
        op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding_vector")
    except Exception:
        pass
    
    # Drop indexes for chunk_index and created_at
    op.drop_index('ix_document_chunks_created_at', table_name='document_chunks')
    op.drop_index('ix_document_chunks_chunk_index', table_name='document_chunks')
    
    # Drop table
    op.drop_table('document_chunks')
    
    # Note: We don't drop the pgvector extension as it may be used by other tables
    # op.execute('DROP EXTENSION IF EXISTS vector')
