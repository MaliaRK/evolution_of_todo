# Data Model: Cloud-Native Event-Driven Todo System

## Core Entities

### Task (Maintained from Previous Phases)
- **task_id**: UUID (Primary Key)
- **title**: String (255 chars, required)
- **description**: Text (optional)
- **completed**: Boolean (default: false)
- **created_at**: DateTime (auto-generated)
- **updated_at**: DateTime (auto-generated)
- **due_date**: DateTime (optional)
- **priority**: Enum ['low', 'medium', 'high'] (default: 'medium')
- **user_id**: UUID (foreign key to user)

### Event Models (New for Phase V)

#### BaseEventSchema
- **event_id**: UUID (Primary Key)
- **event_type**: String (type discriminator)
- **user_id**: UUID (identifies tenant)
- **correlation_id**: UUID (request correlation)
- **timestamp**: DateTime (event occurrence)
- **payload**: JSON (event-specific data)
- **version**: Integer (schema version, default: 1)

#### TaskEvent (Inherits BaseEventSchema)
- **task_id**: UUID (references affected task)
- **previous_state**: JSON (optional, for updates)
- **new_state**: JSON (after change)

#### ActivityEvent (Inherits BaseEventSchema)
- **activity_type**: String ('task_created', 'task_updated', 'task_completed', etc.)
- **metadata**: JSON (activity-specific details)

## Event Schemas

### TaskCreatedEvent
```
{
  "event_type": "task.created",
  "user_id": "uuid-string",
  "correlation_id": "uuid-string",
  "timestamp": "ISO8601-datetime",
  "task_id": "uuid-string",
  "payload": {
    "title": "string",
    "description": "string",
    "due_date": "ISO8601-datetime",
    "priority": "enum",
    "completed": false
  }
}
```

### TaskUpdatedEvent
```
{
  "event_type": "task.updated",
  "user_id": "uuid-string",
  "correlation_id": "uuid-string",
  "timestamp": "ISO8601-datetime",
  "task_id": "uuid-string",
  "payload": {
    "fields_changed": ["field1", "field2"],
    "previous_values": { /* previous values */ },
    "new_values": { /* new values */ }
  }
}
```

### TaskCompletedEvent
```
{
  "event_type": "task.completed",
  "user_id": "uuid-string",
  "correlation_id": "uuid-string",
  "timestamp": "ISO8601-datetime",
  "task_id": "uuid-string",
  "payload": {
    "completed_at": "ISO8601-datetime",
    "completed_by": "user-identifier"
  }
}
```

### TaskDeletedEvent
```
{
  "event_type": "task.deleted",
  "user_id": "uuid-string",
  "correlation_id": "uuid-string",
  "timestamp": "ISO8601-datetime",
  "task_id": "uuid-string",
  "payload": {
    "deletion_reason": "string"
  }
}
```

### ActivityEvent
```
{
  "event_type": "activity.tracked",
  "user_id": "uuid-string",
  "correlation_id": "uuid-string",
  "timestamp": "ISO8601-datetime",
  "activity_type": "string",
  "payload": {
    "action": "string",
    "target_entity": "string",
    "target_id": "uuid-string",
    "metadata": {}
  }
}
```

## Consumer State Tracking (for Idempotency)

### ProcessedEvent
- **event_id**: UUID (Foreign Key to BaseEventSchema)
- **consumer_id**: String (identifies which consumer processed)
- **processed_at**: DateTime (processing timestamp)
- **result_status**: Enum ['success', 'failed', 'skipped']
- **retry_count**: Integer (number of processing attempts)

## Validation Rules

### Task Entity
- Title must be 1-255 characters
- User ID must exist in user service
- Due date must be in the future (if provided)
- Priority must be one of allowed values

### Event Schema
- All events must include user_id for tenant isolation
- Correlation_id must be UUID format
- Timestamp must be ISO8601 format
- Payload must conform to event-specific schema
- Event_type must be from predefined list

## State Transitions

### Task States
```
CREATED -> UPDATED -> COMPLETED/DELETED
CREATED -> DELETED
```

### Event Processing States
```
PENDING -> PROCESSING -> SUCCESS/FAILED
FAILED -> RETRYING -> SUCCESS/DEAD_LETTER
```

## Relationships

### Task and Events
- One Task can have many TaskEvents (one-to-many)
- Events reference Tasks but can exist independently for historical tracking

### User and Events
- One User can generate many Events (one-to-many)
- Events are partitioned by user_id for multi-tenant isolation

## Indexing Strategy

### Task Table
- Primary: task_id
- Composite: (user_id, created_at) for user timeline queries
- Index: (user_id, completed) for filtering

### Event Tables
- Primary: event_id
- Composite: (user_id, timestamp) for chronological user events
- Index: (event_type, timestamp) for analytics queries
- Index: (correlation_id) for request tracing