# API Contracts: Cloud Native Todo Chatbot Phase V

## Overview
This document defines the API contracts for the cloud-native infrastructure components of the Todo Chatbot application, including the interfaces between application services, Dapr building blocks, and Kafka messaging.

## Service-to-Service Communication Contracts

### 1. Application Service Interface (HTTP/gRPC)
- **Protocol**: HTTP/1.1 or gRPC over HTTP/2
- **Base Path**: `/v1`
- **Authentication**: Bearer token via Authorization header
- **Rate Limiting**: X-RateLimit headers with limit, remaining, and reset values

#### Common Response Format
```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2026-02-09T10:00:00Z",
  "correlationId": "uuid-v4-string"
}
```

#### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  },
  "timestamp": "2026-02-09T10:00:00Z",
  "correlationId": "uuid-v4-string"
}
```

### 2. Dapr Service Invocation Contract
- **Method**: GET, POST, PUT, PATCH, DELETE
- **Path**: `/v1.0/invoke/{targetAppId}/method/{methodPath}`
- **Headers**:
  - `dapr-app-id`: Target application identifier
  - `dapr-method`: Target method name
  - `dapr-correlation-id`: Trace correlation identifier
- **Response**: Passthrough of target service response with additional Dapr headers

### 3. Dapr State Store Contract
- **Method**: GET, POST, PUT, DELETE
- **Path**: `/v1.0/state/{statestoreName}/{key}`
- **Content-Type**: application/json for state operations
- **State Item Structure**:
  ```json
  {
    "key": "string",
    "value": "any",
    "etag": "string",
    "metadata": {
      "ttlInSeconds": "string"
    }
  }
  ```

### 4. Dapr Publish/Subscribe Contract
- **Method**: POST
- **Path**: `/v1.0/publish/{pubsubname}/{topic}`
- **Content-Type**: application/cloudevents+json or application/json
- **Request Body**:
  ```json
  {
    "specversion": "1.0",
    "id": "unique-event-id",
    "source": "service-identifier",
    "type": "event-type-name",
    "data": {},
    "datacontenttype": "application/json",
    "traceid": "correlation-id"
  }
  ```

## Kafka Event Contracts

### 1. Todo Event Schema
- **Topic**: `todos.events`
- **Event Types**: `todo.created`, `todo.updated`, `todo.deleted`
- **Serialization**: JSON with schema validation

#### Todo Created Event
```json
{
  "eventId": "uuid-v4",
  "eventType": "todo.created",
  "timestamp": "2026-02-09T10:00:00Z",
  "source": "todo-service",
  "data": {
    "id": "string",
    "title": "string",
    "description": "string",
    "completed": false,
    "createdAt": "2026-02-09T10:00:00Z",
    "updatedAt": "2026-02-09T10:00:00Z"
  }
}
```

#### Todo Updated Event
```json
{
  "eventId": "uuid-v4",
  "eventType": "todo.updated",
  "timestamp": "2026-02-09T10:00:00Z",
  "source": "todo-service",
  "data": {
    "id": "string",
    "title": "string",
    "description": "string",
    "completed": false,
    "updatedAt": "2026-02-09T10:00:00Z"
  }
}
```

#### Todo Deleted Event
```json
{
  "eventId": "uuid-v4",
  "eventType": "todo.deleted",
  "timestamp": "2026-02-09T10:00:00Z",
  "source": "todo-service",
  "data": {
    "id": "string",
    "deletedAt": "2026-02-09T10:00:00Z"
  }
}
```

### 2. User Event Schema
- **Topic**: `users.events`
- **Event Types**: `user.created`, `user.updated`, `user.deleted`
- **Serialization**: JSON with schema validation

#### User Created Event
```json
{
  "eventId": "uuid-v4",
  "eventType": "user.created",
  "timestamp": "2026-02-09T10:00:00Z",
  "source": "user-service",
  "data": {
    "id": "string",
    "username": "string",
    "email": "string",
    "createdAt": "2026-02-09T10:00:00Z"
  }
}
```

## Dapr Component Configuration Contracts

### 1. State Store Component Contract
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    secretKeyRef:
      name: redis-password
      key: password
auth:
  secretStore: kubernetes
```

### 2. Pub/Sub Component Contract
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka:9092"
  - name: consumerGroup
    value: "todo-app-group"
  - name: authRequired
    value: "false"
```

## Health Check Contracts

### 1. Kubernetes Health Endpoints
- **Liveness Probe**: `/healthz` - verifies if container is alive
- **Readiness Probe**: `/readyz` - verifies if container is ready to serve traffic
- **Startup Probe**: `/startupz` - verifies if container is fully started (for initialization heavy apps)

### 2. Dapr Health Endpoints
- **Dapr Runtime**: `http://localhost:3500/v1.0/healthz` - Dapr sidecar health
- **Sidecar API**: `http://localhost:3501/v1.0/healthz/outbound` - outbound connectivity health

## Security Contracts

### 1. Authentication Contract
- **JWT Token Format**: RS256 signed tokens with claims validation
- **Token Audience**: Service-specific audience identifier
- **Token TTL**: 1 hour for access tokens, 24 hours for refresh tokens

### 2. Authorization Contract
- **RBAC Model**: Role-based access control with fine-grained permissions
- **Scopes**: Per-service scope definitions with least-privilege access
- **Policy Engine**: Open Policy Agent (OPA) for dynamic policy enforcement

## Observability Contracts

### 1. Metrics Endpoint Contract
- **Endpoint**: `/metrics` - Prometheus-compatible metrics endpoint
- **Format**: Prometheus exposition format
- **Required Metrics**:
  - `http_requests_total` (counter)
  - `http_request_duration_seconds` (histogram)
  - `app_build_info` (gauge)

### 2. Distributed Tracing Contract
- **Propagation Format**: W3C Trace Context standard
- **Sampling Rate**: 100% for error paths, 10% for success paths
- **Trace Headers**: `traceparent`, `tracestate`

### 3. Structured Logging Contract
- **Format**: JSON with timestamp, level, message, and structured fields
- **Required Fields**:
  - `timestamp`: ISO 8601 formatted time
  - `level`: DEBUG, INFO, WARN, ERROR, FATAL
  - `message`: Human-readable log message
  - `correlationId`: Request correlation identifier
  - `service`: Service name
  - `component`: Component generating log

## Error Handling Contracts

### 1. HTTP Status Code Contract
- **2xx**: Success operations
- **4xx**: Client-side errors (validation, authentication, authorization)
- **5xx**: Server-side errors (internal server errors, timeouts)

### 2. Dapr Error Responses
- **Dapr Error Codes**: Standard Dapr error codes (ERR_INVOKE, ERR_PUB_SUB, etc.)
- **Retry Policies**: Exponential backoff with jitter for transient failures
- **Circuit Breaker**: Applied to external service invocations

## Versioning Contracts

### 1. API Versioning
- **URL Versioning**: `/v1`, `/v2` path prefixes
- **Backward Compatibility**: Newer versions support older clients for 6 months
- **Deprecation Policy**: 3 months advance notice before removal

### 2. Event Versioning
- **Schema Evolution**: Forward and backward compatibility through optional fields
- **Event Schemas**: Versioned in schema registry with compatibility checks
- **Consumer Compatibility**: Support multiple event versions simultaneously