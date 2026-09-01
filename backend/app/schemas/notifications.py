"""
Notification Schemas

Pydantic schemas for notification-related operations including:
- Email notification creation
- Notification status tracking
- SQS message schemas for background processing
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# Notification Schemas
class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    user_id: UUID
    event_type: str = Field(..., description="Type of event (e.g., CONSULTATION_BOOKED, MEETING_SCHEDULED, REPORT_UPLOADED)")
    channel: str = Field(default="EMAIL", description="Notification channel (EMAIL, SMS)")
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    subject: Optional[str] = Field(None, description="Email subject line")
    body: Optional[str] = Field(None, description="Email body content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    delivery_status: Optional[str] = Field(None, description="Delivery status (PENDING, SENT, FAILED)")
    provider_message_id: Optional[str] = Field(None, description="Provider message ID")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    sent_at: Optional[datetime] = Field(None, description="Timestamp when sent")


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: UUID
    user_id: UUID
    event_type: str
    channel: str
    recipient_email: str
    subject: Optional[str]
    body: Optional[str]
    delivery_status: str
    provider_message_id: Optional[str]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


# SQS Message Schemas for Email Worker
class EmailMessage(BaseModel):
    """Schema for email messages sent to SQS queue."""
    user_id: UUID
    event_type: str
    recipient_email: EmailStr
    subject: str
    body: str
    metadata: Optional[Dict[str, Any]] = None


# Event-specific notification schemas
class ConsultationBookingNotification(BaseModel):
    """Schema for consultation booking notification."""
    user_id: UUID
    patient_name: str
    patient_email: EmailStr
    consultation_id: UUID
    reason: str
    booked_at: datetime


class MeetingScheduledNotification(BaseModel):
    """Schema for meeting scheduled notification."""
    user_id: UUID
    patient_name: str
    patient_email: EmailStr
    doctor_name: str
    consultation_id: UUID
    scheduled_date: str
    scheduled_time: str
    timezone: str
    zoom_meeting_url: Optional[str] = None


class ReportUploadedNotification(BaseModel):
    """Schema for report uploaded notification."""
    user_id: UUID
    patient_name: str
    patient_email: EmailStr
    doctor_name: str
    consultation_id: UUID
    report_type: str
    report_filename: str
    uploaded_at: datetime
