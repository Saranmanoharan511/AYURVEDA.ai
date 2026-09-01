"""
Role-Based Access Control (RBAC) Module

This module provides role-based access control utilities for FastAPI endpoints.
It defines user roles and provides decorators/dependencies to protect routes
based on user permissions.

Roles:
- PATIENT: Can access own records, consultations, appointments, reports
- DOCTOR: Can access authorized clinic patients, consultations, reports, AI tools
- ADMIN: Can access operational administration, user management, system configuration
"""

from fastapi import Depends, HTTPException, status
from typing import List, Callable, Union
from functools import wraps
from app.core.auth import get_current_user
from app.models.user import User


# Role constants
ROLE_PATIENT = "patient"
ROLE_DOCTOR = "doctor"
ROLE_ADMIN = "admin"

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    ROLE_PATIENT: 1,
    ROLE_DOCTOR: 2,
    ROLE_ADMIN: 3
}

# Valid roles
VALID_ROLES = [ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN]


def require_role(required_role: str):
    """
    Dependency that requires a specific role.
    
    Args:
        required_role: The required role (patient, doctor, admin)
        
    Returns:
        Dependency function that checks user role
        
    Raises:
        HTTPException: If user does not have the required role
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.lower() if current_user.role else ""
        
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


def require_any_role(*allowed_roles: str):
    """
    Dependency that requires any of the specified roles.
    
    Args:
        *allowed_roles: List of allowed roles
        
    Returns:
        Dependency function that checks if user has any of the allowed roles
        
    Raises:
        HTTPException: If user does not have any of the allowed roles
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.lower() if current_user.role else ""
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Allowed roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_checker


def require_minimum_role(minimum_role: str):
    """
    Dependency that requires a minimum role level based on hierarchy.
    
    Args:
        minimum_role: The minimum required role level
        
    Returns:
        Dependency function that checks if user has sufficient role level
        
    Raises:
        HTTPException: If user's role level is below the minimum
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.lower() if current_user.role else ""
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required minimum role: {minimum_role}"
            )
        
        return current_user
    
    return role_checker


# Pre-built role dependencies
require_patient = require_role(ROLE_PATIENT)
require_doctor = require_role(ROLE_DOCTOR)
require_admin = require_role(ROLE_ADMIN)

# Pre-built multi-role dependencies
require_doctor_or_admin = require_any_role(ROLE_DOCTOR, ROLE_ADMIN)
require_patient_or_doctor = require_any_role(ROLE_PATIENT, ROLE_DOCTOR)


def check_role(user: Union[User, dict], required_role: str) -> bool:
    """
    Check if a user has a specific role.
    
    Args:
        user: User ORM object or dictionary with role field
        required_role: Required role to check
        
    Returns:
        True if user has the required role, False otherwise
    """
    if isinstance(user, User):
        user_role = user.role.lower() if user.role else ""
    else:
        user_role = user.get("role", "").lower()
    return user_role == required_role


def check_any_role(user: Union[User, dict], *allowed_roles: str) -> bool:
    """
    Check if a user has any of the specified roles.
    
    Args:
        user: User ORM object or dictionary with role field
        *allowed_roles: Allowed roles to check
        
    Returns:
        True if user has any of the allowed roles, False otherwise
    """
    if isinstance(user, User):
        user_role = user.role.lower() if user.role else ""
    else:
        user_role = user.get("role", "").lower()
    return user_role in allowed_roles


def check_minimum_role(user: Union[User, dict], minimum_role: str) -> bool:
    """
    Check if a user has at least the minimum role level.
    
    Args:
        user: User ORM object or dictionary with role field
        minimum_role: Minimum required role level
        
    Returns:
        True if user's role level is at least the minimum, False otherwise
    """
    if isinstance(user, User):
        user_role = user.role.lower() if user.role else ""
    else:
        user_role = user.get("role", "").lower()
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(minimum_role, 0)
    return user_level >= required_level
