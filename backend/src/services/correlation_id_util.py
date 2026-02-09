"""
Correlation ID Generation and Propagation Utility for Todo AI System
Manages correlation IDs for request tracing across async event flows
"""

import uuid
import logging
from contextvars import ContextVar
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Context variable to store correlation ID for the current async context
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID
    
    Returns:
        str: Generated correlation ID
    """
    return str(uuid.uuid4())


def set_current_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID for the current async context
    
    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def get_current_correlation_id() -> Optional[str]:
    """
    Get the correlation ID for the current async context
    
    Returns:
        Optional[str]: Current correlation ID, None if not set
    """
    return correlation_id_var.get()


def extract_correlation_id_from_request(request: Request) -> Optional[str]:
    """
    Extract correlation ID from incoming request headers
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: Correlation ID if found in headers, None otherwise
    """
    try:
        # Try to get correlation ID from standard header
        correlation_id = request.headers.get("X-Correlation-ID")
        if correlation_id:
            return correlation_id
        
        # Try to get correlation ID from alternate header
        correlation_id = request.headers.get("X-Request-ID")
        if correlation_id:
            return correlation_id
        
        # Try to get correlation ID from custom header
        correlation_id = request.headers.get("X-Trace-ID")
        if correlation_id:
            return correlation_id
            
        return None
    except Exception as e:
        logger.error(f"Error extracting correlation ID from request: {str(e)}")
        return None


def create_correlation_id_if_missing(request: Request) -> str:
    """
    Create a new correlation ID if one doesn't exist in the request
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Existing or newly created correlation ID
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        return correlation_id
    else:
        return generate_correlation_id()


def add_correlation_id_to_response_headers(response: Response, correlation_id: str) -> None:
    """
    Add correlation ID to response headers
    
    Args:
        response: Starlette response object
        correlation_id: Correlation ID to add to headers
    """
    try:
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = correlation_id  # Also add as alternate header
    except Exception as e:
        logger.error(f"Error adding correlation ID to response headers: {str(e)}")


def propagate_correlation_id_to_event_context(event_data: dict, correlation_id: Optional[str] = None) -> dict:
    """
    Add correlation ID to event data for downstream processing
    
    Args:
        event_data: Event data dictionary
        correlation_id: Correlation ID to propagate (optional, will use current if not provided)
        
    Returns:
        dict: Event data with correlation ID context
    """
    if not correlation_id:
        correlation_id = get_current_correlation_id()
    
    if correlation_id:
        event_data["correlation_id"] = correlation_id
    
    return event_data


def get_or_create_correlation_id(request: Request) -> str:
    """
    Get existing correlation ID from request or create a new one
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Correlation ID from request or newly generated one
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        # Set it in the current context
        set_current_correlation_id(correlation_id)
        return correlation_id
    else:
        # Generate new correlation ID and set it in context
        new_correlation_id = generate_correlation_id()
        set_current_correlation_id(new_correlation_id)
        return new_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically handle correlation IDs in HTTP requests
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get or create correlation ID
        correlation_id = get_or_create_correlation_id(request)
        
        # Add correlation ID to request state for easy access
        request.state.correlation_id = correlation_id
        
        # Process the request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        add_correlation_id_to_response_headers(response, correlation_id)
        
        return response


def add_correlation_id_to_logging_context(correlation_id: Optional[str] = None) -> dict:
    """
    Add correlation ID to logging context
    
    Args:
        correlation_id: Correlation ID to add to logging context (optional)
        
    Returns:
        dict: Logging context with correlation ID
    """
    if not correlation_id:
        correlation_id = get_current_correlation_id()
    
    return {"correlation_id": correlation_id} if correlation_id else {}


def create_tracing_context(extra_context: Optional[dict] = None) -> dict:
    """
    Create a tracing context with correlation ID and optional extra context
    
    Args:
        extra_context: Additional context to include in tracing
        
    Returns:
        dict: Tracing context with correlation ID and extra context
    """
    context = add_correlation_id_to_logging_context()
    
    if extra_context:
        context.update(extra_context)
    
    return context


# Async wrapper functions for use in async contexts
async def get_current_correlation_id_async() -> Optional[str]:
    """Async wrapper for getting current correlation ID"""
    return get_current_correlation_id()


async def set_current_correlation_id_async(correlation_id: str) -> None:
    """Async wrapper for setting current correlation ID"""
    set_current_correlation_id(correlation_id)


async def generate_correlation_id_async() -> str:
    """Async wrapper for generating correlation ID"""
    return generate_correlation_id()