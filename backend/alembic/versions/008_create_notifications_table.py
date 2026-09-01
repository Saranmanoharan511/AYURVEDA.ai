"""
create notifications table

Revision ID: 008
Revises: 007
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_notifications'
down_revision = '007_documents'
branch_labels = None
depends_on = None


def upgrade():
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('channel', sa.String(50), nullable=False, default='EMAIL'),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('delivery_status', sa.String(50), nullable=False, default='PENDING', index=True),
        sa.Column('provider_message_id', sa.String(255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('notification_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create index for created_at (not automatically indexed)
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])


def downgrade():
    # Drop index for created_at
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    
    # Drop table
    op.drop_table('notifications')
