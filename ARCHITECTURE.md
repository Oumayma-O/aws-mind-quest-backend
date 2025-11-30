# 🏗️ AWS Mind Quest Backend - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (Angular)                          │
│                    (Will be created next)                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                   HTTPS (Port 80/443)
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                             │
        │         API Gateway (AWS)                   │
        │     (or Direct to FastAPI)                  │
        │                                             │
        └──────────────────────┬──────────────────────┘
                               │
                    HTTP (Port 8000)
                               │
        ┌──────────────────────▼──────────────────────┐
        │                                             │
        │         FastAPI Backend                     │
        │      (Migrated from Supabase)              │
        │                                             │
        │    ┌─────────────────────────────────┐     │
        │    │     Router Layer                │     │
        │    ├─────────────────────────────────┤     │
        │    │ • auth.py      (JWT auth)       │     │
        │    │ • certification.py              │     │
        │    │ • quiz.py      (MIGRATED ✓)    │     │
        │    │ • progress.py                   │     │
        │    │ • profile.py                    │     │
        │    └─────────────────────────────────┘     │
        │               │                            │
        │    ┌──────────▼──────────────────────┐     │
        │    │     Service Layer               │     │
        │    ├────────────────────────────────-┤     │
        │    │ • AuthService                   │     │
        │    │ • LLMService (OpenAI)           │     │
        │    │ • QuizGeneratorService (MIG)    │     │
        │    │ • QuizEvaluatorService (MIG)    │     │
        │    └──────────────────────────────────┘    │
        │               │                            │
        │    ┌──────────▼──────────────────────┐     │
        │    │   Database Layer                │     │
        │    │    (SQLAlchemy ORM)             │     │
        │    ├────────────────────────────────-┤     │
        │    │ • Models (7 tables)             │     │
        │    │ • Sessions                      │     │
        │    │ • Queries                       │     │
        │    └──────────────────────────────────┘    │
        │                                             │
        └─────────────────────┬──────────────────────┘
                              │
              PostgreSQL (Port 5432)
                              │
        ┌─────────────────────▼──────────────────────┐
        │                                             │
        │         PostgreSQL Database                │
        │                                             │
        │    ┌─────────────────────────────────┐     │
        │    │     Core Tables                 │     │
        │    ├─────────────────────────────────┤     │
        │    │ users                           │     │
        │    │ profiles                        │     │
        │    │ certifications                  │     │
        │    │ quizzes                         │     │
        │    │ questions                       │     │
        │    │ user_progress                   │     │
        │    │ achievements                    │     │
        │    └─────────────────────────────────┘     │
        │                                             │
        └─────────────────────────────────────────────┘


        ┌──────────────────────────────────┐
        │    External Services             │
        └──────────────────────────────────┘
                    │         │
        ┌───────────▼┐       │
        │  OpenAI    │       │
        │  API       │       │
        │(Quiz Gen)  │       │
        └────────────┘       │
                             │
                    (Future: AWS Services)
                    • Bedrock (LLM)
                    • S3 (Resources)
                    • Lambda (Compute)
                    • RDS (Database)
```

---

## Data Flow

### 1. Quiz Generation Flow
```
Client Request (Generate Quiz)
    │
    ├─→ FastAPI Route Handler
    │   │
    │   ├─→ Authentication (JWT)
    │   │
    │   ├─→ QuizGeneratorService.generate_quiz()
    │   │   │
    │   │   ├─→ Fetch Certification from DB
    │   │   │
    │   │   ├─→ Get Weak Domains (if any)
    │   │   │
    │   │   ├─→ LLMService.generate_quiz()
    │   │   │   │
    │   │   │   └─→ OpenAI API Call
    │   │   │       (GPT-4o-mini)
    │   │   │
    │   │   ├─→ Parse LLM Response
    │   │   │
    │   │   ├─→ Create Quiz in DB
    │   │   │
    │   │   └─→ Create Questions in DB
    │   │
    │   └─→ Return QuizGenerateResponse
    │
    └─→ Client (JSON)


Supabase Function: generate-quiz/index.ts → FastAPI: quiz.py + services
```

### 2. Quiz Evaluation Flow
```
Client Request (Evaluate Quiz)
    │
    ├─→ FastAPI Route Handler
    │   │
    │   ├─→ Authentication (JWT)
    │   │
    │   ├─→ QuizEvaluatorService.evaluate_quiz()
    │   │   │
    │   │   ├─→ Fetch Quiz + Questions from DB
    │   │   │
    │   │   ├─→ For each Question:
    │   │   │   ├─→ Get User Answer
    │   │   │   ├─→ Compare with Correct Answer
    │   │   │   ├─→ Calculate XP (if correct)
    │   │   │   ├─→ Track Domain Performance
    │   │   │   └─→ Update Question in DB
    │   │   │
    │   │   ├─→ Calculate Overall Score
    │   │   │
    │   │   ├─→ Update User Profile
    │   │   │   ├─→ Add XP
    │   │   │   ├─→ Update Level
    │   │   │   └─→ Update Streak
    │   │   │
    │   │   ├─→ Identify Weak Domains (< 60%)
    │   │   │
    │   │   ├─→ Update User Progress
    │   │   │
    │   │   ├─→ Check Achievements
    │   │   │   ├─→ 7-Day Streak?
    │   │   │   ├─→ 90%+ Accuracy?
    │   │   │   └─→ 100 Questions?
    │   │   │
    │   │   ├─→ Determine Next Difficulty
    │   │   │   ├─→ If ≥80%: Increase
    │   │   │   ├─→ If <50%: Decrease
    │   │   │   └─→ Otherwise: Keep Same
    │   │   │
    │   │   └─→ Return QuizEvaluateResponse
    │   │
    │   └─→ Return to Client (JSON)
    │
    └─→ Client (Score, XP, Achievements, Weak Domains)


Supabase Function: evaluate-quiz/index.ts → FastAPI: quiz.py + services
```

---

## Database Schema (Entity Relationship)

```
                    ┌──────────────────┐
                    │      Users       │
                    ├──────────────────┤
                    │ id (PK, UUID)    │
                    │ email (UNIQUE)   │
                    │ username (UNQ)   │
                    │ password_hash    │
                    │ is_active        │
                    │ created_at       │
                    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
          ┌─────────▼─────────┐   ┌───▼─────────────┐
          │    Profiles       │   │ Achievements    │
          ├──────────────────┤   ├─────────────────┤
          │ id (PK)          │   │ id (PK)         │
          │ user_id (FK)     │   │ user_id (FK)    │
          │ xp, level        │   │ achievement_... │
          │ current_streak   │   │ earned_at       │
          │ last_quiz_date   │   └─────────────────┘
          └─────────┬────────┘
                    │
         ┌──────────▼──────────┐
         │ selected_cert_id    │
         │      (FK)           │
         └──────────┬──────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    │   ┌───────────▼─────────────┐ │
    │   │  Certifications         │ │
    │   ├────────────────────────┤ │ (Shared Reference)
    │   │ id (PK)                │ │
    │   │ name (UNIQUE)          │ │
    │   │ description            │ │
    │   └───────────┬────────────┘ │
    │               │              │
    │   ┌───────────┴──────────┬───▼──────┐
    │   │                      │          │
    │   ▼                      │          │
    │┌──────────────┐          │          │
    ││   Quizzes    │          │          │
    │├──────────────┤          │          │
    ││ id (PK)      │          │          │
    ││ user_id (FK) │          │          │
    ││ cert_id (FK) │          │          │
    ││ difficulty   │          │          │
    ││ score        │          │          │
    ││ xp_earned    │          │          │
    │└──────┬───────┘          │          │
    │       │                  │          │
    │   ┌───▼────────────┐     │          │
    │   │   Questions    │     │          │
    │   ├────────────────┤     │          │
    │   │ id (PK)        │     │          │
    │   │ quiz_id (FK)   │     │          │
    │   │ question_text  │     │          │
    │   │ options (JSON) │     │          │
    │   │ correct_answer │     │          │
    │   │ user_answer    │     │          │
    │   │ is_correct     │     │          │
    │   │ difficulty     │     │          │
    │   │ domain         │     │          │
    │   │ xp_earned      │     │          │
    │   └────────────────┘     │          │
    │                          │          │
    └──────────────────────┬───┴──────────┘
                           │
            ┌──────────────▼────────────────┐
            │   UserProgress               │
            ├──────────────────────────────┤
            │ id (PK)                      │
            │ user_id (FK)                 │
            │ certification_id (FK)        │
            │ total_xp, total_quizzes      │
            │ correct_answers, accuracy    │
            │ current_difficulty           │
            │ domain_difficulties (JSON)   │
            │ weak_domains (JSON)          │
            │ UNIQUE(user_id, cert_id)    │
            └──────────────────────────────┘
```

---

## API Endpoint Map

```
/api/
│
├── /health                    → Health check
├── /                          → Root endpoint
│
├── /auth
│   ├── POST /register         → Create user
│   ├── POST /login            → Get JWT token
│   └── GET /me                → Current user
│
├── /certifications
│   ├── GET /                  → List all
│   ├── GET /{id}              → Get specific
│   └── POST /                 → Create (admin)
│
├── /quizzes  ⭐ MIGRATED
│   ├── POST /generate         → Generate quiz (LLM)
│   ├── POST /{id}/evaluate    → Grade quiz
│   ├── GET /                  → Quiz history
│   └── GET /{id}              → Quiz details
│
├── /progress
│   ├── GET /dashboard         → User stats
│   ├── GET /certifications    → All progress
│   ├── GET /certifications/{id} → Cert progress
│   └── GET /achievements      → Badges
│
└── /profile
    ├── GET /                  → Get profile
    └── PATCH /                → Update profile
```

---

## Key Improvements from Supabase

### Before (Supabase)
```typescript
// supabase/functions/generate-quiz/index.ts
serve(async (req) => {
  const { userId, certificationId, difficulty, weakDomains } = await req.json();
  // Everything in one function
  // Hard to test
  // Hard to reuse logic
  // Hard to scale
})
```

### After (FastAPI)
```
✅ Separated concerns:
   ├── Router (HTTP handling)
   ├── Service (business logic)
   ├── Database (data access)
   └── LLM (external API)

✅ Reusable services
✅ Easy to test
✅ Easy to scale
✅ Better error handling
✅ Better logging
✅ Type safety with Pydantic
✅ Automatic API documentation
```

---

## Deployment Architecture Options

### Option 1: Docker Compose (Current - Local/VPS)
```
Your Machine/VPS
├── Docker
│   ├── FastAPI Container
│   │   ├── Port 8000
│   │   └── Uvicorn Server
│   │
│   └── PostgreSQL Container
│       ├── Port 5432
│       └── Database
```

### Option 2: AWS Deployment
```
AWS Cloud
├── API Gateway
│   └── REST API
│
├── Lambda Function
│   └── FastAPI App (via Mangum)
│       ├── Timeout: 60s
│       └── Memory: 512MB
│
├── RDS
│   └── PostgreSQL (db.t3.micro)
│       └── Free tier eligible
│
└── (Optional) S3
    └── Training resources
```

### Option 3: Hybrid (Recommended for Free Tier)
```
AWS Free Tier ($0/month)
├── Lambda (1M requests/month)
├── API Gateway (free tier)
└── RDS (db.t3.micro, 20GB)

Local Machine (Development)
├── Docker Compose
├── PostgreSQL
└── FastAPI
```

---

## Performance Considerations

```
Request Flow Timing:
├── API Request → 1ms
├── Auth Validation → 5ms
├── Database Query → 10-50ms
├── LLM API Call (Generate) → 2-5 seconds ⚠️
├── Database Writes → 10-20ms
├── Response Serialization → 1ms
└── Total Response Time: 2.5-5+ seconds

Optimization Options:
1. Cache certifications (5 minutes)
2. Async LLM calls for long operations
3. Connection pooling (already configured)
4. Database query optimization
5. Lambda function warming (AWS)
```

---

## Security Features

```
✅ Authentication
   ├── JWT tokens
   ├── Token expiration (30 min default)
   └── Bearer token scheme

✅ Password Security
   ├── Bcrypt hashing
   ├── Validation rules (8+ chars, mixed case, digits)
   └── Never stored in logs

✅ Database Security
   ├── SQLAlchemy ORM (SQL injection prevention)
   ├── Parameterized queries
   └── Foreign key constraints

✅ API Security
   ├── CORS configuration
   ├── Input validation (Pydantic)
   ├── Error handling (no stack traces)
   └── Rate limiting ready

✅ Infrastructure
   ├── Docker non-root user
   ├── Environment variables for secrets
   ├── Health checks
   └── Logging for audit trail
```

---

## Summary

| Aspect | Details |
|--------|---------|
| **Framework** | FastAPI (modern, fast, easy) |
| **Database** | PostgreSQL (proven, reliable) |
| **Authentication** | JWT + bcrypt (standard) |
| **LLM** | OpenAI GPT-4o-mini (cost-effective) |
| **Containerization** | Docker + Docker Compose |
| **AWS Ready** | Lambda + RDS deployment path |
| **Status** | ✅ Production Ready |
| **Test URL** | http://localhost:8000/api/docs |

---

**Ready to deploy?** See `SETUP_GUIDE.md` for step-by-step instructions!
