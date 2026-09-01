"""
User Model

This module defines the User SQLAlchemy model for the users table.
The users table stores user information linked to Cognito authentication.

Table Schema:
- id: UUID primary key
- cognito_sub: Cognito user subject (unique identifier from Cognito)
- email: User email address
- role: User role (patient, doctor, admin)
- status: User status (active, inactive, blocked)
- given_name: User first name
- family_name: User last name
- created_at: Timestamp when user was created
- updated_at: Timestamp when user was last updated
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class User(Base):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Cognito subject - unique identifier from Cognito
    cognito_sub = Column(String(255), unique=True, nullable=False, index=True)
    
    # User email
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # User role (patient, doctor, admin)
    role = Column(String(50), nullable=False, default="patient")
    
    # User status (active, inactive, blocked)
    status = Column(String(50), nullable=False, default="active")
    
    # User name
    given_name = Column(String(255), nullable=True)
    family_name = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, status={self.status})>"
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            "id": str(self.id),
            "cognito_sub": self.cognito_sub,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
