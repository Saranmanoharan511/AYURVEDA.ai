"""
SQL Tool Service

Safe, read-only SQL queries for structured PostgreSQL data.
This tool allows the AI to query business data without destructive operations.
"""

import time
from typing import List, Dict, Any, Optional
from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.consultation import Consultation
from app.models.appointment import Appointment
from app.models.consultation_note import ConsultationNote
from app.schemas.ai import SQLToolRequest, SQLToolResponse


class SQLTool:
    """
    SQL Tool for safe, read-only database queries.
    
    This tool provides controlled access to structured business data.
    All queries are read-only and enforce authorization boundaries.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute_query(self, request: SQLToolRequest) -> SQLToolResponse:
        """
        Execute a safe SQL query based on the request type.
        
        Args:
            request: SQLToolRequest with query type and parameters
            
        Returns:
            SQLToolResponse with query results
        """
        start_time = time.time()
        
        try:
            if request.query_type == "patient_count":
                results = self._get_patient_count(request)
            elif request.query_type == "consultation_status":
                results = self._get_consultation_status(request)
            elif request.query_type == "appointment_status":
                results = self._get_appointment_status(request)
            elif request.query_type == "today_consultations":
                results = self._get_today_consultations(request)
            elif request.query_type == "monthly_stats":
                results = self._get_monthly_stats(request)
            elif request.query_type == "patient_search":
                results = self._search_patients(request)
            else:
                raise ValueError(f"Unknown query type: {request.query_type}")
            
            execution_time = (time.time() - start_time) * 1000
            
            return SQLToolResponse(
                query_type=request.query_type,
                results=results,
                row_count=len(results),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            raise Exception(f"SQL Tool execution failed: {str(e)}")
    
    def _get_patient_count(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get patient count with optional filters."""
        query = select(func.count(Patient.id))
        
        if request.doctor_id:
            # Count patients that have consultations with this doctor
            query = select(func.count(Patient.id.distinct())).join(
                Consultation, Patient.id == Consultation.patient_id
            ).where(Consultation.doctor_id == request.doctor_id)
        
        result = self.db.execute(query).scalar()
        return [{"count": result}]
    
    def _get_consultation_status(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get consultation status breakdown."""
        query = select(
            Consultation.consultation_status,
            func.count(Consultation.id).label('count')
        )
        
        if request.doctor_id:
            query = query.where(Consultation.doctor_id == request.doctor_id)
        
        if request.patient_id:
            query = query.where(Consultation.patient_id == request.patient_id)
        
        query = query.group_by(Consultation.consultation_status)
        
        results = self.db.execute(query).all()
        return [
            {
                "status": row.consultation_status,
                "count": row.count
            }
            for row in results
        ]
    
    def _get_appointment_status(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get appointment status breakdown."""
        query = select(
            Appointment.status,
            func.count(Appointment.id).label('count')
        )
        
        if request.doctor_id:
            query = query.join(Consultation).where(Consultation.doctor_id == request.doctor_id)
        
        if request.patient_id:
            query = query.join(Consultation).where(Consultation.patient_id == request.patient_id)
        
        query = query.group_by(Appointment.status)
        
        results = self.db.execute(query).all()
        return [
            {
                "status": row.status,
                "count": row.count
            }
            for row in results
        ]
    
    def _get_today_consultations(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get consultations scheduled for today."""
        today = datetime.utcnow().date()
        
        query = select(
            Consultation.id,
            Consultation.reason,
            Consultation.consultation_status,
            Consultation.created_at,
            Patient.client_id,
            Patient.full_name,
            Appointment.scheduled_date,
            Appointment.scheduled_time
        ).join(
            Patient, Consultation.patient_id == Patient.id
        ).outerjoin(
            Appointment, Consultation.id == Appointment.consultation_id
        ).where(
            func.date(Appointment.scheduled_date) == today
        )
        
        if request.doctor_id:
            query = query.where(Consultation.doctor_id == request.doctor_id)
        
        query = query.order_by(Appointment.scheduled_time)
        
        results = self.db.execute(query).all()
        return [
            {
                "consultation_id": str(row.id),
                "client_id": row.client_id,
                "patient_name": row.full_name,
                "reason": row.reason,
                "status": row.consultation_status,
                "scheduled_date": str(row.scheduled_date) if row.scheduled_date else None,
                "scheduled_time": row.scheduled_time
            }
            for row in results
        ]
    
    def _get_monthly_stats(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get monthly consultation statistics."""
        # Default to last 6 months
        months_back = request.filters.get('months_back', 6) if request.filters else 6
        
        query = select(
            func.date_trunc('month', Consultation.created_at).label('month'),
            func.count(Consultation.id).label('total_consultations'),
            func.count(
                func.case(
                    (Consultation.consultation_status == 'CONSULTATION_COMPLETED', 1),
                    else_=0
                )
            ).label('completed_consultations')
        )
        
        if request.doctor_id:
            query = query.where(Consultation.doctor_id == request.doctor_id)
        
        query = query.where(
            Consultation.created_at >= datetime.utcnow() - timedelta(days=30*months_back)
        )
        
        query = query.group_by(
            func.date_trunc('month', Consultation.created_at)
        ).order_by(
            func.date_trunc('month', Consultation.created_at)
        )
        
        results = self.db.execute(query).all()
        return [
            {
                "month": str(row.month),
                "total_consultations": row.total_consultations,
                "completed_consultations": row.completed_consultations
            }
            for row in results
        ]
    
    def _search_patients(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Search for patients by name, client_id, or email."""
        search_term = request.filters.get('search_term', '') if request.filters else ''
        
        if not search_term:
            return []
        
        query = select(
            Patient.id,
            Patient.client_id,
            Patient.full_name,
            Patient.email,
            Patient.phone,
            Patient.city,
            Patient.state
        )
        
        # Search by name, client_id, or email
        search_pattern = f"%{search_term}%"
        query = query.where(
            or_(
                Patient.full_name.ilike(search_pattern),
                Patient.client_id.ilike(search_pattern),
                Patient.email.ilike(search_pattern)
            )
        )
        
        # Limit results
        limit = request.filters.get('limit', 20) if request.filters else 20
        query = query.limit(limit)
        
        results = self.db.execute(query).all()
        return [
            {
                "patient_id": str(row.id),
                "client_id": row.client_id,
                "full_name": row.full_name,
                "email": row.email,
                "phone": row.phone,
                "city": row.city,
                "state": row.state
            }
            for row in results
        ]
    
    def get_patient_by_client_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get patient information by client ID.
        
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
            "patient_id": str(result.id),
            "client_id": result.client_id,
            "full_name": result.full_name,
            "email": result.email,
            "phone": result.phone,
            "date_of_birth": str(result.date_of_birth) if result.date_of_birth else None,
            "gender": result.gender,
            "city": result.city,
            "state": result.state
        }
    
    def get_patient_consultations(self, patient_id: str, doctor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get consultation history for a patient.
        
        Args:
            patient_id: Patient internal ID
            doctor_id: Optional doctor ID for authorization
            
        Returns:
            List of consultation dictionaries
        """
        query = select(
            Consultation.id,
            Consultation.reason,
            Consultation.description,
            Consultation.consultation_status,
            Consultation.created_at,
            Consultation.completed_at,
            Doctor.name.label('doctor_name')
        ).join(
            Doctor, Consultation.doctor_id == Doctor.id
        ).where(
            Consultation.patient_id == patient_id
        )
        
        if doctor_id:
            query = query.where(Consultation.doctor_id == doctor_id)
        
        query = query.order_by(Consultation.created_at.desc())
        
        results = self.db.execute(query).all()
        return [
            {
                "consultation_id": str(row.id),
                "reason": row.reason,
                "description": row.description,
                "status": row.consultation_status,
                "created_at": str(row.created_at),
                "completed_at": str(row.completed_at) if row.completed_at else None,
                "doctor_name": row.doctor_name
            }
            for row in results
        ]
