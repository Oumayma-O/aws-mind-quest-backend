# FastAPI Backend Setup and Usage Guide

## Directory Structure

```
aws-mind-quest-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py              # Configuration management
│   ├── lambda_handler.py      # AWS Lambda wrapper
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py              # Database connection
│   │   └── models.py          # SQLAlchemy models
│   ├── schemas/               # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── certification.py
│   │   ├── quiz.py
│   │   └── progress.py
│   ├── services/              # Business logic
│   │   ├── llm_service.py     # OpenAI integration
│   │   ├── quiz_generator.py  # Quiz generation (migrated from Supabase)
│   │   ├── quiz_evaluator.py  # Quiz evaluation (migrated from Supabase)
│   │   └── auth_service.py    # Authentication
│   ├── routers/               # API endpoints
│   │   ├── auth.py
│   │   ├── certification.py
│   │   ├── quiz.py
│   │   ├── progress.py
│   │   └── profile.py
│   └── utils/
│       ├── validators.py      # Input validation
│       └── errors.py          # Custom exceptions
├── tests/                     # Test files
├── Dockerfile                 # Container image
├── docker-compose.yml         # Docker Compose config
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

## Setup Instructions

### 1. Initial Setup

```bash
# Navigate to backend directory
cd aws-mind-quest-backend

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-api-key-here
```

### 2. Using Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL + FastAPI)
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f fastapi

# Stop services
docker-compose down

# Stop and remove volumes (clean reset)
docker-compose down -v
```

### 3. Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL separately (using Docker)
docker run -d \
  --name aws-mind-quest-db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=aws_mind_quest \
  -p 5432:5432 \
  postgres:16-alpine

# Create .env file
cp .env.example .env

# Run development server
uvicorn app.main:app --reload

# API will be available at http://localhost:8000
```

## API Endpoints

### Base URL: `http://localhost:8000/api`

### Documentation
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### 1. Authentication (`/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login user |
| GET | `/auth/me` | Get current user |

**Example: Register**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "john_doe",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "john_doe",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

### 2. Certifications (`/certifications`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/certifications` | List all certifications |
| GET | `/certifications/{id}` | Get specific certification |

**Example: List Certifications**
```bash
curl http://localhost:8000/api/certifications
```

### 3. Quizzes (`/quizzes`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/quizzes/generate` | Generate new quiz |
| POST | `/quizzes/{id}/evaluate` | Evaluate quiz answers |
| GET | `/quizzes` | Get quiz history |
| GET | `/quizzes/{id}` | Get quiz details |

**Example: Generate Quiz**
```bash
curl -X POST http://localhost:8000/api/quizzes/generate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "certification_id": "550e8400-e29b-41d4-a716-446655440001",
    "difficulty": "medium",
    "weak_domains": []
  }'
```

**Example: Evaluate Quiz**
```bash
curl -X POST http://localhost:8000/api/quizzes/550e8400-e29b-41d4-a716-446655440002/evaluate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "question-id-1": "Option A",
      "question-id-2": ["Option A", "Option C"],
      "question-id-3": "True"
    }
  }'
```

### 4. Progress (`/progress`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/progress/dashboard` | Dashboard statistics |
| GET | `/progress/certifications` | All certifications progress |
| GET | `/progress/certifications/{id}` | Specific certification progress |
| GET | `/progress/achievements` | User achievements |

### 5. Profile (`/profile`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile` | Get user profile |
| PATCH | `/profile` | Update user profile |

## Key Features Implementation

### 1. Quiz Generation (Migrated from Supabase)

**From:** `supabase/functions/generate-quiz/index.ts`
**To:** `app/services/quiz_generator.py` + `app/routers/quiz.py`

Features:
- AI-powered question generation using OpenAI
- Focuses on weak domains for targeted learning
- Generates mix of question types: multiple choice, multi-select, true/false
- Includes detailed explanations for each answer

**Code Flow:**
```
POST /api/quizzes/generate
  → quiz.py (route handler)
  → QuizGeneratorService.generate_quiz()
  → LLMService.generate_quiz() (OpenAI API call)
  → Database: Create Quiz + Questions
  → Return QuizGenerateResponse
```

### 2. Quiz Evaluation (Migrated from Supabase)

**From:** `supabase/functions/evaluate-quiz/index.ts`
**To:** `app/services/quiz_evaluator.py` + `app/routers/quiz.py`

Features:
- Automatic scoring with multi-question type support
- XP calculation based on difficulty
- User profile updates (XP, level, streak)
- Weak domain identification
- Achievement unlocking
- Adaptive difficulty recommendation

**Code Flow:**
```
POST /api/quizzes/{id}/evaluate
  → quiz.py (route handler)
  → QuizEvaluatorService.evaluate_quiz()
  → Grade all questions
  → Update user profile, progress, achievements
  → Identify weak domains
  → Return QuizEvaluateResponse
```

### 3. Authentication

- JWT-based token authentication
- Password hashing with bcrypt
- Token expiration (default 30 minutes)
- Dependency injection for protected routes

## Database Seeding

To seed initial certifications:

```python
# In Python shell or script
from app.database.db import SessionLocal
from app.database.models import Certification

db = SessionLocal()

certifications = [
    Certification(
        name="AWS Cloud Practitioner",
        description="Foundational understanding of AWS Cloud"
    ),
    Certification(
        name="AWS Solutions Architect Associate",
        description="Design and deploy scalable systems on AWS"
    ),
    Certification(
        name="AWS Developer Associate",
        description="Develop and maintain applications on AWS"
    ),
    Certification(
        name="AWS DevOps Engineer",
        description="Implement and manage continuous delivery systems on AWS"
    ),
]

db.add_all(certifications)
db.commit()
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

## Common Issues & Solutions

### PostgreSQL Connection Error
```
Error: could not connect to server
```

**Solution:**
```bash
# Check if postgres container is running
docker ps | grep postgres

# If not, start it
docker run -d \
  --name aws-mind-quest-db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=aws_mind_quest \
  -p 5432:5432 \
  postgres:16-alpine
```

### OpenAI API Error
```
Error: Invalid API key
```

**Solution:**
- Verify your OpenAI API key in `.env`
- Check API key is active: https://platform.openai.com/api-keys
- Ensure you have available API credits

### Port Already in Use
```
Error: Address already in use
```

**Solution:**
```bash
# Find and kill process using port 8000
# On Linux/Mac:
lsof -i :8000
kill -9 <PID>

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Deployment

### To AWS Lambda

1. Install Mangum:
```bash
pip install mangum
```

2. Package function:
```bash
pip install -r requirements.txt -t package/
cd package && zip -r ../function.zip . && cd ..
zip -r function.zip app/
```

3. Deploy to Lambda:
```bash
aws lambda create-function \
  --function-name aws-mind-quest-api \
  --runtime python3.11 \
  --handler app.lambda_handler.handler \
  --zip-file fileb://function.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables={OPENAI_API_KEY=sk-xxx,DATABASE_URL=postgresql://xxx}
```

### To Docker Hub

```bash
# Build and tag
docker build -t yourusername/aws-mind-quest-api:latest .

# Push to registry
docker push yourusername/aws-mind-quest-api:latest
```

## Next Steps

1. ✅ Run locally with Docker
2. ✅ Test API endpoints
3. ⬜ Setup Angular frontend
4. ⬜ Deploy to AWS (Lambda + RDS)
5. ⬜ Setup CI/CD pipeline
6. ⬜ Add monitoring and logging

## Useful Commands

```bash
# View all running containers
docker ps

# View logs
docker-compose logs -f fastapi
docker-compose logs -f postgres

# Execute command in container
docker exec aws-mind-quest-api python script.py

# Access database shell
docker exec -it aws-mind-quest-db psql -U admin -d aws_mind_quest

# Rebuild containers
docker-compose build --no-cache

# Remove all volumes (clean slate)
docker-compose down -v
```

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Docker Documentation](https://docs.docker.com/)
