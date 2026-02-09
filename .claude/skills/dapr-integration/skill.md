# Dapr Integration Skill

## Purpose
This skill provides implementation details for using Dapr building blocks instead of direct infrastructure SDKs. It focuses on leveraging Dapr's pub/sub, secrets management, scheduled jobs (reminders), and state storage to abstract infrastructure complexity and promote portable, maintainable applications.

## Capabilities
- Use Dapr pub/sub building block to abstract Kafka complexity
- Implement secrets management through Dapr's secret store
- Utilize Dapr reminders for scheduled job execution
- Leverage Dapr state management for temporary data storage
- Avoid direct infrastructure SDK usage in application code
- Promote infrastructure-agnostic application design

## Implementation Details

### Dapr Pub/Sub Implementation
- Use Dapr's pub/sub building block to publish and subscribe to events
- Abstract underlying message broker (Kafka, RabbitMQ, etc.) through Dapr
- Define topic subscriptions using Dapr configuration
- Implement proper error handling for message publishing/subscribing
- Configure delivery guarantees and retry policies through Dapr

### Secrets Management
- Retrieve secrets through Dapr's secret store API
- Configure secret stores (HashiCorp Vault, Azure Key Vault, etc.) in Dapr
- Access secrets programmatically using Dapr SDK
- Implement proper secret rotation and refresh mechanisms
- Never hardcode secrets in application code

### Scheduled Jobs (Reminders)
- Use Dapr reminders for scheduled task execution
- Configure reminder intervals and callbacks
- Implement idempotent reminder handlers
- Monitor reminder execution and failures
- Handle reminder state management through Dapr

### State Storage
- Use Dapr state management for temporary data storage
- Configure state stores (Redis, CosmosDB, etc.) in Dapr
- Implement state operations using Dapr SDK
- Configure consistency and concurrency models
- Handle state transactions where supported

### Infrastructure Abstraction
- Avoid direct SDK usage for infrastructure services
- Use Dapr building blocks as the primary interface
- Configure infrastructure providers through Dapr components
- Maintain infrastructure-agnostic application code
- Enable easy provider switching through configuration

## Usage Guidelines

### Dapr Component Configuration:
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
    value: "localhost:9092"
```

### Application Integration:
- Import Dapr SDK for your language
- Use Dapr client for pub/sub, state, secrets operations
- Configure Dapr sidecar injection
- Define Dapr component configurations
- Test with local Dapr runtime

### Best Practices:
- Always use Dapr building blocks over direct SDKs
- Configure infrastructure through Dapr components
- Implement proper error handling for Dapr operations
- Monitor Dapr sidecar health and performance
- Keep application code infrastructure-agnostic

### Prohibited Practices:
- Never use direct Kafka client libraries
- Never access secrets directly from code
- Never implement custom infrastructure SDK wrappers
- Never hardcode infrastructure connection details
- Never bypass Dapr for infrastructure services