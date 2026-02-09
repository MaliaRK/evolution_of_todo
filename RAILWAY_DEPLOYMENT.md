# Deployment Configuration for Railway

This project can be deployed to Railway with the following configuration:

## Backend Service (Python FastAPI)

### Dockerfile
```Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
Set these variables in Railway dashboard:

- `DATABASE_URL`: PostgreSQL database connection string
- `OPENAI_API_KEY`: OpenAI API key
- `COHERE_API_KEY`: Cohere API key
- `BETTER_AUTH_SECRET`: Better Auth secret
- `BETTER_AUTH_URL`: Better Auth URL (usually your backend URL)

### Build Command
```
pip install -r requirements.txt
```

### Start Command
```
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

## Frontend Service (Next.js)

### Dockerfile
```Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy built application from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

# Start the application
CMD ["npm", "start"]
```

### Environment Variables
- `NEXT_PUBLIC_API_BASE_URL`: Your backend URL (e.g., https://your-backend.onrender.com)

### Build Command
```
npm install && npm run build
```

### Start Command
```
npm start
```

## Alternative: Using Railway CLI

1. Install Railway CLI:
```
npm install -g @railway/cli
```

2. Login:
```
railway login
```

3. For backend:
```
cd backend
railway init
railway link
railway variables set DATABASE_URL=<your-db-url>
railway variables set OPENAI_API_KEY=<your-openai-key>
railway variables set COHERE_API_KEY=<your-cohere-key>
railway variables set BETTER_AUTH_SECRET=<your-auth-secret>
railway variables set BETTER_AUTH_URL=<your-auth-url>
railway up
```

4. For frontend:
```
cd frontend
railway init
railway link
railway variables set NEXT_PUBLIC_API_BASE_URL=<your-backend-url>
railway up
```

## Health Checks

Once deployed, verify your services are running by checking:

- Backend health: `GET /health`
- Backend detailed health: `GET /health/detailed`
- Backend metrics: `GET /metrics`

## Notes

- Make sure your database is accessible from the internet
- Adjust CORS settings in production (currently allows all origins)
- Monitor resource usage and scale accordingly
- Set up proper logging and monitoring for production