"""
Authentication Schemas

This module defines Pydantic schemas for authentication-related requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserRegister(BaseModel):
    """Schema for user registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    given_name: str = Field(..., min_length=1, max_length=255)
    family_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="patient", description="User role: patient, doctor, or admin")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "patient@example.com",
                "password": "securePassword123",
                "given_name": "John",
                "family_name": "Doe",
                "role": "patient"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "patient@example.com",
                "password": "securePassword123"
            }
        }


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    id_token: str
    refresh_token: Optional[str] = None  # Optional - not returned on refresh
    expires_in: int
    token_type: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJSUzI1NiIs...",
                "id_token": "eyJhbGciOiJSUzI1NiIs...",
                "refresh_token": "eyJjdHkiOiJKV1QiLCJlb...",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    role: str
    status: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "patient@example.com",
                "role": "patient",
                "status": "active",
                "given_name": "John",
                "family_name": "Doe",
                "created_at": "2026-08-10T12:00:00Z",
                "updated_at": "2026-08-10T12:00:00Z"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJjdHkiOiJKV1QiLCJlb..."
            }
        }


class MessageResponse(BaseModel):
    """Schema for simple message response."""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation successful"
            }
        }
