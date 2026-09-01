"""
create prescription_documents table

Revision ID: 015
Revises: 014_create_prescriptions_table
Create Date: 2026-08-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_prescription_docs'
down_revision = '014_prescriptions'
branch_labels = None
depends_on = None


def upgrade():
    # Create prescription_documents table
    op.create_table(
        'prescription_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('s3_object_key', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False, server_default='application/pdf'),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )


def downgrade():
    # Drop table
    op.drop_table('prescription_documents')
