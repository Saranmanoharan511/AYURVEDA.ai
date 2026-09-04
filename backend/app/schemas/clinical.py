"""
Clinical Schemas

This module defines Pydantic schemas for clinical/business system entities:
- Patients
- Doctors
- Consultations
- Appointments
- Consultation Notes
"""

from pydantic import BaseModel, Field, validator
from datetime import date, datetime, time
from typing import Optional
from uuid import UUID


# ============ Patient Schemas ============

class PatientBase(BaseModel):
    """Base patient schema."""
    full_name: str = Field(..., min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: str = Field(..., max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)


class PatientCreate(PatientBase):
    """Schema for creating a patient."""
    user_id: UUID
    cognito_sub: str


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)


class PatientResponse(PatientBase):
    """Schema for patient response."""
    id: UUID
    client_id: str
    user_id: UUID
    cognito_sub: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Doctor Schemas ============

class DoctorBase(BaseModel):
    """Base doctor schema."""
    name: str = Field(..., min_length=1, max_length=255)
    qualifications: Optional[str] = None
    specialization: Optional[str] = Field(None, max_length=255)


class DoctorCreate(DoctorBase):
    """Schema for creating a doctor."""
    user_id: UUID
    cognito_sub: str


class DoctorUpdate(BaseModel):
    """Schema for updating a doctor."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    qualifications: Optional[str] = None
    specialization: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)


class DoctorResponse(DoctorBase):
    """Schema for doctor response."""
    id: UUID
    user_id: UUID
    cognito_sub: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Consultation Schemas ============

class ConsultationBase(BaseModel):
    """Base consultation schema."""
    patient_id: UUID
    doctor_id: UUID
    reason: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ConsultationCreate(BaseModel):
    """Schema for creating a consultation."""
    reason: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ConsultationUpdate(BaseModel):
    """Schema for updating a consultation."""
    consultation_status: Optional[str] = Field(None, max_length=50)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ConsultationResponse(ConsultationBase):
    """Schema for consultation response."""
    id: UUID
    consultation_status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Appointment Schemas ============

class AppointmentBase(BaseModel):
    """Base appointment schema."""
    consultation_id: UUID
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    timezone: Optional[str] = Field(None, max_length=50)
    zoom_meeting_url: Optional[str] = Field(None, max_length=500)


class AppointmentCreate(AppointmentBase):
    """Schema for creating an appointment."""
    pass


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None
    timezone: Optional[str] = Field(None, max_length=50)
    zoom_meeting_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=50)


class AppointmentResponse(AppointmentBase):
    """Schema for appointment response."""
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Consultation Note Schemas ============

class ConsultationNoteBase(BaseModel):
    """Base consultation note schema."""
    consultation_id: UUID
    doctor_id: UUID
    diagnosis: Optional[str] = None
    ayurvedic_assessment: Optional[str] = None
    medicines: Optional[str] = None
    lifestyle_advice: Optional[str] = None
    diet_plan: Optional[str] = None
    follow_up_instructions: Optional[str] = None


class ConsultationNoteCreate(ConsultationNoteBase):
    """Schema for creating a consultation note."""
    pass


class ConsultationNoteUpdate(BaseModel):
    """Schema for updating a consultation note."""
    diagnosis: Optional[str] = None
    ayurvedic_assessment: Optional[str] = None
    medicines: Optional[str] = None
    lifestyle_advice: Optional[str] = None
    diet_plan: Optional[str] = None
    follow_up_instructions: Optional[str] = None


class ConsultationNoteResponse(ConsultationNoteBase):
    """Schema for consultation note response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Combined Schemas ============

class ConsultationWithDetails(ConsultationResponse):
    """Schema for consultation with related details."""
    patient: Optional[PatientResponse] = None
    doctor: Optional[DoctorResponse] = None
    appointment: Optional[AppointmentResponse] = None
    notes: Optional[ConsultationNoteResponse] = None


class PatientWithConsultations(PatientResponse):
    """Schema for patient with consultation history."""
    consultations: list[ConsultationResponse] = []


class DoctorWithConsultations(DoctorResponse):
    """Schema for doctor with consultation history."""
    consultations: list[ConsultationResponse] = []


# ============ Prescription Schemas ============

class PrescriptionBase(BaseModel):
    """Base prescription schema."""
    consultation_id: UUID
    patient_id: UUID
    doctor_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    morning_dosage: int = Field(0, ge=0, le=3)
    afternoon_dosage: int = Field(0, ge=0, le=3)
    night_dosage: int = Field(0, ge=0, le=3)
    food_timing: str = Field(..., max_length=50)
    notes: Optional[str] = None


class PrescriptionCreate(BaseModel):
    """Schema for creating a prescription."""
    name: str = Field(..., min_length=1, max_length=255)
    morning_dosage: int = Field(0, ge=0, le=3)
    afternoon_dosage: int = Field(0, ge=0, le=3)
    night_dosage: int = Field(0, ge=0, le=3)
    food_timing: str = Field(..., max_length=50)
    notes: Optional[str] = None


class PrescriptionUpdate(BaseModel):
    """Schema for updating a prescription."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    morning_dosage: Optional[int] = Field(None, ge=0, le=3)
    afternoon_dosage: Optional[int] = Field(None, ge=0, le=3)
    night_dosage: Optional[int] = Field(None, ge=0, le=3)
    food_timing: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class PrescriptionResponse(PrescriptionBase):
    """Schema for prescription response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Prescription Document Schemas ============

class PrescriptionDocumentBase(BaseModel):
    """Base prescription document schema."""
    consultation_id: UUID
    patient_id: UUID
    doctor_id: UUID
    s3_object_key: str
    original_filename: str
    content_type: str
    file_size: Optional[int] = None


class PrescriptionDocumentResponse(PrescriptionDocumentBase):
    """Schema for prescription document response."""
    id: UUID
    generated_at: datetime
    download_url: Optional[str] = None

    class Config:
        from_attributes = True
