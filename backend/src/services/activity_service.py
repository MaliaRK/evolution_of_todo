"""
Activity Logging Service for Todo AI System
Handles capturing and processing user activity events for analytics
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from sqlmodel import Session

from ..models.event_models import ActivityLoggedEvent, create_activity_event
from ..services.event_publisher import event_publisher, EventPublisher
from ..services.logging_config import get_component_logger
from ..services.correlation_id_util import get_current_correlation_id
from ..services.jwt_propagation_util import validate_and_extract_user_id

# Configure logging
logger = get_component_logger("database")


class ActivityService:
    """
    Service for handling user activity logging and analytics
    """

    def __init__(self, event_publisher_instance: EventPublisher = None):
        """
        Initialize the activity service

        Args:
            event_publisher_instance: Event publisher instance to use
        """
        self.event_publisher = event_publisher_instance or event_publisher

    async def log_user_activity(
        self,
        user_id: str,
        activity_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> bool:
        """
        Log a user activity event

        Args:
            user_id: ID of the user performing the activity
            activity_type: Type of activity (e.g., 'task_created', 'task_updated', etc.)
            metadata: Additional metadata about the activity
            resource_id: ID of the resource involved in the activity
            resource_type: Type of resource involved in the activity

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        correlation_id_str = get_current_correlation_id()
        correlation_id = UUID(correlation_id_str) if correlation_id_str else None

        try:
            # Validate activity type
            if not activity_type or not isinstance(activity_type, str):
                logger.error(
                    f"Invalid activity type: {activity_type}",
                    event_type="activity_validation_error",
                    user_id=user_id,
                    correlation_id=str(correlation_id) if correlation_id else None
                )
                return False

            # Validate user ID
            if not user_id or not isinstance(user_id, str):
                logger.error(
                    f"Invalid user ID: {user_id}",
                    event_type="activity_validation_error",
                    correlation_id=str(correlation_id) if correlation_id else None
                )
                return False

            # Prepare metadata
            activity_metadata = metadata or {}
            if resource_id:
                if isinstance(resource_id, str) and resource_id.strip():
                    activity_metadata['resource_id'] = resource_id
                else:
                    logger.warning(
                        f"Invalid resource ID: {resource_id}",
                        event_type="activity_validation_warning",
                        user_id=user_id,
                        correlation_id=str(correlation_id) if correlation_id else None
                    )
            if resource_type:
                if isinstance(resource_type, str) and resource_type.strip():
                    activity_metadata['resource_type'] = resource_type
                else:
                    logger.warning(
                        f"Invalid resource type: {resource_type}",
                        event_type="activity_validation_warning",
                        user_id=user_id,
                        correlation_id=str(correlation_id) if correlation_id else None
                    )

            # Convert user_id to UUID for event
            try:
                user_uuid = UUID(user_id) if isinstance(user_id, str) and len(user_id) == 36 else UUID(int=int(user_id, 16) if len(user_id) == 16 else 0)
            except:
                user_uuid = UUID(int=hash(user_id) & 0xffffffffffffffff)

            # Create and publish activity event
            activity_event = create_activity_event(
                user_id=user_uuid,
                activity_type=activity_type,
                metadata=activity_metadata
            )

            # Validate the event schema before publishing
            is_valid, error_msg = self._validate_activity_event(activity_event)
            if not is_valid:
                logger.error(
                    f"Activity event validation failed: {error_msg}",
                    event_type="activity_schema_validation_failed",
                    user_id=user_id,
                    activity_type=activity_type,
                    correlation_id=str(correlation_id) if correlation_id else None
                )
                return False

            # Publish to Kafka via Dapr
            success = await self.event_publisher.publish_event(activity_event)

            if success:
                logger.info(
                    f"Logged activity '{activity_type}' for user {user_id}",
                    event_type="activity_logged",
                    user_id=user_id,
                    activity_type=activity_type,
                    resource_id=resource_id,
                    correlation_id=str(correlation_id) if correlation_id else None
                )
            else:
                logger.error(
                    f"Failed to log activity '{activity_type}' for user {user_id}",
                    event_type="activity_log_failed",
                    user_id=user_id,
                    activity_type=activity_type,
                    correlation_id=str(correlation_id) if correlation_id else None
                )

            return success
        except Exception as e:
            logger.error(
                f"Error logging activity '{activity_type}' for user {user_id}: {str(e)}",
                event_type="activity_logging_error",
                user_id=user_id,
                activity_type=activity_type,
                correlation_id=str(correlation_id) if correlation_id else None,
                error=str(e)
            )
            return False

    def _validate_activity_event(self, event: ActivityLoggedEvent) -> tuple[bool, Optional[str]]:
        """
        Validate the activity event schema

        Args:
            event: Activity event to validate

        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Check required fields
            if not event.event_type:
                return False, "Missing event_type"

            if not event.user_id:
                return False, "Missing user_id"

            if not event.activity_type:
                return False, "Missing activity_type"

            # Validate activity type format
            if not isinstance(event.activity_type, str) or len(event.activity_type.strip()) == 0:
                return False, "Invalid activity_type format"

            # Validate user_id format
            if not isinstance(event.user_id, UUID):
                return False, "Invalid user_id format"

            # Validate metadata
            if not isinstance(event.metadata, dict):
                return False, "Metadata must be a dictionary"

            return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    async def log_task_creation_activity(
        self,
        user_id: str,
        task_id: int,
        task_title: str
    ) -> bool:
        """
        Log a task creation activity

        Args:
            user_id: ID of the user creating the task
            task_id: ID of the created task
            task_title: Title of the created task

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        metadata = {
            "task_id": task_id,
            "task_title": task_title
        }

        return await self.log_user_activity(
            user_id=user_id,
            activity_type="task_created",
            metadata=metadata,
            resource_id=str(task_id),
            resource_type="task"
        )

    async def log_task_update_activity(
        self,
        user_id: str,
        task_id: int,
        task_title: str,
        changed_fields: list
    ) -> bool:
        """
        Log a task update activity

        Args:
            user_id: ID of the user updating the task
            task_id: ID of the updated task
            task_title: Title of the updated task
            changed_fields: List of fields that were changed

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        metadata = {
            "task_id": task_id,
            "task_title": task_title,
            "changed_fields": changed_fields
        }

        return await self.log_user_activity(
            user_id=user_id,
            activity_type="task_updated",
            metadata=metadata,
            resource_id=str(task_id),
            resource_type="task"
        )

    async def log_task_completion_activity(
        self,
        user_id: str,
        task_id: int,
        task_title: str
    ) -> bool:
        """
        Log a task completion activity

        Args:
            user_id: ID of the user completing the task
            task_id: ID of the completed task
            task_title: Title of the completed task

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        metadata = {
            "task_id": task_id,
            "task_title": task_title
        }

        return await self.log_user_activity(
            user_id=user_id,
            activity_type="task_completed",
            metadata=metadata,
            resource_id=str(task_id),
            resource_type="task"
        )

    async def log_task_deletion_activity(
        self,
        user_id: str,
        task_id: int,
        task_title: str
    ) -> bool:
        """
        Log a task deletion activity

        Args:
            user_id: ID of the user deleting the task
            task_id: ID of the deleted task
            task_title: Title of the deleted task

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        metadata = {
            "task_id": task_id,
            "task_title": task_title
        }

        return await self.log_user_activity(
            user_id=user_id,
            activity_type="task_deleted",
            metadata=metadata,
            resource_id=str(task_id),
            resource_type="task"
        )

    async def log_api_access_activity(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        response_status: int
    ) -> bool:
        """
        Log an API access activity

        Args:
            user_id: ID of the user accessing the API
            endpoint: API endpoint accessed
            method: HTTP method used
            response_status: HTTP response status code

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        metadata = {
            "endpoint": endpoint,
            "method": method,
            "response_status": response_status
        }

        return await self.log_user_activity(
            user_id=user_id,
            activity_type="api_access",
            metadata=metadata,
            resource_type="api_endpoint"
        )

    async def log_authentication_activity(
        self,
        user_id: str,
        activity_type: str,  # 'login', 'logout', 'token_refresh', etc.
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Log an authentication-related activity

        Args:
            user_id: ID of the user
            activity_type: Type of authentication activity
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        metadata = {
            "ip_address": ip_address,
            "user_agent": user_agent
        }

        return await self.log_user_activity(
            user_id=user_id,
            activity_type=f"auth_{activity_type}",
            metadata=metadata,
            resource_type="authentication"
        )


# Global instance of the activity service
activity_service = ActivityService()