"""
create prescriptions table

Revision ID: 014
Revises: 013_add_upload_status_to_reports
Create Date: 2026-08-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_prescriptions'
down_revision = '013_upload_status'
branch_labels = None
depends_on = None


def upgrade():
    # Create prescriptions table
    op.create_table(
        'prescriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('morning_dosage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('afternoon_dosage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('night_dosage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('food_timing', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create indexes for created_at and updated_at (not automatically indexed)
    op.create_index('ix_prescriptions_created_at', 'prescriptions', ['created_at'])
    op.create_index('ix_prescriptions_updated_at', 'prescriptions', ['updated_at'])


def downgrade():
    # Drop indexes for created_at and updated_at
    op.drop_index('ix_prescriptions_created_at', table_name='prescriptions')
    op.drop_index('ix_prescriptions_updated_at', table_name='prescriptions')
    
    # Drop table
    op.drop_table('prescriptions')
