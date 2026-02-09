"""
Metrics Collection Service for Todo AI System
Collects and reports metrics for event processing and system performance
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict, deque
from threading import Lock
from dataclasses import dataclass
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
from prometheus_client.registry import CollectorRegistry

from ..models.event_models import EventType
from ..services.logging_config import get_component_logger

# Configure logging
logger = get_component_logger("event_processing")


class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"


@dataclass
class EventProcessingMetrics:
    """Data class for event processing metrics"""
    event_type: str
    processing_time_seconds: float
    success: bool
    timestamp: datetime
    user_id: Optional[str] = None


class MetricsService:
    """
    Service for collecting and reporting application metrics
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize the metrics service
        
        Args:
            registry: Optional Prometheus collector registry
        """
        self.registry = registry or CollectorRegistry()
        self.lock = Lock()
        
        # Initialize Prometheus metrics
        self._initialize_prometheus_metrics()
        
        # Local metrics storage for additional analysis
        self.event_processing_times = defaultdict(deque)
        self.event_counts = defaultdict(lambda: {'success': 0, 'failure': 0})
        self.active_connections = 0
        self.total_processed_events = 0
        self.total_failed_events = 0
        
        # Performance tracking
        self.start_time = time.time()
        
        logger.info(
            "Metrics service initialized",
            event_type="metrics_service_initialized"
        )
    
    def _initialize_prometheus_metrics(self):
        """Initialize Prometheus metrics collectors"""
        # Event processing counters
        self.event_processed_counter = Counter(
            'todo_event_processed_total',
            'Total number of events processed',
            ['event_type', 'result'],
            registry=self.registry
        )
        
        self.event_processing_duration = Histogram(
            'todo_event_processing_duration_seconds',
            'Time spent processing events',
            ['event_type'],
            registry=self.registry,
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')]
        )
        
        # System performance gauges
        self.active_connections_gauge = Gauge(
            'todo_active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        self.processed_events_gauge = Gauge(
            'todo_processed_events_total',
            'Total number of processed events',
            registry=self.registry
        )
        
        self.failed_events_gauge = Gauge(
            'todo_failed_events_total',
            'Total number of failed events',
            registry=self.registry
        )
        
        # Database metrics
        self.db_queries_counter = Counter(
            'todo_db_queries_total',
            'Total number of database queries',
            ['operation'],
            registry=self.registry
        )
        
        # Dapr/Kafka metrics
        self.dapr_calls_counter = Counter(
            'todo_dapr_calls_total',
            'Total number of Dapr calls',
            ['operation', 'result'],
            registry=self.registry
        )
        
        self.kafka_messages_counter = Counter(
            'todo_kafka_messages_total',
            'Total number of Kafka messages processed',
            ['topic', 'operation'],
            registry=self.registry
        )
        
        # Business metrics
        self.user_actions_counter = Counter(
            'todo_user_actions_total',
            'Total number of user actions',
            ['action_type', 'user_id'],
            registry=self.registry
        )
        
        logger.info(
            "Prometheus metrics initialized",
            event_type="prometheus_metrics_initialized"
        )
    
    def record_event_processing(self, event_type: str, processing_time: float, success: bool, user_id: Optional[str] = None):
        """
        Record metrics for event processing
        
        Args:
            event_type: Type of event processed
            processing_time: Time taken to process the event in seconds
            success: Whether the processing was successful
            user_id: Optional user ID associated with the event
        """
        with self.lock:
            # Update local metrics
            self.event_processing_times[event_type].append({
                'processing_time': processing_time,
                'success': success,
                'timestamp': datetime.utcnow()
            })
            
            # Limit stored metrics to prevent memory issues
            if len(self.event_processing_times[event_type]) > 1000:
                self.event_processing_times[event_type].popleft()
            
            # Update success/failure counts
            result_key = 'success' if success else 'failure'
            self.event_counts[event_type][result_key] += 1
            
            # Update totals
            if success:
                self.total_processed_events += 1
                self.processed_events_gauge.inc()
            else:
                self.total_failed_events += 1
                self.failed_events_gauge.inc()
        
        # Update Prometheus metrics
        result_label = 'success' if success else 'failure'
        self.event_processed_counter.labels(event_type=event_type, result=result_label).inc()
        self.event_processing_duration.labels(event_type=event_type).observe(processing_time)
        
        # Add user-specific metrics if user_id is provided
        if user_id:
            self.user_actions_counter.labels(action_type=f'event_{event_type}', user_id=user_id).inc()
        
        logger.debug(
            f"Recorded event processing metrics: {event_type}, time={processing_time}s, success={success}",
            event_type="event_processing_metrics_recorded",
            event_type_detail=event_type,
            processing_time=processing_time,
            success=success,
            user_id=user_id
        )
    
    def record_dapr_call(self, operation: str, success: bool):
        """
        Record metrics for Dapr calls
        
        Args:
            operation: Type of Dapr operation
            success: Whether the operation was successful
        """
        result_label = 'success' if success else 'failure'
        self.dapr_calls_counter.labels(operation=operation, result=result_label).inc()
        
        logger.debug(
            f"Recorded Dapr call metrics: {operation}, success={success}",
            event_type="dapr_call_metrics_recorded",
            operation=operation,
            success=success
        )
    
    def record_kafka_message(self, topic: str, operation: str):
        """
        Record metrics for Kafka messages
        
        Args:
            topic: Kafka topic name
            operation: Type of operation (produce/consume)
        """
        self.kafka_messages_counter.labels(topic=topic, operation=operation).inc()
        
        logger.debug(
            f"Recorded Kafka message metrics: {topic}, operation={operation}",
            event_type="kafka_message_metrics_recorded",
            topic=topic,
            operation=operation
        )
    
    def record_db_query(self, operation: str):
        """
        Record metrics for database queries
        
        Args:
            operation: Type of database operation
        """
        self.db_queries_counter.labels(operation=operation).inc()
        
        logger.debug(
            f"Recorded DB query metrics: {operation}",
            event_type="db_query_metrics_recorded",
            operation=operation
        )
    
    def update_active_connections(self, count: int):
        """
        Update the count of active connections
        
        Args:
            count: Number of active connections
        """
        with self.lock:
            self.active_connections = count
        self.active_connections_gauge.set(count)
        
        logger.debug(
            f"Updated active connections: {count}",
            event_type="active_connections_updated",
            count=count
        )
    
    def get_event_processing_stats(self, event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for event processing
        
        Args:
            event_type: Optional specific event type to get stats for
            
        Returns:
            Dict[str, Any]: Statistics for event processing
        """
        with self.lock:
            if event_type:
                if event_type in self.event_counts:
                    counts = self.event_counts[event_type]
                    total = counts['success'] + counts['failure']
                    success_rate = counts['success'] / total if total > 0 else 0
                    
                    # Calculate average processing time
                    times = [item['processing_time'] for item in self.event_processing_times[event_type]]
                    avg_processing_time = sum(times) / len(times) if times else 0
                    
                    return {
                        'event_type': event_type,
                        'total_processed': total,
                        'success_count': counts['success'],
                        'failure_count': counts['failure'],
                        'success_rate': success_rate,
                        'average_processing_time': avg_processing_time,
                        'recent_processing_times': times[-10:]  # Last 10 processing times
                    }
                else:
                    return {}
            else:
                # Return stats for all event types
                all_stats = {}
                for evt_type in self.event_counts:
                    all_stats[evt_type] = self.get_event_processing_stats(evt_type)
                return all_stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get overall system statistics
        
        Returns:
            Dict[str, Any]: System statistics
        """
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'total_processed_events': self.total_processed_events,
            'total_failed_events': self.total_failed_events,
            'success_rate': (
                self.total_processed_events / (self.total_processed_events + self.total_failed_events)
                if (self.total_processed_events + self.total_failed_events) > 0
                else 0
            ),
            'active_connections': self.active_connections,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_prometheus_metrics(self) -> str:
        """
        Get metrics in Prometheus format
        
        Returns:
            str: Metrics in Prometheus text format
        """
        from prometheus_client import generate_latest
        return generate_latest(self.registry).decode('utf-8')
    
    def start_metrics_server(self, port: int = 8001):
        """
        Start a metrics server for Prometheus to scrape
        
        Args:
            port: Port to run the metrics server on
        """
        try:
            start_http_server(port, registry=self.registry)
            logger.info(
                f"Metrics server started on port {port}",
                event_type="metrics_server_started",
                port=port
            )
        except Exception as e:
            logger.error(
                f"Failed to start metrics server: {str(e)}",
                event_type="metrics_server_start_error",
                port=port,
                error=str(e)
            )
            raise
    
    def record_business_metric(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a custom business metric
        
        Args:
            metric_name: Name of the metric
            value: Value of the metric
            labels: Optional labels for the metric
        """
        # In a real implementation, this would create dynamic metrics
        # For now, we'll just log the metric
        logger.info(
            f"Business metric recorded: {metric_name} = {value}",
            event_type="business_metric_recorded",
            metric_name=metric_name,
            value=value,
            labels=labels
        )
    
    def cleanup_old_metrics(self, max_age_minutes: int = 60):
        """
        Clean up old metrics to prevent memory issues
        
        Args:
            max_age_minutes: Maximum age of metrics to keep in minutes
        """
        with self.lock:
            cutoff_time = datetime.utcnow().timestamp() - (max_age_minutes * 60)
            
            for event_type in list(self.event_processing_times.keys()):
                # Remove old entries
                old_count = len(self.event_processing_times[event_type])
                self.event_processing_times[event_type] = deque([
                    item for item in self.event_processing_times[event_type]
                    if item['timestamp'].timestamp() > cutoff_time
                ])
                new_count = len(self.event_processing_times[event_type])
                
                if old_count != new_count:
                    logger.info(
                        f"Cleaned up {old_count - new_count} old metrics for {event_type}",
                        event_type="metrics_cleanup_performed",
                        event_type_detail=event_type,
                        cleaned_count=old_count - new_count
                    )


# Global instance of the metrics service
metrics_service = MetricsService()


# Context manager for timing operations
class Timer:
    """
    Context manager for timing operations and recording metrics
    """
    
    def __init__(self, event_type: str, user_id: Optional[str] = None):
        self.event_type = event_type
        self.user_id = user_id
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            success = exc_type is None
            metrics_service.record_event_processing(
                event_type=self.event_type,
                processing_time=duration,
                success=success,
                user_id=self.user_id
            )