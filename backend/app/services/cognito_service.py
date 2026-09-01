"""
Amazon Cognito Integration Service

This service provides integration with Amazon Cognito for user authentication.
It handles user registration, login, and token validation.

AWS Code-Only Mode: This code integrates with Cognito but does not create
Cognito resources. The actual Cognito User Pool must be created manually
by the developer in the AWS Cognito Console.
"""

import boto3
import jwt
from typing import Dict, Optional, List
from app.core.config import settings
import requests
import json
import logging
logger = logging.getLogger(__name__)


class CognitoService:
    """Service for interacting with Amazon Cognito User Pool."""
    
    def __init__(self):
        """Initialize Cognito client."""
        self.region = settings.COGNITO_REGION
        self.user_pool_id = settings.COGNITO_USER_POOL_ID
        self.client_id = settings.COGNITO_CLIENT_ID
        
        # Initialize Cognito IDP client
        try:
            self.client = boto3.client(
                'cognito-idp',
                region_name=self.region
            )
        except Exception as e:
            # Client will be initialized when AWS credentials are configured
            self.client = None
    
    def sign_up(
        self,
        email: str,
        password: str,
        given_name: str,
        family_name: str,
        role: str = "patient"
    ) -> Dict:
        """
        Register a new user in Cognito User Pool.
        
        Args:
            email: User email address
            password: User password
            given_name: User first name
            family_name: User last name
            role: User role (patient, doctor, admin)
            
        Returns:
            Dict with registration response
            
        Raises:
            Exception: If Cognito is not configured or registration fails
        """
        if not self.client:
            raise Exception("Cognito client not initialized. Configure AWS credentials.")
        
        if not self.user_pool_id or not self.client_id:
            raise Exception("Cognito User Pool ID and Client ID must be configured")
        
        try:
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    },
                    {
                        'Name': 'given_name',
                        'Value': given_name
                    },
                    {
                        'Name': 'family_name',
                        'Value': family_name
                    },
                    {
                        'Name': 'custom:role',
                        'Value': role
                    }
                ]
            )
            return response
        except self.client.exceptions.UsernameExistsException:
            raise Exception("User already exists")
        except self.client.exceptions.InvalidPasswordException:
            raise Exception("Password does not meet complexity requirements")
        except Exception as e:
            raise Exception(f"Registration failed: {str(e)}")
    
    def sign_in(self, email: str, password: str) -> Dict:
        """
        Authenticate user with Cognito.
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            Dict with authentication tokens (access_token, id_token, refresh_token)
            
        Raises:
            Exception: If authentication fails
        """
        if not self.client:
            raise Exception("Cognito client not initialized. Configure AWS credentials.")
        
        if not self.user_pool_id or not self.client_id:
            raise Exception("Cognito User Pool ID and Client ID must be configured")
        
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            return {
                'access_token': response['AuthenticationResult']['AccessToken'],
                'id_token': response['AuthenticationResult']['IdToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn'],
                'token_type': response['AuthenticationResult']['TokenType']
            }
        except self.client.exceptions.NotAuthorizedException:
            raise Exception("Incorrect username or password")
        except self.client.exceptions.UserNotFoundException:
            raise Exception("User does not exist")
        except self.client.exceptions.UserNotConfirmedException:
            raise Exception("User account is not confirmed")
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token from initial authentication
            
        Returns:
            Dict with new access token and id token
        """
        if not self.client:
            raise Exception("Cognito client not initialized. Configure AWS credentials.")
        
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            return {
                'access_token': response['AuthenticationResult']['AccessToken'],
                'id_token': response['AuthenticationResult']['IdToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn'],
                'token_type': response['AuthenticationResult']['TokenType']
            }
        except Exception as e:
            raise Exception(f"Token refresh failed: {str(e)}")
    
    def get_user(self, access_token: str) -> Dict:
        """
        Get user details using access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            Dict with user details
        """
        if not self.client:
            raise Exception("Cognito client not initialized. Configure AWS credentials.")
        
        try:
            response = self.client.get_user(AccessToken=access_token)
            return response
        except Exception as e:
            raise Exception(f"Failed to get user details: {str(e)}")
    
    def verify_jwt_token(self, token: str) -> Dict:
        """
        Verify and decode JWT token from Cognito.
        
        This method validates the token signature and extracts claims.
        
        Args:
            token: JWT token (id_token or access_token)
            
        Returns:
            Dict with decoded token claims
            
        Raises:
            Exception: If token is invalid or verification fails
        """
        try:
            # Get Cognito public keys
            # For production, this should cache the keys and refresh periodically
            region = self.region
            user_pool_id = self.user_pool_id
            
            # Get the JWT header to find the kid (key ID)
            headers = jwt.get_unverified_header(token)
            kid = headers['kid']
            
            # Fetch Cognito public keys
            keys_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
            response = requests.get(keys_url)
            keys = response.json()['keys']
            
            # Find the matching key
            public_key = None
            for key in keys:
                if key['kid'] == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                    break
            
            if not public_key:
                raise Exception("Public key not found for token")
            
            # Verify and decode the token
            # Note: Cognito access tokens don't include 'aud' claim, so we don't validate audience by default
            # ID tokens do include 'aud' as client_id
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options={'verify_aud': False},  # Don't verify audience by default
                issuer=f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
            )
            
            # Validate token_use claim (should be "access" or "id")
            token_use = decoded.get('token_use')
            if token_use not in ['access', 'id']:
                raise Exception(f"Invalid token_use claim: {token_use}")
            
            # For ID tokens, validate audience (client_id)
            # For access tokens, validate client_id in the token
            if token_use == 'id':
                if not decoded.get('aud') or decoded['aud'] != self.client_id:
                    raise Exception("Invalid audience for ID token")
            elif token_use == 'access':
                # Access tokens have 'client_id' claim instead of 'aud'
                if not decoded.get('client_id') or decoded['client_id'] != self.client_id:
                    raise Exception("Invalid client_id for access token")
            
            return decoded
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid token: {str(e)}")
        except Exception as e:
            raise Exception(f"Token verification failed: {str(e)}")
    
    def logout(self, access_token: str) -> Dict:
        """
        Log out user by invalidating the token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            Dict with logout response
        """
        if not self.client:
            raise Exception("Cognito client not initialized. Configure AWS credentials.")
        
        try:
            response = self.client.global_sign_out(AccessToken=access_token)
            return response
        except Exception as e:
            raise Exception(f"Logout failed: {str(e)}")


# Global Cognito service instance
cognito_service = CognitoService()
