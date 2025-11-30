#!/bin/bash
# Quick start script for AWS Mind Quest Backend

set -e

echo "🚀 AWS Mind Quest Backend - Quick Start"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OpenAI API key!"
    echo ""
    read -p "Press Enter to continue after editing .env..."
fi

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check if services are running
echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""

# Display useful information
echo "📚 Useful Information:"
echo "===================="
echo ""
echo "API Documentation:"
echo "  Swagger UI: http://localhost:8000/api/docs"
echo "  ReDoc: http://localhost:8000/api/redoc"
echo ""
echo "API Base URL: http://localhost:8000/api"
echo ""
echo "Database:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: aws_mind_quest"
echo "  User: admin"
echo "  Password: password"
echo ""
echo "Useful Commands:"
echo "  docker-compose logs -f fastapi    # View API logs"
echo "  docker-compose logs -f postgres   # View database logs"
echo "  docker-compose down               # Stop all services"
echo "  docker-compose down -v            # Stop and remove volumes"
echo ""
echo "🎉 Backend is ready! Visit http://localhost:8000/api/docs to test the API"
