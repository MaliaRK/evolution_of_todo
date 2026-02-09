"""
Event-Driven Todo Service for Todo AI System
Handles business logic with event publishing to Kafka via Dapr
"""

from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from ..models.todo_models import Todo, TodoCreate, TodoUpdate, TodoWithEventContext
from ..services.event_publisher import event_publisher, EventPublisher
from ..services.logging_config import get_component_logger
from ..services.correlation_id_util import get_current_correlation_id, extract_correlation_id_from_request
from ..services.jwt_propagation_util import validate_and_extract_user_id
from ..services.activity_service import activity_service

# Configure logging
logger = get_component_logger("database")


class TodoService:
    def __init__(self, event_publisher_instance: EventPublisher = None):
        self.event_publisher = event_publisher_instance or event_publisher

    @staticmethod
    def _convert_task_to_todo(task_data) -> Todo:
        """Convert legacy Task object to Todo object for backward compatibility"""
        from ..models.task_model import Task
        if isinstance(task_data, Task):
            # Convert Task to Todo
            return Todo(
                id=task_data.id,
                title=task_data.title,
                description=task_data.description,
                is_completed=task_data.is_completed,
                user_id=task_data.user_id,
                created_at=task_data.created_at,
                updated_at=task_data.updated_at,
                last_event_id=None,
                last_correlation_id=None,
                event_version=0,
                due_date=getattr(task_data, 'due_date', None),
                priority=getattr(task_data, 'priority', 'medium'),
                tags=getattr(task_data, 'tags', None)
            )
        return task_data

    async def create_todo_with_event(self, todo_data: TodoCreate, user_id: str, session: Session) -> Todo:
        """
        Create a new todo and publish a creation event to Kafka

        Args:
            todo_data: Todo creation data
            user_id: ID of the user creating the todo
            session: Database session

        Returns:
            Todo: Created todo object
        """
        correlation_id_str = get_current_correlation_id()
        correlation_id = UUID(correlation_id_str) if correlation_id_str else None

        # Create todo instance manually to handle datetime fields properly
        todo = Todo(
            title=todo_data.title,
            description=todo_data.description,
            is_completed=todo_data.is_completed or False,
            user_id=user_id,
            due_date=todo_data.due_date,
            priority=todo_data.priority or "medium",
            tags=todo_data.tags
        )

        session.add(todo)
        session.commit()
        session.refresh(todo)

        # Convert user_id to UUID for event
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) and len(user_id) == 36 else UUID(int=int(user_id, 16) if len(user_id) == 16 else 0)
        except:
            # If user_id is not a valid UUID string, generate a placeholder
            user_uuid = UUID(int=hash(user_id) & 0xffffffffffffffff)

        # Publish creation event to Kafka via Dapr
        try:
            # Check if event_publisher is available before attempting to publish
            if hasattr(self.event_publisher, 'publish_task_created') and self.event_publisher:
                await self.event_publisher.publish_task_created(
                    user_id=user_uuid,
                    task_id=UUID(str(todo.id)) if todo.id else None,
                    task_data=todo.dict()
                )

                logger.info(
                    f"Published task created event for todo {todo.id}",
                    event_type="task_created_published",
                    todo_id=todo.id,
                    user_id=user_id,
                    correlation_id=str(correlation_id) if correlation_id else None
                )
            else:
                logger.warning(
                    f"Event publisher not available, skipping event publishing for todo {todo.id}",
                    event_type="event_publisher_unavailable",
                    todo_id=todo.id,
                    user_id=user_id,
                    correlation_id=str(correlation_id) if correlation_id else None
                )
        except Exception as e:
            logger.error(
                f"Failed to publish task created event for todo {todo.id}: {str(e)}",
                event_type="task_creation_publish_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if event publishing fails - just log the error

        # Log the activity
        try:
            await activity_service.log_task_creation_activity(
                user_id=user_id,
                task_id=todo.id,
                task_title=todo.title
            )
        except Exception as e:
            logger.error(
                f"Failed to log task creation activity for todo {todo.id}: {str(e)}",
                event_type="task_creation_activity_log_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if activity logging fails - just log the error

        return todo

    async def update_todo_with_event(self, todo_id: int, todo_data: TodoUpdate, user_id: str, session: Session) -> Optional[Todo]:
        """
        Update a todo and publish an update event to Kafka

        Args:
            todo_id: ID of the todo to update
            todo_data: Todo update data
            user_id: ID of the user updating the todo
            session: Database session

        Returns:
            Optional[Todo]: Updated todo object, None if not found
        """
        correlation_id_str = get_current_correlation_id()
        correlation_id = UUID(correlation_id_str) if correlation_id_str else None

        # Get current todo
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        todo = session.exec(statement).first()

        if not todo:
            return None

        # Store previous state for event
        previous_state = todo.dict()

        # Update only provided fields
        update_data = todo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(todo, field):
                setattr(todo, field, value)

        # Update the updated_at timestamp
        todo.updated_at = datetime.utcnow()

        session.add(todo)
        session.commit()
        session.refresh(todo)

        # Convert user_id and todo_id to UUIDs for event
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) and len(user_id) == 36 else UUID(int=int(user_id, 16) if len(user_id) == 16 else 0)
            todo_uuid = UUID(str(todo.id)) if todo.id else None
        except:
            user_uuid = UUID(int=hash(user_id) & 0xffffffffffffffff)
            todo_uuid = UUID(int=hash(str(todo.id)) & 0xffffffffffffffff) if todo.id else None

        # Publish update event to Kafka via Dapr
        try:
            await self.event_publisher.publish_task_updated(
                user_id=user_uuid,
                task_id=todo_uuid,
                previous_data=previous_state,
                new_data=todo.dict()
            )

            logger.info(
                f"Published task updated event for todo {todo.id}",
                event_type="task_updated_published",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None
            )
        except Exception as e:
            logger.error(
                f"Failed to publish task updated event for todo {todo.id}: {str(e)}",
                event_type="task_update_publish_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if event publishing fails - just log the error

        # Log the activity
        try:
            changed_fields = [k for k, v in update_data.items() if previous_state.get(k) != v]
            await activity_service.log_task_update_activity(
                user_id=user_id,
                task_id=todo.id,
                task_title=todo.title,
                changed_fields=changed_fields
            )
        except Exception as e:
            logger.error(
                f"Failed to log task update activity for todo {todo.id}: {str(e)}",
                event_type="task_update_activity_log_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if activity logging fails - just log the error

        return todo

    async def complete_todo_with_event(self, todo_id: int, user_id: str, session: Session) -> Optional[Todo]:
        """
        Mark a todo as completed and publish a completion event to Kafka

        Args:
            todo_id: ID of the todo to complete
            user_id: ID of the user completing the todo
            session: Database session

        Returns:
            Optional[Todo]: Updated todo object, None if not found
        """
        correlation_id_str = get_current_correlation_id()
        correlation_id = UUID(correlation_id_str) if correlation_id_str else None

        # Get current todo
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        todo = session.exec(statement).first()

        if not todo:
            return None

        # Store previous state for event
        previous_state = todo.dict()

        # Update completion status and timestamp
        todo.is_completed = True
        todo.updated_at = datetime.utcnow()

        session.add(todo)
        session.commit()
        session.refresh(todo)

        # Convert user_id and todo_id to UUIDs for event
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) and len(user_id) == 36 else UUID(int=int(user_id, 16) if len(user_id) == 16 else 0)
            todo_uuid = UUID(str(todo.id)) if todo.id else None
        except:
            user_uuid = UUID(int=hash(user_id) & 0xffffffffffffffff)
            todo_uuid = UUID(int=hash(str(todo.id)) & 0xffffffffffffffff) if todo.id else None

        # Publish completion event to Kafka via Dapr
        try:
            completion_data = {
                "completed_at": todo.updated_at.isoformat(),
                "previous_state": previous_state,
                "completed_by": user_id
            }

            await self.event_publisher.publish_task_completed(
                user_id=user_uuid,
                task_id=todo_uuid,
                completion_data=completion_data
            )

            logger.info(
                f"Published task completed event for todo {todo.id}",
                event_type="task_completed_published",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None
            )
        except Exception as e:
            logger.error(
                f"Failed to publish task completed event for todo {todo.id}: {str(e)}",
                event_type="task_completion_publish_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if event publishing fails - just log the error

        # Log the activity
        try:
            await activity_service.log_task_completion_activity(
                user_id=user_id,
                task_id=todo.id,
                task_title=todo.title
            )
        except Exception as e:
            logger.error(
                f"Failed to log task completion activity for todo {todo.id}: {str(e)}",
                event_type="task_completion_activity_log_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if activity logging fails - just log the error

        return todo

    async def delete_todo_with_event(self, todo_id: int, user_id: str, session: Session) -> bool:
        """
        Delete a todo and publish a deletion event to Kafka

        Args:
            todo_id: ID of the todo to delete
            user_id: ID of the user deleting the todo
            session: Database session

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        correlation_id_str = get_current_correlation_id()
        correlation_id = UUID(correlation_id_str) if correlation_id_str else None

        # Get current todo
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        todo = session.exec(statement).first()

        if not todo:
            return False

        # Store previous state for event
        previous_state = todo.dict()

        # Delete the todo
        session.delete(todo)
        session.commit()

        # Convert user_id and todo_id to UUIDs for event
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) and len(user_id) == 36 else UUID(int=int(user_id, 16) if len(user_id) == 16 else 0)
            todo_uuid = UUID(str(todo.id)) if todo.id else None
        except:
            user_uuid = UUID(int=hash(user_id) & 0xffffffffffffffff)
            todo_uuid = UUID(int=hash(str(todo.id)) & 0xffffffffffffffff) if todo.id else None

        # Publish deletion event to Kafka via Dapr
        try:
            deletion_data = {
                "deleted_at": datetime.utcnow().isoformat(),
                "previous_state": previous_state,
                "deleted_by": user_id
            }

            await self.event_publisher.publish_task_deleted(
                user_id=user_uuid,
                task_id=todo_uuid,
                deletion_data=deletion_data
            )

            logger.info(
                f"Published task deleted event for todo {todo.id}",
                event_type="task_deleted_published",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None
            )
        except Exception as e:
            logger.error(
                f"Failed to publish task deleted event for todo {todo.id}: {str(e)}",
                event_type="task_deletion_publish_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if event publishing fails - just log the error

        # Log the activity
        try:
            await activity_service.log_task_deletion_activity(
                user_id=user_id,
                task_id=todo.id,
                task_title=previous_state.get('title', '')
            )
        except Exception as e:
            logger.error(
                f"Failed to log task deletion activity for todo {todo.id}: {str(e)}",
                event_type="task_deletion_activity_log_error",
                todo_id=todo.id,
                user_id=user_id,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            # Don't fail the operation if activity logging fails - just log the error

        return True

    @staticmethod
    def get_todo_by_id_for_user(todo_id: int, user_id: str, session: Session) -> Optional[Todo]:
        """
        Get a todo by ID for a specific user

        Args:
            todo_id: ID of the todo to retrieve
            user_id: ID of the user requesting the todo
            session: Database session

        Returns:
            Optional[Todo]: Todo object if found and belongs to user, None otherwise
        """
        statement = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
        todo = session.exec(statement).first()
        return todo

    @staticmethod
    def get_user_todos(user_id: str, session: Session) -> List[Todo]:
        """
        Get all todos for a specific user

        Args:
            user_id: ID of the user
            session: Database session

        Returns:
            List[Todo]: List of todos belonging to the user
        """
        statement = select(Todo).where(Todo.user_id == user_id)
        todos = session.exec(statement).all()
        return todos

    # Backward compatibility methods for existing Task model
    @staticmethod
    def create_task_for_user(task_data, user_id: str, session: Session):
        """Backward compatibility wrapper"""
        from .task_service import TaskService
        return TaskService.create_task_for_user(task_data, user_id, session)

    @staticmethod
    def get_task_by_id_for_user(task_id: int, user_id: str, session: Session):
        """Backward compatibility wrapper"""
        from .task_service import TaskService
        return TaskService.get_task_by_id_for_user(task_id, user_id, session)

    @staticmethod
    def get_user_tasks(user_id: str, session: Session):
        """Backward compatibility wrapper"""
        from .task_service import TaskService
        return TaskService.get_user_tasks(user_id, session)

    @staticmethod
    def update_task_for_user(task_id: int, task_data, user_id: str, session: Session):
        """Backward compatibility wrapper"""
        from .task_service import TaskService
        return TaskService.update_task_for_user(task_id, task_data, user_id, session)

    @staticmethod
    def delete_task_for_user(task_id: int, user_id: str, session: Session) -> bool:
        """Backward compatibility wrapper"""
        from .task_service import TaskService
        return TaskService.delete_task_for_user(task_id, user_id, session)

    @staticmethod
    def toggle_task_completion_for_user(task_id: int, user_id: str, session: Session):
        """Backward compatibility wrapper"""
        from .task_service import TaskService
        return TaskService.toggle_task_completion_for_user(task_id, user_id, session)