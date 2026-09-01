"""
Authentication and JWT Validation Module

This module provides JWT token validation and authentication utilities
for FastAPI endpoints. It validates Cognito JWT tokens and extracts user claims.

AWS Code-Only Mode: This code validates tokens but does not create
Cognito resources. The actual Cognito User Pool must be created manually.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.services.cognito_service import cognito_service
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


# HTTP Bearer token scheme
security = HTTPBearer()


class AuthError(Exception):
    """Custom authentication error."""
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Verify and decode JWT token from Authorization header.
    
    This dependency validates the Cognito JWT token and returns the decoded claims.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        Dict with decoded token claims including:
        - sub: User unique identifier (cognito_sub)
        - email: User email
        - given_name: User first name
        - family_name: User last name
        - custom:role: User role (patient, doctor, admin)
        
    Raises:
        HTTPException: If token is invalid, expired, or verification fails
    """
    try:
        token = credentials.credentials
        
        # Verify token with Cognito (without audience check for access tokens)
        decoded = cognito_service.verify_jwt_token(token)
        return decoded
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user(
    token_data: Dict = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract current user from verified token and return ORM User object.
    
    Args:
        token_data: Decoded token claims from verify_token
        db: Database session
        
    Returns:
        User ORM object from database
        
    Raises:
        HTTPException: If user is not found or not active
    """
    try:
        cognito_sub = token_data.get("sub")
        
        # Get user from database using cognito_sub
        db_user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database"
            )
        
        # Check if user is active
        if db_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )
        
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting current user: {str(e)}"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optionally extract user from token.
    
    This dependency allows endpoints to work with or without authentication.
    Returns None if no valid token is provided.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session
        
    Returns:
        User ORM object if token is valid, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token_data = cognito_service.verify_jwt_token(credentials.credentials)
        cognito_sub = token_data.get("sub")
        
        # Get user from database using cognito_sub
        db_user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
        
        if db_user and db_user.status == "active":
            return db_user
        return None
    except Exception:
        return None


def require_auth():
    """
    Dependency that requires authentication.
    
    Use this for endpoints that must have a valid authenticated user.
    """
    return Depends(get_current_user)


def optional_auth():
    """
    Dependency that optionally accepts authentication.
    
    Use this for endpoints that work with or without authentication.
    """
    return Depends(get_optional_user)
