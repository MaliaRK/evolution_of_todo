#!/bin/bash

# Deployment script for Todo AI System

set -e  # Exit on any error

echo "🚀 Starting deployment of Todo AI System..."

# Function to deploy backend
deploy_backend() {
    echo "📦 Building backend..."
    cd backend
    
    # Build Docker image
    echo "🐳 Building backend Docker image..."
    docker build -t todo-backend .
    
    # Tag for deployment (this would be customized for your cloud platform)
    docker tag todo-backend todo-backend:latest
    
    echo "✅ Backend built successfully!"
    cd ..
}

# Function to deploy frontend
deploy_frontend() {
    echo "📦 Building frontend..."
    cd frontend
    
    # Build Docker image
    echo "🐳 Building frontend Docker image..."
    docker build -t todo-frontend .
    
    # Tag for deployment (this would be customized for your cloud platform)
    docker tag todo-frontend todo-frontend:latest
    
    echo "✅ Frontend built successfully!"
    cd ..
}

# Function to deploy to cloud platform (example for Railway)
deploy_to_railway() {
    echo "☁️ Deploying to Railway..."
    
    # Check if railway CLI is installed
    if ! command -v railway &> /dev/null; then
        echo "❌ Railway CLI not found. Please install it first:"
        echo "npm install -g @railway/cli"
        exit 1
    fi
    
    # Login to Railway (if not already logged in)
    railway login
    
    # Deploy backend
    echo "🏗️ Deploying backend to Railway..."
    cd backend
    railway up -n "todo-backend"
    cd ..
    
    # Deploy frontend
    echo "🏗️ Deploying frontend to Railway..."
    cd frontend
    railway up -n "todo-frontend"
    cd ..
    
    echo "✅ Deployment to Railway completed!"
}

# Function to deploy to Heroku
deploy_to_heroku() {
    echo "☁️ Deploying to Heroku..."
    
    # Check if heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        echo "❌ Heroku CLI not found. Please install it first:"
        echo "https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    # Login to Heroku (if not already logged in)
    heroku auth:whoami || heroku login
    
    # Create Heroku apps (if they don't exist)
    if ! heroku apps:info todo-backend-app &> /dev/null; then
        echo "Creating Heroku app for backend..."
        heroku create todo-backend-app
    fi
    
    if ! heroku apps:info todo-frontend-app &> /dev/null; then
        echo "Creating Heroku app for frontend..."
        heroku create todo-frontend-app
    fi
    
    # Deploy backend
    echo "🏗️ Deploying backend to Heroku..."
    cd backend
    git init
    heroku git:remote -a todo-backend-app
    heroku config:set DATABASE_URL=$DATABASE_URL -a todo-backend-app
    heroku config:set OPENAI_API_KEY=$OPENAI_API_KEY -a todo-backend-app
    heroku config:set COHERE_API_KEY=$COHERE_API_KEY -a todo-backend-app
    heroku config:set BETTER_AUTH_SECRET=$BETTER_AUTH_SECRET -a todo-backend-app
    heroku config:set BETTER_AUTH_URL=$BETTER_AUTH_URL -a todo-backend-app
    git add .
    git commit -m "Deploy backend" || echo "No changes to commit"
    git push heroku main
    cd ..
    
    # Deploy frontend
    echo "🏗️ Deploying frontend to Heroku..."
    cd frontend
    git init
    heroku git:remote -a todo-frontend-app
    heroku config:set NEXT_PUBLIC_API_BASE_URL=$(heroku config:get HEROKU_APP_NAME -a todo-backend-app).herokuapp.com -a todo-frontend-app
    git add .
    git commit -m "Deploy frontend" || echo "No changes to commit"
    git push heroku main
    cd ..
    
    echo "✅ Deployment to Heroku completed!"
}

# Function to deploy to Render
deploy_to_render() {
    echo "☁️ Deploying to Render..."
    
    echo "💡 Render deployment instructions:"
    echo "1. Create a new Web Service on Render"
    echo "2. Connect your GitHub/GitLab repository"
    echo "3. Set the root directory to './backend' for the backend service"
    echo "4. Set the build command to: pip install -r requirements.txt"
    echo "5. Set the start command to: uvicorn src.main:app --host 0.0.0.0 --port \$PORT"
    echo "6. Add environment variables in Render dashboard"
    echo ""
    echo "For frontend:"
    echo "1. Create a new Static Site on Render"
    echo "2. Connect your GitHub/GitLab repository"
    echo "3. Set the root directory to './frontend'"
    echo "4. Set the build command to: npm install && npm run build"
    echo "5. Set the publish directory to: out"
    echo "6. Set environment variable NEXT_PUBLIC_API_BASE_URL to your backend URL"
    
    echo "✅ Render deployment instructions provided!"
}

# Function to show deployment options
show_help() {
    echo "Usage: $0 [option]"
    echo "Options:"
    echo "  --backend          Deploy only the backend"
    echo "  --frontend         Deploy only the frontend"
    echo "  --railway          Deploy to Railway"
    echo "  --heroku           Deploy to Heroku"
    echo "  --render           Show Render deployment instructions"
    echo "  --all              Deploy both backend and frontend locally"
    echo "  --help             Show this help message"
}

# Main script logic
case "$1" in
    --backend)
        deploy_backend
        ;;
    --frontend)
        deploy_frontend
        ;;
    --railway)
        deploy_backend
        deploy_frontend
        deploy_to_railway
        ;;
    --heroku)
        deploy_backend
        deploy_frontend
        deploy_to_heroku
        ;;
    --render)
        deploy_to_render
        ;;
    --all)
        deploy_backend
        deploy_frontend
        ;;
    --help|*)
        show_help
        ;;
esac

echo "🎉 Deployment process completed!"