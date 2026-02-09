"""
User Service for Todo AI System
Demonstrates service-to-service invocation via Dapr
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from ..models.user_model import User
from .dapr_integration import dapr_integration_service
from .logging_config import get_component_logger
from .correlation_id_util import get_current_correlation_id

logger = get_component_logger("dapr")


class UserService:
    """
    Service to handle user-related operations using Dapr service-to-service invocation
    """
    
    def __init__(self):
        self.dapr_service = dapr_integration_service
        self.app_id = "user-service"  # Target service for Dapr invocation
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID using Dapr service invocation
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            # Prepare the request data
            request_data = {
                "user_id": user_id
            }
            
            # Invoke the user service via Dapr
            response = await self.dapr_service.invoke_service(
                app_id=self.app_id,
                method="get_user",
                data=request_data
            )
            
            if response:
                # Map the response to a User object
                user_data = response.get("data", {})
                user = User(
                    id=user_data.get("id", user_id),
                    username=user_data.get("username", ""),
                    email=user_data.get("email", ""),
                    role=user_data.get("role", "user"),
                    is_active=user_data.get("is_active", True)
                )
                
                logger.info(
                    f"Retrieved user {user_id} via service invocation",
                    event_type="user_retrieved_via_dapr",
                    user_id=user_id,
                    correlation_id=correlation_id
                )
                
                return user
            else:
                logger.warning(
                    f"No user found for ID {user_id}",
                    event_type="user_not_found_via_dapr",
                    user_id=user_id,
                    correlation_id=correlation_id
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to retrieve user {user_id} via service invocation: {str(e)}",
                event_type="user_retrieval_error_via_dapr",
                user_id=user_id,
                correlation_id=correlation_id,
                error=str(e)
            )
            return None
    
    async def validate_user_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """
        Validate user permissions using Dapr service invocation
        
        Args:
            user_id: ID of the user
            resource: Resource to check permissions for
            action: Action to check permissions for
            
        Returns:
            bool: True if user has permissions, False otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            # Prepare the request data
            request_data = {
                "user_id": user_id,
                "resource": resource,
                "action": action
            }
            
            # Invoke the authorization service via Dapr
            response = await self.dapr_service.invoke_service(
                app_id="auth-service",
                method="validate_permission",
                data=request_data
            )
            
            if response:
                has_permission = response.get("has_permission", False)
                
                logger.info(
                    f"Permission validation for user {user_id}: {has_permission}",
                    event_type="permission_validation_result",
                    user_id=user_id,
                    resource=resource,
                    action=action,
                    has_permission=has_permission,
                    correlation_id=correlation_id
                )
                
                return has_permission
            else:
                logger.warning(
                    f"Permission validation failed for user {user_id}",
                    event_type="permission_validation_failed",
                    user_id=user_id,
                    resource=resource,
                    action=action,
                    correlation_id=correlation_id
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Failed to validate permissions for user {user_id}: {str(e)}",
                event_type="permission_validation_error",
                user_id=user_id,
                resource=resource,
                action=action,
                correlation_id=correlation_id,
                error=str(e)
            )
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile using Dapr service invocation
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[Dict[str, Any]]: User profile data if found, None otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            # Prepare the request data
            request_data = {
                "user_id": user_id
            }
            
            # Invoke the user profile service via Dapr
            response = await self.dapr_service.invoke_service(
                app_id="profile-service",
                method="get_profile",
                data=request_data
            )
            
            if response:
                profile_data = response.get("profile", {})
                
                logger.info(
                    f"Retrieved profile for user {user_id}",
                    event_type="user_profile_retrieved",
                    user_id=user_id,
                    correlation_id=correlation_id
                )
                
                return profile_data
            else:
                logger.warning(
                    f"No profile found for user {user_id}",
                    event_type="user_profile_not_found",
                    user_id=user_id,
                    correlation_id=correlation_id
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to retrieve profile for user {user_id}: {str(e)}",
                event_type="user_profile_error",
                user_id=user_id,
                correlation_id=correlation_id,
                error=str(e)
            )
            return None
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences using Dapr service invocation
        
        Args:
            user_id: ID of the user
            preferences: Preferences to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            # Prepare the request data
            request_data = {
                "user_id": user_id,
                "preferences": preferences
            }
            
            # Invoke the user preferences service via Dapr
            response = await self.dapr_service.invoke_service(
                app_id="preferences-service",
                method="update_preferences",
                data=request_data
            )
            
            if response:
                success = response.get("success", False)
                
                logger.info(
                    f"Preferences update for user {user_id}: {success}",
                    event_type="user_preferences_updated",
                    user_id=user_id,
                    success=success,
                    correlation_id=correlation_id
                )
                
                return success
            else:
                logger.warning(
                    f"Preferences update failed for user {user_id}",
                    event_type="user_preferences_update_failed",
                    user_id=user_id,
                    correlation_id=correlation_id
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Failed to update preferences for user {user_id}: {str(e)}",
                event_type="user_preferences_update_error",
                user_id=user_id,
                correlation_id=correlation_id,
                error=str(e)
            )
            return False
    
    async def notify_user(self, user_id: str, notification_type: str, message: str) -> bool:
        """
        Notify user using Dapr service invocation
        
        Args:
            user_id: ID of the user
            notification_type: Type of notification
            message: Notification message
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        correlation_id = get_current_correlation_id()
        
        try:
            # Prepare the request data
            request_data = {
                "user_id": user_id,
                "notification_type": notification_type,
                "message": message
            }
            
            # Invoke the notification service via Dapr
            response = await self.dapr_service.invoke_service(
                app_id="notification-service",
                method="send_notification",
                data=request_data
            )
            
            if response:
                success = response.get("success", False)
                
                logger.info(
                    f"Notification sent to user {user_id}: {success}",
                    event_type="user_notification_sent",
                    user_id=user_id,
                    notification_type=notification_type,
                    success=success,
                    correlation_id=correlation_id
                )
                
                return success
            else:
                logger.warning(
                    f"Notification failed for user {user_id}",
                    event_type="user_notification_failed",
                    user_id=user_id,
                    notification_type=notification_type,
                    correlation_id=correlation_id
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Failed to send notification to user {user_id}: {str(e)}",
                event_type="user_notification_error",
                user_id=user_id,
                notification_type=notification_type,
                correlation_id=correlation_id,
                error=str(e)
            )
            return False


# Global instance for use throughout the application
user_service = UserService()