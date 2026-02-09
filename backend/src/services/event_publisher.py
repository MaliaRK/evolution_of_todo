"""
Event Publisher Service for Todo AI System
Publishes events to Kafka via Dapr pub/sub
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

# Try to import Dapr, but provide fallback if not available
try:
    from dapr.ext.fastapi import DaprApp
    from dapr.clients import DaprClient
    from fastapi import HTTPException
    DAPR_AVAILABLE = True
except ImportError:
    DAPR_AVAILABLE = False
    # Define mock classes for when Dapr is not available
    class DaprClient:
        def __init__(self, *args, **kwargs):
            pass
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
        
        def publish_event(self, *args, **kwargs):
            # Mock implementation - just log the event
            print(f"Mock Dapr publish_event called with args: {args}, kwargs: {kwargs}")
            return None
        
        def close(self):
            pass

from ..models.event_models import (
    TaskCreatedEvent, TaskUpdatedEvent, TaskCompletedEvent, 
    TaskDeletedEvent, ActivityLoggedEvent, EventType,
    create_task_created_event, create_task_updated_event, 
    create_task_completed_event, create_task_deleted_event, 
    create_activity_event
)
from .logging_config import (
    get_component_logger, log_kafka_operation, 
    log_event_processing_error
)

logger = get_component_logger("kafka")


class EventPublisher:
    """
    Service to publish events to Kafka via Dapr pub/sub
    Falls back to mock implementation if Dapr is not available
    """
    
    def __init__(self, dapr_client_instance=None):
        self.dapr_available = DAPR_AVAILABLE
        self._client = dapr_client_instance
        self.pubsub_name = "kafka-pubsub"
        self.default_topic = "todo-tasks"
        self.activity_topic = "todo-activities"
        self.deadletter_topic = "todo-deadletter"
        
        if not self.dapr_available:
            logger.warning(
                "Dapr not available, using mock implementation",
                event_type="dapr_unavailable_fallback"
            )
    
    @property
    def client(self):
        """Lazy load the Dapr client to avoid startup issues"""
        if self._client is None and self.dapr_available:
            try:
                self._client = DaprClient()
            except Exception as e:
                logger.error(
                    f"Failed to initialize Dapr client: {str(e)}",
                    event_type="dapr_client_init_error",
                    error=str(e)
                )
                self.dapr_available = False
                self._client = None
        return self._client

    async def publish_event(self, event) -> bool:
        """
        Publish a generic event to the appropriate Kafka topic via Dapr
        
        Args:
            event: Event object to publish
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Determine the appropriate topic based on event type
            topic = self._get_topic_for_event(event)
            
            # Convert event to dictionary
            event_dict = event.dict()
            
            if self.dapr_available and self.client:
                # Publish to Dapr pub/sub
                with self.client as client:
                    client.publish_event(
                        pubsub_name=self.pubsub_name,
                        topic_name=topic,
                        data=json.dumps(event_dict),
                        data_content_type='application/json'
                    )
            else:
                # Fallback: log the event instead of publishing
                logger.info(
                    f"Fallback: Event {event.event_type} would be published to topic {topic}",
                    event_type="event_fallback_logged",
                    event_id=str(event.event_id),
                    event_type_detail=event.event_type,
                    topic=topic,
                    user_id=str(event.user_id),
                    correlation_id=str(event.correlation_id) if event.correlation_id else None
                )
                # In a real fallback, you might write to a file or database
                return True
            
            # Log the successful publication
            log_kafka_operation(
                logger,
                operation="publish",
                topic=topic,
                event_type=event.event_type,
                correlation_id=event.correlation_id
            )
            
            logger.info(
                f"Published event {event.event_type} to topic {topic}",
                event_type="event_published",
                event_id=str(event.event_id),
                event_type_detail=event.event_type,
                topic=topic,
                user_id=str(event.user_id),
                correlation_id=str(event.correlation_id) if event.correlation_id else None
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to publish event {event.event_type}: {str(e)}",
                event_type="event_publish_error",
                event_id=str(getattr(event, 'event_id', 'unknown')),
                event_type_detail=getattr(event, 'event_type', 'unknown'),
                error=str(e)
            )
            return False
    
    def _get_topic_for_event(self, event) -> str:
        """
        Determine the appropriate Kafka topic for an event
        
        Args:
            event: Event object
            
        Returns:
            str: Kafka topic name
        """
        if hasattr(event, 'event_type'):
            if event.event_type == EventType.ACTIVITY_LOGGED.value:
                return self.activity_topic
            elif event.event_type in [EventType.TASK_CREATED.value, 
                                     EventType.TASK_UPDATED.value, 
                                     EventType.TASK_COMPLETED.value, 
                                     EventType.TASK_DELETED.value]:
                return self.default_topic
        
        # Default to main topic if event type is unknown
        return self.default_topic
    
    async def publish_task_created(self, user_id: UUID, task_id: UUID, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task created event
        
        Args:
            user_id: ID of the user who created the task
            task_id: ID of the created task
            task_data: Task data to include in the event
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            event = create_task_created_event(user_id, task_id, task_data)
            return await self.publish_event(event)
        except Exception as e:
            logger.error(
                f"Failed to create and publish task created event: {str(e)}",
                event_type="task_created_event_creation_error",
                user_id=str(user_id),
                task_id=str(task_id),
                error=str(e)
            )
            return False
    
    async def publish_task_updated(self, user_id: UUID, task_id: UUID, 
                                  previous_data: Dict[str, Any], 
                                  new_data: Dict[str, Any]) -> bool:
        """
        Publish a task updated event
        
        Args:
            user_id: ID of the user who updated the task
            task_id: ID of the updated task
            previous_data: Previous task state
            new_data: New task state
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            event = create_task_updated_event(user_id, task_id, previous_data, new_data)
            return await self.publish_event(event)
        except Exception as e:
            logger.error(
                f"Failed to create and publish task updated event: {str(e)}",
                event_type="task_updated_event_creation_error",
                user_id=str(user_id),
                task_id=str(task_id),
                error=str(e)
            )
            return False
    
    async def publish_task_completed(self, user_id: UUID, task_id: UUID, 
                                   completion_data: Dict[str, Any]) -> bool:
        """
        Publish a task completed event
        
        Args:
            user_id: ID of the user who completed the task
            task_id: ID of the completed task
            completion_data: Completion-related data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            event = create_task_completed_event(user_id, task_id, completion_data)
            return await self.publish_event(event)
        except Exception as e:
            logger.error(
                f"Failed to create and publish task completed event: {str(e)}",
                event_type="task_completed_event_creation_error",
                user_id=str(user_id),
                task_id=str(task_id),
                error=str(e)
            )
            return False
    
    async def publish_task_deleted(self, user_id: UUID, task_id: UUID, 
                                 deletion_data: Dict[str, Any]) -> bool:
        """
        Publish a task deleted event
        
        Args:
            user_id: ID of the user who deleted the task
            task_id: ID of the deleted task
            deletion_data: Deletion-related data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            event = create_task_deleted_event(user_id, task_id, deletion_data)
            return await self.publish_event(event)
        except Exception as e:
            logger.error(
                f"Failed to create and publish task deleted event: {str(e)}",
                event_type="task_deleted_event_creation_error",
                user_id=str(user_id),
                task_id=str(task_id),
                error=str(e)
            )
            return False
    
    async def publish_activity_event(self, user_id: UUID, activity_type: str, 
                                   metadata: Dict[str, Any]) -> bool:
        """
        Publish an activity event
        
        Args:
            user_id: ID of the user performing the activity
            activity_type: Type of activity
            metadata: Activity metadata
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            event = create_activity_event(user_id, activity_type, metadata)
            return await self.publish_event(event)
        except Exception as e:
            logger.error(
                f"Failed to create and publish activity event: {str(e)}",
                event_type="activity_event_creation_error",
                user_id=str(user_id),
                activity_type=activity_type,
                error=str(e)
            )
            return False
    
    async def publish_to_dead_letter_queue(self, event_data: Dict[str, Any], 
                                         error_reason: str) -> bool:
        """
        Publish an event to the dead letter queue
        
        Args:
            event_data: Event data to publish to DLQ
            error_reason: Reason why the event is in the DLQ
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Add error information to the event data
            event_data['dlq_reason'] = error_reason
            event_data['dlq_timestamp'] = datetime.utcnow().isoformat()
            
            if self.dapr_available and self.client:
                # Publish to dead letter topic
                with self.client as client:
                    client.publish_event(
                        pubsub_name=self.pubsub_name,
                        topic_name=self.deadletter_topic,
                        data=json.dumps(event_data),
                        data_content_type='application/json'
                    )
            else:
                # Fallback: log the DLQ event
                logger.warning(
                    f"Fallback: Event would be published to dead letter queue: {error_reason}",
                    event_type="dlq_fallback_logged",
                    dlq_reason=error_reason,
                    original_event_data=event_data
                )
                return True
            
            logger.warning(
                f"Published event to dead letter queue: {error_reason}",
                event_type="event_published_to_dlq",
                dlq_reason=error_reason,
                original_event_data=event_data
            )
            
            return True
        except Exception as e:
            logger.error(
                f"Failed to publish event to dead letter queue: {str(e)}",
                event_type="dlq_publish_error",
                error=str(e),
                original_event_data=event_data
            )
            return False


# Global instance for use throughout the application
# Create the instance but don't initialize Dapr client immediately
event_publisher = EventPublisher()


# Async context manager for temporary event publisher instances
class EventPublisherContext:
    """
    Context manager for temporary event publisher instances
    """
    
    def __init__(self, dapr_client_instance=None):
        self.publisher = EventPublisher(dapr_client_instance)
    
    async def __aenter__(self):
        return self.publisher
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass