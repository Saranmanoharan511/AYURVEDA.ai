"""
Create consultation_notes table

Revision ID: 006_notes
Revises: 005_create_appointments_table
Create Date: 2026-08-10

This migration creates the consultation_notes table to store doctor notes
from consultations including diagnosis, ayurvedic assessment, medicines,
lifestyle advice, diet plan, and follow-up instructions.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_notes'
down_revision = '005_appointments'
branch_labels = None
depends_on = None


def upgrade():
    """Create consultation_notes table."""
    op.create_table(
        'consultation_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('diagnosis', sa.Text(), nullable=True),
        sa.Column('ayurvedic_assessment', sa.Text(), nullable=True),
        sa.Column('medicines', sa.Text(), nullable=True),
        sa.Column('lifestyle_advice', sa.Text(), nullable=True),
        sa.Column('diet_plan', sa.Text(), nullable=True),
        sa.Column('follow_up_instructions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('ix_consultation_notes_consultation_id', 'consultation_notes', ['consultation_id'])
    op.create_index('ix_consultation_notes_doctor_id', 'consultation_notes', ['doctor_id'])
    
    # Create foreign keys
    op.create_foreign_key(
        'fk_consultation_notes_consultation_id',
        'consultation_notes', 'consultations',
        ['consultation_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_consultation_notes_doctor_id',
        'consultation_notes', 'doctors',
        ['doctor_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    """Drop consultation_notes table."""
    op.drop_constraint('fk_consultation_notes_doctor_id', 'consultation_notes', type_='foreignkey')
    op.drop_constraint('fk_consultation_notes_consultation_id', 'consultation_notes', type_='foreignkey')
    op.drop_index('ix_consultation_notes_doctor_id', 'consultation_notes')
    op.drop_index('ix_consultation_notes_consultation_id', 'consultation_notes')
    op.drop_table('consultation_notes')
