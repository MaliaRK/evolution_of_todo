"""
Event Consumer Service for Todo AI System
Consumes events from Kafka via Dapr and processes them
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from dapr.ext.fastapi import DaprApp
from fastapi import FastAPI
from sqlmodel import Session, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.todo_models import Todo
from ..models.event_models import (
    BaseEventSchema,
    TaskCreatedEvent,
    TaskUpdatedEvent,
    TaskCompletedEvent,
    TaskDeletedEvent,
    ActivityLoggedEvent,
    EVENT_TYPE_TO_SCHEMA,
    EventType
)
from ..services.logging_config import get_component_logger
from ..services.jwt_propagation_util import validate_user_in_event_context
from ..config.auth_config import USER_ISOLATION_ENABLED

# Configure logging
logger = get_component_logger("event_processing")


class EventConsumer:
    """
    Service for consuming events from Kafka via Dapr pub/sub
    """

    def __init__(self, db_session: Session = None):
        """
        Initialize the event consumer

        Args:
            db_session: Database session for processing events
        """
        self.db_session = db_session
        self.processed_events = set()  # Track processed events for idempotency
        self.retry_count = {}  # Track retry attempts for each event
        self.max_retries = 3  # Maximum number of retries for failed events

    async def process_task_created_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process a task created event

        Args:
            event_data: Event data dictionary

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Deserialize the event
            event = TaskCreatedEvent(**event_data)

            logger.info(
                f"Processing task created event {event.event_id}",
                event_type="task_created_processing",
                event_id=str(event.event_id),
                user_id=str(event.user_id)
            )

            # Validate user context if isolation is enabled
            if USER_ISOLATION_ENABLED:
                is_valid = validate_user_in_event_context(event.payload, str(event.user_id))
                if not is_valid:
                    logger.error(
                        f"User validation failed for event {event.event_id}",
                        event_type="task_created_validation_failed",
                        event_id=str(event.event_id),
                        user_id=str(event.user_id)
                    )
                    return False

            # Verify user isolation - ensure the event's user_id matches expected user
            # This provides an additional layer of protection against data leakage
            event_user_id = str(event.user_id)
            payload_user_id = event.payload.get('user_id')
            if payload_user_id and str(payload_user_id) != event_user_id:
                logger.error(
                    f"User ID mismatch in event {event.event_id}: event.user_id={event_user_id}, payload.user_id={payload_user_id}",
                    event_type="user_isolation_violation",
                    event_id=str(event.event_id),
                    event_user_id=event_user_id,
                    payload_user_id=payload_user_id
                )
                return False

            # Check for idempotency - if we've already processed this event
            if str(event.event_id) in self.processed_events:
                logger.info(
                    f"Event {event.event_id} already processed (idempotency check)",
                    event_type="task_created_idempotency_check",
                    event_id=str(event.event_id)
                )
                return True

            # Process the event - in a real implementation, this would update the database
            # For now, we'll just log that we processed it
            logger.info(
                f"Processed task created event {event.event_id} for user {event.user_id}",
                event_type="task_created_processed",
                event_id=str(event.event_id),
                user_id=str(event.user_id),
                task_data=event.new_state
            )

            # Mark event as processed for idempotency
            self.processed_events.add(str(event.event_id))

            return True
        except Exception as e:
            logger.error(
                f"Error processing task created event {event_data.get('event_id', 'unknown')}: {str(e)}",
                event_type="task_created_processing_error",
                event_id=event_data.get('event_id'),
                error=str(e)
            )
            return False

    async def process_task_updated_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process a task updated event

        Args:
            event_data: Event data dictionary

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Deserialize the event
            event = TaskUpdatedEvent(**event_data)

            logger.info(
                f"Processing task updated event {event.event_id}",
                event_type="task_updated_processing",
                event_id=str(event.event_id),
                user_id=str(event.user_id)
            )

            # Validate user context if isolation is enabled
            if USER_ISOLATION_ENABLED:
                is_valid = validate_user_in_event_context(event.payload, str(event.user_id))
                if not is_valid:
                    logger.error(
                        f"User validation failed for event {event.event_id}",
                        event_type="task_updated_validation_failed",
                        event_id=str(event.event_id),
                        user_id=str(event.user_id)
                    )
                    return False

            # Verify user isolation - ensure the event's user_id matches expected user
            event_user_id = str(event.user_id)
            payload_user_id = event.payload.get('user_id')
            if payload_user_id and str(payload_user_id) != event_user_id:
                logger.error(
                    f"User ID mismatch in event {event.event_id}: event.user_id={event_user_id}, payload.user_id={payload_user_id}",
                    event_type="user_isolation_violation",
                    event_id=str(event.event_id),
                    event_user_id=event_user_id,
                    payload_user_id=payload_user_id
                )
                return False

            # Check for idempotency
            if str(event.event_id) in self.processed_events:
                logger.info(
                    f"Event {event.event_id} already processed (idempotency check)",
                    event_type="task_updated_idempotency_check",
                    event_id=str(event.event_id)
                )
                return True

            # Process the event - in a real implementation, this would update the database
            logger.info(
                f"Processed task updated event {event.event_id} for user {event.user_id}",
                event_type="task_updated_processed",
                event_id=str(event.event_id),
                user_id=str(event.user_id),
                task_id=str(event.task_id),
                fields_changed=event.payload.get("fields_changed", [])
            )

            # Mark event as processed for idempotency
            self.processed_events.add(str(event.event_id))

            return True
        except Exception as e:
            logger.error(
                f"Error processing task updated event {event_data.get('event_id', 'unknown')}: {str(e)}",
                event_type="task_updated_processing_error",
                event_id=event_data.get('event_id'),
                error=str(e)
            )
            return False

    async def process_task_completed_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process a task completed event

        Args:
            event_data: Event data dictionary

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Deserialize the event
            event = TaskCompletedEvent(**event_data)

            logger.info(
                f"Processing task completed event {event.event_id}",
                event_type="task_completed_processing",
                event_id=str(event.event_id),
                user_id=str(event.user_id)
            )

            # Validate user context if isolation is enabled
            if USER_ISOLATION_ENABLED:
                is_valid = validate_user_in_event_context(event.payload, str(event.user_id))
                if not is_valid:
                    logger.error(
                        f"User validation failed for event {event.event_id}",
                        event_type="task_completed_validation_failed",
                        event_id=str(event.event_id),
                        user_id=str(event.user_id)
                    )
                    return False

            # Verify user isolation - ensure the event's user_id matches expected user
            event_user_id = str(event.user_id)
            payload_user_id = event.payload.get('user_id')
            if payload_user_id and str(payload_user_id) != event_user_id:
                logger.error(
                    f"User ID mismatch in event {event.event_id}: event.user_id={event_user_id}, payload.user_id={payload_user_id}",
                    event_type="user_isolation_violation",
                    event_id=str(event.event_id),
                    event_user_id=event_user_id,
                    payload_user_id=payload_user_id
                )
                return False

            # Check for idempotency
            if str(event.event_id) in self.processed_events:
                logger.info(
                    f"Event {event.event_id} already processed (idempotency check)",
                    event_type="task_completed_idempotency_check",
                    event_id=str(event.event_id)
                )
                return True

            # Process the event - in a real implementation, this would update the database
            logger.info(
                f"Processed task completed event {event.event_id} for user {event.user_id}",
                event_type="task_completed_processed",
                event_id=str(event.event_id),
                user_id=str(event.user_id),
                task_id=str(event.task_id)
            )

            # Mark event as processed for idempotency
            self.processed_events.add(str(event.event_id))

            return True
        except Exception as e:
            logger.error(
                f"Error processing task completed event {event_data.get('event_id', 'unknown')}: {str(e)}",
                event_type="task_completed_processing_error",
                event_id=event_data.get('event_id'),
                error=str(e)
            )
            return False

    async def process_task_deleted_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process a task deleted event

        Args:
            event_data: Event data dictionary

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Deserialize the event
            event = TaskDeletedEvent(**event_data)

            logger.info(
                f"Processing task deleted event {event.event_id}",
                event_type="task_deleted_processing",
                event_id=str(event.event_id),
                user_id=str(event.user_id)
            )

            # Validate user context if isolation is enabled
            if USER_ISOLATION_ENABLED:
                is_valid = validate_user_in_event_context(event.payload, str(event.user_id))
                if not is_valid:
                    logger.error(
                        f"User validation failed for event {event.event_id}",
                        event_type="task_deleted_validation_failed",
                        event_id=str(event.event_id),
                        user_id=str(event.user_id)
                    )
                    return False

            # Verify user isolation - ensure the event's user_id matches expected user
            event_user_id = str(event.user_id)
            payload_user_id = event.payload.get('user_id')
            if payload_user_id and str(payload_user_id) != event_user_id:
                logger.error(
                    f"User ID mismatch in event {event.event_id}: event.user_id={event_user_id}, payload.user_id={payload_user_id}",
                    event_type="user_isolation_violation",
                    event_id=str(event.event_id),
                    event_user_id=event_user_id,
                    payload_user_id=payload_user_id
                )
                return False

            # Check for idempotency
            if str(event.event_id) in self.processed_events:
                logger.info(
                    f"Event {event.event_id} already processed (idempotency check)",
                    event_type="task_deleted_idempotency_check",
                    event_id=str(event.event_id)
                )
                return True

            # Process the event - in a real implementation, this would update the database
            logger.info(
                f"Processed task deleted event {event.event_id} for user {event.user_id}",
                event_type="task_deleted_processed",
                event_id=str(event.event_id),
                user_id=str(event.user_id),
                task_id=str(event.task_id)
            )

            # Mark event as processed for idempotency
            self.processed_events.add(str(event.event_id))

            return True
        except Exception as e:
            logger.error(
                f"Error processing task deleted event {event_data.get('event_id', 'unknown')}: {str(e)}",
                event_type="task_deleted_processing_error",
                event_id=event_data.get('event_id'),
                error=str(e)
            )
            return False

    async def process_activity_logged_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process an activity logged event

        Args:
            event_data: Event data dictionary

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Deserialize the event
            event = ActivityLoggedEvent(**event_data)

            logger.info(
                f"Processing activity logged event {event.event_id}",
                event_type="activity_logged_processing",
                event_id=str(event.event_id),
                user_id=str(event.user_id),
                activity_type=event.activity_type
            )

            # Validate user context if isolation is enabled
            if USER_ISOLATION_ENABLED:
                is_valid = validate_user_in_event_context(event.payload, str(event.user_id))
                if not is_valid:
                    logger.error(
                        f"User validation failed for event {event.event_id}",
                        event_type="activity_logged_validation_failed",
                        event_id=str(event.event_id),
                        user_id=str(event.user_id)
                    )
                    return False

            # Verify user isolation - ensure the event's user_id matches expected user
            event_user_id = str(event.user_id)
            payload_user_id = event.payload.get('user_id')
            if payload_user_id and str(payload_user_id) != event_user_id:
                logger.error(
                    f"User ID mismatch in event {event.event_id}: event.user_id={event_user_id}, payload.user_id={payload_user_id}",
                    event_type="user_isolation_violation",
                    event_id=str(event.event_id),
                    event_user_id=event_user_id,
                    payload_user_id=payload_user_id
                )
                return False

            # Check for idempotency
            if str(event.event_id) in self.processed_events:
                logger.info(
                    f"Event {event.event_id} already processed (idempotency check)",
                    event_type="activity_logged_idempotency_check",
                    event_id=str(event.event_id)
                )
                return True

            # Process the event - in a real implementation, this would store in analytics database
            logger.info(
                f"Processed activity logged event {event.event_id} for user {event.user_id}",
                event_type="activity_logged_processed",
                event_id=str(event.event_id),
                user_id=str(event.user_id),
                activity_type=event.activity_type,
                metadata=event.metadata
            )

            # Mark event as processed for idempotency
            self.processed_events.add(str(event.event_id))

            return True
        except Exception as e:
            logger.error(
                f"Error processing activity logged event {event_data.get('event_id', 'unknown')}: {str(e)}",
                event_type="activity_logged_processing_error",
                event_id=event_data.get('event_id'),
                error=str(e)
            )
            return False

    async def consume_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Main method to consume and process an event based on its type

        Args:
            event_data: Event data dictionary

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        # Get the event ID and type
        event_id = event_data.get("event_id")
        event_type = event_data.get("event_type", "")

        logger.info(
            f"Consuming event of type {event_type}",
            event_type="event_consumption_started",
            event_id=event_id,
            event_type_detail=event_type
        )

        # Validate the event schema first
        is_valid, error_msg = self.validate_event_schema(event_data)
        if not is_valid:
            logger.error(
                f"Event schema validation failed: {error_msg}",
                event_type="event_schema_validation_failed",
                event_id=event_id,
                error=error_msg
            )
            # Move to dead letter queue for invalid events
            self.add_to_dead_letter_queue(event_data, error_msg)
            return False

        # Check for idempotency - if we've already processed this event
        if event_id in self.processed_events:
            logger.info(
                f"Event {event_id} already processed (idempotency check)",
                event_type="event_idempotency_check",
                event_id=event_id
            )
            return True

        # Process based on event type
        success = False
        if event_type == EventType.TASK_CREATED:
            success = await self.process_task_created_event(event_data)
        elif event_type == EventType.TASK_UPDATED:
            success = await self.process_task_updated_event(event_data)
        elif event_type == EventType.TASK_COMPLETED:
            success = await self.process_task_completed_event(event_data)
        elif event_type == EventType.TASK_DELETED:
            success = await self.process_task_deleted_event(event_data)
        elif event_type == EventType.ACTIVITY_LOGGED:
            success = await self.process_activity_logged_event(event_data)
        else:
            logger.warning(
                f"Unknown event type: {event_type}",
                event_type="unknown_event_type",
                event_id=event_id
            )
            # Don't add to dead letter queue for unknown event types, just log
            return False

        # Handle success or failure
        if success:
            # Mark event as processed for idempotency
            self.processed_events.add(event_id)
            logger.info(
                f"Successfully processed event {event_id}",
                event_type="event_processing_success",
                event_id=event_id
            )
            return True
        else:
            # Track retry attempts
            if event_id not in self.retry_count:
                self.retry_count[event_id] = 0
            self.retry_count[event_id] += 1

            if self.retry_count[event_id] <= self.max_retries:
                logger.warning(
                    f"Event {event_id} processing failed, will retry ({self.retry_count[event_id]}/{self.max_retries})",
                    event_type="event_processing_retry",
                    event_id=event_id,
                    retry_count=self.retry_count[event_id]
                )
                return False  # Return False to indicate processing should be retried
            else:
                logger.error(
                    f"Event {event_id} failed after {self.max_retries} retries, moving to dead letter queue",
                    event_type="event_processing_failed_permanently",
                    event_id=event_id,
                    max_retries=self.max_retries
                )
                self.add_to_dead_letter_queue(event_data, f"Failed after {self.max_retries} retries")
                return False

    def add_to_dead_letter_queue(self, event_data: Dict[str, Any], error: str):
        """
        Move a failed event to the dead letter queue

        Args:
            event_data: The failed event data
            error: Error message
        """
        # Add error information to the event data
        enriched_event_data = event_data.copy()
        enriched_event_data['dlq_error'] = error
        enriched_event_data['dlq_timestamp'] = datetime.utcnow().isoformat()
        enriched_event_data['dlq_processing_attempts'] = self.retry_count.get(event_data.get('event_id'), 1)

        logger.error(
            f"Moving event to dead letter queue: {error}",
            event_type="event_moved_to_dlq",
            event_id=event_data.get("event_id"),
            error=error,
            processing_attempts=enriched_event_data['dlq_processing_attempts']
        )

        # In a real implementation, this would send the event to a dead letter topic via Dapr
        # For now, we'll simulate sending to a dead letter queue
        try:
            from .event_publisher import event_publisher
            # Publish to dead letter topic
            asyncio.create_task(
                event_publisher.publish_to_dead_letter_queue(enriched_event_data, error)
            )
        except Exception as e:
            logger.error(
                f"Failed to publish to dead letter queue: {str(e)}",
                event_type="dlq_publish_error",
                error=str(e)
            )

    def validate_event_schema(self, event_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that the event conforms to the expected schema

        Args:
            event_data: Event data to validate

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            event_type = event_data.get("event_type", "")
            if not event_type:
                return False, "Missing event_type field"

            # Check if event type is recognized
            if event_type not in EVENT_TYPE_TO_SCHEMA:
                return False, f"Unknown event type: {event_type}"

            # Validate required fields
            required_fields = ["event_id", "user_id", "correlation_id", "timestamp", "payload"]
            for field in required_fields:
                if field not in event_data:
                    return False, f"Missing required field: {field}"

            return True, None
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"


# Global instance of the event consumer
event_consumer = EventConsumer()