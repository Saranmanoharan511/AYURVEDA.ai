"""
ConsultationNote Model

This module defines the ConsultationNote SQLAlchemy model for the consultation_notes table.
The consultation_notes table stores doctor notes from consultations including diagnosis,
ayurvedic assessment, medicines, lifestyle advice, diet plan, and follow-up instructions.

Table Schema:
- id: UUID primary key
- consultation_id: Foreign key to consultations table
- doctor_id: Foreign key to doctors table
- diagnosis: Doctor's diagnosis
- ayurvedic_assessment: Ayurvedic assessment of the patient
- medicines: Prescribed medicines
- lifestyle_advice: Lifestyle recommendations
- diet_plan: Diet recommendations
- follow_up_instructions: Follow-up instructions for the patient
- created_at: Timestamp when note was created
- updated_at: Timestamp when note was last updated
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class ConsultationNote(Base):
    """ConsultationNote model for storing consultation notes."""
    
    __tablename__ = "consultation_notes"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    consultation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Consultation note content
    diagnosis = Column(Text(), nullable=True)
    ayurvedic_assessment = Column(Text(), nullable=True)
    medicines = Column(Text(), nullable=True)
    lifestyle_advice = Column(Text(), nullable=True)
    diet_plan = Column(Text(), nullable=True)
    follow_up_instructions = Column(Text(), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ConsultationNote(id={self.id}, consultation_id={self.consultation_id}, doctor_id={self.doctor_id})>"
    
    def to_dict(self):
        """Convert consultation note object to dictionary."""
        return {
            "id": str(self.id),
            "consultation_id": str(self.consultation_id),
            "doctor_id": str(self.doctor_id),
            "diagnosis": self.diagnosis,
            "ayurvedic_assessment": self.ayurvedic_assessment,
            "medicines": self.medicines,
            "lifestyle_advice": self.lifestyle_advice,
            "diet_plan": self.diet_plan,
            "follow_up_instructions": self.follow_up_instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
