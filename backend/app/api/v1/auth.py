"""
Authentication API Endpoints

This module provides authentication endpoints for user registration, login, logout,
and profile management. All endpoints integrate with Amazon Cognito for authentication.

AWS Code-Only Mode: This code integrates with Cognito but does not create
Cognito resources. The actual Cognito User Pool must be created manually.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, MessageResponse, RefreshTokenRequest
from app.services.cognito_service import cognito_service
from app.core.auth import get_current_user
from app.core.rbac import require_any_role
from app.core.rate_limit import auth_rate_limit, standard_rate_limit

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@auth_rate_limit()
async def register_user(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    This endpoint registers a new user in Cognito and creates a corresponding
    user record in the database. For patients, it also creates a patient profile.
    
    Args:
        user_data: User registration data (email, password, name, role)
        db: Database session
        
    Returns:
        MessageResponse with registration status
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Force role to 'patient' for public registration
        # Doctors and admins must be created through privileged admin endpoints
        role = "patient"
        
        # Register user in Cognito
        cognito_response = cognito_service.sign_up(
            email=user_data.email,
            password=user_data.password,
            given_name=user_data.given_name,
            family_name=user_data.family_name,
            role=role
        )
        
        # Don't create DB user yet - wait for confirmation/login
        # This avoids the email collision issue
        # The user will be created on first login after confirmation
        
        return MessageResponse(
            message="User registered successfully. Please confirm your email to complete registration."
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
@auth_rate_limit()
async def login_user(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return tokens.
    
    This endpoint authenticates a user with Cognito and returns
    access, ID, and refresh tokens. It also ensures a user record
    exists in the database.
    
    Args:
        login_data: User login credentials (email, password)
        db: Database session
        
    Returns:
        TokenResponse with authentication tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Authenticate with Cognito
        tokens = cognito_service.sign_in(
            email=login_data.email,
            password=login_data.password
        )
        
        # Get user details from Cognito
        user_details = cognito_service.get_user(tokens['access_token'])
        
        # Extract cognito_sub and user attributes
        cognito_sub = None
        email = None
        given_name = None
        family_name = None
        role = "patient"
        
        for attr in user_details.get('UserAttributes', []):
            if attr['Name'] == 'sub':
                cognito_sub = attr['Value']
            elif attr['Name'] == 'email':
                email = attr['Value']
            elif attr['Name'] == 'given_name':
                given_name = attr['Value']
            elif attr['Name'] == 'family_name':
                family_name = attr['Value']
            elif attr['Name'] == 'custom:role':
                role = attr['Value']
        
        # Check if user exists in database by cognito_sub
        db_user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
        
        if not db_user:
            # Check if user exists by email (from pre-registration)
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                # Update existing user with actual cognito_sub
                existing_user.cognito_sub = cognito_sub
                existing_user.role = role  # Update role from Cognito
                existing_user.given_name = given_name
                existing_user.family_name = family_name
                db.commit()
                db.refresh(existing_user)
                db_user = existing_user
            else:
                # Create new user record
                db_user = User(
                    cognito_sub=cognito_sub,
                    email=email,
                    role=role,
                    status="active",
                    given_name=given_name,
                    family_name=family_name
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
        else:
            # Update user information if needed
            db_user.email = email
            db_user.role = role
            db_user.given_name = given_name
            db_user.family_name = family_name
            db.commit()
            db.refresh(db_user)
        
        # Check if user is active
        if db_user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )
        
        # Create patient profile if it doesn't exist and user is a patient
        if db_user.role == "patient":
            from app.models.patient import Patient
            patient = db.query(Patient).filter(Patient.user_id == db_user.id).first()
            if not patient:
                # Generate client_id (AYU-XXXXXX format)
                last_patient = db.query(Patient).order_by(Patient.id.desc()).first()
                if last_patient and last_patient.client_id:
                    last_number = int(last_patient.client_id.split("-")[1])
                    new_number = last_number + 1
                else:
                    new_number = 1
                
                client_id = f"AYU-{new_number:06d}"
                
                patient = Patient(
                    client_id=client_id,
                    user_id=db_user.id,
                    cognito_sub=cognito_sub,
                    full_name=f"{given_name} {family_name}",
                    email=email
                )
                db.add(patient)
                db.commit()
        
        return TokenResponse(**tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
@standard_rate_limit()
async def logout_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout current user.
    
    This endpoint invalidates the user's current access token in Cognito.
    
    Args:
        credentials: HTTP Bearer credentials containing the access token
        
    Returns:
        MessageResponse with logout status
    """
    try:
        # Extract access token from Authorization header
        access_token = credentials.credentials
        
        # Call Cognito global sign-out to invalidate the token
        cognito_service.logout(access_token)
        
        return MessageResponse(
            message="Logged out successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
@standard_rate_limit()
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user profile.
    
    This endpoint returns the profile information of the currently
    authenticated user from the database.
    
    Args:
        current_user: Current authenticated user from JWT token (User ORM object)
        db: Database session
        
    Returns:
        UserResponse with user profile information
        
    Raises:
        HTTPException: If user is not found
    """
    try:
        # current_user is already the User ORM object from get_current_user
        return UserResponse.model_validate(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching profile: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
@auth_rate_limit()
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest
):
    """
    Refresh access token using refresh token.
    
    This endpoint uses the refresh token to obtain new access and ID tokens.
    
    Args:
        request: Refresh token request with refresh_token field
        
    Returns:
        TokenResponse with new tokens
        
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        tokens = cognito_service.refresh_token(refresh_request.refresh_token)
        return TokenResponse(**tokens)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )
