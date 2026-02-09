# Cloud Deployment Guide

This guide explains how to deploy the Todo AI System to various cloud platforms.

## Prerequisites

Before deploying, ensure you have:

1. **Environment Variables**:
   - `DATABASE_URL`: PostgreSQL database connection string
   - `OPENAI_API_KEY`: OpenAI API key
   - `COHERE_API_KEY`: Cohere API key
   - `BETTER_AUTH_SECRET`: Better Auth secret
   - `BETTER_AUTH_URL`: Better Auth URL
   - `NEXT_PUBLIC_API_BASE_URL`: Frontend API base URL

2. **Database**: A PostgreSQL database (Neon, AWS RDS, Google Cloud SQL, etc.)

3. **AI API Keys**: OpenAI and Cohere API keys

## Platform-Specific Instructions

### 1. Railway Deployment

#### Backend Deployment:
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Navigate to backend directory: `cd backend`
4. Link to new project: `railway init`
5. Set environment variables:
   ```bash
   railway variables set DATABASE_URL=<your-database-url>
   railway variables set OPENAI_API_KEY=<your-openai-key>
   railway variables set COHERE_API_KEY=<your-cohere-key>
   railway variables set BETTER_AUTH_SECRET=<your-auth-secret>
   railway variables set BETTER_AUTH_URL=<your-auth-url>
   ```
6. Deploy: `railway up`

#### Frontend Deployment:
1. Navigate to frontend directory: `cd frontend`
2. Link to new project: `railway init`
3. Set environment variable:
   ```bash
   railway variables set NEXT_PUBLIC_API_BASE_URL=<your-backend-url>
   ```
4. Deploy: `railway up`

### 2. Heroku Deployment

#### Backend Deployment:
1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Login: `heroku login`
3. Create app: `heroku create <your-app-name>`
4. Set buildpack: `heroku buildpacks:set heroku/python`
5. Set environment variables:
   ```bash
   heroku config:set DATABASE_URL=<your-database-url>
   heroku config:set OPENAI_API_KEY=<your-openai-key>
   heroku config:set COHERE_API_KEY=<your-cohere-key>
   heroku config:set BETTER_AUTH_SECRET=<your-auth-secret>
   heroku config:set BETTER_AUTH_URL=<your-auth-url>
   ```
6. Deploy: `git push heroku main`

#### Frontend Deployment:
1. Create separate app: `heroku create <your-frontend-app-name>`
2. Set buildpack: `heroku buildpacks:set https://github.com/mars/create-react-app-buildpack.git`
3. Set environment variable:
   ```bash
   heroku config:set NEXT_PUBLIC_API_BASE_URL=<your-backend-url>
   ```
4. Deploy: `git push heroku main`

### 3. Render Deployment

#### Backend Deployment:
1. Create new Web Service on Render
2. Connect your GitHub/GitLab repository
3. Set Root Directory to `./backend`
4. Set Build Command to: `pip install -r requirements.txt`
5. Set Start Command to: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables in Render dashboard

#### Frontend Deployment:
1. Create new Static Site on Render
2. Connect your GitHub/GitLab repository
3. Set Root Directory to `./frontend`
4. Set Build Command to: `npm install && npm run build`
5. Set Publish Directory to: `out`
6. Set Environment Variable `NEXT_PUBLIC_API_BASE_URL` to your backend URL

### 4. Vercel Deployment (Frontend Only)

1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Navigate to frontend directory: `cd frontend`
4. Deploy: `vercel --env NEXT_PUBLIC_API_BASE_URL=<your-backend-url>`
5. Follow prompts to link to your Git repo for automatic deployments

## Docker Deployment

You can also deploy using Docker:

1. Build images:
   ```bash
   cd backend && docker build -t todo-backend .
   cd ../frontend && docker build -t todo-frontend .
   ```

2. Run with docker-compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Important Notes

1. **Database Migration**: Ensure your database is properly migrated before deploying
2. **CORS Settings**: The backend allows all origins (`"*"`), adjust for production
3. **Security**: Change the default database credentials and secrets
4. **Scaling**: Configure appropriate instance sizes based on expected load
5. **Monitoring**: Set up logging and monitoring for production deployments

## Troubleshooting

1. **Backend not starting**: Check environment variables and database connectivity
2. **Frontend can't connect to backend**: Verify `NEXT_PUBLIC_API_BASE_URL` is correctly set
3. **Database connection issues**: Ensure your database allows connections from the cloud platform
4. **API key issues**: Verify your OpenAI and Cohere API keys are valid and have sufficient quota

## Post-Deployment

After deployment:

1. Test the health endpoints: `GET /health` and `GET /health/detailed`
2. Verify all services are running properly
3. Check the metrics endpoint: `GET /metrics`
4. Test basic functionality with sample requests
5. Monitor logs for any errors or warnings