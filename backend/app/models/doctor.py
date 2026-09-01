"""
Doctor Model

This module defines the Doctor SQLAlchemy model for the doctors table.
The doctors table stores doctor information linked to user authentication.

Table Schema:
- id: UUID primary key
- user_id: Foreign key to users table
- cognito_sub: Cognito user subject
- name: Doctor name
- qualifications: Doctor qualifications (degrees, certifications)
- specialization: Doctor specialization (e.g., Ayurveda, Panchakarma)
- status: Doctor status (active, inactive)
- created_at: Timestamp when doctor was created
- updated_at: Timestamp when doctor was last updated
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class Doctor(Base):
    """Doctor model for storing doctor information."""
    
    __tablename__ = "doctors"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to users table
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Cognito subject
    cognito_sub = Column(String(255), nullable=False, index=True)
    
    # Doctor information
    name = Column(String(255), nullable=False)
    qualifications = Column(Text(), nullable=True)
    specialization = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default="active", index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Doctor(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self):
        """Convert doctor object to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "cognito_sub": self.cognito_sub,
            "name": self.name,
            "qualifications": self.qualifications,
            "specialization": self.specialization,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
