"""
Consultation Model

This module defines the Consultation SQLAlchemy model for the consultations table.
The consultations table stores consultation information linking patients and doctors.

Table Schema:
- id: UUID primary key
- patient_id: Foreign key to patients table
- doctor_id: Foreign key to doctors table
- reason: Reason for consultation
- description: Detailed description of the consultation request
- consultation_status: Status of consultation (APPOINTMENT_BOOKED, WAITING_FOR_MEETING_SCHEDULE, 
                       MEETING_SCHEDULED, WAITING_FOR_CONSULTATION, CONSULTATION_COMPLETED,
                       WAITING_FOR_DOCTOR_REPORT, REPORT_UPLOADED, REPORT_SENT, CONSULTATION_CLOSED)
- started_at: Timestamp when consultation started
- completed_at: Timestamp when consultation completed
- created_at: Timestamp when consultation was created
- updated_at: Timestamp when consultation was last updated
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class Consultation(Base):
    """Consultation model for storing consultation information."""
    
    __tablename__ = "consultations"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Consultation details
    reason = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)
    
    # Status follows the appointment state machine
    consultation_status = Column(String(50), nullable=False, default="APPOINTMENT_BOOKED", index=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Consultation(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, status={self.consultation_status})>"
    
    def to_dict(self):
        """Convert consultation object to dictionary."""
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "doctor_id": str(self.doctor_id),
            "reason": self.reason,
            "description": self.description,
            "consultation_status": self.consultation_status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
