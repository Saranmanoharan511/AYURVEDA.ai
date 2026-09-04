"""
Clinical API Endpoints

This module defines FastAPI endpoints for the clinical/business system:
- Patient profile management
- Consultation lifecycle
- Appointment scheduling
- Consultation notes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging
from datetime import datetime

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_patient, require_doctor, require_admin
from app.core.authorization import check_doctor_patient_access
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.consultation import Consultation
from app.models.appointment import Appointment
from app.models.consultation_note import ConsultationNote
from app.models.prescription import Prescription
from app.models.prescription_document import PrescriptionDocument
from app.services.sqs_service import sqs_service
from app.services.pdf_service import pdf_service
from app.services.s3_service import s3_service
from app.services.ses_service import ses_service
from app.schemas.clinical import (
    PatientCreate, PatientUpdate, PatientResponse, PatientWithConsultations,
    DoctorCreate, DoctorUpdate, DoctorResponse, DoctorWithConsultations,
    ConsultationCreate, ConsultationUpdate, ConsultationResponse, ConsultationWithDetails,
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    ConsultationNoteCreate, ConsultationNoteUpdate, ConsultationNoteResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse, PrescriptionDocumentResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============ Patient Endpoints ============

@router.get("/patients", response_model=List[PatientResponse], dependencies=[Depends(require_doctor)])
async def list_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all patients the current doctor has consultations with.
    
    This endpoint is for the doctor client search functionality.
    Doctors can only see patients they have consultations with.
    """
    # Get doctor ID
    from app.models.doctor import Doctor
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    
    # Get patients the doctor has consultations with
    from app.models.consultation import Consultation
    consultations = db.query(Consultation).filter(
        Consultation.doctor_id == doctor.id
    ).all()
    
    # Get unique patient IDs
    patient_ids = list(set([c.patient_id for c in consultations]))
    
    # Get patient records
    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    
    return [PatientResponse.model_validate(p) for p in patients]


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Create a new patient profile.
    
    Only patients can create their own profile.
    """
    # Check if patient already exists for this user
    existing_patient = db.query(Patient).filter(Patient.user_id == patient_data.user_id).first()
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient profile already exists for this user"
        )
    
    # Generate client_id (AYU-XXXXXX format)
    # For now, use a simple increment. In production, use a sequence or counter
    last_patient = db.query(Patient).order_by(Patient.id.desc()).first()
    if last_patient and last_patient.client_id:
        last_number = int(last_patient.client_id.split("-")[1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    client_id = f"AYU-{new_number:06d}"
    
    patient = Patient(
        client_id=client_id,
        user_id=patient_data.user_id,
        cognito_sub=patient_data.cognito_sub,
        full_name=patient_data.full_name,
        date_of_birth=patient_data.date_of_birth,
        age=patient_data.age,
        gender=patient_data.gender,
        phone=patient_data.phone,
        email=patient_data.email,
        city=patient_data.city,
        state=patient_data.state
    )
    
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    return patient


@router.get("/patients/me", response_model=PatientResponse)
async def get_my_patient_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Get the current patient's profile.
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    return patient


@router.put("/patients/me", response_model=PatientResponse)
async def update_my_patient_profile(
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Update the current patient's profile.
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    # Update fields if provided
    for field, value in patient_data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    
    return patient


@router.get("/patients/{patient_id}", response_model=PatientResponse, dependencies=[Depends(require_doctor)])
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific patient by ID (doctor only).
    
    Doctors can only access patients they have consultations with.
    """
    # Check doctor-patient authorization
    check_doctor_patient_access(current_user, patient_id, db)
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return PatientResponse.model_validate(patient)


@router.get("/patients/me/consultations", response_model=List[ConsultationWithDetails])
async def get_my_consultations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Get current patient's consultations.
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    consultations = db.query(Consultation).filter(
        Consultation.patient_id == patient.id
    ).order_by(Consultation.created_at.desc()).all()
    
    # Add patient details to each consultation
    result = []
    for consultation in consultations:
        result.append(ConsultationWithDetails(
            **consultation.to_dict(),
            patient=patient.to_dict(),
            doctor=None,
            appointment=None,
            notes=None
        ))
    
    return result


@router.get("/patients/{patient_id}/consultations", response_model=PatientWithConsultations)
async def get_patient_consultations(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Get a patient's consultation history.
    
    Doctors can only access patients they have consultations with.
    """
    # Check doctor-patient authorization
    check_doctor_patient_access(current_user, str(patient_id), db)
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    consultations = db.query(Consultation).filter(
        Consultation.patient_id == patient_id
    ).order_by(Consultation.created_at.desc()).all()
    
    return PatientWithConsultations(
        **patient.to_dict(),
        consultations=[consultation.to_dict() for consultation in consultations]
    )


# ============ Doctor Endpoints ============

@router.post("/doctors", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new doctor profile.
    
    Only admins can create doctor profiles.
    """
    # Check if doctor already exists for this user
    existing_doctor = db.query(Doctor).filter(Doctor.user_id == doctor_data.user_id).first()
    if existing_doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor profile already exists for this user"
        )
    
    doctor = Doctor(
        user_id=doctor_data.user_id,
        cognito_sub=doctor_data.cognito_sub,
        name=doctor_data.name,
        qualifications=doctor_data.qualifications,
        specialization=doctor_data.specialization,
        status="active"
    )
    
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    
    return doctor


@router.get("/doctors/me", response_model=DoctorResponse)
async def get_my_doctor_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Get the current doctor's profile.
    """
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    
    return doctor


@router.put("/doctors/me", response_model=DoctorResponse)
async def update_my_doctor_profile(
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Update the current doctor's profile.
    """
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    
    # Update fields if provided
    for field, value in doctor_data.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    
    db.commit()
    db.refresh(doctor)
    
    return doctor


@router.get("/doctors", response_model=List[DoctorResponse])
async def list_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all doctors.
    
    Only admins can list all doctors.
    """
    doctors = db.query(Doctor).filter(Doctor.status == "active").all()
    return doctors


# ============ Consultation Endpoints ============

@router.post("/consultations", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation_data: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    """
    Create a new consultation request.
    
    Only patients can create consultations.
    """
    # Verify patient ownership
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    # Get the first active doctor (in production, this should be configurable)
    doctor = db.query(Doctor).filter(Doctor.status == "active").first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active doctors available"
        )
    
    consultation = Consultation(
        patient_id=patient.id,
        doctor_id=doctor.id,
        reason=consultation_data.reason,
        description=consultation_data.description,
        consultation_status="APPOINTMENT_BOOKED"
    )
    
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    
    # Create appointment record
    appointment = Appointment(
        consultation_id=consultation.id,
        status="APPOINTMENT_BOOKED"
    )
    db.add(appointment)
    db.commit()
    
    # Queue email notification for consultation booking
    try:
        from app.models.user import User as UserModel
        patient_user = db.query(UserModel).filter(UserModel.id == patient.user_id).first()
        if patient_user:
            sqs_service.send_email_message(
                user_id=str(patient_user.id),
                event_type='CONSULTATION_BOOKED',
                recipient_email=patient_user.email,
                subject='Consultation Booking Confirmed',
                body=f'Your consultation has been successfully booked.',
                metadata={
                    'patient_name': patient.full_name,
                    'consultation_id': str(consultation.id),
                    'reason': consultation.reason
                }
            )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to queue consultation booking email: {str(e)}")
    
    return consultation


@router.get("/consultations/{consultation_id}", response_model=ConsultationWithDetails)
async def get_consultation(
    consultation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a consultation by ID.
    
    Patients can only access their own consultations.
    Doctors can access consultations they are assigned to.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    # Check authorization
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or consultation.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this consultation"
            )
    elif current_user.role == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or consultation.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this consultation"
            )
    
    # Get related data
    patient = db.query(Patient).filter(Patient.id == consultation.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == consultation.doctor_id).first()
    appointment = db.query(Appointment).filter(Appointment.consultation_id == consultation.id).first()
    notes = db.query(ConsultationNote).filter(ConsultationNote.consultation_id == consultation.id).first()
    
    return ConsultationWithDetails(
        **consultation.to_dict(),
        patient=patient.to_dict() if patient else None,
        doctor=doctor.to_dict() if doctor else None,
        appointment=appointment.to_dict() if appointment else None,
        notes=notes.to_dict() if notes else None
    )


@router.put("/consultations/{consultation_id}/status", response_model=ConsultationResponse)
async def update_consultation_status(
    consultation_id: UUID,
    consultation_data: ConsultationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Update consultation status.
    
    Only doctors can update consultation status.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    # Verify doctor is assigned to this consultation
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor or consultation.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this consultation"
        )
    
    # Update fields if provided
    for field, value in consultation_data.model_dump(exclude_unset=True).items():
        setattr(consultation, field, value)
    
    db.commit()
    db.refresh(consultation)
    
    return consultation


@router.get("/doctors/me/consultations", response_model=List[ConsultationResponse])
async def get_doctor_consultations(
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Get doctor's consultations with optional status filter.
    """
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )
    
    query = db.query(Consultation).filter(Consultation.doctor_id == doctor.id)
    
    if status_filter:
        query = query.filter(Consultation.consultation_status == status_filter)
    
    consultations = query.order_by(Consultation.created_at.desc()).all()
    
    return consultations


# ============ Appointment Endpoints ============

@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Update appointment details (schedule meeting, update status).
    
    Only doctors can update appointments.
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Verify doctor is assigned to this consultation
    consultation = db.query(Consultation).filter(Consultation.id == appointment.consultation_id).first()
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor or consultation.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this appointment"
        )
    
    # Update fields if provided
    for field, value in appointment_data.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    
    # If meeting is scheduled, update consultation status
    if appointment_data.zoom_meeting_url and appointment_data.scheduled_date:
        consultation.consultation_status = "MEETING_SCHEDULED"
        db.commit()
    
    db.commit()
    db.refresh(appointment)
    
    return appointment


@router.post("/consultations/{consultation_id}/schedule-meeting", response_model=AppointmentResponse)
async def schedule_meeting(
    consultation_id: UUID,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Schedule a meeting for a consultation.
    
    This is a convenience endpoint that updates the appointment with meeting details
    and transitions the consultation status to MEETING_SCHEDULED.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    # Verify doctor is assigned to this consultation
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor or consultation.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to schedule this consultation"
        )
    
    # Get or create appointment
    appointment = db.query(Appointment).filter(Appointment.consultation_id == consultation_id).first()
    if not appointment:
        appointment = Appointment(consultation_id=consultation_id, status="APPOINTMENT_BOOKED")
        db.add(appointment)
    
    # Update appointment details
    if appointment_data.scheduled_date:
        appointment.scheduled_date = appointment_data.scheduled_date
    if appointment_data.scheduled_time:
        appointment.scheduled_time = appointment_data.scheduled_time
    if appointment_data.timezone:
        appointment.timezone = appointment_data.timezone
    if appointment_data.zoom_meeting_url:
        appointment.zoom_meeting_url = appointment_data.zoom_meeting_url
    
    # Update status
    appointment.status = "MEETING_SCHEDULED"
    consultation.consultation_status = "MEETING_SCHEDULED"
    
    db.commit()
    db.refresh(appointment)
    
    # Queue email notification for meeting scheduled
    try:
        from app.models.user import User as UserModel
        patient = db.query(Patient).filter(Patient.id == consultation.patient_id).first()
        
        if not patient:
            logger.warning(f"Patient not found for consultation {consultation_id}, cannot send meeting scheduled email")
        else:
            patient_user = db.query(UserModel).filter(UserModel.id == patient.user_id).first()
            if not patient_user:
                logger.warning(f"User not found for patient {patient.id}, cannot send meeting scheduled email")
            elif not doctor:
                logger.warning(f"Doctor not found for consultation {consultation_id}, cannot send meeting scheduled email")
            else:
                sqs_service.send_email_message(
                    user_id=str(patient_user.id),
                    event_type='MEETING_SCHEDULED',
                    recipient_email=patient_user.email,
                    subject='Meeting Scheduled',
                    body=f'Your consultation meeting has been scheduled.',
                    metadata={
                        'patient_name': patient.full_name,
                        'doctor_name': doctor.name,
                        'scheduled_date': str(appointment.scheduled_date) if appointment.scheduled_date else None,
                        'scheduled_time': str(appointment.scheduled_time) if appointment.scheduled_time else None,
                        'timezone': appointment.timezone,
                        'zoom_meeting_url': appointment.zoom_meeting_url
                    }
                )
                logger.info(f"Meeting scheduled email queued successfully for consultation {consultation_id}")
    except Exception as e:
        logger.error(f"Failed to queue meeting scheduled email for consultation {consultation_id}: {str(e)}")
    
    return appointment


# ============ Consultation Note Endpoints ============

@router.post("/consultations/{consultation_id}/notes", response_model=ConsultationNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation_note(
    consultation_id: UUID,
    note_data: ConsultationNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Add consultation notes (diagnosis, medicines, advice).
    
    Only doctors can add consultation notes.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    # Verify doctor is assigned to this consultation
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor or consultation.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add notes to this consultation"
        )
    
    # Check if notes already exist
    existing_notes = db.query(ConsultationNote).filter(
        ConsultationNote.consultation_id == consultation_id
    ).first()
    
    if existing_notes:
        # Update existing notes
        for field, value in note_data.model_dump(exclude_unset=True).items():
            setattr(existing_notes, field, value)
        db.commit()
        db.refresh(existing_notes)
        return existing_notes
    else:
        # Create new notes
        note = ConsultationNote(
            consultation_id=consultation_id,
            doctor_id=doctor.id,
            diagnosis=note_data.diagnosis,
            ayurvedic_assessment=note_data.ayurvedic_assessment,
            medicines=note_data.medicines,
            lifestyle_advice=note_data.lifestyle_advice,
            diet_plan=note_data.diet_plan,
            follow_up_instructions=note_data.follow_up_instructions
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note


@router.get("/consultations/{consultation_id}/notes", response_model=ConsultationNoteResponse)
async def get_consultation_notes(
    consultation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get consultation notes.
    
    Patients can only access notes for their own consultations.
    Doctors can access notes for consultations they are assigned to.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
    )
    
    # Check authorization
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or consultation.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these notes"
            )
    elif current_user.role == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or consultation.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these notes"
            )
    
    notes = db.query(ConsultationNote).filter(
        ConsultationNote.consultation_id == consultation_id
    ).first()
    
    if not notes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation notes not found"
        )
    
    return notes


# ============ Prescription Endpoints ============

@router.post("/consultations/{consultation_id}/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    consultation_id: UUID,
    prescription_data: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Create a new prescription item for a consultation.
    
    Only doctors can create prescriptions for consultations they are assigned to.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    # Verify doctor is assigned to this consultation
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor or consultation.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add prescriptions to this consultation"
        )
    
    prescription = Prescription(
        consultation_id=consultation_id,
        patient_id=consultation.patient_id,
        doctor_id=doctor.id,
        name=prescription_data.name,
        morning_dosage=prescription_data.morning_dosage,
        afternoon_dosage=prescription_data.afternoon_dosage,
        night_dosage=prescription_data.night_dosage,
        food_timing=prescription_data.food_timing,
        notes=prescription_data.notes
    )
    
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    
    return prescription


@router.get("/consultations/{consultation_id}/prescriptions", response_model=List[PrescriptionResponse])
async def get_consultation_prescriptions(
    consultation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all prescriptions for a consultation.
    
    Patients can only access prescriptions for their own consultations.
    Doctors can access prescriptions for consultations they are assigned to.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    # Check authorization
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or consultation.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these prescriptions"
            )
    elif current_user.role == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or consultation.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these prescriptions"
            )
    
    prescriptions = db.query(Prescription).filter(
        Prescription.consultation_id == consultation_id
    ).order_by(Prescription.created_at.asc()).all()
    
    return prescriptions


@router.put("/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: UUID,
    prescription_data: PrescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Update a prescription.
    
    Only doctors can update prescriptions they created.
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    
    # Verify doctor is assigned to this consultation
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor or prescription.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this prescription"
        )
    
    # Update fields if provided
    for field, value in prescription_data.model_dump(exclude_unset=True).items():
        setattr(prescription, field, value)
    
    db.commit()
    db.refresh(prescription)
    
    return prescription


@router.delete("/prescriptions/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription(
    prescription_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Delete a prescription.
    
    Only doctors can delete prescriptions they created.
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    
    # Verify doctor is assigned to this consultation
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor or prescription.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this prescription"
        )
    
    db.delete(prescription)
    db.commit()
    
    return None


@router.post("/consultations/{consultation_id}/prescriptions/generate-pdf", response_model=PrescriptionDocumentResponse)
async def generate_prescription_pdf(
    consultation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Generate a PDF from all prescriptions for a consultation and upload to S3.
    
    Only doctors can generate prescription PDFs for consultations they are assigned to.
    """
    try:
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        # Verify doctor is assigned to this consultation
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or consultation.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to generate prescription PDF for this consultation"
            )
        
        # Get patient and appointment details
        patient = db.query(Patient).filter(Patient.id == consultation.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        from app.models.appointment import Appointment
        appointment = db.query(Appointment).filter(Appointment.consultation_id == consultation_id).first()
        
        # Get all prescriptions for this consultation
        prescriptions = db.query(Prescription).filter(
            Prescription.consultation_id == consultation_id
        ).order_by(Prescription.created_at.asc()).all()
        
        if not prescriptions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No prescriptions found for this consultation"
            )
        
        # Generate PDF
        consultation_date = appointment.scheduled_date.strftime('%Y-%m-%d') if appointment and appointment.scheduled_date else consultation.created_at.strftime('%Y-%m-%d')
        
        prescription_data = [
            {
                'name': p.name,
                'morning_dosage': p.morning_dosage,
                'afternoon_dosage': p.afternoon_dosage,
                'night_dosage': p.night_dosage,
                'food_timing': p.food_timing,
                'notes': p.notes
            }
            for p in prescriptions
        ]
        
        logger.info(f"Generating PDF for consultation {consultation_id} with {len(prescriptions)} prescriptions")
        
        pdf_buffer = pdf_service.generate_prescription_pdf(
            patient_name=patient.full_name,
            patient_email=patient.email,
            doctor_name=doctor.name,
            doctor_qualifications=doctor.qualifications or 'N/A',
            consultation_id=str(consultation_id),
            consultation_date=consultation_date,
            prescriptions=prescription_data
        )
        
        logger.info(f"PDF generated successfully, size: {len(pdf_buffer.getvalue())} bytes")
        
        # Upload to S3
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"prescription_{consultation_id}_{timestamp}.pdf"
        object_key = f"prescriptions/{consultation_id}/{filename}"
        
        logger.info(f"Uploading PDF to S3 with key: {object_key}")
        
        try:
            s3_service.upload_file(
                file_data=pdf_buffer.getvalue(),
                object_key=object_key,
                content_type='application/pdf'
            )
            logger.info(f"PDF uploaded successfully to S3")
        except Exception as e:
            logger.error(f"Failed to upload prescription PDF to S3: {str(e)}")
            logger.error(f"S3 Bucket Name: {settings.S3_BUCKET_NAME}")
            logger.error(f"AWS Region: {settings.AWS_REGION}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload prescription PDF to S3: {str(e)}. Please check S3 configuration."
            )
        
        # Create prescription document record
        prescription_document = PrescriptionDocument(
            consultation_id=consultation_id,
            patient_id=consultation.patient_id,
            doctor_id=doctor.id,
            s3_object_key=object_key,
            original_filename=filename,
            content_type='application/pdf',
            file_size=len(pdf_buffer.getvalue())
        )
        
        db.add(prescription_document)
        db.commit()
        db.refresh(prescription_document)
        
        logger.info(f"Prescription document record created: {prescription_document.id}")
        
        return prescription_document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating prescription PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/consultations/{consultation_id}/reports", response_model=List[dict])
async def get_consultation_reports(
    consultation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all reports (doctor-uploaded documents) for a consultation.
    
    Patients can only access reports for their own consultations.
    Doctors can access reports for consultations they are assigned to.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )
    
    # Check authorization
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or consultation.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these reports"
            )
    elif current_user.role == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or consultation.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these reports"
            )
    
    from app.models.report import Report
    reports = db.query(Report).filter(
        Report.consultation_id == consultation_id,
        Report.upload_status == 'COMPLETED'
    ).order_by(Report.uploaded_at.desc()).all()
    
    # Generate download URLs for each report
    result = []
    for report in reports:
        try:
            download_url = s3_service.generate_presigned_download_url(
                object_key=report.s3_object_key,
                expires_in=3600
            )
            result.append({
                **report.to_dict(),
                'download_url': download_url
            })
        except Exception as e:
            logger.error(f"Failed to generate download URL for report {report.id}: {str(e)}")
            # Still include the report even if URL generation fails
            result.append({
                **report.to_dict(),
                'download_url': None
            })
    
    return result


@router.get("/consultations/{consultation_id}/prescription-documents", response_model=List[PrescriptionDocumentResponse])
async def get_consultation_prescription_documents(
    consultation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all prescription documents (generated PDFs) for a consultation.
    
    Patients can only view their own consultation's prescription documents.
    Doctors can only view prescription documents for consultations they are assigned to.
    """
    try:
        # Verify user has access to this consultation
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        # Check authorization
        if current_user.role == 'patient':
            from app.models.patient import Patient
            patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
            if not patient or consultation.patient_id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view prescription documents for this consultation"
                )
        elif current_user.role == 'doctor':
            from app.models.doctor import Doctor
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
            if not doctor or consultation.doctor_id != doctor.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view prescription documents for this consultation"
                )
        
        # Get prescription documents
        prescription_documents = db.query(PrescriptionDocument).filter(
            PrescriptionDocument.consultation_id == consultation_id
        ).order_by(PrescriptionDocument.generated_at.desc()).all()
        
        # Generate download URLs for each document
        result = []
        for doc in prescription_documents:
            try:
                download_url = s3_service.generate_presigned_download_url(
                    object_key=doc.s3_object_key,
                    expires_in=3600
                )
                result.append(PrescriptionDocumentResponse(
                    id=doc.id,
                    consultation_id=doc.consultation_id,
                    patient_id=doc.patient_id,
                    doctor_id=doc.doctor_id,
                    s3_object_key=doc.s3_object_key,
                    original_filename=doc.original_filename,
                    content_type=doc.content_type,
                    file_size=doc.file_size,
                    generated_at=doc.generated_at,
                    download_url=download_url
                ))
            except Exception as e:
                logger.error(f"Failed to generate download URL for prescription document {doc.id}: {str(e)}")
                # Still include document without download URL
                result.append(PrescriptionDocumentResponse(
                    id=doc.id,
                    consultation_id=doc.consultation_id,
                    patient_id=doc.patient_id,
                    doctor_id=doc.doctor_id,
                    s3_object_key=doc.s3_object_key,
                    original_filename=doc.original_filename,
                    content_type=doc.content_type,
                    file_size=doc.file_size,
                    generated_at=doc.generated_at,
                    download_url=None
                ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prescription documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch prescription documents"
        )


@router.post("/consultations/{consultation_id}/send-documents")
async def send_consultation_documents(
    consultation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Send all consultation documents (reports and prescriptions) to the patient via email.
    
    Only doctors can send documents for consultations they are assigned to.
    This endpoint downloads all reports and prescription PDFs from S3 and attaches them to an email.
    """
    try:
        # Get consultation
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        # Verify doctor is assigned to this consultation
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or consultation.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to send documents for this consultation"
            )
        
        # Get patient
        patient = db.query(Patient).filter(Patient.id == consultation.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Get patient user for email
        from app.models.user import User as UserModel
        patient_user = db.query(UserModel).filter(UserModel.id == patient.user_id).first()
        if not patient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient user not found"
            )
        
        # Get all reports for this consultation
        from app.models.report import Report
        reports = db.query(Report).filter(
            Report.consultation_id == consultation_id,
            Report.upload_status == 'COMPLETED'
        ).all()
        
        # Get all prescription documents for this consultation
        prescription_documents = db.query(PrescriptionDocument).filter(
            PrescriptionDocument.consultation_id == consultation_id
        ).all()
        
        if not reports and not prescription_documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents available to send. Please upload reports or generate prescriptions first."
            )
        
        # Download reports from S3
        report_attachments = []
        for report in reports:
            try:
                file_data = s3_service.download_file(report.s3_object_key)
                report_attachments.append({
                    'filename': report.original_filename,
                    'data': file_data
                })
            except Exception as e:
                logger.error(f"Failed to download report {report.id}: {str(e)}")
        
        # Download prescription PDFs from S3
        prescription_attachments = []
        for doc in prescription_documents:
            try:
                file_data = s3_service.download_file(doc.s3_object_key)
                prescription_attachments.append({
                    'filename': doc.original_filename,
                    'data': file_data
                })
            except Exception as e:
                logger.error(f"Failed to download prescription document {doc.id}: {str(e)}")
        
        # Send email with attachments
        message_id = ses_service.send_documents_email(
            to_email=patient_user.email,
            patient_name=patient.full_name,
            doctor_name=doctor.name,
            consultation_id=str(consultation_id),
            report_attachments=report_attachments,
            prescription_attachments=prescription_attachments
        )
        
        logger.info(f"Documents sent to patient {patient_user.email} for consultation {consultation_id}. Message ID: {message_id}")
        
        return {
            "message": "Documents sent successfully",
            "message_id": message_id,
            "reports_count": len(report_attachments),
            "prescriptions_count": len(prescription_attachments)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending consultation documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send documents: {str(e)}"
        )
