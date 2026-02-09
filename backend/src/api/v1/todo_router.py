"""
Event-Driven Todo Router for Todo AI System
Handles API endpoints for todo operations with event-driven processing
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from sqlmodel import Session
from uuid import UUID

from ...models.todo_models import Todo, TodoCreate, TodoUpdate, TodoWithEventContext
from ...services.todo_service import TodoService
from ...database import get_session
from ...auth.jwt_auth import get_current_user
from ...models.user_model import User
from ...services.correlation_id_util import (
    extract_correlation_id_from_request,
    set_current_correlation_id,
    generate_correlation_id
)
from ...services.logging_config import get_component_logger, log_api_request
from ...services.event_publisher import event_publisher

# Configure logging
logger = get_component_logger("api")

# Create router
router = APIRouter(prefix="/api/v1", tags=["todos"])


@router.get("/todos", response_model=List[Todo])
async def get_todos(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    request: Request = None
):
    """
    Get all todos for the current user

    Args:
        current_user: Currently authenticated user
        session: Database session
        request: HTTP request object for logging

    Returns:
        List[Todo]: List of todos for the user
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        set_current_correlation_id(correlation_id)
    else:
        correlation_id = generate_correlation_id()
        set_current_correlation_id(correlation_id)

    start_time = __import__('time').time()

    try:
        todos = TodoService.get_user_todos(current_user.id, session)

        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "GET",
            "/api/v1/todos",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=200,
            duration_ms=duration
        )

        return todos
    except Exception as e:
        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "GET",
            "/api/v1/todos",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=500,
            duration_ms=duration
        )

        logger.error(
            f"Error retrieving todos for user {current_user.id}: {str(e)}",
            event_type="get_todos_error",
            user_id=current_user.id,
            correlation_id=correlation_id
        )

        raise HTTPException(status_code=500, detail="Error retrieving todos")


@router.post("/todos", response_model=Todo)
async def create_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    request: Request = None
):
    """
    Create a new todo and publish a creation event

    Args:
        todo_data: Todo creation data
        current_user: Currently authenticated user
        session: Database session
        request: HTTP request object for logging

    Returns:
        Todo: Created todo object
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        set_current_correlation_id(correlation_id)
    else:
        correlation_id = generate_correlation_id()
        set_current_correlation_id(correlation_id)

    start_time = __import__('time').time()
    todo_service = TodoService(event_publisher_instance=event_publisher)

    try:
        # Create todo with event publishing
        todo = await todo_service.create_todo_with_event(todo_data, current_user.id, session)

        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "POST",
            "/api/v1/todos",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=201,
            duration_ms=duration
        )

        # Log the user action
        from ...services.logging_config import log_user_action
        log_user_action(
            logger,
            "todo_created",
            UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            "todo",
            UUID(str(todo.id)) if todo.id else None,
            UUID(correlation_id) if correlation_id else None,
            {"title": todo.title}
        )

        return todo
    except Exception as e:
        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "POST",
            "/api/v1/todos",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=500,
            duration_ms=duration
        )

        logger.error(
            f"Error creating todo for user {current_user.id}: {str(e)}",
            event_type="create_todo_error",
            user_id=current_user.id,
            correlation_id=correlation_id
        )

        raise HTTPException(status_code=500, detail="Error creating todo")


@router.get("/todos/{todo_id}", response_model=Todo)
async def get_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    request: Request = None
):
    """
    Get a specific todo by ID

    Args:
        todo_id: ID of the todo to retrieve
        current_user: Currently authenticated user
        session: Database session
        request: HTTP request object for logging

    Returns:
        Todo: Retrieved todo object
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        set_current_correlation_id(correlation_id)
    else:
        correlation_id = generate_correlation_id()
        set_current_correlation_id(correlation_id)

    start_time = __import__('time').time()

    try:
        todo = TodoService.get_todo_by_id_for_user(todo_id, current_user.id, session)

        if not todo:
            duration = (__import__('time').time() - start_time) * 1000

            log_api_request(
                logger,
                "GET",
                f"/api/v1/todos/{todo_id}",
                user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
                correlation_id=UUID(correlation_id) if correlation_id else None,
                response_status=404,
                duration_ms=duration
            )

            raise HTTPException(status_code=404, detail="Todo not found")

        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "GET",
            f"/api/v1/todos/{todo_id}",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=200,
            duration_ms=duration
        )

        return todo
    except Exception as e:
        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "GET",
            f"/api/v1/todos/{todo_id}",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=500,
            duration_ms=duration
        )

        logger.error(
            f"Error retrieving todo {todo_id} for user {current_user.id}: {str(e)}",
            event_type="get_todo_error",
            todo_id=todo_id,
            user_id=current_user.id,
            correlation_id=correlation_id
        )

        raise HTTPException(status_code=500, detail="Error retrieving todo")


@router.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    request: Request = None
):
    """
    Update a specific todo and publish an update event

    Args:
        todo_id: ID of the todo to update
        todo_data: Todo update data
        current_user: Currently authenticated user
        session: Database session
        request: HTTP request object for logging

    Returns:
        Todo: Updated todo object
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        set_current_correlation_id(correlation_id)
    else:
        correlation_id = generate_correlation_id()
        set_current_correlation_id(correlation_id)

    start_time = __import__('time').time()
    todo_service = TodoService(event_publisher_instance=event_publisher)

    try:
        # Update todo with event publishing
        todo = await todo_service.update_todo_with_event(todo_id, todo_data, current_user.id, session)

        if not todo:
            duration = (__import__('time').time() - start_time) * 1000

            log_api_request(
                logger,
                "PUT",
                f"/api/v1/todos/{todo_id}",
                user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
                correlation_id=UUID(correlation_id) if correlation_id else None,
                response_status=404,
                duration_ms=duration
            )

            raise HTTPException(status_code=404, detail="Todo not found")

        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "PUT",
            f"/api/v1/todos/{todo_id}",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=200,
            duration_ms=duration
        )

        # Log the user action
        from ...services.logging_config import log_user_action
        log_user_action(
            logger,
            "todo_updated",
            UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            "todo",
            UUID(str(todo.id)) if todo.id else None,
            UUID(correlation_id) if correlation_id else None,
            {"title": todo.title, "changes": todo_data.model_dump(exclude_unset=True)}
        )

        return todo
    except Exception as e:
        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "PUT",
            f"/api/v1/todos/{todo_id}",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=500,
            duration_ms=duration
        )

        logger.error(
            f"Error updating todo {todo_id} for user {current_user.id}: {str(e)}",
            event_type="update_todo_error",
            todo_id=todo_id,
            user_id=current_user.id,
            correlation_id=correlation_id
        )

        raise HTTPException(status_code=500, detail="Error updating todo")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    request: Request = None
):
    """
    Delete a specific todo and publish a deletion event

    Args:
        todo_id: ID of the todo to delete
        current_user: Currently authenticated user
        session: Database session
        request: HTTP request object for logging

    Returns:
        dict: Success message
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        set_current_correlation_id(correlation_id)
    else:
        correlation_id = generate_correlation_id()
        set_current_correlation_id(correlation_id)

    start_time = __import__('time').time()
    todo_service = TodoService(event_publisher_instance=event_publisher)

    try:
        # Delete todo with event publishing
        success = await todo_service.delete_todo_with_event(todo_id, current_user.id, session)

        if not success:
            duration = (__import__('time').time() - start_time) * 1000

            log_api_request(
                logger,
                "DELETE",
                f"/api/v1/todos/{todo_id}",
                user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
                correlation_id=UUID(correlation_id) if correlation_id else None,
                response_status=404,
                duration_ms=duration
            )

            raise HTTPException(status_code=404, detail="Todo not found")

        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "DELETE",
            f"/api/v1/todos/{todo_id}",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=200,
            duration_ms=duration
        )

        # Log the user action
        from ...services.logging_config import log_user_action
        log_user_action(
            logger,
            "todo_deleted",
            UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            "todo",
            UUID(str(todo_id)),
            UUID(correlation_id) if correlation_id else None,
            {}
        )

        return {"message": "Todo deleted successfully"}
    except Exception as e:
        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "DELETE",
            f"/api/v1/todos/{todo_id}",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=500,
            duration_ms=duration
        )

        logger.error(
            f"Error deleting todo {todo_id} for user {current_user.id}: {str(e)}",
            event_type="delete_todo_error",
            todo_id=todo_id,
            user_id=current_user.id,
            correlation_id=correlation_id
        )

        raise HTTPException(status_code=500, detail="Error deleting todo")


@router.patch("/todos/{todo_id}/complete", response_model=Todo)
async def complete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    request: Request = None
):
    """
    Mark a specific todo as completed and publish a completion event

    Args:
        todo_id: ID of the todo to complete
        current_user: Currently authenticated user
        session: Database session
        request: HTTP request object for logging

    Returns:
        Todo: Updated todo object
    """
    correlation_id = extract_correlation_id_from_request(request)
    if correlation_id:
        set_current_correlation_id(correlation_id)
    else:
        correlation_id = generate_correlation_id()
        set_current_correlation_id(correlation_id)

    start_time = __import__('time').time()
    todo_service = TodoService(event_publisher_instance=event_publisher)

    try:
        # Complete todo with event publishing
        todo = await todo_service.complete_todo_with_event(todo_id, current_user.id, session)

        if not todo:
            duration = (__import__('time').time() - start_time) * 1000

            log_api_request(
                logger,
                "PATCH",
                f"/api/v1/todos/{todo_id}/complete",
                user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
                correlation_id=UUID(correlation_id) if correlation_id else None,
                response_status=404,
                duration_ms=duration
            )

            raise HTTPException(status_code=404, detail="Todo not found")

        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "PATCH",
            f"/api/v1/todos/{todo_id}/complete",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=200,
            duration_ms=duration
        )

        # Log the user action
        from ...services.logging_config import log_user_action
        log_user_action(
            logger,
            "todo_completed",
            UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            "todo",
            UUID(str(todo.id)) if todo.id else None,
            UUID(correlation_id) if correlation_id else None,
            {"completed": True}
        )

        return todo
    except Exception as e:
        duration = (__import__('time').time() - start_time) * 1000

        log_api_request(
            logger,
            "PATCH",
            f"/api/v1/todos/{todo_id}/complete",
            user_id=UUID(current_user.id) if len(current_user.id) == 36 else UUID(int=hash(current_user.id)),
            correlation_id=UUID(correlation_id) if correlation_id else None,
            response_status=500,
            duration_ms=duration
        )

        logger.error(
            f"Error completing todo {todo_id} for user {current_user.id}: {str(e)}",
            event_type="complete_todo_error",
            todo_id=todo_id,
            user_id=current_user.id,
            correlation_id=correlation_id
        )

        raise HTTPException(status_code=500, detail="Error completing todo")


