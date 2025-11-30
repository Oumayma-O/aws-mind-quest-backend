# ✅ FastAPI Backend - Getting Started Checklist

## 🎯 Pre-Deployment Checklist

### Prerequisites
- [ ] Docker installed (`docker --version`)
- [ ] Docker Compose installed (`docker-compose --version`)
- [ ] OpenAI API key ready (from https://platform.openai.com/api-keys)
- [ ] Git installed (for version control)

### Quick Start (5 minutes)
1. [ ] Navigate to `aws-mind-quest-backend` directory
2. [ ] Copy `.env.example` to `.env`
3. [ ] Add your OpenAI API key to `.env`
4. [ ] Run `quickstart.sh` (Mac/Linux) or `quickstart.cmd` (Windows)
5. [ ] Wait for services to start (should show "Services started successfully!")
6. [ ] Visit http://localhost:8000/api/docs

### First Test (2 minutes)
1. [ ] Open Swagger UI (http://localhost:8000/api/docs)
2. [ ] Register a test user
3. [ ] Login to get JWT token
4. [ ] List certifications
5. [ ] Generate a quiz
6. [ ] Submit quiz answers
7. [ ] Check progress/dashboard

---

## 📋 API Testing Sequence

### 1. Health Check
```bash
curl http://localhost:8000/health
```
**Expected Response:** `{"status": "healthy", ...}`

### 2. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass123"
  }'
```
**Expected Response:** JWT token + user data
- [ ] Copy the `access_token` value
- [ ] Use it in `Bearer {token}` header for protected endpoints

### 3. List Certifications
```bash
curl http://localhost:8000/api/certifications
```
**Expected Response:** List of AWS certifications
- [ ] Should include: Cloud Practitioner, Solutions Architect, Developer, DevOps
- [ ] Copy one certification ID for next step

### 4. Generate Quiz
```bash
curl -X POST http://localhost:8000/api/quizzes/generate \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "certification_id": "{cert-id-from-step-3}",
    "difficulty": "easy"
  }'
```
**Expected Response:** Quiz with 5 questions
- [ ] Should have questions, options, domains, difficulties
- [ ] Copy the `quiz_id` for next step
- [ ] Note the question IDs

### 5. Evaluate Quiz
```bash
curl -X POST http://localhost:8000/api/quizzes/{quiz-id}/evaluate \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "{question-id-1}": "Option A",
      "{question-id-2}": ["Option A", "Option B"],
      "{question-id-3}": "True",
      "{question-id-4}": "Option C",
      "{question-id-5}": "False"
    }
  }'
```
**Expected Response:** Score, XP, achievements
- [ ] Score should be calculated
- [ ] XP should be awarded
- [ ] Accuracy should be shown
- [ ] Weak domains identified (if applicable)

### 6. Get Dashboard
```bash
curl http://localhost:8000/api/progress/dashboard \
  -H "Authorization: Bearer {your-token}"
```
**Expected Response:** User statistics
- [ ] Total XP updated
- [ ] Level increased
- [ ] Streak updated
- [ ] Certifications progress shown

---

## 🔧 Troubleshooting Guide

### Issue: "PostgreSQL connection refused"
**Solution:**
```bash
# Check if postgres is running
docker ps | grep postgres

# If not running, start it
docker-compose up -d postgres

# Wait a moment then check logs
docker-compose logs postgres
```

### Issue: "OpenAI API error: Invalid API key"
**Solution:**
1. Check `.env` file has correct `OPENAI_API_KEY`
2. Verify API key is active at https://platform.openai.com/api-keys
3. Check if you have API credits: https://platform.openai.com/account/billing/overview
4. Restart FastAPI: `docker-compose restart fastapi`

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Kill existing process
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On Mac/Linux:
lsof -i :8000
kill -9 <PID>

# Then restart
docker-compose up -d
```

### Issue: "Docker daemon is not running"
**Solution:**
- Mac: Open Docker Desktop application
- Windows: Open Docker Desktop application
- Linux: `sudo systemctl start docker`

### Issue: Swagger UI not loading
**Solution:**
1. Verify FastAPI container is running: `docker ps | grep fastapi`
2. Check logs: `docker-compose logs fastapi`
3. Try refreshing browser (Ctrl+Shift+R)
4. Clear browser cache

---

## 📊 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Just FastAPI
docker-compose logs -f fastapi

# Just PostgreSQL
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100
```

### Database Inspection
```bash
# Connect to database
docker exec -it aws-mind-quest-db psql -U admin -d aws_mind_quest

# Useful SQL queries:
# List all tables
\dt

# Check users
SELECT * FROM users;

# Check quiz history
SELECT * FROM quizzes;

# Exit
\q
```

### Service Health
```bash
# Check all services
docker-compose ps

# Expected output:
# NAME                          STATUS
# aws-mind-quest-api           Up (healthy)
# aws-mind-quest-db            Up (healthy)
```

---

## 🚀 Next Steps After Getting It Running

### Week 1: Local Development
- [ ] Explore all API endpoints
- [ ] Review database schema
- [ ] Modify business logic as needed
- [ ] Add custom validations
- [ ] Setup database seeding script

### Week 2: Frontend Integration
- [ ] Start Angular frontend project
- [ ] Integrate with FastAPI backend
- [ ] Test end-to-end workflow
- [ ] Style and polish UI

### Week 3: AWS Deployment
- [ ] Setup RDS PostgreSQL instance
- [ ] Deploy Lambda function
- [ ] Setup API Gateway
- [ ] Configure Cognito (optional)
- [ ] Setup S3 for resources (optional)

### Week 4: Production Ready
- [ ] Add CI/CD pipeline
- [ ] Setup monitoring and logging
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation completion

---

## 📁 Important Files to Know

| File | Purpose | Edit? |
|------|---------|-------|
| `.env` | Configuration secrets | ✏️ YES |
| `docker-compose.yml` | Service definitions | ℹ️ Rarely |
| `requirements.txt` | Python dependencies | ✏️ When adding packages |
| `app/main.py` | FastAPI app entry | ℹ️ Reference only |
| `app/services/quiz_*.py` | Core business logic | ✏️ Customize here |
| `app/routers/quiz.py` | API endpoints | ✏️ Customize here |
| `app/database/models.py` | Database schema | ✏️ For new tables |

---

## 🔑 Key Environment Variables

```bash
# .env file must include:

OPENAI_API_KEY=sk-...          # Required! Get from OpenAI
DATABASE_URL=postgresql://...  # Auto set by docker-compose
SECRET_KEY=your-secret         # Change in production
ENV=development                # Or "production"
DEBUG=True                      # Set to False in production
CORS_ORIGINS=[...]            # Add your frontend URL
```

---

## 🌐 URLs to Remember

| Service | URL |
|---------|-----|
| **API Docs (Swagger)** | http://localhost:8000/api/docs |
| **API Docs (ReDoc)** | http://localhost:8000/api/redoc |
| **API Base** | http://localhost:8000/api |
| **Health Check** | http://localhost:8000/health |
| **Database** | localhost:5432 (postgres container) |
| **PgAdmin** | Not installed, but can add if needed |

---

## 💡 Pro Tips

1. **Use Swagger UI** - Don't memorize curl commands, use http://localhost:8000/api/docs
2. **Keep logs open** - `docker-compose logs -f` in a separate terminal
3. **Save your tokens** - Copy JWT tokens to test multiple endpoints
4. **Test gradually** - Don't generate 100 quizzes at once
5. **Monitor costs** - Each quiz generation costs ~$0.01 with OpenAI
6. **Use environment variables** - Never hardcode secrets

---

## ✅ Success Indicators

You'll know everything is working when:
- ✅ `docker-compose ps` shows both containers as "Up (healthy)"
- ✅ http://localhost:8000/api/docs loads without errors
- ✅ Can register and login with a test user
- ✅ Can generate a quiz (takes 2-5 seconds)
- ✅ Can evaluate a quiz and see score
- ✅ Swagger UI shows all endpoints documented
- ✅ Dashboard endpoint returns user stats

---

## 📞 Quick Support

### Common Questions

**Q: How much will this cost on AWS?**
A: Free tier: $0/month. After free tier: ~$15-30/month for RDS + Lambda

**Q: Can I use a different LLM?**
A: Yes! See `ARCHITECTURE.md` for options (Ollama, Bedrock, etc.)

**Q: Do I need to scale this?**
A: Not initially. FastAPI + PostgreSQL handles thousands of requests

**Q: How do I add more certifications?**
A: Use the POST `/certifications` endpoint or SQL INSERT directly

**Q: Can I run without Docker?**
A: Yes, follow "Local Development" section in `SETUP_GUIDE.md`

---

## 🎓 Learning Resources

- FastAPI Official Docs: https://fastapi.tiangolo.com/
- SQLAlchemy Tutorial: https://docs.sqlalchemy.org/
- PostgreSQL Basics: https://www.postgresql.org/docs/
- OpenAI API Guide: https://platform.openai.com/docs/guides
- Docker Basics: https://docs.docker.com/get-started/

---

## 🎉 Ready to Go!

You're all set! Start with the **Quick Start (5 minutes)** section above, then follow **First Test (2 minutes)**.

**Questions?** Check `SETUP_GUIDE.md` for more detailed help.

**Happy coding! 🚀**

---

**Project Status:** ✅ Ready for Development
**Last Updated:** November 29, 2025
