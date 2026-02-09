# Kubernetes Deployment Skill

## Purpose
This skill provides implementation details for deploying applications on Kubernetes using Helm charts and best practices. It focuses on writing Helm values, defining probes and resource limits, using ConfigMaps and Secrets, and enabling horizontal scaling for deployment on both local Minikube and managed Kubernetes environments.

## Capabilities
- Write comprehensive Helm values files for application configuration
- Define health probes (liveness and readiness) for application monitoring
- Set appropriate resource limits and requests for containers
- Configure ConfigMaps and Secrets for application configuration
- Enable horizontal pod autoscaling based on metrics
- Deploy applications to Minikube and managed Kubernetes environments
- Implement rolling updates and blue-green deployment strategies

## Implementation Details

### Helm Values Configuration
- Define application parameters in values.yaml
- Configure replica counts and scaling parameters
- Set up resource requests and limits for containers
- Configure environment variables and configuration
- Define service ports and networking configuration
- Set up ingress rules and TLS configuration

### Health Probes Implementation
- Configure readiness probes to verify application startup
- Implement liveness probes to detect application health
- Set appropriate probe timeouts and failure thresholds
- Use HTTP endpoints, TCP connections, or command execution
- Configure initial delay and period for optimal performance
- Design probes that accurately reflect application health

### Resource Management
- Set CPU and memory requests for guaranteed resources
- Configure CPU and memory limits to prevent resource exhaustion
- Balance resource allocation with application performance
- Use resource quotas at namespace level for multi-tenant clusters
- Monitor resource usage and adjust limits accordingly
- Implement resource budgets for availability management

### ConfigMaps and Secrets
- Store configuration in ConfigMaps for non-sensitive data
- Use Secrets for sensitive information (passwords, tokens)
- Mount ConfigMaps and Secrets as volumes or environment variables
- Implement secret encryption at rest
- Rotate secrets regularly and securely
- Use external secret stores when appropriate

### Horizontal Scaling Configuration
- Configure Horizontal Pod Autoscaler (HPA) based on CPU/memory
- Implement custom metrics-based scaling using Prometheus adapter
- Set minimum and maximum replica counts
- Configure scaling behavior for rapid scaling/in
- Monitor scaling events and performance impact
- Plan for scaling limitations and constraints

### Deployment Strategies
- Implement rolling updates with configurable max surge/unavailable
- Configure blue-green deployments for zero-downtime releases
- Use canary deployments for gradual rollout of new versions
- Implement rollback procedures for failed deployments
- Set up deployment monitoring and health checks
- Plan for database migrations during deployments

## Usage Guidelines

### Helm Chart Structure:
```yaml
# values.yaml example
image:
  repository: my-app
  tag: latest
  pullPolicy: IfNotPresent

replicaCount: 3

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Target Environments:
- Minikube for local development and testing
- AKS (Azure Kubernetes Service) for Azure deployments
- GKE (Google Kubernetes Engine) for Google Cloud deployments
- OKE (Oracle Kubernetes Engine) for Oracle Cloud deployments
- Self-managed clusters for on-premises deployments

### Best Practices:
- Use semantic versioning for Helm charts
- Implement proper security contexts for containers
- Configure network policies for service isolation
- Use init containers for setup tasks
- Implement proper logging and monitoring
- Test deployments in staging before production