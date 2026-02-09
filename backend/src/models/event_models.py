"""
Event Models for Todo AI System
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
import json


class EventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    ACTIVITY_LOGGED = "activity.logged"


class BaseEventSchema(SQLModel):
    """
    Base event schema with common fields for all events in the system
    """
    event_id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_type: str  # Discriminator field for different event types
    user_id: UUID    # Identifies tenant/user for multi-tenancy
    correlation_id: UUID = Field(default_factory=uuid4)  # For request correlation
    timestamp: datetime = Field(default_factory=datetime.utcnow)  # Event occurrence time
    payload: Dict[str, Any] = Field(default={})  # Event-specific data (stored as JSON)
    version: int = Field(default=1)  # Schema version for compatibility

    def dict(self, **kwargs):
        """Override to properly serialize datetime and UUID fields"""
        data = super().dict(**kwargs)
        if isinstance(data.get('timestamp'), datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        if isinstance(data.get('event_id'), UUID):
            data['event_id'] = str(data['event_id'])
        if isinstance(data.get('user_id'), UUID):
            data['user_id'] = str(data['user_id'])
        if isinstance(data.get('correlation_id'), UUID):
            data['correlation_id'] = str(data['correlation_id'])
        return data


class TaskEvent(BaseEventSchema):
    """
    Event representing task lifecycle changes
    """
    task_id: UUID  # References the affected task
    previous_state: Optional[Dict[str, Any]] = Field(default=None)  # State before change (for updates)
    new_state: Optional[Dict[str, Any]] = Field(default=None)      # State after change


class ActivityEvent(BaseEventSchema):
    """
    Event representing user activity for analytics and audit trails
    """
    activity_type: str  # Type of activity (e.g., 'task_created', 'user_login', etc.)
    metadata: Dict[str, Any] = Field(default={})  # Additional activity-specific metadata


class TaskCreatedEvent(TaskEvent):
    """
    Specific event for task creation
    """
    event_type: str = EventType.TASK_CREATED.value
    task_id: UUID
    previous_state: Optional[Dict[str, Any]] = None  # No previous state for creation
    new_state: Dict[str, Any]


class TaskUpdatedEvent(TaskEvent):
    """
    Specific event for task updates
    """
    event_type: str = EventType.TASK_UPDATED.value
    task_id: UUID
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]


class TaskCompletedEvent(TaskEvent):
    """
    Specific event for task completion
    """
    event_type: str = EventType.TASK_COMPLETED.value
    task_id: UUID
    previous_state: Optional[Dict[str, Any]]
    new_state: Dict[str, Any]


class TaskDeletedEvent(TaskEvent):
    """
    Specific event for task deletion
    """
    event_type: str = EventType.TASK_DELETED.value
    task_id: UUID
    previous_state: Optional[Dict[str, Any]]
    new_state: Optional[Dict[str, Any]]


class ActivityLoggedEvent(ActivityEvent):
    """
    Specific event for activity logging
    """
    event_type: str = EventType.ACTIVITY_LOGGED.value
    activity_type: str
    metadata: Dict[str, Any] = Field(default={})


# Event schema registry for type mapping
EVENT_TYPE_TO_SCHEMA = {
    EventType.TASK_CREATED: TaskCreatedEvent,
    EventType.TASK_UPDATED: TaskUpdatedEvent,
    EventType.TASK_COMPLETED: TaskCompletedEvent,
    EventType.TASK_DELETED: TaskDeletedEvent,
    EventType.ACTIVITY_LOGGED: ActivityLoggedEvent,
}


def create_task_created_event(user_id: UUID, task_id: UUID, task_data: Dict[str, Any]) -> TaskCreatedEvent:
    """Helper function to create a TaskCreatedEvent"""
    return TaskCreatedEvent(
        user_id=user_id,
        task_id=task_id,
        new_state=task_data,
        payload=task_data
    )


def create_task_updated_event(user_id: UUID, task_id: UUID, previous_data: Dict[str, Any], new_data: Dict[str, Any]) -> TaskUpdatedEvent:
    """Helper function to create a TaskUpdatedEvent"""
    return TaskUpdatedEvent(
        user_id=user_id,
        task_id=task_id,
        previous_state=previous_data,
        new_state=new_data,
        payload={
            "fields_changed": [k for k in new_data if previous_data.get(k) != new_data[k]],
            "previous_values": previous_data,
            "new_values": new_data
        }
    )


def create_task_completed_event(user_id: UUID, task_id: UUID, completion_data: Dict[str, Any]) -> TaskCompletedEvent:
    """Helper function to create a TaskCompletedEvent"""
    return TaskCompletedEvent(
        user_id=user_id,
        task_id=task_id,
        previous_state=completion_data.get("previous_state"),
        new_state=completion_data,
        payload=completion_data
    )


def create_task_deleted_event(user_id: UUID, task_id: UUID, deletion_data: Dict[str, Any]) -> TaskDeletedEvent:
    """Helper function to create a TaskDeletedEvent"""
    return TaskDeletedEvent(
        user_id=user_id,
        task_id=task_id,
        previous_state=deletion_data,
        new_state=None,  # No state after deletion
        payload=deletion_data
    )


def create_activity_event(user_id: UUID, activity_type: str, metadata: Dict[str, Any]) -> ActivityLoggedEvent:
    """Helper function to create an ActivityLoggedEvent"""
    return ActivityLoggedEvent(
        user_id=user_id,
        activity_type=activity_type,
        metadata=metadata,
        payload={
            "activity_type": activity_type,
            "metadata": metadata
        }
    )