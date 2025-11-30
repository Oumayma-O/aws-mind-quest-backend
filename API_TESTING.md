# API Testing Guide - AWS Mind Quest

## Database Status

Your database has 7 tables:
- `users` - User accounts
- `certifications` - AWS certifications
- `profiles` - User profiles
- `quizzes` - Quiz attempts
- `questions` - Quiz questions
- `user_progress` - User progress tracking
- `achievements` - User achievements

**Status:** Currently empty (no certifications or users yet)

---

## Step-by-Step API Testing

### Base URL
```
http://localhost:8000
```

### API Documentation
```
http://localhost:8000/api/docs
```

---

## 1️⃣ Register a User

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "email": "john@example.com",
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Expected Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john@example.com",
    "username": "john_doe",
    "is_active": true,
    "created_at": "2025-11-30T15:00:00"
  }
}
```

**Save the `access_token`** - you'll need it for authenticated requests!

---

## 2️⃣ Login (Alternative)

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:** Same as registration

---

## 3️⃣ Get Current User Info

**Endpoint:** `GET /api/auth/me`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Example with curl:**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/api/auth/me
```

---

## 4️⃣ Create/Add Certifications

**Endpoint:** `POST /api/certifications/`

**Request Body:**
```json
{
  "name": "AWS Certified Solutions Architect - Associate",
  "description": "Validate your ability to design and implement AWS solutions"
}
```

**Response (201 Created):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "AWS Certified Solutions Architect - Associate",
  "description": "Validate your ability to design and implement AWS solutions",
  "created_at": "2025-11-30T15:00:00"
}
```

**Create Multiple Certifications:**

```json
{
  "name": "AWS Certified Developer - Associate",
  "description": "Validate your ability to develop and maintain applications on AWS"
}
```

```json
{
  "name": "AWS Certified SysOps Administrator - Associate",
  "description": "Validate your ability to provision, operate, and manage AWS systems"
}
```

---

## 5️⃣ Get All Certifications

**Endpoint:** `GET /api/certifications/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "AWS Certified Solutions Architect - Associate",
    "description": "..."
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "name": "AWS Certified Developer - Associate",
    "description": "..."
  }
]
```

---

## 6️⃣ Select Certification for User

**Endpoint:** `POST /api/profile/select-certification`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body:**
```json
{
  "certification_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "selected_certification_id": "660e8400-e29b-41d4-a716-446655440001",
  "xp": 0,
  "level": 1,
  "current_streak": 0,
  "last_quiz_date": null,
  "created_at": "2025-11-30T15:00:00",
  "updated_at": "2025-11-30T15:00:00"
}
```

---

## 7️⃣ Generate a Quiz

**Endpoint:** `POST /api/quiz/generate`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body:**
```json
{
  "certification_id": "660e8400-e29b-41d4-a716-446655440001",
  "difficulty": "medium",
  "num_questions": 5
}
```

**Parameters:**
- `difficulty`: `"easy"`, `"medium"`, or `"hard"`
- `num_questions`: Number of questions (e.g., 5, 10)

**Response (201 Created):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "certification_id": "660e8400-e29b-41d4-a716-446655440001",
  "difficulty": "medium",
  "score": null,
  "total_questions": 5,
  "xp_earned": null,
  "completed_at": null,
  "created_at": "2025-11-30T15:00:00",
  "questions": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "question_text": "What does S3 stand for?",
      "question_type": "multiple_choice",
      "options": ["Simple Storage Service", "Static Storage Service", "System Storage Service"],
      "difficulty": "easy",
      "domain": "Storage Services"
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440001",
      "question_text": "Which AWS service is used for relational databases?",
      "question_type": "multiple_choice",
      "options": ["RDS", "DynamoDB", "ElastiCache"],
      "difficulty": "medium",
      "domain": "Databases"
    }
  ]
}
```

---

## 8️⃣ Submit Quiz Answers

**Endpoint:** `POST /api/quiz/{quiz_id}/submit`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body:**
```json
{
  "answers": [
    {
      "question_id": "990e8400-e29b-41d4-a716-446655440000",
      "user_answer": "Simple Storage Service"
    },
    {
      "question_id": "990e8400-e29b-41d4-a716-446655440001",
      "user_answer": "RDS"
    },
    {
      "question_id": "990e8400-e29b-41d4-a716-446655440002",
      "user_answer": "true"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "score": 4,
  "total_questions": 5,
  "percentage": 80,
  "xp_earned": 80,
  "completed_at": "2025-11-30T15:01:00",
  "results": [
    {
      "question_id": "990e8400-e29b-41d4-a716-446655440000",
      "is_correct": true,
      "user_answer": "Simple Storage Service",
      "correct_answer": "Simple Storage Service",
      "explanation": "S3 stands for Simple Storage Service, AWS's object storage solution."
    },
    {
      "question_id": "990e8400-e29b-41d4-a716-446655440001",
      "is_correct": true,
      "user_answer": "RDS",
      "correct_answer": "RDS"
    }
  ]
}
```

---

## 9️⃣ Get User Progress

**Endpoint:** `GET /api/progress/{certification_id}`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "certification_id": "660e8400-e29b-41d4-a716-446655440001",
  "total_xp": 240,
  "total_quizzes": 3,
  "total_questions_answered": 15,
  "correct_answers": 12,
  "accuracy": 80.0,
  "current_difficulty": "hard",
  "weak_domains": ["VPC Configuration", "Lambda Advanced"],
  "updated_at": "2025-11-30T15:05:00"
}
```

---

## Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0"
}
```

---

## Testing Workflow

### 1. Check Health
```
GET /health
```

### 2. Register User
```
POST /api/auth/register
{
  "email": "john@example.com",
  "username": "john_doe",
  "password": "SecurePass123!"
}
```
**Copy the `access_token`**

### 3. Add Certifications
```
POST /api/certifications/
{
  "name": "AWS Certified Solutions Architect - Associate",
  "description": "Validate your ability to design and implement AWS solutions"
}
```

### 4. Select Certification
```
POST /api/profile/select-certification
{
  "certification_id": "CERTIFICATION_ID_FROM_STEP_3"
}
```

### 5. Generate Quiz
```
POST /api/quiz/generate
{
  "certification_id": "CERTIFICATION_ID_FROM_STEP_3",
  "difficulty": "medium",
  "num_questions": 5
}
```
**Copy the `quiz_id`**

### 6. Submit Answers
```
POST /api/quiz/{QUIZ_ID}/submit
{
  "answers": [...]
}
```

### 7. Check Progress
```
GET /api/progress/{CERTIFICATION_ID}
```

---

## Using Postman or VS Code REST Client

### VS Code REST Client Extension
Create a file `api-test.http`:

```http
### Health Check
GET http://localhost:8000/health

### Register User
POST http://localhost:8000/api/auth/register
Content-Type: application/json

{
  "email": "john@example.com",
  "username": "john_doe",
  "password": "SecurePass123!"
}

### Get Current User
GET http://localhost:8000/api/auth/me
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## Notes

- ✅ All requests go to `http://localhost:8000`
- ✅ Authenticated endpoints require `Authorization: Bearer TOKEN` header
- ✅ Replace `YOUR_ACCESS_TOKEN` with the token from registration/login
- ✅ Replace IDs with actual values from responses
- ✅ Use the Swagger UI at `/api/docs` for interactive testing

**Ready to test!** 🚀
