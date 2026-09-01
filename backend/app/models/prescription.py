"""
Prescription Model

This module defines the Prescription SQLAlchemy model for the prescriptions table.
The prescriptions table stores individual prescription items for consultations.

Table Schema:
- id: UUID primary key
- consultation_id: Foreign key to consultations table
- patient_id: Foreign key to patients table
- doctor_id: Foreign key to doctors table
- name: Medicine/herbal name (mandatory)
- morning_dosage: Dosage for morning (0, 1, 2, 3)
- afternoon_dosage: Dosage for afternoon (0, 1, 2, 3)
- night_dosage: Dosage for night (0, 1, 2, 3)
- food_timing: When to take (before_food or after_food)
- notes: Additional notes for this prescription item
- created_at: Timestamp when prescription was created
- updated_at: Timestamp when prescription was last updated
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class Prescription(Base):
    """Prescription model for storing individual prescription items."""
    
    __tablename__ = "prescriptions"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    consultation_id = Column(UUID(as_uuid=True), ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Prescription details
    name = Column(String(255), nullable=False)
    morning_dosage = Column(Integer(), nullable=False, default=0)
    afternoon_dosage = Column(Integer(), nullable=False, default=0)
    night_dosage = Column(Integer(), nullable=False, default=0)
    food_timing = Column(String(50), nullable=False)  # 'before_food' or 'after_food'
    notes = Column(Text(), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Prescription(id={self.id}, consultation_id={self.consultation_id}, name={self.name})>"
    
    def to_dict(self):
        """Convert prescription object to dictionary."""
        return {
            "id": str(self.id),
            "consultation_id": str(self.consultation_id),
            "patient_id": str(self.patient_id),
            "doctor_id": str(self.doctor_id),
            "name": self.name,
            "morning_dosage": self.morning_dosage,
            "afternoon_dosage": self.afternoon_dosage,
            "night_dosage": self.night_dosage,
            "food_timing": self.food_timing,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
