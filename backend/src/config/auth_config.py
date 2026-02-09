"""
Authentication Configuration for Todo AI System
"""

import os

# JWT Configuration
JWT_SECRET = os.getenv("BETTER_AUTH_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# User isolation settings
USER_ISOLATION_ENABLED = os.getenv("USER_ISOLATION_ENABLED", "true").lower() == "true"
ENFORCE_JWT_IN_EVENTS = os.getenv("ENFORCE_JWT_IN_EVENTS", "true").lower() == "true"

# JWT claims
USER_ID_CLAIM = os.getenv("USER_ID_CLAIM", "sub")
CORRELATION_ID_HEADER = os.getenv("CORRELATION_ID_HEADER", "x-correlation-id")