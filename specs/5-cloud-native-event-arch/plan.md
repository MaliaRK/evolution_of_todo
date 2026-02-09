# Implementation Plan: Cloud-Native Event-Driven Architecture for Todo AI System

**Branch**: `5-cloud-native-event-arch` | **Date**: 2026-02-07 | **Spec**: [link](spec.md)
**Input**: Feature specification from `/specs/5-cloud-native-event-arch/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementation of event-driven architecture using Apache Kafka for task lifecycle management and Dapr for service-to-service communication. The system will transition from synchronous REST-based operations to an asynchronous, resilient architecture that supports horizontal scaling, improved observability, and fault tolerance while maintaining backward compatibility with existing REST APIs.

## Technical Context

**Language/Version**: Python 3.11+ (FastAPI), JavaScript/TypeScript (Next.js)
**Primary Dependencies**: Apache Kafka, Dapr, FastAPI, SQLModel, Neon PostgreSQL, Better Auth
**Storage**: Neon Serverless PostgreSQL with potential Dapr state stores
**Testing**: pytest for backend, Jest/Cypress for frontend, integration tests for event flows
**Target Platform**: Kubernetes (Minikube locally, DigitalOcean in cloud)
**Project Type**: Microservices architecture with event-driven communication
**Performance Goals**: <100ms response times during high load, 99.9% event processing success rate, 10,000 events/minute processing capability
**Constraints**: Must maintain backward compatibility with Phase II/III APIs, zero trust between services, user isolation in event processing
**Scale/Scope**: 1000+ concurrent users, 10,000+ events per minute, horizontal scaling of event processors

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Code generation must be performed by Claude Code (no manual code writing) ✓
- Implementation must follow written specifications from spec.md ✓
- Developer acts as Product Architect (intentional design) ✓
- Technology stack must match current phase requirements (no future-phase tech) ✓
- Clean architecture and separation of concerns must be maintained ✓
- All source code must reside in appropriate directory structure with modular logic ✓
- Implementation must respect current phase's architectural constraints ✓
- No global mutable state leakage allowed ✓
- Follow phase-specific quality and documentation standards ✓

## Project Structure

### Documentation (this feature)

```text
specs/5-cloud-native-event-arch/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── todo_models.py          # Updated models for event context
│   │   └── event_models.py         # Models for event schemas
│   ├── services/
│   │   ├── todo_service.py         # Business logic with event publishing
│   │   ├── event_publisher.py      # Kafka event publishers
│   │   ├── event_consumer.py       # Kafka event consumers
│   │   └── dapr_integration.py     # Dapr service invocation
│   ├── api/
│   │   ├── v1/
│   │   │   ├── todo_router.py      # Updated router with event-driven operations
│   │   │   └── event_router.py     # New event-specific endpoints
│   │   └── deps.py                 # Dependency injection
│   ├── config/
│   │   ├── kafka_config.py         # Kafka configuration
│   │   ├── dapr_config.py          # Dapr configuration
│   │   └── auth_config.py          # JWT/auth configuration
│   └── main.py                     # Application entry point with Dapr integration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── event_flow_tests.py         # End-to-end event processing tests
└── docker-compose.yml              # Docker setup with Kafka and Dapr

dapr/
├── components/
│   ├── pubsub.yaml                 # Kafka pub/sub component
│   ├── statestore.yaml             # State management component (optional)
│   └── secrets.yaml                # Secret management component
└── config/
    └── config.yaml                 # Dapr configuration

helm/
└── todo-app/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── kafka/
        ├── dapr/
        ├── backend/
        └── frontend/

frontend/
└── (Existing Next.js app remains with minor updates for event-driven UX feedback)
```

**Structure Decision**: The existing multi-service structure (backend/Next.js frontend) is extended with Kafka and Dapr integration points. New event publisher/consumer services are added alongside existing FastAPI backend to maintain backward compatibility while introducing asynchronous capabilities. All new event-driven functionality is encapsulated in dedicated modules to preserve the existing architecture's integrity.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple services/components | Event-driven architecture requires decoupled services | Monolithic approach would not scale or provide resilience |
| Kafka + Dapr complexity | Need both reliable messaging and service mesh capabilities | Single technology cannot provide both event streaming and service invocation |

## Phase V – Part A Implementation Plan

### Phase 0: Research & Discovery

1. **Research Kafka Integration Patterns**
   - Task: Analyze Kafka partitioning strategies for multi-tenant todo system
   - Task: Research JWT token propagation in async Kafka messages
   - Task: Investigate correlation ID patterns for request tracing

2. **Research Dapr Best Practices**
   - Task: Study Dapr pub/sub patterns with Kafka
   - Task: Examine Dapr service invocation in Kubernetes
   - Task: Analyze Dapr state management for optional caching

3. **Architecture Pattern Analysis**
   - Task: Research event sourcing vs eventual consistency patterns
   - Task: Evaluate idempotent consumer implementation strategies
   - Task: Analyze dead letter queue patterns for failed events

### Phase 1: Design & Foundation

#### A. Event Architecture Design
1. **Define Kafka Topic Strategy**
   - todo-events: Task lifecycle events (create, update, complete, delete)
   - activity-stream: User activity logs for analytics
   - notifications: Potential future notification triggers
   - dead-letter: Failed event processing

2. **Design Event Schemas**
   - TaskCreatedEvent: { user_id, task_id, correlation_id, timestamp, task_data }
   - TaskUpdatedEvent: { user_id, task_id, correlation_id, timestamp, updated_fields }
   - TaskCompletedEvent: { user_id, task_id, correlation_id, timestamp, completion_data }
   - ActivityEvent: { user_id, action_type, correlation_id, timestamp, metadata }

3. **Implement Event Publisher Interface**
   - Async event publishing to Kafka
   - JWT token attachment to events
   - Correlation ID generation and propagation

#### B. Dapr Integration Design
1. **Configure Dapr Components**
   - Kafka pub/sub component configuration
   - Secret management for Kafka/Dapr credentials
   - State management for optional caching

2. **Design Service-to-Service Patterns**
   - Dapr service invocation for API calls
   - Circuit breaker patterns
   - Retry mechanisms with exponential backoff

#### C. Security & Isolation Design
1. **JWT Token Propagation**
   - Token inclusion in event headers
   - Token validation in consumers
   - User context preservation across async boundaries

2. **Multi-Tenant Isolation**
   - User ID verification in all consumers
   - Tenant-specific event processing
   - Data access controls in event handlers

### Phase 2: Implementation Sequence

#### Milestone 1: Kafka Infrastructure
1. Set up Kafka topics and configurations
2. Implement basic event publisher
3. Create event consumer skeleton
4. Integrate with existing FastAPI services

#### Milestone 2: Core Event-Driven Flows
1. Task creation via Kafka events
2. Task update via Kafka events
3. Task completion/deletion via Kafka events
4. Event-driven activity logging

#### Milestone 3: Dapr Integration
1. Configure Dapr sidecars
2. Implement Dapr service invocation
3. Set up pub/sub abstraction over Kafka
4. Enable circuit breakers and retries

#### Milestone 4: Advanced Patterns
1. Implement idempotent consumers
2. Add dead-letter queue handling
3. Configure horizontal pod autoscaling
4. Implement structured logging and tracing

#### Milestone 5: Validation & Testing
1. Event flow validation tests
2. Failure scenario testing
3. Performance and scalability validation
4. Backward compatibility verification