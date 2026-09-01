"""
Report Model

This module defines the Report SQLAlchemy model for the reports table.
The reports table stores doctor-generated reports for consultations,
including prescription PDFs, medical reports, and other documents uploaded by doctors.

Table Schema:
- id: UUID primary key
- consultation_id: Foreign key to consultations table
- patient_id: Foreign key to patients table
- report_type: Type of report (e.g., prescription, medical_report, lab_results)
- s3_object_key: S3 object key for the stored file
- original_filename: Original filename of the uploaded file
- content_type: MIME type of the file
- file_size: Size of the file in bytes
- upload_status: Status of upload (PENDING, COMPLETED, FAILED)
- processing_status: Status of document processing (PENDING, PROCESSING, COMPLETED, FAILED, AVAILABLE_FOR_RAG)
- uploaded_by: Foreign key to users table (who uploaded the report)
- uploaded_at: Timestamp when report was uploaded
"""

from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class Report(Base):
    """Report model for storing doctor-generated consultation reports."""
    
    __tablename__ = "reports"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    consultation_id = Column(UUID(as_uuid=True), ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True)
    
    # Report information
    report_type = Column(String(100), nullable=False, index=True)
    
    # S3 storage information
    s3_object_key = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger(), nullable=True)
    
    # Status tracking
    # upload_status: PENDING, COMPLETED, FAILED
    upload_status = Column(String(50), nullable=False, server_default='PENDING', default='PENDING', index=True)
    # processing_status: PENDING, PROCESSING, COMPLETED, FAILED, AVAILABLE_FOR_RAG
    processing_status = Column(String(50), nullable=False, server_default='PENDING', default='PENDING', index=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Report(id={self.id}, consultation_id={self.consultation_id}, report_type={self.report_type})>"
    
    def to_dict(self):
        """Convert report object to dictionary."""
        return {
            "id": str(self.id),
            "consultation_id": str(self.consultation_id),
            "patient_id": str(self.patient_id),
            "report_type": self.report_type,
            "s3_object_key": self.s3_object_key,
            "original_filename": self.original_filename,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "upload_status": self.upload_status,
            "processing_status": self.processing_status,
            "uploaded_by": str(self.uploaded_by),
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }
