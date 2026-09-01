"""
Create patients table

Revision ID: 002_patients
Revises: 001_create_users_table
Create Date: 2026-08-10

This migration creates the patients table to store patient information.
Each patient has both an internal UUID and a public client_id (e.g., AYU-000001).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_patients'
down_revision = '001_users'
branch_labels = None
depends_on = None


def upgrade():
    """Create patients table."""
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', sa.String(20), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cognito_sub', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(50), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('ix_patients_client_id', 'patients', ['client_id'])
    op.create_index('ix_patients_user_id', 'patients', ['user_id'])
    op.create_index('ix_patients_cognito_sub', 'patients', ['cognito_sub'])
    op.create_index('ix_patients_email', 'patients', ['email'])
    
    # Create foreign key to users table
    op.create_foreign_key(
        'fk_patients_user_id',
        'patients', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    """Drop patients table."""
    op.drop_constraint('fk_patients_user_id', 'patients', type_='foreignkey')
    op.drop_index('ix_patients_email', 'patients')
    op.drop_index('ix_patients_cognito_sub', 'patients')
    op.drop_index('ix_patients_user_id', 'patients')
    op.drop_index('ix_patients_client_id', 'patients')
    op.drop_table('patients')
