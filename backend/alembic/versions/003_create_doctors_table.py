"""
Create doctors table

Revision ID: 003_doctors
Revises: 002_create_patients_table
Create Date: 2026-08-10

This migration creates the doctors table to store doctor information.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_doctors'
down_revision = '002_patients'
branch_labels = None
depends_on = None


def upgrade():
    """Create doctors table."""
    op.create_table(
        'doctors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cognito_sub', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('qualifications', sa.Text(), nullable=True),
        sa.Column('specialization', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('ix_doctors_user_id', 'doctors', ['user_id'])
    op.create_index('ix_doctors_cognito_sub', 'doctors', ['cognito_sub'])
    op.create_index('ix_doctors_status', 'doctors', ['status'])
    
    # Create foreign key to users table
    op.create_foreign_key(
        'fk_doctors_user_id',
        'doctors', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    """Drop doctors table."""
    op.drop_constraint('fk_doctors_user_id', 'doctors', type_='foreignkey')
    op.drop_index('ix_doctors_status', 'doctors')
    op.drop_index('ix_doctors_cognito_sub', 'doctors')
    op.drop_index('ix_doctors_user_id', 'doctors')
    op.drop_table('doctors')
