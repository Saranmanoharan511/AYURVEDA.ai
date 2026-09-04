from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
import json

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_admin
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.consultation import Consultation
from app.models.patient_document import PatientDocument
from app.models.report import Report
from app.models.audit_log import AuditLog
from app.schemas.admin import (
    UserManagementResponse,
    UserStatusUpdate,
    UserListResponse,
    DoctorManagementResponse,
    DoctorStatusUpdate,
    DoctorListResponse,
    SystemSettings,
    SystemSettingsUpdate,
    SystemAnalytics,
    AuditLogResponse,
    AuditLogFilter,
    AuditLogListResponse,
    FailedDocumentProcessing,
    RetryDocumentProcessing,
    DLQListResponse,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplate,
)

router = APIRouter()


# User Management Endpoints
@router.get("/users", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all users with filtering and pagination (admin only)."""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.given_name.ilike(f"%{search}%")) |
            (User.family_name.ilike(f"%{search}%"))
        )
    
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return UserListResponse(
        users=[UserManagementResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=UserManagementResponse, dependencies=[Depends(require_admin)])
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get a specific user by ID (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserManagementResponse.model_validate(user)


@router.put("/users/{user_id}/status", response_model=UserManagementResponse, dependencies=[Depends(require_admin)])
async def update_user_status(
    user_id: UUID,
    status_update: UserStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user status (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_status = user.status
    user.status = status_update.status
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Create audit log
    audit_log = AuditLog(
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="UPDATE_USER_STATUS",
        resource_type="USER",
        resource_id=user.id,
        resource_identifier=user.email,
        old_values={"status": old_status},
        new_values={"status": user.status},
        success=True,
    )
    db.add(audit_log)
    db.commit()
    
    return UserManagementResponse.model_validate(user)


# Doctor Management Endpoints
@router.get("/doctors", response_model=DoctorListResponse, dependencies=[Depends(require_admin)])
async def list_doctors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all doctors with filtering and pagination (admin only)."""
    query = db.query(Doctor).join(User)
    
    if status:
        query = query.filter(Doctor.status == status)
    if search:
        query = query.filter(
            (Doctor.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    total = query.count()
    doctors = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return DoctorListResponse(
        doctors=[
            DoctorManagementResponse(
                id=doctor.id,
                user_id=doctor.user_id,
                name=doctor.name,
                qualifications=doctor.qualifications,
                specialization=doctor.specialization,
                status=doctor.status,
                email=doctor.user.email,
                created_at=doctor.created_at,
                updated_at=doctor.updated_at,
            )
            for doctor in doctors
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/doctors/{doctor_id}/status", response_model=DoctorManagementResponse, dependencies=[Depends(require_admin)])
async def update_doctor_status(
    doctor_id: UUID,
    status_update: DoctorStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update doctor status (admin only)."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    old_status = doctor.status
    doctor.status = status_update.status
    doctor.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doctor)
    
    # Create audit log
    audit_log = AuditLog(
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="UPDATE_DOCTOR_STATUS",
        resource_type="DOCTOR",
        resource_id=doctor.id,
        resource_identifier=doctor.name,
        old_values={"status": old_status},
        new_values={"status": doctor.status},
        success=True,
    )
    db.add(audit_log)
    db.commit()
    
    return DoctorManagementResponse(
        id=doctor.id,
        user_id=doctor.user_id,
        name=doctor.name,
        qualifications=doctor.qualifications,
        specialization=doctor.specialization,
        status=doctor.status,
        email=doctor.user.email,
        created_at=doctor.created_at,
        updated_at=doctor.updated_at,
    )


# System Configuration Endpoints
@router.get("/settings", response_model=SystemSettings, dependencies=[Depends(require_admin)])
async def get_system_settings(db: Session = Depends(get_db)):
    """Get current system settings (admin only)."""
    # For now, return default settings
    # In production, these would be stored in database or environment variables
    return SystemSettings()


@router.put("/settings", response_model=SystemSettings, dependencies=[Depends(require_admin)])
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update system settings (admin only)."""
    # For now, just return the updated settings
    # In production, these would be stored in database or environment variables
    
    # Create audit log
    audit_log = AuditLog(
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="UPDATE_SYSTEM_SETTINGS",
        resource_type="SYSTEM_SETTINGS",
        old_values={},
        new_values=settings_update.model_dump(exclude_none=True),
        success=True,
    )
    db.add(audit_log)
    db.commit()
    
    current_settings = SystemSettings()
    update_data = settings_update.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(current_settings, field, value)
    
    return current_settings


# System Analytics Endpoint
@router.get("/analytics", response_model=SystemAnalytics, dependencies=[Depends(require_admin)])
async def get_system_analytics(db: Session = Depends(get_db)):
    """Get system-wide analytics (admin only)."""
    
    # Total counts
    total_patients = db.query(Patient).count()
    total_doctors = db.query(Doctor).count()
    total_consultations = db.query(Consultation).count()
    total_documents = db.query(PatientDocument).count()
    total_reports = db.query(Report).count()
    
    # Consultation status breakdown
    active_consultations = db.query(Consultation).filter(
        Consultation.consultation_status.in_(
            ["APPOINTMENT_BOOKED", "WAITING_FOR_MEETING_SCHEDULE", 
             "MEETING_SCHEDULED", "WAITING_FOR_CONSULTATION"]
        )
    ).count()
    
    completed_consultations = db.query(Consultation).filter(
        Consultation.consultation_status == "CONSULTATION_COMPLETED"
    ).count()
    
    # Time-based metrics
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    consultations_this_month = db.query(Consultation).filter(
        Consultation.created_at >= month_start
    ).count()
    
    consultations_this_week = db.query(Consultation).filter(
        Consultation.created_at >= week_start
    ).count()
    
    patients_this_month = db.query(Patient).filter(
        Patient.created_at >= month_start
    ).count()
    
    # Most common conditions (from consultation reasons)
    common_conditions = db.query(
        Consultation.reason,
        db.func.count(Consultation.id).label("count")
    ).group_by(Consultation.reason).order_by(
        db.desc("count")
    ).limit(10).all()
    
    most_common_conditions = [
        {"condition": reason, "count": count} for reason, count in common_conditions
    ]
    
    # Patient distribution by city
    city_distribution = db.query(
        Patient.city,
        db.func.count(Patient.id).label("count")
    ).group_by(Patient.city).order_by(
        db.desc("count")
    ).limit(10).all()
    
    patient_distribution_by_city = [
        {"city": city or "Unknown", "count": count} for city, count in city_distribution
    ]
    
    # Document processing status
    document_status = db.query(
        PatientDocument.processing_status,
        db.func.count(PatientDocument.id).label("count")
    ).group_by(PatientDocument.processing_status).all()
    
    document_processing_status = {
        status: count for status, count in document_status
    }
    
    return SystemAnalytics(
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_consultations=total_consultations,
        active_consultations=active_consultations,
        completed_consultations=completed_consultations,
        total_documents=total_documents,
        total_reports=total_reports,
        consultations_this_month=consultations_this_month,
        consultations_this_week=consultations_this_week,
        patients_this_month=patients_this_month,
        most_common_conditions=most_common_conditions,
        patient_distribution_by_city=patient_distribution_by_city,
        document_processing_status=document_processing_status,
    )


# Audit Log Endpoints
@router.get("/audit-logs", response_model=AuditLogListResponse, dependencies=[Depends(require_admin)])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    actor_role: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    success: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """List audit logs with filtering and pagination (admin only)."""
    query = db.query(AuditLog)
    
    if actor_role:
        query = query.filter(AuditLog.actor_role == actor_role)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if success is not None:
        query = query.filter(AuditLog.success == success)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    # Order by timestamp descending
    query = query.order_by(AuditLog.timestamp.desc())
    
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return AuditLogListResponse(
        logs=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


# DLQ Management Endpoints
@router.get("/dlq/documents", response_model=DLQListResponse, dependencies=[Depends(require_admin)])
async def list_failed_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List failed document processing jobs (admin only)."""
    # Updated to query reports instead of patient_documents for reports-only RAG architecture
    query = db.query(Report).filter(
        Report.processing_status == "FAILED"
    ).join(Patient)
    
    total = query.count()
    documents = query.offset((page - 1) * page_size).limit(page_size).all()
    
    failed_documents = []
    for doc in documents:
        error_message = doc.upload_status  # Reports don't have document_metadata like patient documents
        retry_count = 0  # Reports don't track retry count in metadata
        last_attempt = doc.uploaded_at
        
        failed_documents.append(
            FailedDocumentProcessing(
                document_id=doc.id,
                patient_id=doc.patient_id,
                patient_name=doc.patient.full_name if doc.patient else "Unknown",
                document_type=doc.report_type,
                filename=doc.original_filename,
                error_message=error_message,
                retry_count=retry_count,
                last_attempt=last_attempt,
                can_retry=retry_count < 3,
            )
        )
    
    return DLQListResponse(
        failed_documents=failed_documents,
        total=total,
    )


@router.post("/dlq/documents/{document_id}/retry", dependencies=[Depends(require_admin)])
async def retry_document_processing(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retry failed document processing (admin only)."""
    # Updated to query reports instead of patient_documents for reports-only RAG architecture
    document = db.query(Report).filter(
        Report.id == document_id,
        Report.processing_status == "FAILED"
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Failed document not found")
    
    # Update document status to trigger reprocessing
    document.processing_status = "PENDING"
    db.commit()
    
    # Create audit log
    audit_log = AuditLog(
        actor_user_id=current_user.id,
        actor_role=current_user.role,
        action="RETRY_DOCUMENT_PROCESSING",
        resource_type="REPORT",
        resource_id=document.id,
        resource_identifier=document.original_filename,
        new_values={"processing_status": "PENDING"},
        success=True,
    )
    db.add(audit_log)
    db.commit()
    
    # Send message to SQS to trigger document processing
    try:
        import boto3
        from app.core.config import settings
        
        sqs = boto3.client('sqs', region_name=settings.AWS_REGION)
        
        message_body = {
            "document_id": str(document_id),
            "patient_id": str(document.patient_id),
            "consultation_id": str(document.consultation_id),
            "s3_object_key": document.s3_object_key,
            "original_filename": document.original_filename,
            "document_type": document.report_type,
            "document_source": "report"
        }
        
        sqs.send_message(
            QueueUrl=settings.SQS_DOCUMENT_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
    except Exception as e:
        # Log error but don't fail the retry - the document status is already updated
        print(f"Failed to send SQS message for document retry: {str(e)}")
    
    return {"message": "Document processing retry initiated", "document_id": str(document_id)}


# Email Template Management Endpoints
@router.get("/email-templates", dependencies=[Depends(require_admin)])
async def list_email_templates():
    """List all SES email templates (admin only)."""
    try:
        from app.services.ses_template_service import ses_template_service
        templates = ses_template_service.list_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email-templates/{template_name}", response_model=EmailTemplate, dependencies=[Depends(require_admin)])
async def get_email_template(template_name: str):
    """Get a specific SES email template (admin only)."""
    try:
        from app.services.ses_template_service import ses_template_service
        template = ses_template_service.get_template(template_name)
        return EmailTemplate(
            template_name=template['Name'],
            subject=template['SubjectPart'],
            body_html=template['HtmlPart'],
            body_text=template.get('TextPart'),
            variables=[],  # Variables would need to be parsed from the template
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email-templates", dependencies=[Depends(require_admin)])
async def create_email_template(
    template: EmailTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new SES email template (admin only)."""
    try:
        from app.services.ses_template_service import ses_template_service
        ses_template_service.create_template(
            template_name=template.template_name,
            subject=template.subject,
            html_body=template.body_html,
            text_body=template.body_text,
        )
        
        # Create audit log
        audit_log = AuditLog(
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="CREATE_EMAIL_TEMPLATE",
            resource_type="EMAIL_TEMPLATE",
            resource_identifier=template.template_name,
            new_values={"template_name": template.template_name},
            success=True,
        )
        db.add(audit_log)
        db.commit()
        
        return {"message": "Email template created successfully", "template_name": template.template_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/email-templates/{template_name}", dependencies=[Depends(require_admin)])
async def update_email_template(
    template_name: str,
    template_update: EmailTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing SES email template (admin only)."""
    try:
        from app.services.ses_template_service import ses_template_service
        
        # First get the current template
        current = ses_template_service.get_template(template_name)
        
        # Update with new values
        ses_template_service.update_template(
            template_name=template_name,
            subject=template_update.subject or current['SubjectPart'],
            html_body=template_update.body_html or current['HtmlPart'],
            text_body=template_update.body_text or current.get('TextPart'),
        )
        
        # Create audit log
        audit_log = AuditLog(
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="UPDATE_EMAIL_TEMPLATE",
            resource_type="EMAIL_TEMPLATE",
            resource_identifier=template_name,
            new_values=template_update.model_dump(exclude_none=True),
            success=True,
        )
        db.add(audit_log)
        db.commit()
        
        return {"message": "Email template updated successfully", "template_name": template_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/email-templates/{template_name}", dependencies=[Depends(require_admin)])
async def delete_email_template(
    template_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an SES email template (admin only)."""
    try:
        from app.services.ses_template_service import ses_template_service
        ses_template_service.delete_template(template_name)
        
        # Create audit log
        audit_log = AuditLog(
            actor_user_id=current_user.id,
            actor_role=current_user.role,
            action="DELETE_EMAIL_TEMPLATE",
            resource_type="EMAIL_TEMPLATE",
            resource_identifier=template_name,
            success=True,
        )
        db.add(audit_log)
        db.commit()
        
        return {"message": "Email template deleted successfully", "template_name": template_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
