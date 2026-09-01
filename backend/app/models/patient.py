"""
Patient Model

This module defines the Patient SQLAlchemy model for the patients table.
The patients table stores patient information with both an internal UUID
and a public client_id (e.g., AYU-000001).

Table Schema:
- id: UUID primary key
- client_id: Public human-readable identifier (e.g., AYU-000001)
- user_id: Foreign key to users table
- cognito_sub: Cognito user subject
- full_name: Patient full name
- date_of_birth: Patient date of birth
- age: Patient age (calculated or stored)
- gender: Patient gender
- phone: Contact phone number
- email: Contact email
- city: City of residence
- state: State of residence
- created_at: Timestamp when patient was created
- updated_at: Timestamp when patient was last updated
"""

from sqlalchemy import Column, String, Integer, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class Patient(Base):
    """Patient model for storing patient information."""
    
    __tablename__ = "patients"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Public client ID (e.g., AYU-000001)
    client_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Foreign key to users table
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Cognito subject
    cognito_sub = Column(String(255), nullable=False, index=True)
    
    # Personal information
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date(), nullable=True)
    age = Column(Integer(), nullable=True)
    gender = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    
    # Location information
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Patient(id={self.id}, client_id={self.client_id}, full_name={self.full_name})>"
    
    def to_dict(self):
        """Convert patient object to dictionary."""
        return {
            "id": str(self.id),
            "client_id": self.client_id,
            "user_id": str(self.user_id),
            "cognito_sub": self.cognito_sub,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "gender": self.gender,
            "phone": self.phone,
            "email": self.email,
            "city": self.city,
            "state": self.state,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
