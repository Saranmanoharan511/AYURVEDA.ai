"""
create patient_documents table

Revision ID: 007
Revises: 006
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_documents'
down_revision = '006_notes'
branch_labels = None
depends_on = None


def upgrade():
    # Create patient_documents table
    op.create_table(
        'patient_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('document_type', sa.String(100), nullable=False, index=True),
        sa.Column('s3_object_key', sa.String(500), nullable=False, unique=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('upload_status', sa.String(50), nullable=False, default='PENDING', index=True),
        sa.Column('processing_status', sa.String(50), nullable=False, default='PENDING', index=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True),
        sa.Column('document_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
    )
    
    # Create index for created_at (not automatically indexed)
    op.create_index('ix_patient_documents_created_at', 'patient_documents', ['created_at'])


def downgrade():
    # Drop index for created_at
    op.drop_index('ix_patient_documents_created_at', table_name='patient_documents')
    
    # Drop table
    op.drop_table('patient_documents')
