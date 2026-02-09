# Quickstart Guide: Cloud Native Todo Chatbot Phase V

## Overview
This guide provides the essential steps to set up and run the cloud-native deployment infrastructure for the Todo Chatbot application using Kubernetes, Dapr, and Kafka.

## Prerequisites

### Local Development Environment
- **Operating System**: Windows, macOS, or Linux
- **Kubernetes**: Minikube v1.28+ or equivalent local cluster
- **Helm**: v3.10+ installed and configured
- **kubectl**: v1.25+ installed and configured
- **Docker**: v20+ with Docker Desktop or equivalent
- **Dapr CLI**: Latest version installed for local development

### Cloud Access (for deployment)
- **Cloud Provider Account**: AKS, GKE, or Oracle Cloud Infrastructure account
- **CLI Tools**: Azure CLI, gcloud, or OCI CLI installed and authenticated
- **Kubernetes Credentials**: Appropriate permissions to create resources
- **Domain Name**: For ingress configuration (if required)

## Installation Steps

### 1. Local Minikube Setup
1. Start Minikube cluster with adequate resources:
   ```bash
   minikube start --cpus=4 --memory=8192 --disk-size=40g
   ```

2. Install Dapr runtime in the cluster:
   ```bash
   dapr init -k
   ```

3. Install Kafka using Helm chart:
   ```bash
   helm repo add confluentinc https://confluentinc.github.io/cp-helm-charts/
   helm repo update
   helm install kafka confluentinc/cp-helm-charts --version 0.6.0
   ```

### 2. Deploy Application Infrastructure
1. Navigate to the Helm chart directory:
   ```bash
   cd charts/todo-app
   ```

2. Install the application using Helm:
   ```bash
   helm install todo-app . -f values-local.yaml
   ```

3. Verify all services are running:
   ```bash
   kubectl get pods -n todo-app
   kubectl get services -n todo-app
   ```

### 3. Access the Application
1. Port forward to the frontend service:
   ```bash
   kubectl port-forward -n todo-app svc/todo-frontend 3000:80
   ```

2. Open browser to http://localhost:3000 to access the application

3. Verify Dapr sidecars are injected and operational:
   ```bash
   dapr status -k
   ```

## Configuration Management

### Environment-Specific Values
- `values-local.yaml`: Configuration for local Minikube development
- `values-staging.yaml`: Configuration for staging environment
- `values-prod.yaml`: Configuration for production environment

### Secrets Management
- Store sensitive configuration in Kubernetes secrets
- Use external secret stores (HashiCorp Vault, cloud providers) for production
- Reference secrets through Dapr secret store building blocks

### Dapr Component Configuration
Components are defined as Kubernetes Custom Resources:
- State stores in `config/dapr/statestores/`
- Pub/sub brokers in `config/dapr/pubsub/`
- Secret stores in `config/dapr/secrets/`

## Key Commands

### Development Workflow
- Deploy application: `helm install todo-app . -f values-local.yaml`
- Update application: `helm upgrade todo-app . -f values-local.yaml`
- Remove application: `helm uninstall todo-app`
- Check deployment: `kubectl get pods,services,ingress -n todo-app`

### Dapr Operations
- Check Dapr status: `dapr status -k`
- View Dapr logs: `kubectl logs -n dapr-system <dapr-component-pod>`
- List Dapr components: `kubectl get components.dapr.io -A`
- Monitor Dapr placement: `kubectl get pods -n dapr-system`

### Kafka Operations
- List Kafka topics: `kubectl exec -n kafka <kafka-pod> -- kafka-topics --list --bootstrap-server localhost:9092`
- Check broker status: `kubectl get pods -n kafka`
- View Kafka logs: `kubectl logs -n kafka <kafka-pod>`

### Monitoring
- View application logs: `kubectl logs -n todo-app <app-pod-name>`
- Check pod resource usage: `kubectl top pods -n todo-app`
- Monitor cluster events: `kubectl get events -n todo-app --watch`

## Troubleshooting

### Common Issues
1. **Pods in Pending state**: Check resource availability and node capacity
2. **Services not accessible**: Verify ingress configuration and load balancer status
3. **Dapr sidecar not injected**: Check Dapr operator status and annotations
4. **Kafka connectivity issues**: Verify network policies and service discovery

### Debugging Commands
- Check pod status and events: `kubectl describe pod <pod-name> -n <namespace>`
- View container logs: `kubectl logs <pod-name> -c <container-name> -n <namespace>`
- Execute commands in pod: `kubectl exec -it <pod-name> -n <namespace> -- /bin/sh`
- Check cluster health: `kubectl get nodes && kubectl get cs`

## Next Steps
1. Review the full documentation in the `docs/` directory
2. Set up the CI/CD pipeline following the guide in `pipelines/`
3. Configure monitoring and alerting as described in `monitoring/`
4. Prepare for cloud deployment by reviewing cloud-specific configurations