"""
Dead Letter Queue Processor for Todo AI System
Handles processing of failed events that couldn't be processed normally
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from dapr.ext.fastapi import DaprApp
from fastapi import FastAPI
from sqlmodel import Session, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

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
from ..services.logging_config import get_component_logger, log_dead_letter_queue_addition
from ..services.event_publisher import event_publisher
from ..config.connection_config import get_connection_settings

# Configure logging
logger = get_component_logger("event_processing")


class DeadLetterProcessor:
    """
    Service for processing events from the dead letter queue
    """

    def __init__(self, db_session: Session = None):
        """
        Initialize the dead letter processor

        Args:
            db_session: Database session for processing events
        """
        self.db_session = db_session
        self.settings = get_connection_settings()
        self.max_redelivery_attempts = 5  # Max attempts to reprocess a dead letter event
        self.redelivery_delay_seconds = 60  # Delay before redelivering an event
        self.processed_events = set()  # Track processed events to avoid infinite loops

    async def process_dead_letter_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process a dead letter event by attempting to reprocess it

        Args:
            event_data: Event data dictionary from the dead letter queue

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Extract original event data (before it was put in DLQ)
            original_event_data = self.extract_original_event_data(event_data)
            event_id = original_event_data.get("event_id")
            event_type = original_event_data.get("event_type", "")

            logger.info(
                f"Attempting to reprocess dead letter event {event_id}",
                event_type="dlq_reprocessing_started",
                event_id=event_id,
                original_error=event_data.get("dlq_error"),
                processing_attempts=event_data.get("dlq_processing_attempts", 1)
            )

            # Check if we've already tried to reprocess this event too many times
            if event_data.get("dlq_processing_attempts", 0) >= self.max_redelivery_attempts:
                logger.error(
                    f"Event {event_id} exceeded max reprocessing attempts, moving to permanent failure",
                    event_type="dlq_max_attempts_exceeded",
                    event_id=event_id,
                    max_attempts=self.max_redelivery_attempts
                )
                await self.handle_permanent_failure(event_data)
                return False

            # Attempt to reprocess the original event
            success = await self.reprocess_original_event(original_event_data)

            if success:
                logger.info(
                    f"Successfully reprocessed dead letter event {event_id}",
                    event_type="dlq_reprocessing_success",
                    event_id=event_id
                )
                return True
            else:
                # Failed again, increment attempt count and put back in DLQ
                updated_event_data = event_data.copy()
                updated_event_data["dlq_processing_attempts"] = event_data.get("dlq_processing_attempts", 1) + 1
                updated_event_data["dlq_last_retry"] = datetime.utcnow().isoformat()

                logger.warning(
                    f"Dead letter event {event_id} failed reprocessing, putting back in DLQ",
                    event_type="dlq_reprocessing_failed",
                    event_id=event_id,
                    new_attempt_count=updated_event_data["dlq_processing_attempts"]
                )

                # Put back in dead letter queue with incremented attempt count
                await self.put_back_in_dead_letter_queue(updated_event_data, "Reprocessing failed")
                return False

        except Exception as e:
            logger.error(
                f"Error processing dead letter event {event_data.get('event_id', 'unknown')}: {str(e)}",
                event_type="dlq_processing_error",
                event_id=event_data.get('event_id'),
                error=str(e)
            )
            return False

    def extract_original_event_data(self, dlq_event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the original event data from dead letter queue data

        Args:
            dlq_event_data: Event data from the dead letter queue

        Returns:
            Dict[str, Any]: Original event data
        """
        # Create a copy and remove DLQ-specific fields to get the original event
        original_data = dlq_event_data.copy()
        dlq_fields = ["dlq_error", "dlq_timestamp", "dlq_processing_attempts", "dlq_last_retry"]
        for field in dlq_fields:
            original_data.pop(field, None)
        
        return original_data

    async def reprocess_original_event(self, original_event_data: Dict[str, Any]) -> bool:
        """
        Reprocess the original event by routing it to the appropriate handler

        Args:
            original_event_data: Original event data to reprocess

        Returns:
            bool: True if reprocessing succeeded, False otherwise
        """
        try:
            event_type = original_event_data.get("event_type", "")

            # Import the main event consumer to reuse processing logic
            from .event_consumer import event_consumer
            
            # Temporarily increase the retry limit for reprocessing
            original_max_retries = event_consumer.max_retries
            event_consumer.max_retries = 1  # Don't retry within reprocessing
            
            # Process the event using the main consumer logic
            success = await event_consumer.consume_event(original_event_data)
            
            # Restore original retry limit
            event_consumer.max_retries = original_max_retries
            
            return success
        except Exception as e:
            logger.error(
                f"Error in reprocessing logic: {str(e)}",
                event_type="dlq_reprocessing_logic_error",
                error=str(e)
            )
            return False

    async def put_back_in_dead_letter_queue(self, event_data: Dict[str, Any], reason: str):
        """
        Put an event back in the dead letter queue with updated information

        Args:
            event_data: Event data to put back in DLQ
            reason: Reason for putting back in DLQ
        """
        try:
            # Add updated information
            event_data["dlq_error"] = reason
            event_data["dlq_timestamp"] = datetime.utcnow().isoformat()
            
            # Publish back to dead letter queue
            success = await event_publisher.publish_to_dead_letter_queue(event_data, reason)
            
            if success:
                logger.info(
                    f"Event put back in dead letter queue",
                    event_type="event_put_back_in_dlq",
                    event_id=event_data.get("event_id")
                )
            else:
                logger.error(
                    f"Failed to put event back in dead letter queue",
                    event_type="dlq_put_back_failed",
                    event_id=event_data.get("event_id")
                )
        except Exception as e:
            logger.error(
                f"Error putting event back in dead letter queue: {str(e)}",
                event_type="dlq_put_back_error",
                event_id=event_data.get("event_id"),
                error=str(e)
            )

    async def handle_permanent_failure(self, event_data: Dict[str, Any]):
        """
        Handle an event that has permanently failed processing

        Args:
            event_data: Event data that permanently failed
        """
        logger.error(
            f"Handling permanent failure for event {event_data.get('event_id')}",
            event_type="permanent_failure_handled",
            event_id=event_data.get("event_id"),
            original_error=event_data.get("dlq_error")
        )
        
        # In a real implementation, you might:
        # 1. Send an alert/notification
        # 2. Store in a permanent failure archive
        # 3. Notify administrators
        # 4. Trigger manual intervention workflow
        
        # For now, just log the permanent failure
        pass

    async def process_stale_events(self, max_age_hours: int = 24) -> int:
        """
        Process stale events that have been in the DLQ for too long

        Args:
            max_age_hours: Maximum age in hours before considering an event stale

        Returns:
            int: Number of stale events processed
        """
        logger.info(
            f"Processing stale events older than {max_age_hours} hours",
            event_type="dlq_stale_processing_started",
            max_age_hours=max_age_hours
        )
        
        # In a real implementation, this would:
        # 1. Query the DLQ for events older than max_age_hours
        # 2. Attempt to reprocess them with special handling
        # 3. Move permanently failed ones to an archive
        
        # For now, return 0 as we don't have a persistent DLQ
        return 0

    async def get_dlq_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the dead letter queue

        Returns:
            Dict[str, Any]: Statistics about the DLQ
        """
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_dlq_events": 0,  # Would come from actual DLQ storage
            "events_by_type": {},
            "avg_processing_time": None,
            "failed_events_by_error": {},
            "oldest_event_age_minutes": None
        }
        
        # In a real implementation, this would query the actual DLQ storage
        # to get real statistics
        
        logger.info(
            "DLQ statistics retrieved",
            event_type="dlq_stats_retrieved",
            stats=stats
        )
        
        return stats

    async def retry_specific_event(self, event_id: str) -> bool:
        """
        Retry processing a specific event from the dead letter queue

        Args:
            event_id: ID of the event to retry

        Returns:
            bool: True if retry was initiated successfully, False otherwise
        """
        logger.info(
            f"Initiating retry for specific DLQ event {event_id}",
            event_type="dlq_specific_retry_initiated",
            event_id=event_id
        )
        
        # In a real implementation, this would:
        # 1. Find the specific event in the DLQ
        # 2. Remove it from the DLQ
        # 3. Re-attempt processing
        
        # For now, return False as we don't have a persistent DLQ
        return False

    async def flush_dlq_to_archive(self) -> bool:
        """
        Flush all events from the dead letter queue to a permanent archive

        Returns:
            bool: True if flush was successful, False otherwise
        """
        logger.info(
            "Initiating flush of DLQ to archive",
            event_type="dlq_flush_to_archive_initiated"
        )
        
        # In a real implementation, this would:
        # 1. Move all events from DLQ to a permanent archive
        # 2. Keep track of archived events for compliance/review
        
        # For now, return True
        return True


# Global instance of the dead letter processor
dead_letter_processor = DeadLetterProcessor()