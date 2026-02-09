# Event Driven Systems Skill

## Purpose
This skill provides implementation details for designing and implementing event-driven systems using Kafka abstracted through Dapr pub/sub. It focuses on defining domain events, designing event schemas, ensuring idempotent consumers, and avoiding tight coupling between services.

## Capabilities
- Define domain events that represent business state changes
- Design event schemas with proper versioning and compatibility
- Ensure idempotent event consumers that can handle duplicate events
- Avoid tight coupling between event publishers and consumers
- Implement proper error handling and retry mechanisms
- Design for eventual consistency in distributed systems

## Implementation Details

### Domain Event Definition
- Events should represent something that has already occurred
- Use past tense for event names (e.g., UserCreated, OrderShipped)
- Include essential context data in events
- Design events for multiple potential consumers
- Consider event granularity and data completeness

### Event Schema Design
- Use consistent naming conventions for event schemas
- Include version information for backward compatibility
- Define clear data contracts with validation rules
- Design schemas for extensibility and evolution
- Document event schema changes and migration strategies

### Idempotent Consumer Implementation
- Design consumers to handle duplicate events gracefully
- Use event identifiers to detect and skip duplicates
- Implement幂等操作 that produce the same result regardless of multiple executions
- Store processed event IDs for deduplication
- Use transactional processing where appropriate

### Loose Coupling Strategies
- Publishers should not know about specific consumers
- Events should be self-contained with necessary context
- Avoid sending service-specific data in events
- Design events for multiple potential use cases
- Use generic event formats where possible

### Retry and Error Handling
- Implement exponential backoff for transient failures
- Use dead letter queues for poisoned messages
- Track event processing metrics and errors
- Implement circuit breakers for failing consumers
- Design graceful degradation for event processing

### Event-Driven Best Practices
- Emit events instead of calling services directly
- Never assume consumer existence or availability
- Handle retries gracefully without overwhelming systems
- Design for eventual consistency in distributed systems
- Implement proper monitoring and observability for event flows

## Usage Guidelines

### Event Design Process:
1. Identify state changes that generate events
2. Define event schemas with proper context
3. Plan for schema evolution and versioning
4. Implement idempotent consumer logic
5. Design error handling and retry mechanisms

### Consumer Implementation:
- Validate incoming event schemas
- Process events transactionally
- Implement deduplication logic
- Log event processing for debugging
- Monitor consumer lag and performance

### Testing Strategies:
- Test event schema compatibility
- Verify idempotent consumer behavior
- Simulate consumer failures and retries
- Validate event ordering requirements
- Measure event processing performance