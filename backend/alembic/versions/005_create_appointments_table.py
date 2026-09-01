"""
Create appointments table

Revision ID: 005_appointments
Revises: 004_create_consultations_table
Create Date: 2026-08-10

This migration creates the appointments table to store appointment information.
Appointments follow a state machine: APPOINTMENT_BOOKED -> WAITING_FOR_MEETING_SCHEDULE 
-> MEETING_SCHEDULED -> WAITING_FOR_CONSULTATION -> CONSULTATION_COMPLETED 
-> WAITING_FOR_DOCTOR_REPORT -> REPORT_UPLOADED -> REPORT_SENT -> CONSULTATION_CLOSED
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_appointments'
down_revision = '004_consultations'
branch_labels = None
depends_on = None


def upgrade():
    """Create appointments table."""
    op.create_table(
        'appointments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('scheduled_time', sa.Time(), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('zoom_meeting_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='APPOINTMENT_BOOKED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('ix_appointments_consultation_id', 'appointments', ['consultation_id'])
    op.create_index('ix_appointments_status', 'appointments', ['status'])
    op.create_index('ix_appointments_scheduled_date', 'appointments', ['scheduled_date'])
    
    # Create foreign key to consultations table
    op.create_foreign_key(
        'fk_appointments_consultation_id',
        'appointments', 'consultations',
        ['consultation_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    """Drop appointments table."""
    op.drop_constraint('fk_appointments_consultation_id', 'appointments', type_='foreignkey')
    op.drop_index('ix_appointments_scheduled_date', 'appointments')
    op.drop_index('ix_appointments_status', 'appointments')
    op.drop_index('ix_appointments_consultation_id', 'appointments')
    op.drop_table('appointments')
