#!/bin/bash

# STAR Analysis - Easy Deployment Script
# This script allows anyone to deploy the STAR application with one command

set -e  # Exit on any error

echo "🌟 STAR Analysis - One-Click Deployment"
echo "======================================"
echo "Hipparcos Star Catalog Analysis Platform"
echo ""

# Configuration
DOCKER_HUB_IMAGE="franzking/star-analysis:latest"  # Replace with your Docker Hub username
COMPOSE_URL="https://raw.githubusercontent.com/Franz-kingstein/STAR---Satelllite_Transmission_Analysis_Reduction/main/docker-compose.prod.yml"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "📥 Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo "📥 Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Determine compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Download production docker-compose file if it doesn't exist
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "📥 Downloading deployment configuration..."
    curl -sL ${COMPOSE_URL} -o docker-compose.prod.yml
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to download deployment configuration"
        echo "🔧 Please ensure you have internet connectivity"
        exit 1
    fi
fi

# Pull latest images
echo "📥 Pulling latest images..."
docker pull mongo:7.0
docker pull ${DOCKER_HUB_IMAGE}

# Stop any existing deployment
echo "🛑 Stopping any existing deployment..."
${COMPOSE_CMD} -f docker-compose.prod.yml down 2>/dev/null || true

# Create logs directory
mkdir -p logs

# Start the application
echo "🚀 Starting STAR Analysis application..."
${COMPOSE_CMD} -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
echo "   This may take 1-2 minutes for first-time setup..."

# Check service status
for i in {1..60}; do
    if ${COMPOSE_CMD} -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo "✅ Services are starting up..."
        break
    fi
    echo -n "."
    sleep 2
done

# Wait a bit more for the application to fully initialize
sleep 30

# Check if services are running and healthy
if ${COMPOSE_CMD} -f docker-compose.prod.yml ps | grep -E "(Up|healthy)" | grep -q star_streamlit_prod; then
    echo ""
    echo "🎉 STAR Analysis is now running!"
    echo ""
    echo "🌐 Access the application at: http://localhost:8501"
    echo "📊 MongoDB is available at: localhost:27017"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: ${COMPOSE_CMD} -f docker-compose.prod.yml logs -f"
    echo "   Stop app:  ${COMPOSE_CMD} -f docker-compose.prod.yml down"
    echo "   Restart:   ${COMPOSE_CMD} -f docker-compose.prod.yml restart"
    echo ""
    echo "🔧 If the application doesn't load immediately, wait 1-2 minutes"
    echo "   for data import to complete, then refresh your browser."
else
    echo ""
    echo "⚠️  Services may still be starting up. Please check the logs:"
    echo "   ${COMPOSE_CMD} -f docker-compose.prod.yml logs"
    echo ""
    echo "🔧 If you encounter issues:"
    echo "   1. Ensure ports 8501 and 27017 are available"
    echo "   2. Check Docker has enough resources allocated"
    echo "   3. Wait a few minutes for data import to complete"
fi

echo ""
echo "📚 Documentation and source code:"
echo "   https://github.com/Franz-kingstein/STAR---Satelllite_Transmission_Analysis_Reduction"
