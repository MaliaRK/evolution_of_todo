"""
Updated Todo Models for Event-Driven Todo AI System
Extends existing task model to include event context and correlation information
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class TodoBase(SQLModel):
    """Base class for Todo model with common fields"""
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10000)
    is_completed: bool = Field(default=False)


class Todo(TodoBase, table=True):
    """Todo model with event context for the event-driven architecture"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", nullable=False)  # Keep existing foreign key
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Event-driven architecture additions
    last_event_id: Optional[UUID] = Field(default=None)  # Last event that modified this todo
    last_correlation_id: Optional[UUID] = Field(default=None)  # Correlation ID of last operation
    event_version: int = Field(default=0)  # Version for optimistic locking in event sourcing

    # Additional fields that might be useful for event-driven context
    due_date: Optional[datetime] = Field(default=None)
    priority: str = Field(default="medium", max_length=20)  # low, medium, high
    tags: Optional[str] = Field(default=None, max_length=500)  # Comma-separated tags for categorization


class TodoCreate(TodoBase):
    """Schema for creating a new todo with event context"""
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"  # low, medium, high
    tags: Optional[str] = None  # Comma-separated tags


class TodoUpdate(SQLModel):
    """Schema for updating a todo with event context"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None  # low, medium, high
    tags: Optional[str] = None  # Comma-separated tags


class TodoPublic(TodoBase):
    """Public schema for returning todo data without sensitive fields"""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    priority: str = "medium"
    tags: Optional[str] = None


class TodoWithEventContext(TodoPublic):
    """Extended schema including event-driven context information"""
    last_event_id: Optional[UUID] = None
    last_correlation_id: Optional[UUID] = None
    event_version: int = 0


class TodoEventContext(SQLModel):
    """Schema for event-related context that can be attached to operations"""
    correlation_id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: Optional[str] = None
    event_metadata: Optional[dict] = Field(default={})
    source_service: str = Field(default="todo-backend")


# Backwards compatibility - alias Task to Todo
Task = Todo
TaskCreate = TodoCreate
TaskUpdate = TodoUpdate