"""
Document Schemas

Pydantic schemas for document-related operations including:
- Patient document upload and metadata
- Report upload and metadata
- Pre-signed URL requests
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# Patient Document Schemas
class PatientDocumentCreate(BaseModel):
    """Schema for creating a patient document."""
    patient_id: UUID
    consultation_id: Optional[UUID] = None
    document_type: str = Field(..., description="Type of document (e.g., medical_report, prescription, lab_results)")
    original_filename: str = Field(..., description="Original filename of the uploaded file")
    content_type: Optional[str] = Field(None, description="MIME type of the file")
    file_size: Optional[int] = Field(None, description="Size of the file in bytes")


class PatientDocumentUpdate(BaseModel):
    """Schema for updating a patient document."""
    upload_status: Optional[str] = Field(None, description="Status of upload (PENDING, COMPLETED, FAILED)")
    processing_status: Optional[str] = Field(None, description="Status of processing (PENDING, PROCESSING, COMPLETED, FAILED)")


class PatientDocumentResponse(BaseModel):
    """Schema for patient document response."""
    id: UUID
    patient_id: UUID
    consultation_id: Optional[UUID]
    document_type: str
    s3_object_key: str
    original_filename: str
    content_type: Optional[str]
    file_size: Optional[int]
    upload_status: str
    processing_status: str
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Report Schemas
class ReportCreate(BaseModel):
    """Schema for creating a report."""
    consultation_id: UUID
    patient_id: UUID
    report_type: str = Field(..., description="Type of report (e.g., prescription, medical_report, lab_results)")
    original_filename: str = Field(..., description="Original filename of the uploaded file")
    content_type: Optional[str] = Field(None, description="MIME type of the file")
    file_size: Optional[int] = Field(None, description="Size of the file in bytes")


class ReportResponse(BaseModel):
    """Schema for report response."""
    id: UUID
    consultation_id: UUID
    patient_id: UUID
    report_type: str
    s3_object_key: str
    original_filename: str
    content_type: Optional[str]
    file_size: Optional[int]
    uploaded_by: UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ReportUploadResponse(BaseModel):
    """Schema for report upload response with presigned URL."""
    report_id: UUID = Field(..., description="ID of the created report record")
    upload_url: str = Field(..., description="Pre-signed S3 upload URL for the file")
    object_key: str = Field(..., description="S3 object key for the file")
    expires_in: int = Field(..., description="URL expiration time in seconds")


# Pre-signed URL Schemas
class PresignedUploadURLRequest(BaseModel):
    """Schema for requesting a pre-signed upload URL."""
    filename: str = Field(..., description="Filename to be uploaded")
    content_type: str = Field(..., description="MIME type of the file")
    consultation_id: Optional[UUID] = Field(None, description="Consultation ID if document is consultation-related")
    document_type: str = Field(..., description="Type of document")


class PresignedUploadURLResponse(BaseModel):
    """Schema for pre-signed upload URL response."""
    upload_url: str = Field(..., description="Pre-signed S3 upload URL")
    object_key: str = Field(..., description="S3 object key for the file")
    expires_in: int = Field(..., description="URL expiration time in seconds")


class PresignedDownloadURLRequest(BaseModel):
    """Schema for requesting a pre-signed download URL."""
    object_key: str = Field(..., description="S3 object key to download")


class PresignedDownloadURLResponse(BaseModel):
    """Schema for pre-signed download URL response."""
    download_url: str = Field(..., description="Pre-signed S3 download URL")
    expires_in: int = Field(..., description="URL expiration time in seconds")


# Document Metadata Schemas
class DocumentMetadataCreate(BaseModel):
    """Schema for saving document metadata after successful upload."""
    object_key: str = Field(..., description="S3 object key of the uploaded file")
    original_filename: str = Field(..., description="Original filename")
    content_type: Optional[str] = Field(None, description="MIME type")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    consultation_id: Optional[UUID] = Field(None, description="Consultation ID if applicable")
    document_type: str = Field(..., description="Type of document")


class DocumentMetadataResponse(BaseModel):
    """Schema for document metadata response."""
    id: UUID
    patient_id: UUID
    consultation_id: Optional[UUID]
    document_type: str
    s3_object_key: str
    original_filename: str
    content_type: Optional[str]
    file_size: Optional[int]
    upload_status: str
    processing_status: str
    uploaded_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True
