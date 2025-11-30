"""
README - AWS Mind Quest FastAPI Backend

## Project Overview

This is a FastAPI backend for the AWS Mind Quest application - an AI-powered platform for AWS certification preparation.

### Key Features

- **Quiz Generation**: AI-powered quiz generation using OpenAI API
- **Quiz Evaluation**: Automatic scoring with detailed feedback
- **User Progress Tracking**: Track learning progress with XP, levels, and streaks
- **Adaptive Difficulty**: Dynamic difficulty adjustment based on performance
- **Weak Domain Identification**: AI identifies areas needing improvement
- **Achievements**: Gamification with badges and milestones
- **Authentication**: JWT-based authentication with role support

### Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0
- **LLM**: OpenAI API (GPT-4o-mini)
- **Auth**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Server**: Uvicorn
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key

### Setup with Docker

1. **Clone the repository**
   ```bash
   cd aws-mind-quest-backend
   ```

2. **Create .env file**
   ```bash
   cp .env.example .env
   ```

3. **Update .env with your OpenAI API key**
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/api/docs
   - Database: localhost:5432

### Local Development (Without Docker)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup PostgreSQL** (using local PostgreSQL or Docker just for DB)
   ```bash
   docker run -d \\
     --name aws-mind-quest-db \\
     -e POSTGRES_USER=admin \\
     -e POSTGRES_PASSWORD=password \\
     -e POSTGRES_DB=aws_mind_quest \\
     -p 5432:5432 \\
     postgres:16-alpine
   ```

4. **Create .env file**
   ```bash
   cp .env.example .env
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start development server**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

### Authentication

#### Register
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass123"
}
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

#### Get Current User
```bash
GET /api/auth/me
Authorization: Bearer {token}
```

### Certifications

#### List Certifications
```bash
GET /api/certifications
```

#### Get Single Certification
```bash
GET /api/certifications/{certification_id}
```

### Quizzes

#### Generate Quiz
Migrated from Supabase `generate-quiz` function
```bash
POST /api/quizzes/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "certification_id": "550e8400-e29b-41d4-a716-446655440000",
  "difficulty": "medium",
  "weak_domains": ["EC2", "VPC"]
}
```

Response includes 5 AI-generated questions with options and explanations.

#### Evaluate Quiz
Migrated from Supabase `evaluate-quiz` function
```bash
POST /api/quizzes/{quiz_id}/evaluate
Authorization: Bearer {token}
Content-Type: application/json

{
  "quiz_id": "550e8400-e29b-41d4-a716-446655440001",
  "answers": {
    "question-id-1": "Option A",
    "question-id-2": ["Option A", "Option C"]
  }
}
```

Returns score, XP, achievements, and weak domains.

#### Get Quiz History
```bash
GET /api/quizzes?certification_id={id}&limit=20&offset=0
Authorization: Bearer {token}
```

#### Get Quiz Details
```bash
GET /api/quizzes/{quiz_id}
Authorization: Bearer {token}
```

### Progress

#### Get Dashboard Stats
```bash
GET /api/progress/dashboard
Authorization: Bearer {token}
```

#### Get Certification Progress
```bash
GET /api/progress/certifications/{certification_id}
Authorization: Bearer {token}
```

#### Get All Progress
```bash
GET /api/progress/certifications
Authorization: Bearer {token}
```

#### Get Achievements
```bash
GET /api/progress/achievements
Authorization: Bearer {token}
```

### Profile

#### Get Profile
```bash
GET /api/profile
Authorization: Bearer {token}
```

#### Update Profile
```bash
PATCH /api/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "selected_certification_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Database Schema

### Core Tables

**Users**
- id (UUID, PK)
- email (unique)
- username (unique)
- hashed_password
- is_active
- created_at, updated_at

**Profiles**
- id (UUID, PK)
- user_id (FK)
- selected_certification_id (FK)
- xp, level, current_streak
- last_quiz_date
- created_at, updated_at

**Certifications**
- id (UUID, PK)
- name (unique)
- description
- created_at

**Quizzes**
- id (UUID, PK)
- user_id (FK)
- certification_id (FK)
- difficulty
- score, total_questions, xp_earned
- completed_at, created_at

**Questions**
- id (UUID, PK)
- quiz_id (FK)
- question_text, question_type
- options (JSON), correct_answer (JSON)
- user_answer (JSON), explanation
- is_correct, difficulty, domain
- xp_earned, created_at

**UserProgress**
- id (UUID, PK)
- user_id (FK), certification_id (FK)
- total_xp, total_quizzes, total_questions_answered
- correct_answers, accuracy
- current_difficulty
- domain_difficulties (JSON)
- weak_domains (JSON)
- updated_at

**Achievements**
- id (UUID, PK)
- user_id (FK)
- achievement_type, achievement_name
- achievement_description
- earned_at

## Architecture

### Service Layer

**LLMService** (`app/services/llm_service.py`)
- Integrates with OpenAI API
- Generates quiz questions
- Handles prompt engineering

**QuizGeneratorService** (`app/services/quiz_generator.py`)
- Migrated from Supabase `generate-quiz` function
- Orchestrates quiz creation
- Manages weak domain prioritization

**QuizEvaluatorService** (`app/services/quiz_evaluator.py`)
- Migrated from Supabase `evaluate-quiz` function
- Grades quiz submissions
- Calculates XP and updates progress
- Awards achievements
- Identifies weak domains
- Determines next difficulty

**AuthService** (`app/services/auth_service.py`)
- Handles user registration and login
- JWT token creation and verification
- Password hashing

### API Routers

- `auth.py`: Authentication endpoints
- `certification.py`: Certification management
- `quiz.py`: Quiz generation and evaluation
- `progress.py`: User progress and stats
- `profile.py`: User profile management

## Configuration

Environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_MODEL`: Model to use (default: gpt-4o-mini)
- `SECRET_KEY`: JWT secret key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry (default: 30)
- `ENV`: Environment (development/production)
- `DEBUG`: Debug mode
- `CORS_ORIGINS`: Allowed CORS origins

## Testing

Run tests with pytest:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

## Deployment

### Docker

1. **Build image**
   ```bash
   docker build -t aws-mind-quest-api:latest .
   ```

2. **Push to registry**
   ```bash
   docker tag aws-mind-quest-api:latest your-registry/aws-mind-quest-api:latest
   docker push your-registry/aws-mind-quest-api:latest
   ```

### AWS Lambda

1. **Install Mangum** (ASGI adapter for Lambda)
   ```bash
   pip install mangum
   ```

2. **Create Lambda handler** (already in `app/lambda_handler.py`)
   ```python
   from mangum import Mangum
   from app.main import app
   
   handler = Mangum(app)
   ```

3. **Package and deploy**
   ```bash
   pip install -r requirements.txt -t package/
   cd package && zip -r ../function.zip . && cd ..
   zip -r function.zip app/
   
   aws lambda create-function \\
     --function-name aws-mind-quest-api \\
     --runtime python3.11 \\
     --handler app.lambda_handler.handler \\
     --zip-file fileb://function.zip
   ```

## Troubleshooting

### Database Connection Issues
- Check PostgreSQL is running: `docker ps`
- Verify DATABASE_URL in .env
- Check firewall/network settings

### OpenAI API Errors
- Verify OPENAI_API_KEY is set correctly
- Check API key is active in OpenAI dashboard
- Monitor API usage limits

### Docker Issues
- Rebuild image: `docker-compose build --no-cache`
- Clear volumes: `docker-compose down -v`
- Check logs: `docker-compose logs -f fastapi`

## Performance Tips

- Use connection pooling (configured in SQLAlchemy)
- Implement caching for certifications
- Consider async LLM calls for high concurrency
- Monitor database query performance

## Security

- Always use HTTPS in production
- Rotate SECRET_KEY regularly
- Use strong passwords (enforced by validators)
- Enable rate limiting
- Implement request validation
- Use environment variables for secrets

## Future Enhancements

- [ ] Role-based access control (RBAC)
- [ ] Email verification
- [ ] OAuth2 integration
- [ ] Advanced analytics
- [ ] Quiz sharing and discussions
- [ ] Offline mode support
- [ ] Mobile app backend
- [ ] Advanced caching strategies

## Support

For issues, questions, or suggestions, please create an issue on GitHub.

## License

MIT License - See LICENSE file for details
"""

# This is a markdown file but we'll create it as a text file since some systems might not render it
