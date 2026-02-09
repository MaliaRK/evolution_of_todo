import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.todo_router import router as todo_router
from .api.auth_router import router as auth_router
from .api.chat import router as chat_router  # Import the new chat router
from .handlers.health_check_handler import router as health_router  # Import health check router
import uvicorn
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .handlers.error_handler import register_error_handlers
from .utils.logging import get_logger

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app):
    """
    Lifespan event handler for the FastAPI application.
    Runs startup and shutdown events.
    """
    logger.info("Starting up AI Todo Chatbot application...")

    # Startup: Create database tables
    try:
        create_db_and_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

    yield

    # Shutdown: Cleanup operations
    logger.info("Shutting down AI Todo Chatbot application...")

# Create FastAPI app instance with lifespan
app = FastAPI(
    title="AI Todo Chatbot API",
    description="An AI-powered todo management system that allows users to manage their tasks using natural language",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Include the existing routers
app.include_router(todo_router)  # New event-driven endpoints
app.include_router(auth_router)

# Include the new chat router
app.include_router(chat_router)

# Include the health check router
app.include_router(health_router)

@app.get("/")
def read_root():
    return {"message": "AI Todo Chatbot API is running!", "version": "1.0.0"}


# The basic health check endpoint is now handled by the health_router
# @app.get("/health")
# def health_check():
#     return {"status": "healthy", "service": "ai-todo-chatbot"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Read PORT env variable
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)  # Enable reload for development


def run_server():
    """Function to run the server, used by Railway deployment"""
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)