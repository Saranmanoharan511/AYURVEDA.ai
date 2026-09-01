"""
Appointment Model

This module defines the Appointment SQLAlchemy model for the appointments table.
The appointments table stores appointment information linked to consultations.
Appointments follow a state machine: APPOINTMENT_BOOKED -> WAITING_FOR_MEETING_SCHEDULE 
-> MEETING_SCHEDULED -> WAITING_FOR_CONSULTATION -> CONSULTATION_COMPLETED 
-> WAITING_FOR_DOCTOR_REPORT -> REPORT_UPLOADED -> REPORT_SENT -> CONSULTATION_CLOSED

Table Schema:
- id: UUID primary key
- consultation_id: Foreign key to consultations table
- scheduled_date: Scheduled date for the appointment
- scheduled_time: Scheduled time for the appointment
- timezone: Timezone for the appointment
- zoom_meeting_url: Zoom meeting URL for the consultation
- status: Appointment status (follows state machine)
- created_at: Timestamp when appointment was created
- updated_at: Timestamp when appointment was last updated
"""

from sqlalchemy import Column, String, DateTime, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class Appointment(Base):
    """Appointment model for storing appointment information."""
    
    __tablename__ = "appointments"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to consultations table
    consultation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Appointment scheduling details
    scheduled_date = Column(Date(), nullable=True, index=True)
    scheduled_time = Column(Time(), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Zoom meeting details
    zoom_meeting_url = Column(String(500), nullable=True)
    
    # Status follows the state machine
    status = Column(String(50), nullable=False, default="APPOINTMENT_BOOKED", index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, consultation_id={self.consultation_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert appointment object to dictionary."""
        return {
            "id": str(self.id),
            "consultation_id": str(self.consultation_id),
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "timezone": self.timezone,
            "zoom_meeting_url": self.zoom_meeting_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
