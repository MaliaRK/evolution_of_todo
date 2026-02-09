"""
Dapr Configuration for Todo AI System
"""

import os

# Dapr configuration
DAPR_SIDECAR_HOST = os.getenv("DAPR_SIDECAR_HOST", "localhost")
DAPR_SIDECAR_PORT = int(os.getenv("DAPR_SIDECAR_PORT", "3500"))
DAPR_APP_ID = os.getenv("DAPR_APP_ID", "todo-backend")
DAPR_APP_PORT = int(os.getenv("DAPR_APP_PORT", "8000"))
DAPR_API_VERSION = os.getenv("DAPR_API_VERSION", "v1.0")

# Dapr pubsub component name
DAPR_PUBSUB_NAME = os.getenv("DAPR_PUBSUB_NAME", "kafka-pubsub")

# Dapr state store component name (if needed)
DAPR_STATE_STORE_NAME = os.getenv("DAPR_STATE_STORE_NAME", "todo-state-store")