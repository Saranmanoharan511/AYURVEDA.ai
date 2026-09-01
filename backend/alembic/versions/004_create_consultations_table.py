"""
Create consultations table

Revision ID: 004_consultations
Revises: 003_create_doctors_table
Create Date: 2026-08-10

This migration creates the consultations table to store consultation information.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_consultations'
down_revision = '003_doctors'
branch_labels = None
depends_on = None


def upgrade():
    """Create consultations table."""
    op.create_table(
        'consultations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('consultation_status', sa.String(50), nullable=False, server_default='APPOINTMENT_BOOKED'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('ix_consultations_patient_id', 'consultations', ['patient_id'])
    op.create_index('ix_consultations_doctor_id', 'consultations', ['doctor_id'])
    op.create_index('ix_consultations_consultation_status', 'consultations', ['consultation_status'])
    op.create_index('ix_consultations_created_at', 'consultations', ['created_at'])
    
    # Create foreign keys
    op.create_foreign_key(
        'fk_consultations_patient_id',
        'consultations', 'patients',
        ['patient_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_consultations_doctor_id',
        'consultations', 'doctors',
        ['doctor_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    """Drop consultations table."""
    op.drop_constraint('fk_consultations_doctor_id', 'consultations', type_='foreignkey')
    op.drop_constraint('fk_consultations_patient_id', 'consultations', type_='foreignkey')
    op.drop_index('ix_consultations_created_at', 'consultations')
    op.drop_index('ix_consultations_consultation_status', 'consultations')
    op.drop_index('ix_consultations_doctor_id', 'consultations')
    op.drop_index('ix_consultations_patient_id', 'consultations')
    op.drop_table('consultations')
