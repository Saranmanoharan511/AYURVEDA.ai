"""
Notification Model

This module defines the Notification SQLAlchemy model for the notifications table.
The notifications table stores notification records for various events such as
consultation bookings, meeting schedules, report uploads, and follow-up reminders.

Table Schema:
- id: UUID primary key
- user_id: Foreign key to users table (recipient of notification)
- event_type: Type of event (e.g., CONSULTATION_BOOKED, MEETING_SCHEDULED, REPORT_UPLOADED)
- channel: Notification channel (e.g., EMAIL, SMS)
- recipient_email: Email address of the recipient
- subject: Email subject line
- body: Email body content
- delivery_status: Status of delivery (PENDING, SENT, FAILED)
- provider_message_id: ID from the email provider (e.g., SES message ID)
- error_message: Error message if delivery failed
- metadata: Additional JSON metadata about the notification
- created_at: Timestamp when notification was created
- sent_at: Timestamp when notification was sent
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class Notification(Base):
    """Notification model for storing notification records."""
    
    __tablename__ = "notifications"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Notification information
    event_type = Column(String(100), nullable=False, index=True)
    channel = Column(String(50), nullable=False, default='EMAIL')
    
    # Email details
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    body = Column(Text(), nullable=True)
    
    # Delivery tracking
    delivery_status = Column(String(50), nullable=False, default='PENDING', index=True)
    provider_message_id = Column(String(255), nullable=True)
    error_message = Column(Text(), nullable=True)
    
    # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    notification_metadata = Column(JSONB(), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, event_type={self.event_type}, delivery_status={self.delivery_status})>"
    
    def to_dict(self):
        """Convert notification object to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_type": self.event_type,
            "channel": self.channel,
            "recipient_email": self.recipient_email,
            "subject": self.subject,
            "body": self.body,
            "delivery_status": self.delivery_status,
            "provider_message_id": self.provider_message_id,
            "error_message": self.error_message,
            "metadata": self.notification_metadata,  # Keep 'metadata' in API response
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None
        }
