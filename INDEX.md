# 📚 AWS Mind Quest Backend - Documentation Index

## 🚀 Start Here

**New to this project?** Follow this order:

1. **[GETTING_STARTED.md](./GETTING_STARTED.md)** ← START HERE
   - Quick 5-minute setup
   - First test walkthrough
   - Troubleshooting common issues

2. **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)**
   - What's been built
   - Key features
   - Technology stack

3. **[ARCHITECTURE.md](./ARCHITECTURE.md)**
   - System architecture diagrams
   - Data flow explanation
   - Database schema

4. **[SETUP_GUIDE.md](./SETUP_GUIDE.md)**
   - Detailed setup instructions
   - All API endpoints documented
   - Local development options

5. **[README.md](./README.md)**
   - Project overview
   - Full documentation
   - Deployment options

---

## 📂 File Structure

```
aws-mind-quest-backend/
│
├── 📖 Documentation
│   ├── GETTING_STARTED.md       ⭐ START HERE
│   ├── PROJECT_SUMMARY.md       What's built
│   ├── ARCHITECTURE.md          System design
│   ├── SETUP_GUIDE.md           Detailed setup
│   ├── README.md                Full documentation
│   └── INDEX.md                 This file
│
├── 🚀 Quick Start
│   ├── quickstart.sh             Mac/Linux
│   ├── quickstart.cmd            Windows
│   └── docker-compose.yml        Full stack
│
├── 🐍 Python Code
│   └── app/
│       ├── main.py              FastAPI app
│       ├── config.py            Configuration
│       ├── lambda_handler.py    AWS Lambda
│       ├── database/
│       │   ├── db.py            DB connection
│       │   └── models.py        SQLAlchemy ORM
│       ├── schemas/             Pydantic models
│       │   ├── user.py
│       │   ├── certification.py
│       │   ├── quiz.py
│       │   └── progress.py
│       ├── services/            Business logic
│       │   ├── auth_service.py
│       │   ├── llm_service.py
│       │   ├── quiz_generator.py ⭐ MIGRATED
│       │   └── quiz_evaluator.py ⭐ MIGRATED
│       ├── routers/             API endpoints
│       │   ├── auth.py
│       │   ├── certification.py
│       │   ├── quiz.py          ⭐ MIGRATED
│       │   ├── progress.py
│       │   └── profile.py
│       └── utils/
│           ├── validators.py
│           └── errors.py
│
├── 🐳 Docker
│   ├── Dockerfile               Container image
│   └── docker-compose.yml       Services config
│
├── ⚙️ Configuration
│   ├── requirements.txt          Python packages
│   ├── .env.example             Environment template
│   └── .gitignore               Git ignore rules
```

---

## 🎯 Quick Navigation by Task

### I want to...

**▶ Get started immediately (5 min)**
→ [GETTING_STARTED.md](./GETTING_STARTED.md) → Run `quickstart.cmd` or `quickstart.sh`

**▶ Understand the architecture**
→ [ARCHITECTURE.md](./ARCHITECTURE.md) → See system design, data flow, schema

**▶ Setup locally without Docker**
→ [SETUP_GUIDE.md](./SETUP_GUIDE.md) → "Local Development" section

**▶ Test all API endpoints**
→ [SETUP_GUIDE.md](./SETUP_GUIDE.md) → "API Documentation" section

**▶ Deploy to AWS Lambda**
→ [README.md](./README.md) → "Deployment" section

**▶ Deploy to production**
→ [README.md](./README.md) → "Deployment" section → AWS or Docker Hub

**▶ Troubleshoot an error**
→ [GETTING_STARTED.md](./GETTING_STARTED.md) → "Troubleshooting Guide" section

**▶ Understand database schema**
→ [ARCHITECTURE.md](./ARCHITECTURE.md) → "Database Schema" section

**▶ Learn how quiz generation works**
→ [ARCHITECTURE.md](./ARCHITECTURE.md) → "Data Flow" section → Quiz Generation

**▶ Learn how quiz evaluation works**
→ [ARCHITECTURE.md](./ARCHITECTURE.md) → "Data Flow" section → Quiz Evaluation

---

## 🔑 Key Concepts

### Migration from Supabase ✅

| Component | Supabase | FastAPI | File |
|-----------|----------|---------|------|
| Quiz Generation | `supabase/functions/generate-quiz/index.ts` | `app/services/quiz_generator.py` + `app/routers/quiz.py` | Line ~80 |
| Quiz Evaluation | `supabase/functions/evaluate-quiz/index.ts` | `app/services/quiz_evaluator.py` + `app/routers/quiz.py` | Line ~150 |
| Database | PostgreSQL (Supabase managed) | PostgreSQL (Docker) + SQLAlchemy | `app/database/models.py` |
| Authentication | Supabase Auth | JWT + bcrypt | `app/services/auth_service.py` |
| API | REST (Supabase) | REST (FastAPI) | `app/routers/*` |

### Technology Stack

```
Frontend (Soon): Angular
    ↓ HTTPS
API Gateway: FastAPI (Python)
    ├── Routers (HTTP handling)
    ├── Services (business logic)
    ├── Database (SQLAlchemy ORM)
    └── External APIs (OpenAI)
    ↓
Database: PostgreSQL 16
```

---

## 📊 API Endpoints Summary

### Authentication (`/api/auth`)
```
POST   /register      Register new user
POST   /login         Login user
GET    /me            Get current user
```

### Certifications (`/api/certifications`)
```
GET    /              List certifications
GET    /{id}          Get specific certification
POST   /              Create certification (admin)
```

### Quizzes (`/api/quizzes`) ⭐ MIGRATED
```
POST   /generate      Generate quiz (LLM powered)
POST   /{id}/evaluate Evaluate and score quiz
GET    /              Quiz history
GET    /{id}          Quiz details with answers
```

### Progress (`/api/progress`)
```
GET    /dashboard               User stats
GET    /certifications          All progress
GET    /certifications/{id}     Specific certification
GET    /achievements            User badges
```

### Profile (`/api/profile`)
```
GET    /              Get profile
PATCH  /              Update profile
```

---

## 🔧 Common Commands

### Docker Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild images
docker-compose build --no-cache

# Clean everything
docker-compose down -v
```

### Database Access
```bash
# Connect to database
docker exec -it aws-mind-quest-db psql -U admin -d aws_mind_quest

# Useful queries
\dt                    # List tables
SELECT * FROM users;   # View users
\q                     # Exit
```

### API Testing
```bash
# Using curl
curl http://localhost:8000/api/docs

# Using Python requests
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"

# Using httpie (if installed)
http GET http://localhost:8000/api/docs
```

---

## 🌍 External Links

### Documentation
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Docker](https://docs.docker.com/)

### Services
- [OpenAI Dashboard](https://platform.openai.com/account)
- [AWS Console](https://console.aws.amazon.com/)
- [PostgreSQL Online Docs](https://www.postgresql.org/docs/)

---

## 📋 Checklist for First Time Setup

- [ ] Read [GETTING_STARTED.md](./GETTING_STARTED.md)
- [ ] Install Docker Desktop
- [ ] Get OpenAI API key
- [ ] Clone repository
- [ ] Create `.env` file from `.env.example`
- [ ] Add OpenAI API key to `.env`
- [ ] Run `quickstart.sh` or `quickstart.cmd`
- [ ] Visit http://localhost:8000/api/docs
- [ ] Register test user
- [ ] Generate quiz
- [ ] Evaluate quiz
- [ ] Check dashboard
- [ ] Read [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ ] Explore code structure

---

## 🆘 Getting Help

### If you encounter an error:
1. Check [GETTING_STARTED.md](./GETTING_STARTED.md) → Troubleshooting
2. Check `docker-compose logs -f` for details
3. Google the error message
4. Check OpenAI API status
5. Verify `.env` configuration

### If you need to understand something:
1. Check relevant documentation file above
2. Look at code examples in `app/routers/*.py`
3. Check inline comments in code
4. Review test files (if available)

---

## 🎓 Learning Path

**Beginner** → Start here
1. [GETTING_STARTED.md](./GETTING_STARTED.md) - Quick start
2. [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - What's built
3. Test API endpoints in Swagger UI

**Intermediate** → Understand the system
1. [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
2. [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Detailed setup
3. Review `app/routers/*.py` files
4. Review `app/services/*.py` files

**Advanced** → Customize and extend
1. [README.md](./README.md) - Full documentation
2. Review database schema in `app/database/models.py`
3. Modify business logic in services
4. Add custom validations
5. Deploy to AWS/production

---

## ✅ Status

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI Backend | ✅ Complete | Production ready |
| Database Models | ✅ Complete | 7 tables with relationships |
| API Endpoints | ✅ Complete | 20+ endpoints |
| Quiz Generation | ✅ Complete | Migrated from Supabase |
| Quiz Evaluation | ✅ Complete | Migrated from Supabase |
| Authentication | ✅ Complete | JWT + bcrypt |
| Docker Setup | ✅ Complete | Full stack ready |
| Documentation | ✅ Complete | 5 comprehensive guides |
| Angular Frontend | ⏳ Next Step | Will create next |
| AWS Deployment | 📋 Ready | Can deploy anytime |

---

## 🎉 You're All Set!

Everything is ready to go. Start with:

### Quick Start (5 minutes)
1. Run `quickstart.cmd` (Windows) or `quickstart.sh` (Mac/Linux)
2. Visit http://localhost:8000/api/docs
3. Test register, generate quiz, evaluate quiz

### Full Documentation
Then read [GETTING_STARTED.md](./GETTING_STARTED.md) for more details.

---

**Questions?** Check the appropriate documentation file above.
**Ready to code?** Start with [GETTING_STARTED.md](./GETTING_STARTED.md).

**Happy coding! 🚀**

---

**Last Updated:** November 29, 2025
**Status:** ✅ Production Ready
