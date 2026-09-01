"""
Patient Context Tool Service

Compiles a holistic view of a patient including profile, consultations,
documents, and appointments based on client_id.
"""

import time
from typing import Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.appointment import Appointment
from app.models.patient_document import PatientDocument
from app.schemas.ai import PatientContextRequest, PatientContextResponse


class PatientContextTool:
    """
    Patient Context Tool for building comprehensive patient views.
    
    This tool aggregates all relevant patient information into a single
    context object for the AI assistant to use when answering questions.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_patient_context(self, request: PatientContextRequest) -> PatientContextResponse:
        """
        Build a comprehensive patient context.
        
        Args:
            request: PatientContextRequest with patient ID and inclusion flags
            
        Returns:
            PatientContextResponse with comprehensive patient information
        """
        start_time = time.time()
        
        # Get patient information
        patient = self._get_patient(request.patient_id)
        if not patient:
            raise ValueError(f"Patient not found: {request.patient_id}")
        
        # Build context based on request parameters
        consultations = []
        documents = []
        appointments = []
        
        if request.include_consultations:
            consultations = self._get_consultations(request.patient_id)
        
        if request.include_documents:
            documents = self._get_documents(request.patient_id)
        
        if request.include_appointments:
            appointments = self._get_appointments(request.patient_id)
        
        execution_time = (time.time() - start_time) * 1000
        
        return PatientContextResponse(
            patient_id=str(patient['id']),
            client_id=patient['client_id'],
            profile=patient,
            consultations=consultations,
            documents=documents,
            appointments=appointments,
            total_consultations=len(consultations),
            total_documents=len(documents)
        )
    
    def _get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient profile information."""
        query = select(Patient).where(Patient.id == patient_id)
        result = self.db.execute(query).scalar_one_or_none()
        
        if not result:
            return None
        
        return {
            "id": str(result.id),
            "client_id": result.client_id,
            "full_name": result.full_name,
            "email": result.email,
            "phone": result.phone,
            "date_of_birth": str(result.date_of_birth) if result.date_of_birth else None,
            "gender": result.gender,
            "city": result.city,
            "state": result.state,
            "created_at": str(result.created_at)
        }
    
    def _get_consultations(self, patient_id: str) -> list:
        """Get consultation history for the patient."""
        from app.models.doctor import Doctor
        
        query = select(
            Consultation.id,
            Consultation.reason,
            Consultation.description,
            Consultation.consultation_status,
            Consultation.started_at,
            Consultation.completed_at,
            Consultation.created_at,
            Doctor.name.label('doctor_name'),
            Doctor.specialization.label('doctor_specialization')
        ).join(
            Doctor, Consultation.doctor_id == Doctor.id
        ).where(
            Consultation.patient_id == patient_id
        ).order_by(
            Consultation.created_at.desc()
        )
        
        results = self.db.execute(query).all()
        return [
            {
                "consultation_id": str(row.id),
                "reason": row.reason,
                "description": row.description,
                "status": row.consultation_status,
                "started_at": str(row.started_at) if row.started_at else None,
                "completed_at": str(row.completed_at) if row.completed_at else None,
                "created_at": str(row.created_at),
                "doctor_name": row.doctor_name,
                "doctor_specialization": row.doctor_specialization
            }
            for row in results
        ]
    
    def _get_documents(self, patient_id: str) -> list:
        """Get document information for the patient."""
        query = select(
            PatientDocument.id,
            PatientDocument.document_type,
            PatientDocument.original_filename,
            PatientDocument.upload_status,
            PatientDocument.processing_status,
            PatientDocument.created_at,
            func.count(PatientDocument.id).over().label('total_count')
        ).where(
            PatientDocument.patient_id == patient_id
        ).order_by(
            PatientDocument.created_at.desc()
        )
        
        results = self.db.execute(query).all()
        return [
            {
                "document_id": str(row.id),
                "document_type": row.document_type,
                "filename": row.original_filename,
                "upload_status": row.upload_status,
                "processing_status": row.processing_status,
                "created_at": str(row.created_at)
            }
            for row in results
        ]
    
    def _get_appointments(self, patient_id: str) -> list:
        """Get appointment information for the patient."""
        query = select(
            Appointment.id,
            Appointment.scheduled_date,
            Appointment.scheduled_time,
            Appointment.timezone,
            Appointment.zoom_meeting_url,
            Appointment.status,
            Consultation.reason.label('consultation_reason')
        ).join(
            Consultation, Appointment.consultation_id == Consultation.id
        ).where(
            Consultation.patient_id == patient_id
        ).order_by(
            Appointment.scheduled_date.desc()
        )
        
        results = self.db.execute(query).all()
        return [
            {
                "appointment_id": str(row.id),
                "scheduled_date": str(row.scheduled_date),
                "scheduled_time": row.scheduled_time,
                "timezone": row.timezone,
                "zoom_meeting_url": row.zoom_meeting_url,
                "status": row.status,
                "consultation_reason": row.consultation_reason
            }
            for row in results
        ]
    
    def get_patient_by_client_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get patient information by public client ID.
        
        Args:
            client_id: Public client ID (e.g., AYU-000001)
            
        Returns:
            Patient information dictionary or None
        """
        query = select(Patient).where(Patient.client_id == client_id)
        result = self.db.execute(query).scalar_one_or_none()
        
        if not result:
            return None
        
        return {
            "id": str(result.id),
            "client_id": result.client_id,
            "full_name": result.full_name,
            "email": result.email,
            "phone": result.phone,
            "date_of_birth": str(result.date_of_birth) if result.date_of_birth else None,
            "gender": result.gender,
            "city": result.city,
            "state": result.state
        }
    
    def format_context_for_ai(self, response: PatientContextResponse) -> str:
        """
        Format patient context as a readable string for AI consumption.
        
        Args:
            response: PatientContextResponse
            
        Returns:
            Formatted context string
        """
        lines = [
            f"Patient: {response.profile['full_name']} (Client ID: {response.client_id})",
            f"Email: {response.profile['email']}",
            f"Phone: {response.profile['phone']}",
            f"Location: {response.profile['city']}, {response.profile['state']}",
            ""
        ]
        
        if response.consultations:
            lines.append(f"Consultation History ({len(response.consultations)} consultations):")
            for i, cons in enumerate(response.consultations[:5], 1):
                lines.append(
                    f"  {i}. {cons['created_at'][:10]} - {cons['reason']} "
                    f"(Status: {cons['status']}, Doctor: {cons['doctor_name']})"
                )
            if len(response.consultations) > 5:
                lines.append(f"  ... and {len(response.consultations) - 5} more consultations")
            lines.append("")
        
        if response.documents:
            lines.append(f"Documents ({len(response.documents)} documents):")
            for i, doc in enumerate(response.documents[:5], 1):
                lines.append(
                    f"  {i}. {doc['filename']} - {doc['document_type']} "
                    f"(Status: {doc['processing_status']})"
                )
            if len(response.documents) > 5:
                lines.append(f"  ... and {len(response.documents) - 5} more documents")
            lines.append("")
        
        if response.appointments:
            lines.append(f"Appointments ({len(response.appointments)} appointments):")
            for i, appt in enumerate(response.appointments[:3], 1):
                lines.append(
                    f"  {i}. {appt['scheduled_date']} at {appt['scheduled_time']} "
                    f"(Status: {appt['status']})"
                )
            if len(response.appointments) > 3:
                lines.append(f"  ... and {len(response.appointments) - 3} more appointments")
        
        return "\n".join(lines)
