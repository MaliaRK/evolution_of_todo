# Documentation Updates for Cloud Native Deployment
# Updates to documentation to reflect cloud native patterns and deployment configurations

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: deployment-documentation
  namespace: todo-app
data:
  deployment-guide.md: |
    # Cloud Native Deployment Guide for Todo AI System
    
    ## Table of Contents
    1. [Overview](#overview)
    2. [Prerequisites](#prerequisites)
    3. [Architecture](#architecture)
    4. [Installation](#installation)
    5. [Configuration](#configuration)
    6. [Operations](#operations)
    7. [Troubleshooting](#troubleshooting)
    8. [Scaling](#scaling)
    9. [Security](#security)
    10. [Monitoring](#monitoring)
    11. [Backup and Recovery](#backup-and-recovery)
    
    ## Overview
    
    This guide provides instructions for deploying the Todo AI system using cloud-native patterns and infrastructure. The system is designed to run on Kubernetes with Dapr for service-to-service communication, Kafka for event streaming, and comprehensive observability.
    
    ### Key Features
    - **Kubernetes-native**: Designed for container orchestration
    - **Dapr integration**: Service mesh for resilient communication
    - **Event-driven architecture**: Kafka-powered messaging
    - **Multi-cloud ready**: Configurable for various cloud providers
    - **Observability**: Comprehensive monitoring and logging
    - **Security**: Built-in security and compliance features
    - **Auto-scaling**: Dynamic resource allocation
    
    ## Prerequisites
    
    ### Infrastructure Requirements
    - Kubernetes cluster (v1.25+)
    - kubectl (v1.25+)
    - Helm (v3.10+)
    - Docker (for local development)
    
    ### Resource Requirements
    - **Minimum**: 4 CPU cores, 8GB RAM, 50GB disk space
    - **Recommended**: 8 CPU cores, 16GB RAM, 100GB disk space
    
    ### Network Requirements
    - Inbound access to load balancer/ingress
    - Outbound access to container registries
    - Internal cluster communication
    
    ## Architecture
    
    ### System Components
    1. **Todo App Service**: Main application service
    2. **Dapr Runtime**: Service mesh and building blocks
    3. **Kafka Cluster**: Event streaming and messaging
    4. **Database**: Persistent data storage
    5. **Cache**: Redis for caching and sessions
    6. **Monitoring Stack**: Prometheus, Grafana, Loki
    7. **Logging Stack**: Fluentd, Elasticsearch, Kibana
    
    ### Deployment Architecture
    ```
    +---------------------+
    |     Load Balancer   |
    +----------+----------+
               |
    +----------v----------+
    |     Ingress NGINX   |
    +----------+----------+
               |
    +----------v----------+
    |   todo-app Service  |
    |  (with Dapr sidecar)|
    +----------+----------+
               |
    +----------v----------+
    |  Dapr Sidecar       |
    |  (State, Pub/Sub,   |
    |   Service Invocation)|
    +----------+----------+
               |
    +----------+----------+    +----------+----------+
    |     Database        |    |    Kafka Cluster    |
    |   (PostgreSQL)      |    |  (for events)       |
    +---------------------+    +---------------------+
    ```
    
    ## Installation
    
    ### 1. Clone the Repository
    ```bash
    git clone https://github.com/your-org/todo-app.git
    cd todo-app
    ```
    
    ### 2. Install Dapr
    ```bash
    # Install Dapr CLI
    wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
    
    # Initialize Dapr on your Kubernetes cluster
    dapr init -k --runtime-version=1.10.0
    ```
    
    ### 3. Install Kafka
    ```bash
    # Add the Bitnami Helm repository
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    
    # Install Kafka
    helm install kafka bitnami/kafka \
      --namespace kafka \
      --create-namespace \
      --set replicaCount=1 \
      --set autoCreateTopicsEnable=true \
      --set logFlushIntervalMessages=1 \
      --set offsetsTopicReplicationFactor=1 \
      --set defaultReplicationFactor=1
    ```
    
    ### 4. Deploy the Todo App
    ```bash
    # Navigate to the Helm chart directory
    cd helm/todo-app
    
    # Install the Todo App with default values
    helm install todo-app . \
      --namespace todo-app \
      --create-namespace \
      --values values-prod.yaml
    ```
    
    ## Configuration
    
    ### Environment-Specific Values
    
    The system supports multiple environments through Helm value files:
    
    - `values-local.yaml`: For local development
    - `values-staging.yaml`: For staging environment
    - `values-prod.yaml`: For production environment
    
    ### Custom Configuration
    
    To customize the deployment, create a custom values file:
    
    ```yaml
    # custom-values.yaml
    replicaCount: 3
    
    image:
      repository: your-registry/todo-app
      pullPolicy: Always
      tag: "latest"
    
    service:
      type: LoadBalancer
      port: 80
    
    ingress:
      enabled: true
      className: "nginx"
      hosts:
        - host: todo-app.example.com
          paths:
            - path: /
              pathType: Prefix
      tls:
        - secretName: todo-app-tls
          hosts:
            - todo-app.example.com
    
    resources:
      limits:
        cpu: 500m
        memory: 512Mi
      requests:
        cpu: 250m
        memory: 256Mi
    
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilizationPercentage: 80
      targetMemoryUtilizationPercentage: 80
    ```
    
    Then deploy with:
    ```bash
    helm install todo-app . -f custom-values.yaml
    ```
    
    ## Operations
    
    ### Managing the Deployment
    
    #### Check Status
    ```bash
    # Check pods
    kubectl get pods -n todo-app
    
    # Check services
    kubectl get svc -n todo-app
    
    # Check deployments
    kubectl get deployments -n todo-app
    
    # Check Dapr status
    dapr status -k
    ```
    
    #### Scaling
    ```bash
    # Scale manually
    kubectl scale deployment todo-app --replicas=5 -n todo-app
    
    # Check HPA status
    kubectl get hpa -n todo-app
    ```
    
    #### Updating
    ```bash
    # Update with new image
    helm upgrade todo-app . \
      --namespace todo-app \
      --set image.tag="new-version"
    
    # Rollback if needed
    helm rollback todo-app -n todo-app
    ```
    
    ### Health Checks
    
    The system provides several health check endpoints:
    
    - `/healthz`: Liveness probe
    - `/readyz`: Readiness probe
    - `/startupz`: Startup probe
    - `/health/overall`: Comprehensive health status
    
    ## Troubleshooting
    
    ### Common Issues
    
    #### Pod Stuck in Pending State
    ```bash
    # Check events
    kubectl describe pod <pod-name> -n todo-app
    
    # Check resource quotas
    kubectl describe resourcequota -n todo-app
    ```
    
    #### Service Unreachable
    ```bash
    # Check service configuration
    kubectl get svc todo-app -n todo-app
    kubectl describe svc todo-app -n todo-app
    
    # Test connectivity
    kubectl run test-pod --image=busybox --rm -it --restart=Never -- nslookup todo-app.todo-app.svc.cluster.local
    ```
    
    #### Dapr Sidecar Issues
    ```bash
    # Check Dapr logs
    kubectl logs <pod-name> -c daprd -n todo-app
    
    # Check Dapr status
    kubectl get configurations -n dapr-system
    kubectl get components -n dapr-system
    ```
    
    ### Diagnostic Commands
    
    ```bash
    # Get comprehensive status
    kubectl get all -n todo-app
    
    # Check logs
    kubectl logs -f deployment/todo-app -n todo-app
    
    # Execute commands in pod
    kubectl exec -it deployment/todo-app -n todo-app -- /bin/sh
    
    # Port forward for local testing
    kubectl port-forward -n todo-app svc/todo-app 8080:80
    ```
    
    ## Scaling
    
    ### Horizontal Pod Autoscaling (HPA)
    
    The system is configured with HPA based on CPU and memory utilization:
    
    ```yaml
    # Example HPA configuration
    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    metadata:
      name: todo-app-hpa
      namespace: todo-app
    spec:
      scaleTargetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: todo-app
      minReplicas: 2
      maxReplicas: 20
      metrics:
      - type: Resource
        resource:
          name: cpu
          target:
            type: Utilization
            averageUtilization: 70
      - type: Resource
        resource:
          name: memory
          target:
            type: Utilization
            averageUtilization: 80
    ```
    
    ### Vertical Pod Autoscaling (VPA)
    
    For automatic resource optimization:
    
    ```yaml
    apiVersion: autoscaling.k8s.io/v1
    kind: VerticalPodAutoscaler
    metadata:
      name: todo-app-vpa
      namespace: todo-app
    spec:
      targetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: todo-app
      updatePolicy:
        updateMode: "Auto"
    ```
    
    ## Security
    
    ### Network Policies
    
    Network policies restrict traffic between namespaces:
    
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: NetworkPolicy
    metadata:
      name: todo-app-netpol
      namespace: todo-app
    spec:
      podSelector:
        matchLabels:
          app: todo-app
      policyTypes:
      - Ingress
      - Egress
      ingress:
      - from:
        - namespaceSelector:
            matchLabels:
              name: dapr-system
        - podSelector:
            matchLabels:
              app: todo-app
      egress:
      - to:
        - namespaceSelector:
            matchLabels:
              name: dapr-system
        - namespaceSelector:
            matchLabels:
              name: kafka
    ```
    
    ### RBAC Configuration
    
    Proper RBAC roles and bindings are configured for least-privilege access.
    
    ### Secrets Management
    
    Secrets are managed using Kubernetes secrets and external secret stores:
    
    ```bash
    # View secrets (values are masked)
    kubectl get secrets -n todo-app
    
    # Create new secret
    kubectl create secret generic my-secret \
      --from-literal=key1=value1 \
      --from-literal=key2=value2 \
      -n todo-app
    ```
    
    ## Monitoring
    
    ### Metrics Collection
    
    Prometheus collects metrics from all services. Key metrics include:
    
    - Application response times
    - Request rates and error rates
    - Resource utilization (CPU, memory, disk)
    - Dapr-specific metrics
    - Kafka metrics
    
    ### Logging
    
    Structured JSON logging is implemented across all services with correlation IDs for tracing requests.
    
    ### Dashboards
    
    Grafana dashboards are available for:
    
    - Application performance
    - Infrastructure metrics
    - Business metrics
    - Security events
    
    ## Backup and Recovery
    
    ### Automated Backups
    
    Backups are configured to run automatically with retention policies.
    
    ### Disaster Recovery
    
    The system supports disaster recovery procedures including:
    
    - Cluster backup and restore
    - Data backup and restore
    - Multi-region deployment for high availability
    - Rollback procedures
    
    ### Backup Schedule
    
    - Daily backups of application data
    - Weekly full system backups
    - Continuous transaction logs
    
    For detailed backup and recovery procedures, refer to the [Backup and Recovery Guide](backup-recovery-guide.md).
  cloud-native-patterns.md: |
    # Cloud Native Patterns Implementation Guide
    
    ## Overview
    This document describes the cloud native patterns implemented in the Todo AI system.
    
    ## 1. Microservices Architecture
    
    ### Pattern: Decompose by Business Capability
    - Each service represents a distinct business capability
    - Loose coupling between services
    - Independent deployment and scaling
    
    ### Pattern: Database per Service
    - Each service has its own database
    - No shared databases between services
    - Eventual consistency through asynchronous communication
    
    ## 2. Service Mesh with Dapr
    
    ### Pattern: Sidecar Pattern
    - Dapr sidecars handle cross-cutting concerns
    - Application code focuses on business logic
    - Consistent communication patterns
    
    ### Pattern: Service Discovery
    - Automatic service discovery
    - Load balancing
    - Circuit breaking
    
    ## 3. Event-Driven Architecture
    
    ### Pattern: Publish-Subscribe
    - Kafka topics for event broadcasting
    - Multiple subscribers to the same events
    - Decoupled communication
    
    ### Pattern: Event Sourcing
    - System state derived from event log
    - Immutable event store
    - Audit trail for all changes
    
    ## 4. Resilience Patterns
    
    ### Pattern: Circuit Breaker
    - Prevents cascade failures
    - Fast fail for unavailable services
    - Automatic recovery
    
    ### Pattern: Retry with Exponential Backoff
    - Handles transient failures
    - Prevents system overload
    - Jitter to prevent thundering herd
    
    ### Pattern: Bulkhead
    - Isolates failures to specific components
    - Limits resource consumption
    - Prevents resource exhaustion
    
    ## 5. Observability Patterns
    
    ### Pattern: Distributed Tracing
    - Correlation IDs across services
    - End-to-end request tracking
    - Performance bottleneck identification
    
    ### Pattern: Structured Logging
    - Consistent log format across services
    - Rich context in log entries
    - Machine-readable logs
    
    ## 6. Security Patterns
    
    ### Pattern: Zero Trust
    - Verify everything
    - Least privilege access
    - Continuous validation
    
    ### Pattern: Defense in Depth
    - Multiple security layers
    - Network segmentation
    - Application-level security
    
    ## 7. Deployment Patterns
    
    ### Pattern: Blue-Green Deployment
    - Zero-downtime deployments
    - Quick rollback capability
    - Risk reduction
    
    ### Pattern: Canary Releases
    - Gradual rollout to users
    - Risk mitigation
    - Real-world testing
    
    ## 8. Configuration Patterns
    
    ### Pattern: Externalized Configuration
    - Configuration external to application
    - Environment-specific values
    - Dynamic configuration updates
    
    ### Pattern: Twelve-Factor App
    - Strict separation of config from code
    - Store config in the environment
    - Treat backing services as attached resources
  operational-runbooks.md: |
    # Operational Runbooks for Todo AI System
    
    ## Table of Contents
    1. [Daily Operations](#daily-operations)
    2. [Incident Response](#incident-response)
    3. [Maintenance Procedures](#maintenance-procedures)
    4. [Disaster Recovery](#disaster-recovery)
    5. [Security Procedures](#security-procedures)
    
    ## Daily Operations
    
    ### Morning Checklist
    1. Check overall system health
    2. Review overnight alerts and incidents
    3. Verify backup completion
    4. Check resource utilization
    5. Review application logs for errors
    
    ### System Health Check
    ```bash
    # Run comprehensive health check
    ./scripts/health-check.sh
    
    # Verify all pods are running
    kubectl get pods --all-namespaces
    
    # Check cluster resources
    kubectl top nodes
    kubectl top pods --all-namespaces
    
    # Check for any failed pods
    kubectl get pods --all-namespaces --field-selector status.phase!=Running,status.phase!=Succeeded
    ```
    
    ### Performance Monitoring
    - Monitor response times (P95 < 500ms)
    - Check error rates (< 1%)
    - Verify throughput requirements are met
    - Review resource utilization
    
    ## Incident Response
    
    ### Incident Classification
    
    | Level | Impact | Response Time | Communication |
    |-------|--------|---------------|---------------|
    | 4 (Critical) | Complete service outage | < 15 minutes | All hands |
    | 3 (High) | Significant functionality loss | < 30 minutes | Management notified |
    | 2 (Medium) | Limited functionality | < 2 hours | Team notified |
    | 1 (Low) | Minor issues | < 4 hours | Internal tracking |
    
    ### Incident Response Steps
    
    1. **Acknowledge**: Acknowledge the incident within SLA time
    2. **Assess**: Determine scope and impact
    3. **Communicate**: Notify stakeholders
    4. **Mitigate**: Implement immediate workaround
    5. **Resolve**: Apply permanent fix
    6. **Verify**: Confirm resolution
    7. **Document**: Record incident details
    
    ### Common Incident Procedures
    
    #### High Error Rate
    1. Check application logs for error patterns
    2. Verify external service dependencies
    3. Check resource utilization
    4. Review recent deployments
    5. Scale services if needed
    6. Rollback if issue is deployment-related
    
    #### High Latency
    1. Identify slowest components using tracing
    2. Check database query performance
    3. Verify cache hit rates
    4. Review network latency
    5. Scale bottleneck services
    6. Optimize queries if needed
    
    #### Service Unavailable
    1. Check pod status and events
    2. Verify service configuration
    3. Check node health
    4. Review network policies
    5. Check load balancer status
    6. Restart problematic pods
    
    ## Maintenance Procedures
    
    ### Scheduled Maintenance
    
    #### Weekly Tasks
    - Review and clean up old logs
    - Update system monitoring dashboards
    - Review security alerts
    - Check backup integrity
    
    #### Monthly Tasks
    - Security patching
    - Dependency updates
    - Performance tuning
    - Capacity planning
    
    #### Quarterly Tasks
    - Disaster recovery drill
    - Security audit
    - Performance benchmarking
    - Architecture review
    
    ### Maintenance Window Procedures
    
    1. **Preparation**
       - Notify users of scheduled maintenance
       - Prepare rollback plan
       - Backup critical data
       - Coordinate with team
    
    2. **Execution**
       - Monitor system during maintenance
       - Document all changes
       - Test functionality after changes
       - Verify system health
    
    3. **Post-Maintenance**
       - Confirm all services are operational
       - Monitor for issues
       - Update documentation
       - Communicate completion
    
    ## Disaster Recovery
    
    ### Disaster Recovery Plan
    
    1. **Assessment**
       - Determine type and scope of disaster
       - Activate disaster recovery team
       - Establish communication channels
    
    2. **Recovery Actions**
       - Activate backup systems
       - Restore from latest backup
       - Verify data integrity
       - Test system functionality
    
    3. **Recovery Verification**
       - Confirm all services operational
       - Validate data consistency
       - Test end-to-end functionality
       - Monitor for issues
    
    ### Backup and Restore Procedures
    
    #### Application Data Backup
    ```bash
    # Run backup script
    ./scripts/backup.sh
    
    # Verify backup integrity
    ./scripts/verify-backup.sh
    ```
    
    #### Database Backup
    ```bash
    # Backup database
    kubectl exec -n todo-app <db-pod> -- pg_dump -U postgres -d todo_app > backup.sql
    
    # Verify backup
    head -20 backup.sql
    ```
    
    #### System Restore
    ```bash
    # Restore from backup
    ./scripts/restore.sh -f backup-file.tar.gz
    
    # Verify restore
    ./scripts/health-check.sh
    ```
    
    ## Security Procedures
    
    ### Security Incident Response
    
    1. **Containment**
       - Isolate affected systems
       - Preserve evidence
       - Document incident details
    
    2. **Eradication**
       - Remove malicious access
       - Patch vulnerabilities
       - Update security configurations
    
    3. **Recovery**
       - Restore systems from clean backups
       - Verify system integrity
       - Monitor for residual issues
    
    4. **Lessons Learned**
       - Conduct post-incident review
       - Update security procedures
       - Implement preventive measures
    
    ### Regular Security Tasks
    
    - Vulnerability scanning (weekly)
    - Security patching (monthly)
    - Access review (quarterly)
    - Security training (biannually)
    
    ### Security Monitoring
    
    - Monitor for unusual access patterns
    - Track failed authentication attempts
    - Review security logs regularly
    - Alert on security events