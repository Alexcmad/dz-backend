#!/bin/bash

# Configuration
AWS_REGION="your-region"
ECR_REPO="your-account-id.dkr.ecr.$AWS_REGION.amazonaws.com"
APP_NAME="hazard-reporting-system"

# Build the Docker image
echo "Building Docker image..."
docker build -t $APP_NAME .

# Tag the image
echo "Tagging image..."
docker tag $APP_NAME:latest $ECR_REPO/$APP_NAME:latest

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

# Push the image
echo "Pushing image to ECR..."
docker push $ECR_REPO/$APP_NAME:latest

echo "Deployment complete! Image pushed to ECR."
echo "To deploy to EC2, SSH into your instance and run:"
echo "docker pull $ECR_REPO/$APP_NAME:latest"
echo "docker run -d -p 80:8000 $ECR_REPO/$APP_NAME:latest" 