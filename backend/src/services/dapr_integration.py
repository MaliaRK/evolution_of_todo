"""
Dapr Integration Service for Todo AI System
Provides abstraction layer for Dapr service-to-service communication
"""

import asyncio
import json
import logging
import random
from typing import Any, Dict, Optional, Union
from datetime import datetime
from uuid import UUID

from dapr.clients import DaprClient
from dapr.clients.exceptions import DaprInternalError, DaprGrpcError
from grpc import RpcError

from .logging_config import get_component_logger, log_event_processing_error
from .correlation_id_util import get_current_correlation_id
from ..config.connection_config import get_dapr_config, get_connection_settings

logger = get_component_logger("dapr")

# Circuit breaker states
CB_CLOSED = "closed"  # Normal operation
CB_OPEN = "open"      # Tripped, requests blocked
CB_HALF_OPEN = "half_open"  # Testing if failure condition is resolved


class CircuitBreaker:
    """
    Advanced circuit breaker implementation for Dapr service calls
    Implements the circuit breaker pattern with configurable thresholds and timeouts
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, 
                 recovery_timeout: int = 30, success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold  # Number of successes to close circuit
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CB_CLOSED
        self.last_attempt_time = None
    
    def call(self, func, *args, **kwargs):
        """
        Execute a function with circuit breaker protection
        
        Args:
            func: Function to call
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            Result of function call
            
        Raises:
            Exception: If circuit breaker is open or function call fails
        """
        if self.state == CB_OPEN:
            if (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout:
                self.state = CB_HALF_OPEN
                logger.info(
                    "Circuit breaker transitioning to HALF_OPEN state",
                    event_type="circuit_breaker_half_open"
                )
            else:
                logger.warning(
                    "Circuit breaker is OPEN, rejecting request",
                    event_type="circuit_breaker_rejection"
                )
                raise Exception("Circuit breaker is OPEN - service temporarily unavailable")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        """Called when a call succeeds"""
        if self.state == CB_HALF_OPEN:
            # In half-open state, increment success counter
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                # Enough successes to close the circuit
                self.state = CB_CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(
                    "Circuit breaker CLOSED after successful calls",
                    event_type="circuit_breaker_closed"
                )
        else:
            # Normal success resets failure count
            self.failure_count = 0
            self.success_count = 0
            if self.state != CB_CLOSED:
                self.state = CB_CLOSED
                logger.info(
                    "Circuit breaker CLOSED after successful call",
                    event_type="circuit_breaker_closed"
                )
    
    def on_failure(self):
        """Called when a call fails"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CB_HALF_OPEN:
            # Failure in half-open state means we need to open again
            self.state = CB_OPEN
            logger.warning(
                f"Circuit breaker OPENED after failure in HALF_OPEN state",
                event_type="circuit_breaker_opened"
            )
        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open the circuit
            self.state = CB_OPEN
            self.success_count = 0
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} failures",
                event_type="circuit_breaker_opened",
                failure_count=self.failure_count
            )
    
    def is_available(self) -> bool:
        """Check if the circuit breaker allows calls"""
        if self.state == CB_OPEN:
            if (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout:
                self.state = CB_HALF_OPEN
                logger.info(
                    "Circuit breaker transitioning to HALF_OPEN for testing",
                    event_type="circuit_breaker_half_open_test"
                )
                return True
            return False
        return True
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get detailed information about the circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "time_until_recovery": (
                self.recovery_timeout - (datetime.now() - self.last_failure_time).seconds
                if self.last_failure_time and self.state == CB_OPEN
                else 0
            )
        }


class DaprIntegrationService:
    """
    Service to handle Dapr integration for service-to-service communication
    """
    
    def __init__(self, dapr_client_instance=None):
        self.client = dapr_client_instance or DaprClient()
        self.config = get_dapr_config()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_settings = get_connection_settings()
    
    async def invoke_service(self, app_id: str, method: str, data: Optional[Union[Dict, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Invoke a service using Dapr service invocation with advanced retry and circuit breaker patterns
        
        Args:
            app_id: Target application ID
            method: Method to invoke
            data: Data to send with the request
            
        Returns:
            Optional[Dict[str, Any]]: Response data from the service
        """
        correlation_id = get_current_correlation_id()
        
        # Create a circuit breaker for this service/method combination
        cb_key = f"{app_id}:{method}"
        if cb_key not in self.circuit_breakers:
            self.circuit_breakers[cb_key] = CircuitBreaker(
                failure_threshold=self.retry_settings.dapr.service_invocation_retry_count
            )
        
        circuit_breaker = self.circuit_breakers[cb_key]
        
        if not circuit_breaker.is_available():
            logger.error(
                f"Circuit breaker tripped for {app_id}/{method}",
                event_type="circuit_breaker_tripped",
                app_id=app_id,
                method=method,
                correlation_id=correlation_id
            )
            raise Exception(f"Circuit breaker tripped for {app_id}/{method}")
        
        # Perform the call with enhanced retry logic with exponential backoff and jitter
        last_exception = None
        
        for attempt in range(self.retry_settings.retry_attempts + 1):
            try:
                # Add correlation ID to metadata if available
                metadata = {}
                if correlation_id:
                    metadata["X-Correlation-ID"] = correlation_id
                
                with self.client as client:
                    # Prepare data for Dapr
                    if isinstance(data, dict):
                        data_bytes = json.dumps(data).encode('utf-8')
                    elif isinstance(data, str):
                        data_bytes = data.encode('utf-8')
                    else:
                        data_bytes = b""
                    
                    # Make the service invocation call
                    response = client.invoke_method(
                        app_id=app_id,
                        method_name=method,
                        data=data_bytes,
                        content_type='application/json',
                        metadata=metadata
                    )
                    
                    # Log successful invocation
                    logger.info(
                        f"Successfully invoked {app_id}/{method}",
                        event_type="service_invocation_success",
                        app_id=app_id,
                        method=method,
                        attempt=attempt + 1,
                        correlation_id=correlation_id
                    )
                    
                    # Reset circuit breaker on success
                    circuit_breaker.on_success()
                    
                    # Return the response data
                    response_data = response.json()
                    return response_data
                    
            except (DaprInternalError, DaprGrpcError, RpcError) as e:
                last_exception = e
                logger.warning(
                    f"Service invocation attempt {attempt + 1} failed for {app_id}/{method}: {str(e)}",
                    event_type="service_invocation_retry",
                    app_id=app_id,
                    method=method,
                    attempt=attempt + 1,
                    correlation_id=correlation_id,
                    error=str(e)
                )
                
                # Update circuit breaker on failure
                circuit_breaker.on_failure()
                
                # Wait before retry with exponential backoff and jitter
                if attempt < self.retry_settings.retry_attempts:
                    # Calculate exponential backoff with jitter to prevent thundering herd
                    base_delay = self.retry_settings.retry_delay
                    exponential_delay = base_delay * (2 ** attempt)
                    # Add jitter (random value between 0 and 1) to prevent synchronized retries
                    jitter = random.uniform(0.5, 1.0)
                    delay = exponential_delay * jitter
                    
                    logger.info(
                        f"Waiting {delay:.2f}s before retry {attempt + 2}",
                        event_type="retry_delay",
                        attempt=attempt + 2,
                        delay=delay,
                        correlation_id=correlation_id
                    )
                    
                    await asyncio.sleep(delay)
            
            except Exception as e:
                last_exception = e
                logger.error(
                    f"Unexpected error invoking {app_id}/{method}: {str(e)}",
                    event_type="service_invocation_error",
                    app_id=app_id,
                    method=method,
                    correlation_id=correlation_id,
                    error=str(e)
                )
                circuit_breaker.on_failure()
                break
        
        # If we exhausted all retries, log the final error
        if last_exception:
            logger.error(
                f"All retry attempts failed for {app_id}/{method}",
                event_type="service_invocation_failed",
                app_id=app_id,
                method=method,
                total_attempts=self.retry_settings.retry_attempts + 1,
                correlation_id=correlation_id,
                error=str(last_exception)
            )
            raise last_exception
        
        return None
    
    async def publish_event(self, pubsub_name: str, topic_name: str, data: Union[Dict, str]) -> bool:
        """
        Publish an event to a pub/sub topic via Dapr
        
        Args:
            pubsub_name: Name of the pub/sub component
            topic_name: Name of the topic
            data: Data to publish
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            with self.client as client:
                # Prepare data for Dapr
                if isinstance(data, dict):
                    data_bytes = json.dumps(data).encode('utf-8')
                elif isinstance(data, str):
                    data_bytes = data.encode('utf-8')
                else:
                    data_bytes = b""
                
                # Publish the event
                client.publish_event(
                    pubsub_name=pubsub_name,
                    topic_name=topic_name,
                    data=data_bytes,
                    data_content_type='application/json'
                )
                
                logger.info(
                    f"Published event to {pubsub_name}/{topic_name}",
                    event_type="dapr_event_published",
                    pubsub_name=pubsub_name,
                    topic_name=topic_name,
                    correlation_id=correlation_id
                )
                
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to publish event to {pubsub_name}/{topic_name}: {str(e)}",
                event_type="dapr_event_publish_error",
                pubsub_name=pubsub_name,
                topic_name=topic_name,
                correlation_id=correlation_id,
                error=str(e)
            )
            return False
    
    async def get_secret(self, store_name: str, key: str, metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Retrieve a secret from Dapr secret store
        
        Args:
            store_name: Name of the secret store
            key: Secret key
            metadata: Optional metadata for the request
            
        Returns:
            Optional[str]: Secret value if found, None otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            with self.client as client:
                response = client.get_secret(
                    store_name=store_name,
                    key=key,
                    metadata=metadata
                )
                
                logger.info(
                    f"Retrieved secret from {store_name}/{key}",
                    event_type="secret_retrieved",
                    store_name=store_name,
                    secret_key=key,
                    correlation_id=correlation_id
                )
                
                # Return the secret value
                return response.data.get(key) if response.data else None
                
        except Exception as e:
            logger.error(
                f"Failed to retrieve secret from {store_name}/{key}: {str(e)}",
                event_type="secret_retrieval_error",
                store_name=store_name,
                secret_key=key,
                correlation_id=correlation_id,
                error=str(e)
            )
            return None
    
    async def save_state(self, store_name: str, key: str, value: Union[Dict, str], 
                         etag: Optional[str] = None, options: Optional[Dict] = None) -> bool:
        """
        Save state to Dapr state store
        
        Args:
            store_name: Name of the state store
            key: State key
            value: Value to save
            etag: Optional etag for concurrency control
            options: Optional state options
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            with self.client as client:
                # Prepare the state item
                if isinstance(value, dict):
                    value_str = json.dumps(value)
                elif isinstance(value, str):
                    value_str = value
                else:
                    value_str = str(value)
                
                # Save the state
                client.save_state(
                    store_name=store_name,
                    key=key,
                    value=value_str,
                    etag=etag,
                    options=options
                )
                
                logger.info(
                    f"Saved state to {store_name}/{key}",
                    event_type="state_saved",
                    store_name=store_name,
                    state_key=key,
                    correlation_id=correlation_id
                )
                
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to save state to {store_name}/{key}: {str(e)}",
                event_type="state_save_error",
                store_name=store_name,
                state_key=key,
                correlation_id=correlation_id,
                error=str(e)
            )
            return False
    
    async def get_state(self, store_name: str, key: str, 
                       options: Optional[Dict] = None) -> Optional[Union[Dict, str]]:
        """
        Get state from Dapr state store
        
        Args:
            store_name: Name of the state store
            key: State key
            options: Optional state options
            
        Returns:
            Optional[Union[Dict, str]]: State value if found, None otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            with self.client as client:
                response = client.get_state(
                    store_name=store_name,
                    key=key,
                    options=options
                )
                
                logger.info(
                    f"Retrieved state from {store_name}/{key}",
                    event_type="state_retrieved",
                    store_name=store_name,
                    state_key=key,
                    correlation_id=correlation_id
                )
                
                # Try to parse as JSON if possible
                try:
                    return json.loads(response.data) if response.data else None
                except json.JSONDecodeError:
                    return response.data if response.data else None
                    
        except Exception as e:
            logger.error(
                f"Failed to retrieve state from {store_name}/{key}: {str(e)}",
                event_type="state_retrieval_error",
                store_name=store_name,
                state_key=key,
                correlation_id=correlation_id,
                error=str(e)
            )
            return None
    
    async def delete_state(self, store_name: str, key: str, 
                          options: Optional[Dict] = None) -> bool:
        """
        Delete state from Dapr state store
        
        Args:
            store_name: Name of the state store
            key: State key to delete
            options: Optional state options
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            with self.client as client:
                client.delete_state(
                    store_name=store_name,
                    key=key,
                    options=options
                )
                
                logger.info(
                    f"Deleted state from {store_name}/{key}",
                    event_type="state_deleted",
                    store_name=store_name,
                    state_key=key,
                    correlation_id=correlation_id
                )
                
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to delete state from {store_name}/{key}: {str(e)}",
                event_type="state_delete_error",
                store_name=store_name,
                state_key=key,
                correlation_id=correlation_id,
                error=str(e)
            )
            return False
    
    def get_circuit_breaker_status(self) -> Dict[str, str]:
        """
        Get the status of all circuit breakers
        
        Returns:
            Dict[str, str]: Mapping of service/method to circuit breaker state
        """
        return {key: cb.state for key, cb in self.circuit_breakers.items()}
    
    async def close(self):
        """
        Close the Dapr client connection
        """
        try:
            self.client.close()
            logger.info(
                "Closed Dapr client connection",
                event_type="dapr_client_closed"
            )
        except Exception as e:
            logger.error(
                f"Error closing Dapr client: {str(e)}",
                event_type="dapr_client_close_error",
                error=str(e)
            )


# Global instance for use throughout the application
dapr_integration_service = DaprIntegrationService()


# Context manager for temporary Dapr integration instances
class DaprIntegrationContext:
    """
    Context manager for temporary Dapr integration instances
    """
    
    def __init__(self, dapr_client_instance=None):
        self.integration_service = DaprIntegrationService(dapr_client_instance)
    
    async def __aenter__(self):
        return self.integration_service
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.integration_service.close()