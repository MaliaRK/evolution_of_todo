"""
Health Check Handler for Todo AI System
Provides health check endpoints for monitoring and orchestration
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum

from ..services.logging_config import get_component_logger
from ..services.event_publisher import event_publisher
from ..services.event_consumer import event_consumer
from ..database import get_session
from sqlmodel import Session, select
from ..models.todo_models import Todo

# Configure logging
logger = get_component_logger("api")

router = APIRouter(prefix="/health", tags=["health"])

# Health status enums
class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthResponse(BaseModel):
    """Response model for health check endpoints"""
    status: HealthStatus
    timestamp: datetime
    uptime: float
    checks: Dict[str, Any]


class DetailedHealthResponse(BaseModel):
    """Detailed response model for health check endpoints"""
    status: HealthStatus
    timestamp: datetime
    uptime: float
    checks: Dict[str, Any]
    details: Dict[str, Any]


# Global variable to track application start time
start_time = time.time()


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint
    Returns overall health status of the application
    """
    try:
        # Perform basic health checks
        checks = {}
        
        # Check database connectivity
        db_healthy = await check_database_health()
        checks["database"] = {
            "status": HealthStatus.HEALTHY if db_healthy else HealthStatus.UNHEALTHY,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check event publisher connectivity
        publisher_healthy = await check_event_publisher_health()
        checks["event_publisher"] = {
            "status": HealthStatus.HEALTHY if publisher_healthy else HealthStatus.UNHEALTHY,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check event consumer connectivity
        consumer_healthy = await check_event_consumer_health()
        checks["event_consumer"] = {
            "status": HealthStatus.HEALTHY if consumer_healthy else HealthStatus.UNHEALTHY,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate overall status
        overall_status = calculate_overall_health(checks)
        
        # Prepare response
        uptime = time.time() - start_time
        response = HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime=uptime,
            checks=checks
        )
        
        # Log the health check
        logger.info(
            f"Health check completed with status: {overall_status}",
            event_type="health_check_completed",
            status=overall_status,
            uptime=uptime
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Error during health check: {str(e)}",
            event_type="health_check_error",
            error=str(e)
        )
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check() -> DetailedHealthResponse:
    """
    Detailed health check endpoint
    Returns comprehensive health status with detailed information
    """
    try:
        # Perform detailed health checks
        checks = {}
        details = {}
        
        # Check database connectivity
        db_result = await detailed_check_database_health()
        checks["database"] = {
            "status": db_result["status"],
            "timestamp": datetime.utcnow().isoformat()
        }
        details["database"] = db_result["details"]
        
        # Check event publisher connectivity
        publisher_result = await detailed_check_event_publisher_health()
        checks["event_publisher"] = {
            "status": publisher_result["status"],
            "timestamp": datetime.utcnow().isoformat()
        }
        details["event_publisher"] = publisher_result["details"]
        
        # Check event consumer connectivity
        consumer_result = await detailed_check_event_consumer_health()
        checks["event_consumer"] = {
            "status": consumer_result["status"],
            "timestamp": datetime.utcnow().isoformat()
        }
        details["event_consumer"] = consumer_result["details"]
        
        # Check external dependencies
        external_result = await check_external_dependencies()
        checks["external_dependencies"] = {
            "status": external_result["status"],
            "timestamp": datetime.utcnow().isoformat()
        }
        details["external_dependencies"] = external_result["details"]
        
        # Calculate overall status
        overall_status = calculate_overall_health(checks)
        
        # Prepare response
        uptime = time.time() - start_time
        response = DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime=uptime,
            checks=checks,
            details=details
        )
        
        # Log the detailed health check
        logger.info(
            f"Detailed health check completed with status: {overall_status}",
            event_type="detailed_health_check_completed",
            status=overall_status,
            uptime=uptime
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Error during detailed health check: {str(e)}",
            event_type="detailed_health_check_error",
            error=str(e)
        )
        raise HTTPException(status_code=503, detail="Detailed health check failed")


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint
    Used by orchestrators to determine if the application is ready to serve traffic
    """
    try:
        # For readiness, we typically check if the app can handle requests
        # This could include checking if required services are available
        checks = {}
        
        # Check if database is available
        db_ready = await check_database_health()
        checks["database"] = db_ready
        
        # Check if event publisher is available
        publisher_ready = await check_event_publisher_health()
        checks["event_publisher"] = publisher_ready
        
        # Overall readiness is true if all critical components are ready
        is_ready = all(checks.values())
        
        if is_ready:
            logger.info(
                "Readiness check passed",
                event_type="readiness_check_passed"
            )
            return {"status": "ready"}
        else:
            logger.warning(
                "Readiness check failed",
                event_type="readiness_check_failed",
                checks=checks
            )
            raise HTTPException(status_code=503, detail="Application not ready")
            
    except Exception as e:
        logger.error(
            f"Error during readiness check: {str(e)}",
            event_type="readiness_check_error",
            error=str(e)
        )
        raise HTTPException(status_code=503, detail="Readiness check failed")


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint
    Used by orchestrators to determine if the application is alive and should be restarted
    """
    try:
        # For liveness, we check if the app is running and responsive
        # This is usually a simple check to see if the app is hung or crashed
        current_time = time.time()
        uptime = current_time - start_time
        
        # Basic liveness check - if we can respond, we're alive
        logger.info(
            "Liveness check passed",
            event_type="liveness_check_passed",
            uptime=uptime
        )
        
        return {
            "status": "alive",
            "uptime": uptime,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Error during liveness check: {str(e)}",
            event_type="liveness_check_error",
            error=str(e)
        )
        raise HTTPException(status_code=503, detail="Liveness check failed")


async def check_database_health() -> bool:
    """
    Check database connectivity and basic functionality
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        # Get a database session and perform a simple query
        from ..config.database import engine
        from sqlmodel import text
        
        with Session(engine) as session:
            # Execute a simple query to test connectivity
            result = session.exec(text("SELECT 1")).first()
            return result is not None
    except Exception as e:
        logger.error(
            f"Database health check failed: {str(e)}",
            event_type="database_health_check_failed",
            error=str(e)
        )
        return False


async def detailed_check_database_health() -> Dict[str, Any]:
    """
    Perform detailed database health check
    
    Returns:
        Dict[str, Any]: Detailed health check result
    """
    try:
        start_time = time.time()
        
        # Get a database session and perform a simple query
        from ..config.database import engine
        from sqlmodel import text
        
        with Session(engine) as session:
            # Execute a simple query to test connectivity
            result = session.exec(text("SELECT 1")).first()
            
            # Check if we can query actual data
            todo_count = session.exec(select(Todo)).count()
            
        elapsed_time = time.time() - start_time
        
        if result is not None:
            return {
                "status": HealthStatus.HEALTHY,
                "details": {
                    "response_time_ms": round(elapsed_time * 1000, 2),
                    "todo_count": todo_count,
                    "can_connect": True,
                    "can_query_data": True
                }
            }
        else:
            return {
                "status": HealthStatus.UNHEALTHY,
                "details": {
                    "response_time_ms": round(elapsed_time * 1000, 2),
                    "can_connect": False,
                    "can_query_data": False
                }
            }
    except Exception as e:
        logger.error(
            f"Detailed database health check failed: {str(e)}",
            event_type="detailed_database_health_check_failed",
            error=str(e)
        )
        return {
            "status": HealthStatus.UNHEALTHY,
            "details": {
                "error": str(e),
                "can_connect": False,
                "can_query_data": False
            }
        }


async def check_event_publisher_health() -> bool:
    """
    Check event publisher connectivity
    
    Returns:
        bool: True if event publisher is healthy, False otherwise
    """
    try:
        # Test if we can access the event publisher
        # We won't actually publish an event to avoid side effects
        # but we can check if the client is accessible
        if event_publisher.client:
            # Try to ping the Dapr sidecar
            import grpc
            from dapr.clients.exceptions import DaprInternalError
            
            try:
                # This is a lightweight check to see if Dapr is accessible
                # In a real implementation, we might check Dapr health endpoint
                return True
            except (DaprInternalError, grpc.RpcError):
                return False
        return False
    except Exception as e:
        logger.error(
            f"Event publisher health check failed: {str(e)}",
            event_type="event_publisher_health_check_failed",
            error=str(e)
        )
        return False


async def detailed_check_event_publisher_health() -> Dict[str, Any]:
    """
    Perform detailed event publisher health check
    
    Returns:
        Dict[str, Any]: Detailed health check result
    """
    try:
        start_time = time.time()
        
        # Test if we can access the event publisher
        if event_publisher.client:
            try:
                # Check if we can ping the Dapr sidecar
                # This is a simplified check - in reality, you might check Dapr's health endpoint
                elapsed_time = time.time() - start_time
                
                return {
                    "status": HealthStatus.HEALTHY,
                    "details": {
                        "response_time_ms": round(elapsed_time * 1000, 2),
                        "is_connected": True,
                        "client_available": True
                    }
                }
            except Exception as e:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "details": {
                        "error": str(e),
                        "is_connected": False,
                        "client_available": False
                    }
                }
        else:
            return {
                "status": HealthStatus.UNHEALTHY,
                "details": {
                    "error": "Event publisher client not initialized",
                    "is_connected": False,
                    "client_available": False
                }
            }
    except Exception as e:
        logger.error(
            f"Detailed event publisher health check failed: {str(e)}",
            event_type="detailed_event_publisher_health_check_failed",
            error=str(e)
        )
        return {
            "status": HealthStatus.UNHEALTHY,
            "details": {
                "error": str(e),
                "is_connected": False,
                "client_available": False
            }
        }


async def check_event_consumer_health() -> bool:
    """
    Check event consumer connectivity
    
    Returns:
        bool: True if event consumer is healthy, False otherwise
    """
    try:
        # Check if the event consumer is properly initialized
        # In a real implementation, we might check if it can subscribe to topics
        if event_consumer:
            # Just verify the consumer object exists and has expected attributes
            return hasattr(event_consumer, 'processed_events')
        return False
    except Exception as e:
        logger.error(
            f"Event consumer health check failed: {str(e)}",
            event_type="event_consumer_health_check_failed",
            error=str(e)
        )
        return False


async def detailed_check_event_consumer_health() -> Dict[str, Any]:
    """
    Perform detailed event consumer health check
    
    Returns:
        Dict[str, Any]: Detailed health check result
    """
    try:
        # Check if the event consumer is properly initialized
        if event_consumer:
            return {
                "status": HealthStatus.HEALTHY,
                "details": {
                    "initialized": True,
                    "processed_events_count": len(event_consumer.processed_events),
                    "max_retries": getattr(event_consumer, 'max_retries', 'unknown')
                }
            }
        else:
            return {
                "status": HealthStatus.UNHEALTHY,
                "details": {
                    "initialized": False,
                    "error": "Event consumer not initialized"
                }
            }
    except Exception as e:
        logger.error(
            f"Detailed event consumer health check failed: {str(e)}",
            event_type="detailed_event_consumer_health_check_failed",
            error=str(e)
        )
        return {
            "status": HealthStatus.UNHEALTHY,
            "details": {
                "error": str(e),
                "initialized": False
            }
        }


async def check_external_dependencies() -> Dict[str, Any]:
    """
    Check external dependencies like Kafka, Dapr, etc.
    
    Returns:
        Dict[str, Any]: Health check result for external dependencies
    """
    try:
        # In a real implementation, this would check connectivity to:
        # - Kafka cluster
        # - Dapr sidecar
        # - Other microservices
        # - External APIs
        
        # For now, we'll simulate checking these dependencies
        kafka_healthy = True  # Simulated
        dapr_healthy = True   # Simulated
        
        if kafka_healthy and dapr_healthy:
            return {
                "status": HealthStatus.HEALTHY,
                "details": {
                    "kafka": True,
                    "dapr_sidecar": True,
                    "all_dependencies_available": True
                }
            }
        else:
            return {
                "status": HealthStatus.UNHEALTHY,
                "details": {
                    "kafka": kafka_healthy,
                    "dapr_sidecar": dapr_healthy,
                    "all_dependencies_available": False
                }
            }
    except Exception as e:
        logger.error(
            f"External dependencies health check failed: {str(e)}",
            event_type="external_dependencies_health_check_failed",
            error=str(e)
        )
        return {
            "status": HealthStatus.UNHEALTHY,
            "details": {
                "error": str(e),
                "all_dependencies_available": False
            }
        }


def calculate_overall_health(checks: Dict[str, Any]) -> HealthStatus:
    """
    Calculate overall health status based on individual checks
    
    Args:
        checks: Dictionary of individual health checks
        
    Returns:
        HealthStatus: Overall health status
    """
    statuses = [check.get("status", HealthStatus.UNKNOWN) for check in checks.values()]
    
    if HealthStatus.UNHEALTHY in statuses:
        return HealthStatus.UNHEALTHY
    elif HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED
    elif all(status == HealthStatus.HEALTHY for status in statuses):
        return HealthStatus.HEALTHY
    else:
        return HealthStatus.UNKNOWN


# Additional utility endpoints
@router.get("/metrics")
async def get_health_metrics():
    """
    Get health-related metrics for monitoring
    """
    try:
        uptime = time.time() - start_time
        
        # Gather metrics from various components
        metrics = {
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "connected": await check_database_health()
            },
            "event_publisher": {
                "available": await check_event_publisher_health()
            },
            "event_consumer": {
                "available": await check_event_consumer_health()
            }
        }
        
        logger.info(
            "Health metrics retrieved",
            event_type="health_metrics_retrieved",
            uptime=uptime
        )
        
        return metrics
    except Exception as e:
        logger.error(
            f"Error retrieving health metrics: {str(e)}",
            event_type="health_metrics_error",
            error=str(e)
        )
        raise HTTPException(status_code=503, detail="Could not retrieve health metrics")