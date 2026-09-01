"""
create audit_logs table

Revision ID: 011
Revises: 010
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_audit'
down_revision = '010_chunks'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('actor_role', sa.String(50), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(100), nullable=False, index=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resource_identifier', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('audit_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, index=True),
    )


def downgrade():
    # Drop table
    op.drop_table('audit_logs')
