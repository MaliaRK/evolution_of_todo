# Data Model: Cloud Native Todo Chatbot Phase V

## Overview
This document defines the data structures and relationships for the cloud-native infrastructure components of the Todo Chatbot application.

## Infrastructure Entities

### 1. Kubernetes Namespace
- **Name**: String, required, unique
- **Purpose**: Defines isolation boundary for infrastructure components
- **Relationships**: Contains multiple Kubernetes resources
- **Validation**: Must follow RFC 1123 DNS label standard

### 2. Dapr Component
- **Type**: Enum (statestore, pubsub, secretstore, bindings, middleware)
- **Version**: String, required
- **Metadata**: Key-value pairs for configuration
- **Scopes**: Array of service names that can access this component
- **Validation**: Must have valid type and required metadata fields

### 3. Kafka Topic
- **Name**: String, required, unique
- **Partitions**: Integer, default 3, min 1
- **ReplicationFactor**: Integer, default 1, min 1, max available brokers
- **RetentionMs**: Integer, default 7 days in milliseconds
- **CleanupPolicy**: Enum (compact, delete, compact,delete)
- **Relationships**: Producers publish to topic, consumers subscribe to topic

### 4. Helm Release
- **Name**: String, required
- **Chart**: Reference to Helm chart with version
- **Values**: Configuration values applied to chart
- **Namespace**: Target namespace for deployment
- **Status**: Current state (deployed, failed, pending)

### 5. Kubernetes Deployment
- **Name**: String, required
- **Replicas**: Integer, default 1
- **Selector**: Labels to match pods
- **Template**: Pod template specification
- **Strategy**: Update strategy (RollingUpdate, Recreate)

### 6. Kubernetes Service
- **Name**: String, required
- **Type**: Enum (ClusterIP, NodePort, LoadBalancer, ExternalName)
- **Ports**: Array of port specifications (port, targetPort, protocol)
- **Selector**: Labels to select pods to expose

## Configuration Entities

### 7. Environment Configuration
- **Environment**: Enum (local, dev, staging, prod)
- **ValuesFile**: Path to environment-specific values
- **Namespace**: Target deployment namespace
- **ImageRegistry**: Registry URL for container images
- **ResourceLimits**: CPU and memory constraints

### 8. CI/CD Pipeline Configuration
- **Repository**: Git repository URL
- **BranchPattern**: Regex pattern for triggering builds
- **Stages**: Ordered array of pipeline stages
- **Credentials**: Secure reference to authentication tokens
- **Notifications**: Destination for pipeline status updates

### 9. Observability Configuration
- **MetricsEndpoint**: Prometheus-compatible endpoint
- **LogDestination**: Centralized logging system
- **TraceCollector**: Distributed tracing backend
- **DashboardUrl**: Visualization tool endpoint
- **AlertChannels**: Notification destinations for alerts

## Security Entities

### 10. Secret Definition
- **Key**: Name of the secret key
- **Source**: Reference to external secret store
- **Permissions**: Access control for different services
- **RotationPolicy**: Schedule and procedure for secret updates
- **Encryption**: Method for encrypting at rest and in transit

### 11. Network Policy
- **Name**: String, required
- **PodSelector**: Selector for pods this policy applies to
- **IngressRules**: Rules for incoming traffic
- **EgressRules**: Rules for outgoing traffic
- **Priority**: Order of rule evaluation

### 12. RBAC Role
- **Name**: String, required
- **Resources**: Kubernetes resources this role applies to
- **Verbs**: Actions permitted (get, list, create, update, delete)
- **ApiGroups**: API groups this role applies to
- **Subjects**: Users, groups, or service accounts assigned to role

## Event Entities

### 13. Event Schema
- **EventType**: Unique identifier for event type
- **Version**: Schema version identifier
- **PayloadSchema**: JSON Schema definition for event payload
- **Source**: Identifier of the event producer
- **Consumers**: List of services that consume this event

### 14. Consumer Group
- **GroupId**: Unique identifier for consumer group
- **Topics**: List of topics this group consumes from
- **OffsetManagement**: Strategy for tracking consumption position
- **RebalanceStrategy**: Algorithm for distributing partitions among consumers
- **FailureHandling**: Strategy for handling consumer failures

## Relationships

### Infrastructure Relationships
- Kubernetes Namespace `contains` multiple Deployments, Services, and Pods
- Dapr Component `is referenced by` multiple Application Services
- Kafka Topic `is produced to by` Producer Services and `consumed by` Consumer Services
- Helm Release `deploys` multiple Kubernetes Resources

### Configuration Relationships
- Environment Configuration `contains` multiple Infrastructure Components
- CI/CD Pipeline Configuration `manages` Helm Release deployments
- Observability Configuration `applies to` all Infrastructure Components

### Security Relationships
- Secret Definition `is accessed by` multiple Services based on Permissions
- Network Policy `controls access to` specific Pods based on Selectors
- RBAC Role `grants permissions to` Subjects for Resources

## State Transitions

### Helm Release States
- `pending-install` → `deployed` (successful installation)
- `deployed` → `failed` (installation error)
- `deployed` → `pending-upgrade` (upgrade initiated)
- `pending-upgrade` → `deployed` (upgrade successful)
- `deployed` → `uninstalled` (deletion requested)

### Deployment States
- `pending` → `running` (pod startup)
- `running` → `terminated` (pod completion)
- `running` → `crashloopbackoff` (repeated failures)
- `running` → `succeeded` (successful completion for Jobs)

## Validation Rules

### Naming Conventions
- All names must follow DNS RFC 1123 guidelines
- Use lowercase letters, numbers, and hyphens only
- Start and end with alphanumeric characters
- Maximum length of 63 characters

### Resource Requirements
- All deployments must specify resource requests and limits
- Memory and CPU values must be within cluster capacity
- Replica counts must be appropriate for workload type

### Security Requirements
- All secrets must be stored in external secret store
- Network policies must be defined for all namespaces
- RBAC must follow principle of least privilege
- All inter-service communication must use mTLS