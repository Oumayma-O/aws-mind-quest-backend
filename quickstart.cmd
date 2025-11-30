@echo off
REM Quick start script for AWS Mind Quest Backend (Windows)

echo 🚀 AWS Mind Quest Backend - Quick Start
echo ========================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is installed
where docker-compose >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your OpenAI API key!
    echo.
    pause
)

REM Build images
echo 🔨 Building Docker images...
docker-compose build

REM Start services
echo 🚀 Starting services...
docker-compose up -d

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak

REM Check if services are running
echo.
echo ✅ Services started successfully!
echo.
echo 📊 Service Status:
docker-compose ps
echo.

REM Display useful information
echo 📚 Useful Information:
echo ====================
echo.
echo API Documentation:
echo   Swagger UI: http://localhost:8000/api/docs
echo   ReDoc: http://localhost:8000/api/redoc
echo.
echo API Base URL: http://localhost:8000/api
echo.
echo Database:
echo   Host: localhost
echo   Port: 5432
echo   Database: aws_mind_quest
echo   User: admin
echo   Password: password
echo.
echo Useful Commands:
echo   docker-compose logs -f fastapi    # View API logs
echo   docker-compose logs -f postgres   # View database logs
echo   docker-compose down               # Stop all services
echo   docker-compose down -v            # Stop and remove volumes
echo.
echo 🎉 Backend is ready! Visit http://localhost:8000/api/docs to test the API
pause
