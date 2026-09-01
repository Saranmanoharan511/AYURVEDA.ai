"""Add upload_status to reports table

Revision ID: 013
Revises: 011_create_audit_logs_table
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_upload_status'
down_revision = '011_audit'
branch_labels = None
depends_on = None


def upgrade():
    """Add upload_status column to reports table."""
    op.add_column('reports', sa.Column('upload_status', sa.String(length=50), nullable=False, server_default='PENDING'))
    
    # Update existing records to have COMPLETED status
    op.execute("UPDATE reports SET upload_status = 'COMPLETED' WHERE upload_status IS NULL")


def downgrade():
    """Remove upload_status column from reports table."""
    op.drop_column('reports', 'upload_status')
