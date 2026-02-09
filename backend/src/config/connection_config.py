"""
Connection Configuration for Kafka and Dapr in Todo AI System
Manages connection settings for distributed messaging infrastructure
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os


class KafkaConfig(BaseModel):
    """
    Kafka connection configuration
    """
    bootstrap_servers: List[str] = Field(default=["localhost:9092"], description="Kafka broker addresses")
    consumer_group: str = Field(default="todo-app", description="Consumer group for the application")
    client_id: str = Field(default="todo-app", description="Client ID for Kafka connections")
    auto_offset_reset: str = Field(default="earliest", description="Offset reset policy")
    enable_auto_commit: bool = Field(default=True, description="Enable auto-commit of offsets")
    session_timeout_ms: int = Field(default=30000, description="Session timeout in milliseconds")
    heartbeat_interval_ms: int = Field(default=10000, description="Heartbeat interval in milliseconds")
    request_timeout_ms: int = Field(default=40000, description="Request timeout in milliseconds")
    max_poll_records: int = Field(default=100, description="Max records to poll at once")
    max_poll_interval_ms: int = Field(default=300000, description="Max poll interval in milliseconds")
    
    # Security settings
    security_protocol: str = Field(default="PLAINTEXT", description="Security protocol")
    ssl_cafile: Optional[str] = Field(default=None, description="SSL CA certificate file")
    ssl_certfile: Optional[str] = Field(default=None, description="SSL certificate file")
    ssl_keyfile: Optional[str] = Field(default=None, description="SSL key file")
    
    # Topic configuration
    default_topic_partitions: int = Field(default=3, description="Default number of partitions for topics")
    default_replication_factor: int = Field(default=1, description="Default replication factor for topics")
    default_retention_ms: int = Field(default=604800000, description="Default retention in milliseconds (7 days)")
    
    class Config:
        env_prefix = "KAFKA_"


class DaprConfig(BaseModel):
    """
    Dapr connection configuration
    """
    dapr_http_port: int = Field(default=3500, description="Dapr HTTP port")
    dapr_grpc_port: int = Field(default=50001, description="Dapr gRPC port")
    dapr_app_id: str = Field(default="todo-app", description="Dapr application ID")
    dapr_app_port: int = Field(default=8000, description="Application port")
    dapr_app_protocol: str = Field(default="http", description="Application protocol")
    dapr_config: str = Field(default="daprConfig", description="Dapr configuration name")
    dapr_components_path: str = Field(default="./dapr/components", description="Path to Dapr components")
    
    # Pub/Sub configuration
    pubsub_name: str = Field(default="kafka-pubsub", description="Name of the pub/sub component")
    pubsub_topic: str = Field(default="todo-tasks", description="Default pub/sub topic")
    pubsub_activity_topic: str = Field(default="todo-activities", description="Activity pub/sub topic")
    pubsub_deadletter_topic: str = Field(default="todo-deadletter", description="Dead letter pub/sub topic")
    
    # Service invocation configuration
    service_invocation_timeout: int = Field(default=30, description="Service invocation timeout in seconds")
    service_invocation_retry_count: int = Field(default=3, description="Number of retry attempts")
    
    class Config:
        env_prefix = "DAPR_"


class ConnectionSettings(BaseSettings):
    """
    Main connection settings combining Kafka and Dapr configurations
    """
    kafka: KafkaConfig = KafkaConfig()
    dapr: DaprConfig = DaprConfig()
    
    # Additional connection settings
    connection_pool_size: int = Field(default=10, description="Connection pool size")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for connections")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


# Load settings
def get_connection_settings() -> ConnectionSettings:
    """
    Get connection settings instance
    
    Returns:
        ConnectionSettings: Loaded connection settings
    """
    return ConnectionSettings()


# Global instance for use throughout the application
connection_settings = get_connection_settings()


def get_kafka_bootstrap_servers() -> List[str]:
    """
    Get Kafka bootstrap servers from configuration
    
    Returns:
        List[str]: List of Kafka bootstrap server addresses
    """
    return connection_settings.kafka.bootstrap_servers


def get_dapr_config() -> DaprConfig:
    """
    Get Dapr configuration
    
    Returns:
        DaprConfig: Dapr configuration object
    """
    return connection_settings.dapr


def get_kafka_config() -> KafkaConfig:
    """
    Get Kafka configuration
    
    Returns:
        KafkaConfig: Kafka configuration object
    """
    return connection_settings.kafka


# Helper functions to get specific settings
def get_pubsub_name() -> str:
    """Get the configured pub/sub name"""
    return connection_settings.dapr.pubsub_name


def get_default_topic() -> str:
    """Get the default pub/sub topic"""
    return connection_settings.dapr.pubsub_topic


def get_activity_topic() -> str:
    """Get the activity pub/sub topic"""
    return connection_settings.dapr.pubsub_activity_topic


def get_deadletter_topic() -> str:
    """Get the dead letter pub/sub topic"""
    return connection_settings.dapr.pubsub_deadletter_topic


def get_consumer_group() -> str:
    """Get the configured consumer group"""
    return connection_settings.kafka.consumer_group


def get_client_id() -> str:
    """Get the configured client ID"""
    return connection_settings.kafka.client_id


# Environment-specific configurations
def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def is_testing() -> bool:
    """Check if running in testing environment"""
    return os.getenv("ENVIRONMENT", "development").lower() == "testing"


# Get environment-specific settings
def get_environment_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration
    
    Returns:
        Dict[str, Any]: Environment-specific configuration
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return {
            "kafka": {
                "session_timeout_ms": 60000,
                "request_timeout_ms": 90000,
                "max_poll_interval_ms": 900000,
                "enable_auto_commit": True
            },
            "dapr": {
                "service_invocation_timeout": 60,
                "service_invocation_retry_count": 5
            }
        }
    elif env == "testing":
        return {
            "kafka": {
                "auto_offset_reset": "earliest",
                "enable_auto_commit": False,
                "session_timeout_ms": 15000
            },
            "dapr": {
                "service_invocation_timeout": 10,
                "service_invocation_retry_count": 1
            }
        }
    else:  # development
        return {
            "kafka": {
                "auto_offset_reset": "earliest",
                "enable_auto_commit": True,
                "session_timeout_ms": 30000
            },
            "dapr": {
                "service_invocation_timeout": 30,
                "service_invocation_retry_count": 3
            }
        }


# Apply environment-specific settings
def apply_environment_config():
    """
    Apply environment-specific configuration settings
    """
    env_config = get_environment_config()
    
    # Update Kafka config
    if "kafka" in env_config:
        for key, value in env_config["kafka"].items():
            setattr(connection_settings.kafka, key, value)
    
    # Update Dapr config
    if "dapr" in env_config:
        for key, value in env_config["dapr"].items():
            setattr(connection_settings.dapr, key, value)


# Apply environment-specific configuration on module load
apply_environment_config()