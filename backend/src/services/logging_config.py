"""
Structured Logging Configuration for Event Processing in Todo AI System
Sets up structured logging for observability across distributed services
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
import sys
from pathlib import Path

from ..config.auth_config import CORRELATION_ID_HEADER


class StructuredLogger:
    """
    A structured logger that outputs JSON-formatted logs with consistent fields
    for better observability in distributed systems
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize the structured logger

        Args:
            name: Logger name
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers if logger already has handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Disable propagation to prevent duplicate logs
        self.logger.propagate = False

    def _log_structured(self, level: int, message: str, event_type: str, **kwargs):
        """
        Internal method to log structured data

        Args:
            level: Log level
            message: Log message
            event_type: Type of event being logged
            **kwargs: Additional structured data
        """
        if self.logger.isEnabledFor(level):
            # Add common fields to the log record
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": logging.getLevelName(level),
                "message": message,
                "event_type": event_type,
                **kwargs
            }

            # Create a log record with structured data
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                __file__,
                0,  # lineno
                json.dumps(log_data),
                (),  # args
                None  # exc_info
            )
            self.logger.handle(record)

    def info(self, message: str, event_type: str = "info", **kwargs):
        """Log an info message with structured data"""
        self._log_structured(logging.INFO, message, event_type, **kwargs)

    def debug(self, message: str, event_type: str = "debug", **kwargs):
        """Log a debug message with structured data"""
        self._log_structured(logging.DEBUG, message, event_type, **kwargs)

    def warning(self, message: str, event_type: str = "warning", **kwargs):
        """Log a warning message with structured data"""
        self._log_structured(logging.WARNING, message, event_type, **kwargs)

    def error(self, message: str, event_type: str = "error", **kwargs):
        """Log an error message with structured data"""
        self._log_structured(logging.ERROR, message, event_type, **kwargs)

    def critical(self, message: str, event_type: str = "critical", **kwargs):
        """Log a critical message with structured data"""
        self._log_structured(logging.CRITICAL, message, event_type, **kwargs)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that ensures logs are in structured JSON format
    """

    def format(self, record):
        """
        Format the log record as a JSON string

        Args:
            record: Log record to format

        Returns:
            str: JSON-formatted log string
        """
        # Parse the message assuming it's already JSON from StructuredLogger
        try:
            log_json = json.loads(record.getMessage())
        except json.JSONDecodeError:
            # If it's not JSON, treat as plain message
            log_json = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage()
            }

        # Add any exception info if present
        if record.exc_info:
            log_json["exception"] = self.formatException(record.exc_info)

        # Add thread info if available
        if hasattr(record, 'thread'):
            log_json["thread_id"] = record.thread

        return json.dumps(log_json)


def setup_logging(service_name: str = "todo-backend"):
    """
    Set up structured logging for the application

    Args:
        service_name: Name of the service for logging context
    """
    # Create a root structured logger for the service
    root_logger = StructuredLogger(service_name)

    # Set up loggers for specific components
    loggers = {
        "event_processing": StructuredLogger(f"{service_name}.event_processing"),
        "kafka": StructuredLogger(f"{service_name}.kafka"),
        "dapr": StructuredLogger(f"{service_name}.dapr"),
        "auth": StructuredLogger(f"{service_name}.auth"),
        "database": StructuredLogger(f"{service_name}.database"),
        "api": StructuredLogger(f"{service_name}.api")
    }

    return root_logger, loggers


def log_event_processing_start(
    logger: StructuredLogger,
    event_id: UUID,
    event_type: str,
    user_id: UUID,
    correlation_id: Optional[UUID] = None
):
    """
    Log the start of event processing

    Args:
        logger: Structured logger instance
        event_id: ID of the event being processed
        event_type: Type of event
        user_id: User ID associated with the event
        correlation_id: Correlation ID for request tracing
    """
    logger.info(
        f"Starting processing of {event_type} event",
        event_type="event_processing_started",
        event_id=str(event_id),
        event_type_detail=event_type,
        user_id=str(user_id),
        correlation_id=str(correlation_id) if correlation_id else None
    )


def log_event_processing_success(
    logger: StructuredLogger,
    event_id: UUID,
    event_type: str,
    user_id: UUID,
    duration_ms: float,
    correlation_id: Optional[UUID] = None
):
    """
    Log successful event processing

    Args:
        logger: Structured logger instance
        event_id: ID of the processed event
        event_type: Type of event
        user_id: User ID associated with the event
        duration_ms: Processing duration in milliseconds
        correlation_id: Correlation ID for request tracing
    """
    logger.info(
        f"Successfully processed {event_type} event",
        event_type="event_processing_success",
        event_id=str(event_id),
        event_type_detail=event_type,
        user_id=str(user_id),
        duration_ms=duration_ms,
        correlation_id=str(correlation_id) if correlation_id else None
    )


def log_event_processing_error(
    logger: StructuredLogger,
    event_id: UUID,
    event_type: str,
    user_id: UUID,
    error_message: str,
    correlation_id: Optional[UUID] = None,
    stack_trace: Optional[str] = None
):
    """
    Log failed event processing

    Args:
        logger: Structured logger instance
        event_id: ID of the event that failed to process
        event_type: Type of event
        user_id: User ID associated with the event
        error_message: Error message
        correlation_id: Correlation ID for request tracing
        stack_trace: Optional stack trace
    """
    logger.error(
        f"Failed to process {event_type} event: {error_message}",
        event_type="event_processing_error",
        event_id=str(event_id),
        event_type_detail=event_type,
        user_id=str(user_id),
        error=str(error_message),
        correlation_id=str(correlation_id) if correlation_id else None,
        stack_trace=stack_trace
    )


def log_event_validation_result(
    logger: StructuredLogger,
    event_id: UUID,
    event_type: str,
    is_valid: bool,
    validation_errors: Optional[list] = None,
    correlation_id: Optional[UUID] = None
):
    """
    Log event validation results

    Args:
        logger: Structured logger instance
        event_id: ID of the event being validated
        event_type: Type of event
        is_valid: Whether the event passed validation
        validation_errors: List of validation errors (if any)
        correlation_id: Correlation ID for request tracing
    """
    if is_valid:
        logger.info(
            f"Event {event_id} passed validation",
            event_type="event_validation_passed",
            event_id=str(event_id),
            event_type_detail=event_type,
            correlation_id=str(correlation_id) if correlation_id else None
        )
    else:
        logger.error(
            f"Event {event_id} failed validation",
            event_type="event_validation_failed",
            event_id=str(event_id),
            event_type_detail=event_type,
            validation_errors=validation_errors,
            correlation_id=str(correlation_id) if correlation_id else None
        )


def log_dead_letter_queue_addition(
    logger: StructuredLogger,
    event_id: UUID,
    event_type: str,
    reason: str,
    original_topic: str,
    correlation_id: Optional[UUID] = None
):
    """
    Log when an event is moved to the dead letter queue

    Args:
        logger: Structured logger instance
        event_id: ID of the event being moved to DLQ
        event_type: Type of event
        reason: Reason for moving to DLQ
        original_topic: Original topic the event came from
        correlation_id: Correlation ID for request tracing
    """
    logger.warning(
        f"Moving event {event_id} to dead letter queue",
        event_type="event_moved_to_dlq",
        event_id=str(event_id),
        event_type_detail=event_type,
        dlq_reason=reason,
        original_topic=original_topic,
        correlation_id=str(correlation_id) if correlation_id else None
    )


def log_idempotency_check(
    logger: StructuredLogger,
    event_id: UUID,
    event_type: str,
    is_duplicate: bool,
    correlation_id: Optional[UUID] = None
):
    """
    Log idempotency check results

    Args:
        logger: Structured logger instance
        event_id: ID of the event being checked
        event_type: Type of event
        is_duplicate: Whether the event is a duplicate
        correlation_id: Correlation ID for request tracing
    """
    if is_duplicate:
        logger.info(
            f"Duplicate event {event_id} detected (idempotency check)",
            event_type="duplicate_event_detected",
            event_id=str(event_id),
            event_type_detail=event_type,
            correlation_id=str(correlation_id) if correlation_id else None
        )
    else:
        logger.info(
            f"New event {event_id} passed idempotency check",
            event_type="event_idempotency_check_passed",
            event_id=str(event_id),
            event_type_detail=event_type,
            correlation_id=str(correlation_id) if correlation_id else None
        )


def log_user_action(
    logger: StructuredLogger,
    action: str,
    user_id: UUID,
    resource: str,
    resource_id: Optional[UUID] = None,
    correlation_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log user actions for audit and analytics

    Args:
        logger: Structured logger instance
        action: Action performed by the user
        user_id: User ID
        resource: Resource acted upon
        resource_id: Resource ID (optional)
        correlation_id: Correlation ID for request tracing
        metadata: Additional metadata about the action
    """
    logger.info(
        f"User {user_id} performed action: {action}",
        event_type="user_action",
        action=action,
        user_id=str(user_id),
        resource=resource,
        resource_id=str(resource_id) if resource_id else None,
        correlation_id=str(correlation_id) if correlation_id else None,
        metadata=metadata or {}
    )


def log_kafka_operation(
    logger: StructuredLogger,
    operation: str,
    topic: str,
    event_type: Optional[str] = None,
    partition: Optional[int] = None,
    offset: Optional[int] = None,
    correlation_id: Optional[UUID] = None
):
    """
    Log Kafka operations for monitoring

    Args:
        logger: Structured logger instance
        operation: Operation performed (produce, consume, etc.)
        topic: Kafka topic name
        event_type: Type of event (optional)
        partition: Partition number (optional)
        offset: Message offset (optional)
        correlation_id: Correlation ID for request tracing
    """
    logger.info(
        f"Kafka {operation} operation on topic {topic}",
        event_type="kafka_operation",
        kafka_operation=operation,
        kafka_topic=topic,
        event_type_detail=event_type,
        partition=partition,
        offset=offset,
        correlation_id=str(correlation_id) if correlation_id else None
    )


# Global logger instances
ROOT_LOGGER, COMPONENT_LOGGERS = setup_logging()


# Convenience functions for common logging scenarios
def get_component_logger(component_name: str) -> StructuredLogger:
    """
    Get a logger for a specific component

    Args:
        component_name: Name of the component

    Returns:
        StructuredLogger: Logger instance for the component
    """
    return COMPONENT_LOGGERS.get(component_name, ROOT_LOGGER)


def log_api_request(
    logger: StructuredLogger,
    method: str,
    path: str,
    user_id: Optional[UUID] = None,
    correlation_id: Optional[UUID] = None,
    response_status: Optional[int] = None,
    duration_ms: Optional[float] = None
):
    """
    Log API requests for monitoring and debugging

    Args:
        logger: Structured logger instance
        method: HTTP method
        path: Request path
        user_id: User ID (optional)
        correlation_id: Correlation ID for request tracing
        response_status: Response status code (optional)
        duration_ms: Request duration in milliseconds (optional)
    """
    logger.info(
        f"API {method} {path} request",
        event_type="api_request",
        http_method=method,
        path=path,
        user_id=str(user_id) if user_id else None,
        correlation_id=str(correlation_id) if correlation_id else None,
        response_status=response_status,
        duration_ms=duration_ms
    )