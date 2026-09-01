"""
Resource-Level Authorization Helpers

This module provides helper functions for resource-level authorization.
These functions ensure users can only access resources they are authorized to access.

Key principles:
- Patients can only access their own records
- Doctors can only access records of their authorized patients
- Admins have operational access within their scope
- Authorization is enforced at the backend, not just frontend
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Union
from app.models.user import User
from app.core.rbac import check_role, check_any_role


class AuthorizationError(Exception):
    """Custom authorization error."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def check_patient_ownership(
    current_user: Union[User, dict],
    resource_patient_id: str,
    resource_type: str = "resource"
) -> bool:
    """
    Check if current patient user owns the resource.
    
    Args:
        current_user: Current authenticated user (ORM or dict)
        resource_patient_id: Patient ID of the resource
        resource_type: Type of resource for error message
        
    Returns:
        True if user owns the resource
        
    Raises:
        AuthorizationError: If user does not own the resource
    """
    if check_role(current_user, "patient"):
        # Get user_id from ORM or dict
        if isinstance(current_user, User):
            # For patients, we need to get their patient record ID
            user_id = str(current_user.id)
        else:
            user_id = current_user.get("user_id")
        
        # Patients can only access their own resources
        if user_id != resource_patient_id:
            raise AuthorizationError(
                f"Access denied. Patients can only access their own {resource_type}."
            )
    return True


def check_doctor_patient_access(
    current_user: Union[User, dict],
    patient_id: str,
    db: Session
) -> bool:
    """
    Check if doctor has access to the specified patient.
    
    Doctors can access patients they have consultations with.
    Admins can access all patients for operational purposes.
    
    Args:
        current_user: Current authenticated user (ORM or dict)
        patient_id: Patient ID to check access for
        db: Database session
        
    Returns:
        True if doctor has access to patient
        
    Raises:
        AuthorizationError: If doctor does not have access
    """
    if check_role(current_user, "admin"):
        # Admins can access all patients for operational purposes
        return True
    
    if check_role(current_user, "doctor"):
        # Get doctor ID from ORM or dict
        if isinstance(current_user, User):
            from app.models.doctor import Doctor
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
            if not doctor:
                raise AuthorizationError("Doctor profile not found")
            doctor_id = doctor.id
        else:
            doctor_id = current_user.get("doctor_id")
        
        if not doctor_id:
            raise AuthorizationError("Doctor ID not found")
        
        # Check if doctor has a consultation with this patient
        from app.models.consultation import Consultation
        consultation = db.query(Consultation).filter(
            Consultation.doctor_id == doctor_id,
            Consultation.patient_id == patient_id
        ).first()
        
        if not consultation:
            raise AuthorizationError(
                "Access denied. You do not have a consultation with this patient."
            )
        
    elif check_role(current_user, "patient"):
        # Patients can only access their own records
        if isinstance(current_user, User):
            user_id = str(current_user.id)
        else:
            user_id = current_user.get("user_id")
        
        if user_id != patient_id:
            raise AuthorizationError(
                "Access denied. Patients can only access their own records."
            )
    
    return True


def check_admin_access(
    current_user: dict,
    resource_type: str = "resource"
) -> bool:
    """
    Check if current user has admin access.
    
    Args:
        current_user: Current authenticated user dict
        resource_type: Type of resource for error message
        
    Returns:
        True if user has admin access
        
    Raises:
        AuthorizationError: If user is not an admin
    """
    if not check_role(current_user, "admin"):
        raise AuthorizationError(
            f"Access denied. Admin access required for {resource_type}."
        )
    return True


def check_doctor_or_admin_access(
    current_user: dict,
    db: Session,
    resource_type: str = "resource"
) -> bool:
    """
    Check if current user has doctor or admin access.
    
    Args:
        current_user: Current authenticated user dict
        resource_type: Type of resource for error message
        
    Returns:
        True if user has doctor or admin access
        
    Raises:
        AuthorizationError: If user is not a doctor or admin
    """
    if not check_any_role(current_user, "doctor", "admin"):
        raise AuthorizationError(
            f"Access denied. Doctor or admin access required for {resource_type}."
        )
    return True


def get_authorized_patient_ids(
    current_user: Union[User, dict],
    db: Session
) -> List[str]:
    """
    Get list of patient IDs the current user is authorized to access.
    
    Args:
        current_user: Current authenticated user (ORM or dict)
        db: Database session
        
    Returns:
        List of patient IDs
        
    Note:
        - Patients: Returns only their own patient record ID
        - Doctors: Returns patients they have consultations with
        - Admins: Returns all patient IDs (for operational purposes)
    """
    if check_role(current_user, "patient"):
        # For patients, get their patient record ID from the patient table
        if isinstance(current_user, User):
            from app.models.patient import Patient
            patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
            if patient:
                return [str(patient.id)]
            return []
        else:
            return [current_user.get("user_id")]
    elif check_role(current_user, "doctor"):
        # Return patients the doctor has consultations with
        if isinstance(current_user, User):
            from app.models.doctor import Doctor
            from app.models.consultation import Consultation
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
            if doctor:
                consultations = db.query(Consultation).filter(
                    Consultation.doctor_id == doctor.id
                ).all()
                return list(set([str(c.patient_id) for c in consultations]))
        return []
    elif check_role(current_user, "admin"):
        # Admins can access all patients for operational purposes
        from app.models.patient import Patient
        patients = db.query(Patient).all()
        return [str(p.id) for p in patients]
    else:
        return []


def verify_user_status(
    db_user: User
) -> bool:
    """
    Verify that user account is in active status.
    
    Args:
        db_user: User object from database
        
    Returns:
        True if user is active
        
    Raises:
        AuthorizationError: If user is not active
    """
    if db_user.status != "active":
        raise AuthorizationError(
            f"Access denied. User account is {db_user.status}."
        )
    return True


def build_patient_context(
    current_user: Union[User, dict],
    patient_id: str,
    db: Session
) -> dict:
    """
    Build authorization context for patient-related operations.
    
    Args:
        current_user: Current authenticated user (ORM or dict)
        patient_id: Patient ID for context
        db: Database session
        
    Returns:
        Dict with authorization context including:
        - authorized: bool
        - user_role: str
        - patient_id: str
        - access_level: str
        
    Raises:
        AuthorizationError: If access is denied
    """
    if isinstance(current_user, User):
        user_role = current_user.role
    else:
        user_role = current_user.get("role")
    
    context = {
        "authorized": False,
        "user_role": user_role,
        "patient_id": patient_id,
        "access_level": None
    }
    
    if check_role(current_user, "patient"):
        # Get patient record ID for patients
        if isinstance(current_user, User):
            from app.models.patient import Patient
            patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
            user_patient_id = str(patient.id) if patient else None
        else:
            user_patient_id = current_user.get("user_id")
        
        if user_patient_id == patient_id:
            context["authorized"] = True
            context["access_level"] = "full"
        else:
            raise AuthorizationError("Patients can only access their own records.")
    
    elif check_role(current_user, "doctor"):
        # TODO: Implement doctor-patient authorization in Sprint 3
        context["authorized"] = True
        context["access_level"] = "doctor"
    
    elif check_role(current_user, "admin"):
        context["authorized"] = True
        context["access_level"] = "admin"
    
    return context
