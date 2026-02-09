"""
JWT Token Propagation Utility for Todo AI System
Handles JWT token extraction and propagation in async event flows
"""

import jwt
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import SECRET_KEY, ALGORITHM
from ..models.user_model import User

logger = logging.getLogger(__name__)
security = HTTPBearer()


def extract_jwt_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from incoming request
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: JWT token if found, None otherwise
    """
    try:
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[len("Bearer "):]
        
        # Try to get token from custom header
        custom_token = request.headers.get("X-Auth-Token")
        if custom_token:
            return custom_token
        
        # Try to get token from cookie
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            return token_cookie
            
        return None
    except Exception as e:
        logger.error(f"Error extracting JWT token from request: {str(e)}")
        return None


def validate_and_extract_user_id(token: str) -> Optional[str]:
    """
    Validate JWT token and extract user ID
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[str]: User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id:
            return user_id
        return None
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during JWT validation: {str(e)}")
        return None


def validate_and_extract_user_data(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token and extract user data
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[Dict[str, Any]]: User data if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_data = {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
        return user_data
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during JWT validation: {str(e)}")
        return None


async def get_current_user_from_token(token: str) -> Optional[User]:
    """
    Get current user from JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[User]: User object if token is valid and user exists, None otherwise
    """
    try:
        user_data = validate_and_extract_user_data(token)
        if not user_data or not user_data.get("user_id"):
            return None
            
        # In a real implementation, you would fetch the user from the database
        # For now, we'll return a minimal user representation
        user = User(
            id=user_data["user_id"],
            username=user_data.get("username", ""),
            email=user_data.get("email", ""),
            role=user_data.get("role", "user")
        )
        return user
    except Exception as e:
        logger.error(f"Error getting user from token: {str(e)}")
        return None


def create_event_context_with_auth(event_data: Dict[str, Any], token: str) -> Dict[str, Any]:
    """
    Add authentication context to event data
    
    Args:
        event_data: Original event data
        token: JWT token string
        
    Returns:
        Dict[str, Any]: Event data with added authentication context
    """
    try:
        user_data = validate_and_extract_user_data(token)
        if user_data:
            event_data["auth_context"] = {
                "user_id": user_data["user_id"],
                "username": user_data.get("username"),
                "role": user_data.get("role"),
                "token_issued_at": user_data.get("iat"),
                "token_expires_at": user_data.get("exp")
            }
        return event_data
    except Exception as e:
        logger.error(f"Error adding auth context to event: {str(e)}")
        return event_data


def propagate_token_to_event_payload(payload: Dict[str, Any], token: Optional[str]) -> Dict[str, Any]:
    """
    Propagate token information to event payload for downstream processing
    
    Args:
        payload: Event payload
        token: JWT token string (optional)
        
    Returns:
        Dict[str, Any]: Payload with token context if available
    """
    if not token:
        return payload
        
    try:
        user_data = validate_and_extract_user_data(token)
        if user_data:
            # Add user context to payload without exposing sensitive token info
            payload["user_context"] = {
                "user_id": user_data["user_id"],
                "username": user_data.get("username"),
                "role": user_data.get("role")
            }
    except Exception as e:
        logger.error(f"Error propagating token to payload: {str(e)}")
        
    return payload


def validate_user_in_event_context(payload: Dict[str, Any], user_id: str) -> bool:
    """
    Validate that the user in the event context matches the expected user
    
    Args:
        payload: Event payload containing user information
        user_id: Expected user ID
        
    Returns:
        bool: True if user is valid, False otherwise
    """
    try:
        # Check if the payload contains user information
        payload_user_id = payload.get('user_id')
        
        # If no user_id in payload, assume it's valid
        if not payload_user_id:
            return True
            
        # Compare the user IDs
        return str(payload_user_id) == str(user_id)
    except Exception as e:
        logger.error(f"Error validating user in event context: {str(e)}")
        return False


# Async wrapper functions for use in async contexts
async def extract_jwt_token_from_request_async(request: Request) -> Optional[str]:
    """Async wrapper for extracting JWT token from request"""
    return extract_jwt_token_from_request(request)


async def validate_and_extract_user_id_async(token: str) -> Optional[str]:
    """Async wrapper for validating JWT token and extracting user ID"""
    return validate_and_extract_user_id(token)


async def validate_and_extract_user_data_async(token: str) -> Optional[Dict[str, Any]]:
    """Async wrapper for validating JWT token and extracting user data"""
    return validate_and_extract_user_data(token)