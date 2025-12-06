# AWS Mind Quest Backend

AI-powered AWS certification exam preparation platform with intelligent quiz generation, adaptive learning, and real-time progress tracking.

## 📋 Project Description

**AWS Mind Quest** is an intelligent learning platform that helps users prepare for AWS certification exams using AI-generated quizzes, personalized feedback, and adaptive difficulty levels. The platform tracks weak domains, awards achievements, and adjusts content based on user performance.

## ✨ Key Features

- 🤖 **AI Quiz Generation**: LLM-powered quiz creation from exam guides using RAG pipeline
- 📊 **Smart Evaluation**: Fast answer validation with domain-specific accuracy tracking
- 📈 **Progress Tracking**: XP system, leveling, streaks, and comprehensive statistics
- 🎯 **Adaptive Learning**: Dynamic difficulty adjustment based on weak domain performance
- 🔍 **Weak Domain Detection**: AI identifies knowledge gaps and prioritizes improvement areas
- 🏆 **Gamification**: Achievements, badges, and progress milestones
- 🔐 **Secure Auth**: JWT-based authentication with role support

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend Framework** | FastAPI 0.104.1 |
| **Database** | PostgreSQL 16 |
| **DB Viewer** | pgAdmin 4 |
| **Vector Database** | Qdrant (embeddings + semantic search) |
| **LLM** | OpenAI GPT-4o-mini (quiz generation) |
| **Vector Embeddings** | OpenAI Embeddings API |
| **RAG Pipeline** | LangChain 0.3.x (document retrieval for context) |
| **Observability** | Langfuse (tracing & monitoring) |
| **ORM** | SQLAlchemy 2.0 |
| **Auth** | JWT (python-jose) + bcrypt |
| **Containerization** | Docker & Docker Compose |
| **Server** | Uvicorn (ASGI)


## 🚀 Quick Start

### With Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/Oumayma-O/aws-mind-quest-backend.git
cd aws-mind-quest-backend

# Create .env file
cp .env.example .env

# Add your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Start all services (API, PostgreSQL, pgAdmin, Qdrant)
docker-compose up -d

# Services available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/api/docs
# - pgAdmin: http://localhost:5050
# - Qdrant: http://localhost:6333/dashboard
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up .env with database credentials
cp .env.example .env

# Start FastAPI server
uvicorn app.main:app --reload
```

## 📦 Services (Docker Compose)


| Service | Port | Purpose |
|---------|------|---------|
| **FastAPI** | 8000 | REST API + Swagger UI |
| **PostgreSQL** | 5432 | Primary data store |
| **pgAdmin** | 5050 | Database management UI |
| **Qdrant** | 6333 | Vector database for embeddings |

## 🧠 AI Pipeline Architecture

### Quiz Generation Flow
1. **Document Processing**: Exam guides → extracted text with layout awareness
2. **Embeddings**: Text chunks → OpenAI embeddings stored in Qdrant
3. **Retrieval**: Query relevant context using semantic search (RAG)
4. **LLM Generation**: Prompt + context → GPT-4o-mini generates 5 questions
5. **Storage**: Questions stored with metadata (domain, difficulty, type)

### Quiz Evaluation Flow
1. **User Submission**: User answers quiz questions
2. **Answer Validation**: Compare user answers to correct answers (string/list matching)
3. **Scoring**: Calculate XP, accuracy, weak domains by question type (single-select, multi-select, true/false)
4. **Progress Update**: Update user statistics, difficulty level, and achievements
5. **Weak Domain Detection**: Identify domains with <60% accuracy for adaptive learning

### Monitoring (Langfuse)
- **Generation Tracing**: Monitor quiz generation LLM calls, latency, and token usage
- **Performance Metrics**: Track generation time, model name, and prompt effectiveness
- **Context Quality**: Analyze retrieved chunks and their relevance to generated questions
- **Dashboard**: Real-time insights into quiz generation pipeline performance

## 📚 Core API Endpoints

```bash
# Authentication
POST   /api/auth/register              # Create account
POST   /api/auth/login                 # Get JWT token
GET    /api/auth/me                    # Current user

# Quizzes (AI-Generated)
POST   /api/quizzes/generate           # Generate 5 questions with RAG context
POST   /api/quizzes/{id}/evaluate      # Evaluate answers & calculate score
GET    /api/quizzes                    # Quiz history

# Progress
GET    /api/progress/dashboard         # Aggregated stats + weak domains
GET    /api/progress/certifications    # Per-certification progress
GET    /api/progress/achievements      # Earned badges

# Profile
GET    /api/profile                    # User info + selected certification
PATCH  /api/profile                    # Update profile

# Certifications
GET    /api/certifications             # Available AWS certs
```



## 📊 Database Schema

**Users** → Profiles → Certifications → Quizzes → Questions  
**UserProgress** (per certification) tracks XP, accuracy, weak domains  
**Achievements** for gamification (badges, milestones)

Key tables:
- `users` - Authentication & identity
- `profiles` - User stats (XP, level, streak)
- `certifications` - AWS exam metadata
- `quizzes` - Quiz attempts with generation metadata
- `questions` - Quiz questions with correct/user answers
- `user_progress` - Per-certification statistics & weak domains
- `achievements` - Earned badges & milestones

## 🔧 Configuration

```env
# Core
DATABASE_URL=postgresql://user:password@localhost:5432/aws_mind_quest
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Qdrant Vector DB
QDRANT_URL=http://qdrant:6333

# Langfuse Monitoring
LANGFUSE_PUBLIC_KEY=your-key
LANGFUSE_SECRET_KEY=your-secret

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENV=development
DEBUG=true
```



## 🚢 Deployment

### Docker Production Build
```bash
# Build production image
docker build -t aws-mind-quest-api:prod .

# Run with compose
docker-compose -f docker-compose.yml up -d
```

### AWS Lambda (Serverless)
```bash
# Already configured in app/lambda_handler.py (Mangum ASGI adapter)
# Package and deploy to AWS Lambda
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app tests/

# Specific test file
pytest tests/test_quiz_generator.py -v
```



## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Database Connection Failed** | Check PostgreSQL running: `docker ps`, verify DATABASE_URL in .env |
| **OpenAI API Error** | Verify OPENAI_API_KEY, check quota limits in OpenAI dashboard |
| **Qdrant Not Found** | Ensure Qdrant service started: `docker-compose ps qdrant` |
| **Port Already in Use** | Change port in docker-compose.yml or kill process: `lsof -ti :8000` |
| **Langfuse Connection** | Verify LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set |

## 📈 Performance & Scaling

- Connection pooling configured in SQLAlchemy
- Vector DB (Qdrant) for fast semantic search
- Async LLM calls for high concurrency
- Database query optimization with indexes
- Caching layer for certifications

## 🔐 Security

- JWT authentication with token rotation
- bcrypt password hashing
- CORS configured per environment
- Input validation via Pydantic
- Rate limiting ready (implement via middleware)
- Secrets stored in environment variables
