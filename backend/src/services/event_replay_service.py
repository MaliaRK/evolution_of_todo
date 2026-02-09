"""
Event Replay Service for Todo AI System
Enables replay of events for recovery scenarios and debugging
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum

from sqlmodel import Session, select
from dapr.clients import DaprClient

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
from ..services.logging_config import get_component_logger, log_event_processing_error
from ..services.event_publisher import event_publisher
from ..services.event_consumer import event_consumer
from ..config.connection_config import get_connection_settings

# Configure logging
logger = get_component_logger("event_processing")


class ReplayMode(Enum):
    """
    Different modes for event replay
    """
    SEQUENTIAL = "sequential"  # Replay events in chronological order
    PARALLEL = "parallel"      # Replay events in parallel (with caution)
    BATCH = "batch"           # Replay events in batches


class EventReplayService:
    """
    Service for replaying events for recovery and debugging purposes
    """

    def __init__(self, db_session: Session = None, dapr_client_instance=None):
        """
        Initialize the event replay service

        Args:
            db_session: Database session for accessing events
            dapr_client_instance: Dapr client instance
        """
        self.db_session = db_session
        self.dapr_client = dapr_client_instance or DaprClient()
        self.settings = get_connection_settings()
        self.max_concurrent_replays = 10  # Max concurrent replays in parallel mode
        self.batch_size = 100  # Events per batch in batch mode
        self.replay_history = []  # Track replay operations

    async def replay_event_by_id(self, event_id: str, force_replay: bool = False) -> bool:
        """
        Replay a specific event by its ID

        Args:
            event_id: ID of the event to replay
            force_replay: Whether to force replay even if already processed

        Returns:
            bool: True if replay was successful, False otherwise
        """
        logger.info(
            f"Initiating replay for event {event_id}",
            event_type="event_replay_started",
            event_id=event_id,
            force_replay=force_replay
        )

        try:
            # In a real implementation, this would fetch the event from storage
            # For now, we'll simulate retrieving an event
            event_data = await self.fetch_event_by_id(event_id)
            
            if not event_data:
                logger.error(
                    f"Event {event_id} not found for replay",
                    event_type="event_replay_not_found",
                    event_id=event_id
                )
                return False

            # If not forcing replay, check if event was already processed recently
            if not force_replay and await self.was_recently_processed(event_id):
                logger.warning(
                    f"Event {event_id} was recently processed, skipping replay (use force_replay=True to override)",
                    event_type="event_replay_skipped_recent",
                    event_id=event_id
                )
                return False

            # Process the event using the consumer
            success = await event_consumer.consume_event(event_data)

            if success:
                logger.info(
                    f"Successfully replayed event {event_id}",
                    event_type="event_replay_success",
                    event_id=event_id
                )
                
                # Record the replay operation
                await self.record_replay_operation(event_id, "success")
            else:
                logger.error(
                    f"Failed to replay event {event_id}",
                    event_type="event_replay_failed",
                    event_id=event_id
                )
                
                # Record the replay operation
                await self.record_replay_operation(event_id, "failed")

            return success

        except Exception as e:
            logger.error(
                f"Error replaying event {event_id}: {str(e)}",
                event_type="event_replay_error",
                event_id=event_id,
                error=str(e)
            )
            return False

    async def replay_events_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        event_types: Optional[List[str]] = None,
        mode: ReplayMode = ReplayMode.SEQUENTIAL
    ) -> Dict[str, Any]:
        """
        Replay events within a specific time range

        Args:
            start_time: Start time for the range
            end_time: End time for the range
            event_types: List of event types to replay (None means all types)
            mode: Replay mode (SEQUENTIAL, PARALLEL, or BATCH)

        Returns:
            Dict[str, Any]: Replay results with counts and status
        """
        logger.info(
            f"Initiating replay for events from {start_time} to {end_time}",
            event_type="event_replay_range_started",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            event_types=event_types,
            mode=mode.value
        )

        try:
            # In a real implementation, this would fetch events from storage
            # For now, we'll simulate retrieving events
            events = await self.fetch_events_by_time_range(start_time, end_time, event_types)
            
            if not events:
                logger.info(
                    f"No events found for replay in time range",
                    event_type="event_replay_range_no_events",
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )
                return {
                    "total_events": 0,
                    "successful_replays": 0,
                    "failed_replays": 0,
                    "skipped_replays": 0,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }

            logger.info(
                f"Found {len(events)} events for replay",
                event_type="event_replay_range_found",
                event_count=len(events),
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )

            # Replay based on the selected mode
            if mode == ReplayMode.SEQUENTIAL:
                results = await self._replay_sequentially(events)
            elif mode == ReplayMode.PARALLEL:
                results = await self._replay_in_parallel(events)
            elif mode == ReplayMode.BATCH:
                results = await self._replay_in_batches(events)
            else:
                raise ValueError(f"Unsupported replay mode: {mode}")

            logger.info(
                f"Completed replay for time range with results: {results}",
                event_type="event_replay_range_completed",
                results=results
            )

            return results

        except Exception as e:
            logger.error(
                f"Error replaying events in time range: {str(e)}",
                event_type="event_replay_range_error",
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                error=str(e)
            )
            return {
                "total_events": 0,
                "successful_replays": 0,
                "failed_replays": 0,
                "skipped_replays": 0,
                "error": str(e)
            }

    async def replay_events_by_user(
        self, 
        user_id: str, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None,
        mode: ReplayMode = ReplayMode.SEQUENTIAL
    ) -> Dict[str, Any]:
        """
        Replay events for a specific user

        Args:
            user_id: ID of the user whose events to replay
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            mode: Replay mode

        Returns:
            Dict[str, Any]: Replay results
        """
        logger.info(
            f"Initiating replay for events for user {user_id}",
            event_type="event_replay_user_started",
            user_id=user_id,
            start_time=start_time.isoformat() if start_time else None,
            end_time=end_time.isoformat() if end_time else None
        )

        try:
            # In a real implementation, this would fetch user events from storage
            # For now, we'll simulate retrieving events
            events = await self.fetch_events_by_user(user_id, start_time, end_time)
            
            if not events:
                logger.info(
                    f"No events found for user {user_id}",
                    event_type="event_replay_user_no_events",
                    user_id=user_id
                )
                return {
                    "total_events": 0,
                    "successful_replays": 0,
                    "failed_replays": 0,
                    "skipped_replays": 0,
                    "user_id": user_id
                }

            logger.info(
                f"Found {len(events)} events for user {user_id}",
                event_type="event_replay_user_found",
                user_id=user_id,
                event_count=len(events)
            )

            # Replay based on the selected mode
            if mode == ReplayMode.SEQUENTIAL:
                results = await self._replay_sequentially(events)
            elif mode == ReplayMode.PARALLEL:
                results = await self._replay_in_parallel(events)
            elif mode == ReplayMode.BATCH:
                results = await self._replay_in_batches(events)
            else:
                raise ValueError(f"Unsupported replay mode: {mode}")

            logger.info(
                f"Completed replay for user {user_id} with results: {results}",
                event_type="event_replay_user_completed",
                user_id=user_id,
                results=results
            )

            return results

        except Exception as e:
            logger.error(
                f"Error replaying events for user {user_id}: {str(e)}",
                event_type="event_replay_user_error",
                user_id=user_id,
                error=str(e)
            )
            return {
                "total_events": 0,
                "successful_replays": 0,
                "failed_replays": 0,
                "skipped_replays": 0,
                "user_id": user_id,
                "error": str(e)
            }

    async def _replay_sequentially(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Replay events sequentially (one after another)

        Args:
            events: List of events to replay

        Returns:
            Dict[str, Any]: Replay results
        """
        results = {
            "total_events": len(events),
            "successful_replays": 0,
            "failed_replays": 0,
            "skipped_replays": 0
        }

        for i, event in enumerate(events):
            event_id = event.get("event_id", f"unknown_{i}")
            
            logger.debug(
                f"Replaying event {i+1}/{len(events)}: {event_id}",
                event_type="event_replay_sequential_progress",
                event_id=event_id,
                progress=f"{i+1}/{len(events)}"
            )

            success = await event_consumer.consume_event(event)
            
            if success:
                results["successful_replays"] += 1
            else:
                results["failed_replays"] += 1

        return results

    async def _replay_in_parallel(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Replay events in parallel (concurrent processing)

        Args:
            events: List of events to replay

        Returns:
            Dict[str, Any]: Replay results
        """
        results = {
            "total_events": len(events),
            "successful_replays": 0,
            "failed_replays": 0,
            "skipped_replays": 0
        }

        # Process events in chunks to avoid overwhelming the system
        semaphore = asyncio.Semaphore(self.max_concurrent_replays)

        async def replay_single_event(event):
            async with semaphore:
                event_id = event.get("event_id", "unknown")
                
                success = await event_consumer.consume_event(event)
                
                return success, event_id

        # Create tasks for all events
        tasks = [replay_single_event(event) for event in events]
        
        # Execute all tasks concurrently
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and failures
        for result in results_list:
            if isinstance(result, Exception):
                logger.error(
                    f"Exception during parallel replay: {str(result)}",
                    event_type="event_replay_parallel_exception",
                    error=str(result)
                )
                results["failed_replays"] += 1
            elif isinstance(result, tuple):
                success, event_id = result
                if success:
                    results["successful_replays"] += 1
                else:
                    results["failed_replays"] += 1
            else:
                results["failed_replays"] += 1

        return results

    async def _replay_in_batches(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Replay events in batches

        Args:
            events: List of events to replay

        Returns:
            Dict[str, Any]: Replay results
        """
        results = {
            "total_events": len(events),
            "successful_replays": 0,
            "failed_replays": 0,
            "skipped_replays": 0
        }

        # Split events into batches
        batches = [events[i:i + self.batch_size] for i in range(0, len(events), self.batch_size)]

        for batch_idx, batch in enumerate(batches):
            logger.info(
                f"Processing batch {batch_idx + 1}/{len(batches)} with {len(batch)} events",
                event_type="event_replay_batch_started",
                batch_number=batch_idx + 1,
                total_batches=len(batches),
                batch_size=len(batch)
            )

            # Process batch sequentially
            batch_results = await self._replay_sequentially(batch)
            
            results["successful_replays"] += batch_results["successful_replays"]
            results["failed_replays"] += batch_results["failed_replays"]
            results["skipped_replays"] += batch_results["skipped_replays"]

            # Optional: Add delay between batches to avoid overwhelming the system
            if batch_idx < len(batches) - 1:  # Not the last batch
                await asyncio.sleep(0.1)  # Small delay between batches

        return results

    async def fetch_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch an event by its ID (simulated implementation)

        Args:
            event_id: ID of the event to fetch

        Returns:
            Optional[Dict[str, Any]]: Event data if found, None otherwise
        """
        # This is a simulated implementation
        # In a real system, this would query the event store/database
        logger.warning(
            f"Simulated fetch for event {event_id} - in a real system this would query the event store",
            event_type="event_replay_simulated_fetch",
            event_id=event_id
        )
        return None

    async def fetch_events_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        event_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch events within a time range (simulated implementation)

        Args:
            start_time: Start time for the range
            end_time: End time for the range
            event_types: List of event types to filter (None means all types)

        Returns:
            List[Dict[str, Any]]: List of events
        """
        # This is a simulated implementation
        # In a real system, this would query the event store/database
        logger.warning(
            f"Simulated fetch for events from {start_time} to {end_time}",
            event_type="event_replay_simulated_fetch_range",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        return []

    async def fetch_events_by_user(
        self, 
        user_id: str, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch events for a specific user (simulated implementation)

        Args:
            user_id: ID of the user
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering

        Returns:
            List[Dict[str, Any]]: List of events
        """
        # This is a simulated implementation
        # In a real system, this would query the event store/database
        logger.warning(
            f"Simulated fetch for events for user {user_id}",
            event_type="event_replay_simulated_fetch_user",
            user_id=user_id
        )
        return []

    async def was_recently_processed(self, event_id: str) -> bool:
        """
        Check if an event was recently processed (to avoid unnecessary replays)

        Args:
            event_id: ID of the event to check

        Returns:
            bool: True if recently processed, False otherwise
        """
        # This is a simulated implementation
        # In a real system, this would check a cache or database of recently processed events
        return False

    async def record_replay_operation(self, event_id: str, status: str):
        """
        Record a replay operation for audit and tracking

        Args:
            event_id: ID of the event that was replayed
            status: Status of the replay operation ('success', 'failed', etc.)
        """
        replay_record = {
            "event_id": event_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "event_replay_service"
        }
        
        self.replay_history.append(replay_record)
        
        logger.info(
            f"Recorded replay operation for event {event_id}",
            event_type="event_replay_recorded",
            event_id=event_id,
            status=status
        )

    async def get_replay_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the history of replay operations

        Args:
            limit: Maximum number of records to return

        Returns:
            List[Dict[str, Any]]: List of replay operation records
        """
        # Return the most recent replay operations
        return self.replay_history[-limit:]

    async def validate_event_before_replay(self, event_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate an event before replaying it

        Args:
            event_data: Event data to validate

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = ["event_id", "event_type", "user_id", "timestamp", "payload"]
            for field in required_fields:
                if field not in event_data:
                    return False, f"Missing required field: {field}"

            # Validate event type
            event_type = event_data.get("event_type")
            if event_type not in [et.value for et in EventType]:
                return False, f"Invalid event type: {event_type}"

            # Validate timestamp format
            timestamp = event_data.get("timestamp")
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    return False, f"Invalid timestamp format: {timestamp}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def replay_from_dead_letter_queue(self, max_events: int = 100) -> Dict[str, Any]:
        """
        Replay events from the dead letter queue

        Args:
            max_events: Maximum number of events to replay

        Returns:
            Dict[str, Any]: Replay results
        """
        logger.info(
            f"Initiating replay from dead letter queue (max {max_events} events)",
            event_type="dlq_replay_started",
            max_events=max_events
        )

        try:
            # In a real implementation, this would fetch events from the actual DLQ
            # For now, we'll simulate retrieving DLQ events
            dlq_events = await self.fetch_dead_letter_events(max_events)
            
            if not dlq_events:
                logger.info(
                    "No events found in dead letter queue",
                    event_type="dlq_replay_no_events"
                )
                return {
                    "total_events": 0,
                    "successful_replays": 0,
                    "failed_replays": 0,
                    "skipped_replays": 0
                }

            logger.info(
                f"Found {len(dlq_events)} events in dead letter queue for replay",
                event_type="dlq_replay_found",
                event_count=len(dlq_events)
            )

            # Replay the events sequentially (safer for DLQ events)
            results = await self._replay_sequentially(dlq_events)

            logger.info(
                f"Completed DLQ replay with results: {results}",
                event_type="dlq_replay_completed",
                results=results
            )

            return results

        except Exception as e:
            logger.error(
                f"Error replaying events from dead letter queue: {str(e)}",
                event_type="dlq_replay_error",
                error=str(e)
            )
            return {
                "total_events": 0,
                "successful_replays": 0,
                "failed_replays": 0,
                "skipped_replays": 0,
                "error": str(e)
            }

    async def fetch_dead_letter_events(self, max_events: int) -> List[Dict[str, Any]]:
        """
        Fetch events from the dead letter queue (simulated implementation)

        Args:
            max_events: Maximum number of events to fetch

        Returns:
            List[Dict[str, Any]]: List of DLQ events
        """
        # This is a simulated implementation
        # In a real system, this would query the dead letter queue
        logger.warning(
            f"Simulated fetch for {max_events} events from dead letter queue",
            event_type="dlq_replay_simulated_fetch",
            max_events=max_events
        )
        return []


# Global instance of the event replay service
event_replay_service = EventReplayService()