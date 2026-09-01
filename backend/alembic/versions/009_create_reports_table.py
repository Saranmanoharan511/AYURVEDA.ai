"""
create reports table

Revision ID: 009
Revises: 008
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_reports'
down_revision = '008_notifications'
branch_labels = None
depends_on = None


def upgrade():
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True),
        sa.Column('report_type', sa.String(100), nullable=False, index=True),
        sa.Column('s3_object_key', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create index for uploaded_at (not automatically indexed)
    op.create_index('ix_reports_uploaded_at', 'reports', ['uploaded_at'])


def downgrade():
    # Drop index for uploaded_at
    op.drop_index('ix_reports_uploaded_at', table_name='reports')
    
    # Drop table
    op.drop_table('reports')
