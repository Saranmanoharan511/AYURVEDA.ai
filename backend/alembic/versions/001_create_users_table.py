"""
Create users table

Revision ID: 001_users
Revises: 
Create Date: 2026-08-10

This migration creates the users table to store user information
linked to Cognito authentication.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create users table."""
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('cognito_sub', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='patient'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('given_name', sa.String(255), nullable=True),
        sa.Column('family_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('ix_users_cognito_sub', 'users', ['cognito_sub'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_status', 'users', ['status'])


def downgrade():
    """Drop users table."""
    op.drop_index('ix_users_status', 'users')
    op.drop_index('ix_users_role', 'users')
    op.drop_index('ix_users_email', 'users')
    op.drop_index('ix_users_cognito_sub', 'users')
    op.drop_table('users')
