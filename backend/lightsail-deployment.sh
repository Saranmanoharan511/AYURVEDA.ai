#!/bin/bash

# AWS Lightsail Deployment Script for Ayurveda AI Backend
# This script is a template for deploying the FastAPI backend to AWS Lightsail
# NOTE: This script requires manual execution by the developer after AWS resources are created

set -e

echo "Starting Ayurveda AI Backend Deployment to Lightsail"

# Configuration - These should be set as environment variables
CONTAINER_NAME=${CONTAINER_NAME:-"ayurveda-backend"}
IMAGE_NAME=${IMAGE_NAME:-"ayurveda-backend:latest"}
PORT=${PORT:-8000}

# Build Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Stop existing container if running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Run new container
echo "Starting new container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p $PORT:8000 \
    --env-file .env \
    $IMAGE_NAME

echo "Deployment complete!"
echo "Container $CONTAINER_NAME is running on port $PORT"
