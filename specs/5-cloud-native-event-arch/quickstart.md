# Quickstart Guide: Cloud-Native Event-Driven Todo System

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (Minikube for local development)
- Dapr CLI installed
- Python 3.11+ with pip
- Node.js 18+ for frontend (if developing frontend)

## Local Development Setup

### 1. Start Dapr and Kafka Infrastructure

```bash
# Initialize Dapr
dapr init

# Start Kafka using Docker Compose
docker-compose -f docker-compose.kafka.yml up -d

# Or use the full stack including all dependencies
docker-compose -f docker-compose.full.yml up -d
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
# Or if using uv: uv pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file in backend directory:
```bash
KAFKA_BROKERS=localhost:9092
DAPR_SIDECAR_HOST=localhost
DAPR_SIDECAR_PORT=3500
DATABASE_URL=postgresql://user:password@localhost/todo_db
BETTER_AUTH_SECRET=your-secret-key
```

### 4. Run the Backend Service

```bash
# Start the backend with Dapr sidecar
dapr run --app-id todo-backend --app-port 8000 --dapr-http-port 3500 -- python src/main.py

# In another terminal, run the event consumers
dapr run --app-id todo-consumer -- python src/services/event_consumer.py
```

### 5. Run Frontend (if needed)

```bash
cd frontend
npm install
npm run dev
```

## Configuration Overview

### Kafka Topics Setup

The system expects these Kafka topics to be available:
- `todo-events` - Task lifecycle events
- `activity-stream` - User activity events
- `dead-letter` - Failed event processing

### Dapr Components

Located in `dapr/components/`:
- `pubsub.yaml` - Kafka pub/sub configuration
- `statestore.yaml` - State management (optional)
- `secrets.yaml` - Secure credential management

### Event Schema Registry

All events follow the BaseEventSchema with standard headers:
```json
{
  "event_id": "uuid",
  "event_type": "string",
  "user_id": "uuid",
  "correlation_id": "uuid",
  "timestamp": "iso8601",
  "payload": {},
  "version": 1
}
```

## Running Tests

### Backend Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires Kafka and Dapr running)
pytest tests/integration/

# Event flow tests
pytest tests/event_flow_tests.py
```

### Manual Testing

1. **Task Creation Event Flow**:
   - Send POST to `/api/v1/todos` with task data
   - Verify event appears in `todo-events` topic
   - Check consumer processed event successfully

2. **Event Replay**:
   - Stop consumer
   - Create several tasks
   - Restart consumer
   - Verify all events processed

3. **Failure Handling**:
   - Configure consumer to fail on certain event types
   - Verify events move to dead-letter queue
   - Check monitoring alerts

## Environment Variables Reference

### Backend Configuration
```bash
KAFKA_BROKERS=comma-separated-list-of-kafka-brokers
KAFKA_CONSUMER_GROUP=consumer-group-name
EVENT_TOPIC_NAME=todo-events
ACTIVITY_TOPIC_NAME=activity-stream
DEAD_LETTER_TOPIC_NAME=dead-letter
DAPR_SIDECAR_HOST=dapr-sidecar-hostname
DAPR_SIDECAR_PORT=dapr-sidecar-port
LOG_LEVEL=INFO|DEBUG|WARNING
MAX_RETRIES=max-number-of-retries
RETRY_BACKOFF_BASE=base-backoff-in-seconds
```

### Database Configuration
```bash
DATABASE_URL=postgresql://username:password@host:port/database
DATABASE_POOL_SIZE=size-of-connection-pool
DATABASE_POOL_TIMEOUT=timeout-in-seconds
```

### Security Configuration
```bash
BETTER_AUTH_SECRET=auth-secret-key
JWT_VERIFY_EXPIRATION=true|false
USER_ISOLATION_ENABLED=true
ENFORCE_JWT_IN_EVENTS=true
```

## Kubernetes Deployment

### 1. Install Dapr on Kubernetes
```bash
dapr init -k
```

### 2. Deploy Applications
```bash
# Apply Dapr configurations
kubectl apply -f dapr/components/

# Deploy applications using Helm
helm install todo-app ./helm/todo-app/ --namespace todo-app --create-namespace
```

## Monitoring and Troubleshooting

### Dapr Dashboard
```bash
dapr dashboard -p 8080
```

### Kafka Management
```bash
# View topics
kafka-topics.sh --bootstrap-server localhost:9092 --list

# View consumer groups
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# Monitor topic messages
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic todo-events --from-beginning
```

### Common Issues

1. **Connection Issues**:
   - Verify Kafka brokers are accessible
   - Check Dapr sidecar is running and connected
   - Confirm environment variables are set correctly

2. **Event Processing Failures**:
   - Check consumer logs for error messages
   - Verify database connectivity
   - Ensure JWT tokens are valid and propagated correctly

3. **Performance Issues**:
   - Monitor Kafka topic lag
   - Check consumer group metrics
   - Adjust consumer concurrency as needed