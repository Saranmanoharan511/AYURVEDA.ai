from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID


# User Management Schemas
class UserManagementResponse(BaseModel):
    id: UUID
    email: str
    role: str
    status: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    status: str = Field(..., description="New status: ACTIVE, BLOCKED, or SUSPENDED")


class UserListResponse(BaseModel):
    users: List[UserManagementResponse]
    total: int
    page: int
    page_size: int


# Doctor Management Schemas
class DoctorManagementResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    qualifications: Optional[str] = None
    specialization: Optional[str] = None
    status: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorStatusUpdate(BaseModel):
    status: str = Field(..., description="New status: ACTIVE or INACTIVE")


class DoctorListResponse(BaseModel):
    doctors: List[DoctorManagementResponse]
    total: int
    page: int
    page_size: int


# System Configuration Schemas
class SystemSettings(BaseModel):
    booking_enabled: bool = Field(default=True, description="Whether new consultations can be booked")
    booking_message: Optional[str] = Field(None, description="Message to show when booking is disabled")
    holiday_dates: List[str] = Field(default_factory=list, description="List of holiday dates (YYYY-MM-DD)")
    maintenance_mode: bool = Field(default=False, description="Whether system is in maintenance mode")
    maintenance_message: Optional[str] = Field(None, description="Message to show during maintenance")


class SystemSettingsUpdate(BaseModel):
    booking_enabled: Optional[bool] = None
    booking_message: Optional[str] = None
    holiday_dates: Optional[List[str]] = None
    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None


# Email Template Schemas
class EmailTemplate(BaseModel):
    template_name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables: List[str] = Field(default_factory=list, description="List of template variables")


class EmailTemplateCreate(EmailTemplate):
    pass


class EmailTemplateUpdate(BaseModel):
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None


# System Analytics Schemas
class SystemAnalytics(BaseModel):
    total_patients: int
    total_doctors: int
    total_consultations: int
    active_consultations: int
    completed_consultations: int
    total_documents: int
    total_reports: int
    consultations_this_month: int
    consultations_this_week: int
    patients_this_month: int
    average_consultation_duration_minutes: Optional[float] = None
    most_common_conditions: List[dict] = Field(default_factory=list)
    patient_distribution_by_city: List[dict] = Field(default_factory=list)
    document_processing_status: dict = Field(default_factory=dict)


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: UUID
    actor_user_id: Optional[UUID] = None
    actor_role: str
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    resource_identifier: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[dict] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    actor_role: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


# DLQ Management Schemas
class FailedDocumentProcessing(BaseModel):
    document_id: UUID
    patient_id: UUID
    patient_name: str
    document_type: str
    filename: str
    error_message: str
    retry_count: int
    last_attempt: datetime
    can_retry: bool

    class Config:
        from_attributes = True


class RetryDocumentProcessing(BaseModel):
    document_id: UUID


class DLQListResponse(BaseModel):
    failed_documents: List[FailedDocumentProcessing]
    total: int
