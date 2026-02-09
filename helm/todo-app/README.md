# Todo App Helm Chart

This Helm chart deploys the Todo AI system with integrated Kafka and Dapr infrastructure.

## Prerequisites

- Kubernetes 1.25+
- Helm 3.10+
- Dapr installed in the cluster (optional, can be deployed via this chart)
- Kafka cluster (optional, can be deployed via this chart)

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
helm install my-release . --values values-local.yaml
```

## Upgrading the Chart

```bash
helm upgrade my-release . --values values-local.yaml
```

## Uninstalling the Chart

```bash
helm uninstall my-release
```

## Configuration

The following table lists the configurable parameters of the todo-app chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of todo-app pods to run | `1` |
| `image.repository` | Todo-app image repository | `"nginx"` |
| `image.pullPolicy` | Image pull policy | `"IfNotPresent"` |
| `image.tag` | Todo-app image tag | `""` |
| `service.type` | Service type | `"ClusterIP"` |
| `service.port` | Service port | `80` |
| `ingress.enabled` | Enable ingress | `false` |
| `resources` | CPU/Memory resource requests/limits | `{}` |
| `autoscaling.enabled` | Enable autoscaling | `false` |
| `kafka.enabled` | Enable Kafka deployment | `true` |
| `dapr.enabled` | Enable Dapr deployment | `true` |

## Environment-Specific Configurations

This chart supports multiple environments through different values files:

- `values-local.yaml` - For local Minikube development
- `values-staging.yaml` - For staging environment
- `values-prod.yaml` - For production environment

## Dapr Integration

The chart includes Dapr components for:
- State management (Redis)
- Pub/Sub messaging (Kafka)
- Secret management
- Service invocation

## Kafka Integration

The chart includes Kafka for:
- Event streaming
- Message queuing
- Event sourcing

## Scaling

Horizontal Pod Autoscaling is supported and can be enabled in the values files.