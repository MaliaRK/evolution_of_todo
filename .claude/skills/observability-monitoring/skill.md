# Observability Monitoring Skill

## Purpose
This skill provides implementation details for adding visibility into distributed systems. It focuses on implementing structured logging, metrics-ready design, trace-friendly APIs, and comprehensive health checks to ensure systems can be effectively monitored, debugged, and maintained in production environments.

## Capabilities
- Implement structured logging with appropriate levels and context
- Design applications with built-in metrics collection capabilities
- Create trace-friendly APIs that support distributed tracing
- Implement comprehensive health checks for system monitoring
- Configure centralized logging and monitoring solutions
- Design alerting and notification systems for operational awareness

## Implementation Details

### Structured Logging Implementation
- Use structured logging formats (JSON) with consistent field names
- Include correlation IDs for distributed tracing across services
- Implement appropriate log levels (debug, info, warn, error, fatal)
- Add contextual information (request IDs, user IDs, session IDs) to logs
- Include performance metrics and timing information in logs
- Configure log retention and archival policies

### Metrics-Ready Design
- Instrument applications with appropriate metrics collection
- Use standard metric types (counters, gauges, histograms, summaries)
- Implement business-relevant metrics alongside system metrics
- Expose metrics endpoints compatible with Prometheus
- Configure proper metric labeling for dimensional analysis
- Set up metrics aggregation and visualization dashboards

### Distributed Tracing
- Implement trace context propagation across service boundaries
- Use standardized trace ID and span ID formats
- Correlate traces with logs and metrics for comprehensive visibility
- Instrument both synchronous and asynchronous operations
- Configure sampling strategies to balance detail with performance
- Use OpenTelemetry or similar standards for vendor neutrality

### Health Check Implementation
- Implement liveness checks to verify service health
- Create readiness checks to indicate service availability
- Design business-specific health indicators
- Configure health check endpoints with appropriate protocols
- Implement dependency health checks (databases, external services)
- Set up automated responses to health check failures

### Centralized Monitoring Solutions
- Configure log aggregation (ELK stack, Fluentd, etc.)
- Set up metrics collection and storage (Prometheus, InfluxDB)
- Implement centralized tracing (Jaeger, Zipkin)
- Configure alerting rules and notification channels
- Create comprehensive dashboards for operational visibility
- Establish monitoring as code practices

### Alerting and Notification
- Define appropriate alert thresholds and conditions
- Configure notification channels (email, Slack, PagerDuty)
- Implement alert grouping and deduplication
- Set up escalation policies for critical issues
- Create runbooks and incident response procedures
- Monitor alert effectiveness and reduce noise

## Usage Guidelines

### Structured Logging Example:
```json
{
  "timestamp": "2023-10-15T10:30:00.000Z",
  "level": "INFO",
  "service": "user-service",
  "traceId": "abc123def456",
  "spanId": "xyz789",
  "message": "User authentication successful",
  "userId": "user123",
  "requestId": "req456",
  "durationMs": 150
}
```

### Metrics Collection:
- Counter: Total requests, errors, processed items
- Gauge: Current active connections, queue sizes
- Histogram: Request duration, response sizes
- Summary: Percentile calculations for performance metrics

### Health Check Endpoints:
- GET /health - Overall service health
- GET /health/readiness - Service readiness for traffic
- GET /health/liveness - Service liveness status
- GET /health/checks - Detailed component health status

### Best Practices:
- Log consistently across all services
- Use correlation IDs for request tracing
- Monitor both system and business metrics
- Implement proactive alerting thresholds
- Regularly review and optimize log volume
- Test monitoring and alerting configurations