"""
Patient Document Model

This module defines the PatientDocument SQLAlchemy model for the patient_documents table.
The patient_documents table stores patient-uploaded documents such as medical reports,
prescriptions, lab results, and other supporting documents.

Table Schema:
- id: UUID primary key
- patient_id: Foreign key to patients table
- consultation_id: Foreign key to consultations table (optional)
- document_type: Type of document (e.g., medical_report, prescription, lab_results)
- s3_object_key: S3 object key for the stored file
- original_filename: Original filename of the uploaded file
- content_type: MIME type of the file
- file_size: Size of the file in bytes
- upload_status: Status of upload (PENDING, COMPLETED, FAILED)
- processing_status: Status of document processing (PENDING, PROCESSING, COMPLETED, FAILED)
- uploaded_by: Foreign key to users table (who uploaded the document)
- created_at: Timestamp when document was created
- updated_at: Timestamp when document was last updated
"""

from sqlalchemy import Column, String, BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class PatientDocument(Base):
    """PatientDocument model for storing patient-uploaded documents."""
    
    __tablename__ = "patient_documents"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    consultation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Document information
    document_type = Column(String(100), nullable=False, index=True)
    
    # S3 storage information
    s3_object_key = Column(String(500), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger(), nullable=True)
    
    # Status tracking
    # upload_status: PENDING, COMPLETED, FAILED
    upload_status = Column(String(50), nullable=False, default='PENDING', index=True)
    # processing_status: PENDING, PROCESSING, COMPLETED, FAILED, AVAILABLE_FOR_RAG
    processing_status = Column(String(50), nullable=False, default='PENDING', index=True)
    
    # Document metadata (JSONB for flexible metadata storage)
    document_metadata = Column(JSONB(), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PatientDocument(id={self.id}, patient_id={self.patient_id}, document_type={self.document_type})>"
    
    def to_dict(self):
        """Convert patient document object to dictionary."""
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "consultation_id": str(self.consultation_id) if self.consultation_id else None,
            "document_type": self.document_type,
            "s3_object_key": self.s3_object_key,
            "original_filename": self.original_filename,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "upload_status": self.upload_status,
            "processing_status": self.processing_status,
            "metadata": self.document_metadata,
            "uploaded_by": str(self.uploaded_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
