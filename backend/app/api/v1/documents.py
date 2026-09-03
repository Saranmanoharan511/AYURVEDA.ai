"""
Documents API Router

FastAPI router for document-related operations including:
- Pre-signed S3 upload URL generation
- Document metadata saving
- Pre-signed S3 download URL generation
- Report upload endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from uuid import UUID
import os
import logging
from datetime import datetime

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_patient, require_doctor, require_admin
from app.core.authorization import get_authorized_patient_ids, check_doctor_patient_access
from app.services.s3_service import s3_service
from app.services.sqs_service import sqs_service
from app.models.user import User
from app.models.patient_document import PatientDocument
from app.models.report import Report
from app.models.notification import Notification
from app.schemas.documents import (
    PresignedUploadURLRequest,
    PresignedUploadURLResponse,
    PresignedDownloadURLRequest,
    PresignedDownloadURLResponse,
    DocumentMetadataCreate,
    DocumentMetadataResponse,
    PatientDocumentCreate,
    PatientDocumentResponse,
    ReportCreate,
    ReportResponse,
    ReportUploadResponse
)
from app.schemas.notifications import NotificationCreate
from app.schemas.document_processing import (
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload-url", response_model=PresignedUploadURLResponse)
async def get_presigned_upload_url(
    request: PresignedUploadURLRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a pre-signed S3 upload URL for secure direct-to-S3 file upload.
    
    This endpoint verifies user permissions and generates a short-lived
    pre-signed URL that allows the browser to upload directly to S3.
    """
    try:
        # Generate unique S3 object key
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        object_key = f"documents/{current_user.id}/{timestamp}_{request.filename}"
        
        # Generate pre-signed upload URL
        upload_url = s3_service.generate_presigned_upload_url(
            object_key=object_key,
            content_type=request.content_type,
            expires_in=3600  # 1 hour
        )
        
        return PresignedUploadURLResponse(
            upload_url=upload_url,
            object_key=object_key,
            expires_in=3600
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


@router.post("/metadata", response_model=DocumentMetadataResponse)
async def save_document_metadata(
    metadata: DocumentMetadataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save document metadata to PostgreSQL after successful S3 upload.
    
    This endpoint should be called after the file is successfully uploaded to S3
    using the pre-signed URL. It creates a record in the patient_documents table.
    """
    try:
        # Get authorized patient IDs based on user role
        authorized_patient_ids = get_authorized_patient_ids(current_user, db)
        if not authorized_patient_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No authorized patients found"
            )
        patient_id = authorized_patient_ids[0]  # Use first authorized patient ID
        
        # Create patient document record
        document = PatientDocument(
            patient_id=patient_id,
            consultation_id=metadata.consultation_id,
            document_type=metadata.document_type,
            s3_object_key=metadata.object_key,
            original_filename=metadata.original_filename,
            content_type=metadata.content_type,
            file_size=metadata.file_size,
            upload_status='COMPLETED',
            processing_status='PENDING',
            uploaded_by=current_user.id
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Queue document processing job (for Sprint 5)
        try:
            sqs_service.send_document_processing_message(
                document_id=str(document.id),
                patient_id=str(patient_id),
                s3_object_key=metadata.object_key,
                document_type=metadata.document_type,
                consultation_id=str(metadata.consultation_id) if metadata.consultation_id else None
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to queue document processing: {str(e)}")
        
        return DocumentMetadataResponse(
            id=document.id,
            patient_id=document.patient_id,
            consultation_id=document.consultation_id,
            document_type=document.document_type,
            s3_object_key=document.s3_object_key,
            original_filename=document.original_filename,
            content_type=document.content_type,
            file_size=document.file_size,
            upload_status=document.upload_status,
            processing_status=document.processing_status,
            uploaded_by=document.uploaded_by,
            created_at=document.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document metadata: {str(e)}"
        )


@router.post("/download-url", response_model=PresignedDownloadURLResponse)
async def get_presigned_download_url(
    request: PresignedDownloadURLRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a pre-signed S3 download URL for secure file download.
    
    This endpoint verifies user permissions and generates a short-lived
    pre-signed URL that allows the browser to download directly from S3.
    """
    try:
        # Verify the user has access to this document
        document = db.query(PatientDocument).filter(
            PatientDocument.s3_object_key == request.object_key
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check authorization
        authorized_patient_ids = get_authorized_patient_ids(current_user, db)
        if current_user.role == 'patient' and document.patient_id not in authorized_patient_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this document"
            )
        
        # Generate pre-signed download URL
        download_url = s3_service.generate_presigned_download_url(
            object_key=request.object_key,
            expires_in=3600  # 1 hour
        )
        
        return PresignedDownloadURLResponse(
            download_url=download_url,
            expires_in=3600
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.post("/reports", response_model=ReportUploadResponse)
async def upload_report(
    report_data: ReportCreate,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """
    Upload a doctor-generated report for a consultation.
    
    This endpoint:
    1. Verifies doctor has access to the patient
    2. Creates a report record in the database
    3. Generates a presigned S3 upload URL for the actual file
    4. Returns both the upload URL and report metadata
    
    The frontend should:
    1. Upload the file to the returned upload_url
    2. Call the report confirmation endpoint after successful upload
    """
    try:
        # Verify doctor has access to the patient
        check_doctor_patient_access(current_user, str(report_data.patient_id), db)
        
        # Verify the consultation belongs to this doctor
        from app.models.doctor import Doctor
        from app.models.consultation import Consultation
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor profile not found")
        
        consultation = db.query(Consultation).filter(
            Consultation.id == report_data.consultation_id,
            Consultation.doctor_id == doctor.id,
            Consultation.patient_id == report_data.patient_id
        ).first()
        
        if not consultation:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this consultation"
            )
        # Generate S3 object key
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        object_key = f"reports/{report_data.consultation_id}/{timestamp}_{report_data.original_filename}"
        
        # Create report record with PENDING status
        report = Report(
            consultation_id=report_data.consultation_id,
            patient_id=report_data.patient_id,
            report_type=report_data.report_type,
            s3_object_key=object_key,
            original_filename=report_data.original_filename,
            content_type=report_data.content_type,
            file_size=report_data.file_size,
            uploaded_by=current_user.id,
            upload_status='PENDING'
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Generate presigned upload URL
        upload_url = s3_service.generate_presigned_upload_url(
            object_key=object_key,
            content_type=report_data.content_type,
            expires_in=3600  # 1 hour
        )
        
        return ReportUploadResponse(
            report_id=report.id,
            upload_url=upload_url,
            object_key=object_key,
            expires_in=3600
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report: {str(e)}"
        )


@router.post("/reports/{report_id}/confirm", response_model=ReportResponse)
async def confirm_report_upload(
    report_id: UUID,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """
    Confirm that a report file has been successfully uploaded to S3.
    
    This endpoint:
    1. Verifies doctor has access to the report's patient
    2. Updates the report status to COMPLETED
    3. Queues an email notification to the patient
    """
    try:
        # Get report record
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Verify doctor has access to the patient
        check_doctor_patient_access(current_user, str(report.patient_id), db)
        
        # Verify the consultation belongs to this doctor
        from app.models.doctor import Doctor
        from app.models.consultation import Consultation
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor profile not found")
        
        consultation = db.query(Consultation).filter(
            Consultation.id == report.consultation_id,
            Consultation.doctor_id == doctor.id
        ).first()
        
        if not consultation:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this consultation"
            )
        
        # Update report status
        report.upload_status = 'COMPLETED'
        report.processing_status = 'PENDING'
        db.commit()
        db.refresh(report)
        
        # Queue document processing for non-prescription reports
        # Prescription PDFs are handled via SQL tool, not RAG
        if report.report_type.lower() != 'prescription':
            try:
                sqs_service.send_document_processing_message(
                    document_id=str(report.id),
                    patient_id=str(report.patient_id),
                    s3_object_key=report.s3_object_key,
                    document_type=report.report_type,
                    consultation_id=str(report.consultation_id),
                    document_source="report"
                )
            except Exception as e:
                # Log error but don't fail the request
                logger.error(f"Failed to queue report processing: {str(e)}")
        
        # Email notification removed - documents will be sent via "Send Documents" button
        
        return ReportResponse(
            id=report.id,
            consultation_id=report.consultation_id,
            patient_id=report.patient_id,
            report_type=report.report_type,
            s3_object_key=report.s3_object_key,
            original_filename=report.original_filename,
            content_type=report.content_type,
            file_size=report.file_size,
            uploaded_by=report.uploaded_by,
            uploaded_at=report.uploaded_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm report upload: {str(e)}"
        )


@router.get("/patient/{patient_id}", response_model=list[PatientDocumentResponse])
async def get_patient_documents(
    patient_id: UUID,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """
    Get all documents for a specific patient (doctor only).
    """
    try:
        # Verify doctor has access to this patient
        if not check_doctor_patient_access(current_user, patient_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this patient's documents"
            )
        
        documents = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id
        ).all()
        
        return [
            PatientDocumentResponse(
                id=doc.id,
                patient_id=doc.patient_id,
                consultation_id=doc.consultation_id,
                document_type=doc.document_type,
                s3_object_key=doc.s3_object_key,
                original_filename=doc.original_filename,
                content_type=doc.content_type,
                file_size=doc.file_size,
                upload_status=doc.upload_status,
                processing_status=doc.processing_status,
                uploaded_by=doc.uploaded_by,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/my-documents", response_model=list[PatientDocumentResponse])
async def get_my_documents(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """
    Get all documents for the current patient.
    """
    try:
        authorized_patient_ids = get_authorized_patient_ids(current_user, db)
        if not authorized_patient_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No authorized patient found"
            )
        patient_id = authorized_patient_ids[0]
        
        documents = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id
        ).all()
        
        return [
            PatientDocumentResponse(
                id=doc.id,
                patient_id=doc.patient_id,
                consultation_id=doc.consultation_id,
                document_type=doc.document_type,
                s3_object_key=doc.s3_object_key,
                original_filename=doc.original_filename,
                content_type=doc.content_type,
                file_size=doc.file_size,
                upload_status=doc.upload_status,
                processing_status=doc.processing_status,
                uploaded_by=doc.uploaded_by,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/consultation/{consultation_id}/patient-uploads", response_model=list[PatientDocumentResponse])
async def get_consultation_patient_uploads(
    consultation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all patient uploaded documents for a specific consultation.
    
    Patients can only access uploads for their own consultations.
    Doctors can access uploads for consultations they are assigned to.
    """
    try:
        from app.models.consultation import Consultation
        from app.models.patient import Patient
        from app.models.doctor import Doctor
        
        # Verify consultation exists
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        # Check authorization
        if current_user.role == 'patient':
            patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
            if not patient or consultation.patient_id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access uploads for this consultation"
                )
        elif current_user.role == 'doctor':
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
            if not doctor or consultation.doctor_id != doctor.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access uploads for this consultation"
                )
        
        # Get patient uploaded documents for this consultation
        documents = db.query(PatientDocument).filter(
            PatientDocument.consultation_id == consultation_id,
            PatientDocument.upload_status == 'COMPLETED'
        ).order_by(PatientDocument.created_at.desc()).all()
        
        # Generate download URLs for each document
        result = []
        for doc in documents:
            try:
                download_url = s3_service.generate_presigned_download_url(
                    object_key=doc.s3_object_key,
                    expires_in=3600
                )
                result.append(PatientDocumentResponse(
                    id=doc.id,
                    patient_id=doc.patient_id,
                    consultation_id=doc.consultation_id,
                    document_type=doc.document_type,
                    s3_object_key=doc.s3_object_key,
                    original_filename=doc.original_filename,
                    content_type=doc.content_type,
                    file_size=doc.file_size,
                    upload_status=doc.upload_status,
                    processing_status=doc.processing_status,
                    uploaded_by=doc.uploaded_by,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    download_url=download_url
                ))
            except Exception as e:
                logger.error(f"Failed to generate download URL for document {doc.id}: {str(e)}")
                # Still include document without download URL
                result.append(PatientDocumentResponse(
                    id=doc.id,
                    patient_id=doc.patient_id,
                    consultation_id=doc.consultation_id,
                    document_type=doc.document_type,
                    s3_object_key=doc.s3_object_key,
                    original_filename=doc.original_filename,
                    content_type=doc.content_type,
                    file_size=doc.file_size,
                    upload_status=doc.upload_status,
                    processing_status=doc.processing_status,
                    uploaded_by=doc.uploaded_by,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    download_url=None
                ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient uploads: {str(e)}"
        )


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_params: DocumentSearchRequest,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """
    Search and filter documents (doctor only).
    
    This endpoint allows doctors to search and filter patient documents
    by various criteria including patient ID, consultation ID, document type,
    processing status, and text search.
    
    For security, doctors must provide a patient_id to search documents.
    """
    try:
        # Require patient_id for doctors to prevent cross-doctor access
        if not search_params.patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id is required for document search"
            )
        
        # Verify doctor has access to this patient
        if not check_doctor_patient_access(current_user, search_params.patient_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this patient's documents"
            )
        
        # Build base query
        query = db.query(PatientDocument)
        
        # Apply filters
        query = query.filter(PatientDocument.patient_id == search_params.patient_id)
        
        if search_params.consultation_id:
            query = query.filter(PatientDocument.consultation_id == search_params.consultation_id)
        
        if search_params.document_type:
            query = query.filter(PatientDocument.document_type == search_params.document_type)
        
        if search_params.processing_status:
            query = query.filter(PatientDocument.processing_status == search_params.processing_status)
        
        if search_params.search_text:
            search_pattern = f"%{search_params.search_text}%"
            query = query.filter(
                or_(
                    PatientDocument.original_filename.ilike(search_pattern),
                    PatientDocument.document_type.ilike(search_pattern)
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        documents = query.order_by(
            PatientDocument.created_at.desc()
        ).offset(search_params.offset).limit(search_params.limit).all()
        
        # Get chunk counts for each document
        from app.models.document_chunk import DocumentChunk
        results = []
        for doc in documents:
            chunk_count = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc.id
            ).count()
            
            results.append(DocumentSearchResult(
                id=doc.id,
                patient_id=doc.patient_id,
                consultation_id=doc.consultation_id,
                document_type=doc.document_type,
                original_filename=doc.original_filename,
                upload_status=doc.upload_status,
                processing_status=doc.processing_status,
                created_at=doc.created_at,
                chunk_count=chunk_count
            ))
        
        return DocumentSearchResponse(
            results=results,
            total_count=total_count,
            limit=search_params.limit,
            offset=search_params.offset
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search documents: {str(e)}"
        )
