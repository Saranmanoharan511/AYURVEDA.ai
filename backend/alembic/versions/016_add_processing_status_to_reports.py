"""Add processing_status to reports table

Revision ID: 016
Revises: 015_create_prescription_documents_table
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016_processing_status'
down_revision = '015_prescription_docs'
branch_labels = None
depends_on = None


def upgrade():
    """Add processing_status column to reports table."""
    # Add processing_status column
    op.add_column('reports', sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='PENDING'))
    
    # Create index on processing_status
    op.create_index('ix_reports_processing_status', 'reports', ['processing_status'])
    
    # Update existing records to have PENDING status
    op.execute("UPDATE reports SET processing_status = 'PENDING' WHERE processing_status IS NULL")


def downgrade():
    """Remove processing_status column from reports table."""
    # Drop the index first
    op.drop_index('ix_reports_processing_status', table_name='reports')
    
    # Remove the column
    op.drop_column('reports', 'processing_status')
