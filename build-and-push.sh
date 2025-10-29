#!/bin/bash

# STAR Analysis - Docker Hub Build and Push Script
# This script builds and pushes your application to Docker Hub

set -e  # Exit on any error

echo "🌟 STAR Analysis - Docker Hub Deployment Script"
echo "=============================================="

# Configuration - UPDATE THESE VALUES
DOCKER_HUB_USERNAME="franzking"  # Replace with your Docker Hub username
IMAGE_NAME="star-analysis"
VERSION="latest"
FULL_IMAGE_NAME="${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if user is logged into Docker Hub
if ! docker info | grep -q "Username"; then
    echo "🔐 Please login to Docker Hub first:"
    docker login
fi

echo "✅ Docker is available and user is logged in"

# Build the Docker image
echo "🔨 Building Docker image: ${FULL_IMAGE_NAME}"
docker build -t ${FULL_IMAGE_NAME} .

# Also tag as versioned release
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
VERSIONED_TAG="${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:v1.0-${TIMESTAMP}"
docker tag ${FULL_IMAGE_NAME} ${VERSIONED_TAG}

echo "🏷️  Tagged images:"
echo "   - ${FULL_IMAGE_NAME}"
echo "   - ${VERSIONED_TAG}"

# Push to Docker Hub
echo "📤 Pushing image to Docker Hub..."
docker push ${FULL_IMAGE_NAME}
docker push ${VERSIONED_TAG}

# Update production docker-compose file
echo "📝 Updating production docker-compose file..."
sed -i.bak "s|image: franzking/star-analysis:latest|image: ${FULL_IMAGE_NAME}|g" docker-compose.prod.yml

echo "✅ Build and push completed successfully!"
echo ""
echo "🚀 Deployment Information:"
echo "   Docker Hub Image: ${FULL_IMAGE_NAME}"
echo "   Versioned Image: ${VERSIONED_TAG}"
echo ""
echo "📋 To deploy anywhere, run:"
echo "   curl -O https://raw.githubusercontent.com/Franz-kingstein/STAR---Satelllite_Transmission_Analysis_Reduction/main/docker-compose.prod.yml"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🌐 After deployment, access at: http://localhost:8501"
