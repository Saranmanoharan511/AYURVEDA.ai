"""
Prescription Document Model

This module defines the PrescriptionDocument SQLAlchemy model for the prescription_documents table.
The prescription_documents table stores generated prescription PDFs for consultations.

Table Schema:
- id: UUID primary key
- consultation_id: Foreign key to consultations table
- patient_id: Foreign key to patients table
- doctor_id: Foreign key to doctors table
- s3_object_key: S3 object key for the stored PDF
- original_filename: Original filename of the PDF
- content_type: MIME type of the file (application/pdf)
- file_size: Size of the file in bytes
- generated_at: Timestamp when prescription PDF was generated
"""

from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class PrescriptionDocument(Base):
    """PrescriptionDocument model for storing generated prescription PDFs."""
    
    __tablename__ = "prescription_documents"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    consultation_id = Column(UUID(as_uuid=True), ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # S3 storage information
    s3_object_key = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False, default='application/pdf')
    file_size = Column(BigInteger(), nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PrescriptionDocument(id={self.id}, consultation_id={self.consultation_id})>"
    
    def to_dict(self):
        """Convert prescription document object to dictionary."""
        return {
            "id": str(self.id),
            "consultation_id": str(self.consultation_id),
            "patient_id": str(self.patient_id),
            "doctor_id": str(self.doctor_id),
            "s3_object_key": self.s3_object_key,
            "original_filename": self.original_filename,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None
        }
