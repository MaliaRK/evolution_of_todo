# AI-Powered Todo Chatbot

An AI-powered todo management system that allows users to manage their tasks using natural language.

## Features

- Natural language todo management (add, list, update, complete, delete tasks)
- Conversational AI interface using OpenAI Agents and Cohere
- MCP (Model Context Protocol) tools for safe database operations
- Stateless architecture with persistent conversation history
- JWT-based authentication with Better Auth
- PostgreSQL database with SQLModel ORM

## Tech Stack

- **Frontend**: OpenAI ChatKit
- **Backend**: Python FastAPI
- **AI Framework**: OpenAI Agents SDK
- **MCP Server**: Official MCP SDK
- **ORM**: SQLModel
- **Database**: Neon Serverless PostgreSQL
- **Authentication**: Better Auth (JWT-based)
- **LLM Provider**: Cohere API (via OpenAI-compatible interface)

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL-compatible database (Neon recommended)
- Better Auth configured
- Cohere API key

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Navigate to backend directory:
   ```bash
   cd backend
   ```

3. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   Copy `.env` and update with your configuration:
   ```bash
   cp .env .env.local
   # Edit .env.local with your settings
   ```

6. Start the backend server:
   ```bash
   uvicorn src.main:app --reload
   ```

7. Navigate to frontend directory and start the frontend:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

## Usage

The AI chatbot understands natural language commands such as:
- "Add a task to buy groceries"
- "Show me my tasks"
- "Complete task number 1"
- "Delete my meeting task"
- "Update task 2 to 'Call John tomorrow'"

## Architecture

The system follows a stateless architecture where:
1. User messages are received via the chat endpoint
2. Conversation history is loaded from the database
3. The AI agent processes the message with MCP tools
4. Tool calls are executed to perform database operations
5. Responses are saved and returned to the user

## API Endpoints

The API is available at `http://localhost:8000/api/`:

- `POST /{user_id}/chat` - Process a user message in a conversation (must match authenticated user)

All endpoints require a valid JWT token in the Authorization header with "Bearer" prefix. The user_id in the path must match the user_id in the JWT token for security validation.

## Project Structure

```
backend/
├── src/
│   ├── models/          # Database models (Task, Conversation, Message)
│   ├── services/        # Business logic (Conversation, Message, Agent services)
│   ├── api/             # API routes (Chat endpoint)
│   ├── mcp/             # MCP server and tools
│   ├── agents/          # AI agent configuration
│   ├── auth/            # Authentication logic
│   └── main.py          # Application entry point
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables

frontend/
├── src/
│   ├── components/      # React components
│   ├── pages/           # Next.js pages
│   ├── services/        # API services
│   └── contexts/        # React contexts
├── package.json         # Node.js dependencies
└── .env.local           # Environment variables
```

## Development

For development, run both the backend and frontend in separate terminals:

Backend:
```bash
cd backend
uvicorn src.main:app --reload
```

Frontend:
```bash
cd frontend
npm run dev
```

## Deployment

The Todo AI System can be deployed to various cloud platforms. Here are the options:

### Railway (Recommended)

Railway provides an excellent platform for deploying both frontend and backend services:

1. **Backend Deployment**:
   - Create a new service in Railway
   - Connect your GitHub repository
   - Set the root directory to `./backend`
   - Add environment variables:
     - `DATABASE_URL`: PostgreSQL database connection string
     - `OPENAI_API_KEY`: OpenAI API key
     - `COHERE_API_KEY`: Cohere API key
     - `BETTER_AUTH_SECRET`: Better Auth secret
     - `BETTER_AUTH_URL`: Better Auth URL (your backend URL)

2. **Frontend Deployment**:
   - Create another service in Railway
   - Connect your GitHub repository
   - Set the root directory to `./frontend`
   - Add environment variable:
     - `NEXT_PUBLIC_API_BASE_URL`: Your backend URL

### Heroku

1. Create Heroku apps for both frontend and backend
2. Set appropriate buildpacks (Python for backend, Node.js for frontend)
3. Configure environment variables as mentioned above
4. Deploy using Git integration

### Render

1. Create Web Services for both frontend and backend
2. Configure build commands and environment variables
3. Set up automatic deployments from GitHub

### Docker

Build and run using Docker:

```bash
# Build images
cd backend && docker build -t todo-backend . && cd ..
cd frontend && docker build -t todo-frontend . && cd ..

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables

Required environment variables for deployment:

**Backend:**
- `DATABASE_URL`: PostgreSQL database connection string
- `OPENAI_API_KEY`: OpenAI API key
- `COHERE_API_KEY`: Cohere API key
- `BETTER_AUTH_SECRET`: Better Auth secret
- `BETTER_AUTH_URL`: Better Auth URL

**Frontend:**
- `NEXT_PUBLIC_API_BASE_URL`: Backend API URL

## Health Checks

After deployment, verify your services are running:

- Backend health: `GET /health`
- Backend detailed health: `GET /health/detailed`
- Backend metrics: `GET /metrics`

## License

This project is licensed under the MIT License.