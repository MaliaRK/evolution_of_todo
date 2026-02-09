# Cloud Native Architecture Skill

## Purpose
This skill provides implementation details for designing scalable, fault-tolerant, cloud-native architectures using microservices, event-driven communication, and Kubernetes. It focuses on breaking monolithic applications into services, defining service boundaries, and leveraging Kafka and Dapr for event-driven communication.

## Capabilities
- Break monolithic applications into microservices
- Define appropriate service boundaries based on domain-driven design
- Recommend Kafka and Dapr usage for event-driven communication
- Ensure loose coupling between services
- Design stateless services with externalized configuration
- Implement configuration management via environment variables and secrets

## Implementation Details

### Microservice Decomposition
- Analyze monolithic applications to identify service boundaries
- Group related functionality based on business domains
- Ensure each service has a single responsibility
- Design services to be independently deployable and scalable
- Minimize cross-service dependencies and communication

### Service Boundary Definition
- Use domain-driven design principles to identify bounded contexts
- Group related entities and operations within service boundaries
- Define clear interfaces and contracts between services
- Consider data ownership and consistency requirements
- Plan for service evolution and independent lifecycle management

### Kafka + Dapr Integration
- Leverage Dapr pub/sub building block to abstract Kafka complexity
- Design event schemas that promote loose coupling
- Implement event sourcing patterns where appropriate
- Ensure proper partitioning and topic management
- Handle event ordering and delivery guarantees appropriately

### Async Communication Patterns
- Prefer asynchronous communication over synchronous calls
- Implement fire-and-forget patterns for non-critical operations
- Use request-response patterns only when necessary
- Design for eventual consistency in distributed systems
- Implement circuit breaker and retry patterns for resilience

### Stateless Service Design
- Design services to be stateless wherever possible
- Externalize state to Dapr state stores or external databases
- Use externalized configuration via environment variables
- Implement proper session management patterns
- Ensure services can be scaled horizontally without shared state

## Usage Guidelines

### Service Decomposition Process:
1. Identify business domains and subdomains
2. Group related functionality into services
3. Define service interfaces and contracts
4. Plan data migration and ownership
5. Design inter-service communication patterns

### Architecture Constraints:
- Services must be stateless
- Configuration managed via env vars/secrets
- Async communication preferred
- Loose coupling enforced
- Independent deployment capability required

### Best Practices:
- Each service owns its data
- Use events for communication
- Implement proper monitoring
- Plan for graceful degradation
- Design for failure scenarios