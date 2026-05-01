# SkillBridge API — Complete Testing Guide

This guide walks through every API endpoint step by step using Postman.  
Follow the sections in order — each step builds on the previous one.

---

## Quick Reference

| # | Method | Endpoint | Role Required |
|---|---|---|---|
| 1 | POST | `/auth/signup` | Anyone |
| 2 | POST | `/auth/login` | Anyone |
| 3 | POST | `/auth/monitoring-token` | Monitoring Officer only |
| 4 | POST | `/batches` | Trainer / Institution |
| 5 | POST | `/batches/{id}/invite` | Trainer |
| 6 | POST | `/batches/join` | Student |
| 7 | GET | `/batches/{id}/summary` | Institution / Programme Manager |
| 8 | POST | `/sessions` | Trainer |
| 9 | GET | `/sessions/{id}/attendance` | Trainer |
| 10 | POST | `/attendance/mark` | Student |
| 11 | GET | `/institutions/{id}/summary` | Programme Manager |
| 12 | GET | `/programme/summary` | Programme Manager |
| 13 | GET | `/monitoring/attendance` | Monitoring Officer (scoped token) |

---

## Base URL

Live:   https://skillbridge-704u.onrender.com
```

## Postman Setup (do this once)

1. Open Postman → click **Environments** (top right) → **New Environment**
2. Name it `SkillBridge`
3. Add these variables:

| Variable | Initial Value |
|---|---|
| `BASE_URL` | `https://skillbridge-704u.onrender.com` |
| `student_token` | *(leave blank — filled automatically)* |
| `trainer_token` | *(leave blank)* |
| `inst_token` | *(leave blank)* |
| `pm_token` | *(leave blank)* |
| `mo_token` | *(leave blank)* |
| `monitoring_token` | *(leave blank)* |
| `batch_id` | *(leave blank)* |
| `session_id` | *(leave blank)* |
| `invite_token` | *(leave blank)* |

4. Select this environment from the top-right dropdown before testing.

---

## Seeded Test Accounts

All passwords are `Password123!`

| Role | Email |
|---|---|
| Student | `student01@skillbridge.dev` |
| Trainer | `trainer1@skillbridge.dev` |
| Institution | `inst1@skillbridge.dev` |
| Programme Manager | `pm@skillbridge.dev` |
| Monitoring Officer | `monitor@skillbridge.dev` |

---

---

# SECTION 1 — Authentication

---

## 1.1 — Signup

**What it does:** Creates a new user account and returns a JWT token.

```
POST https://skillbridge-704u.onrender.com/auth/signup
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "MyPass123!",
  "role": "student"
}
```

**Expected Response — 201 Created:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Error Cases for Signup

**Missing required field (name left out):**
```json
{
  "email": "john@example.com",
  "password": "MyPass123!",
  "role": "student"
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": { "email": "john@example.com", "password": "MyPass123!", "role": "student" }
    }
  ]
}
```

---

**Invalid role:**
```json
{
  "name": "John",
  "email": "john2@example.com",
  "password": "MyPass123!",
  "role": "superadmin"
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": "role must be one of ['institution', 'monitoring_officer', 'programme_manager', 'student', 'trainer']"
}
```

---

**Duplicate email:**
```json
{
  "name": "John Again",
  "email": "john@example.com",
  "password": "MyPass123!",
  "role": "student"
}
```
Response — **409 Conflict:**
```json
{
  "detail": "Email already registered"
}
```

---

**Invalid email format:**
```json
{
  "name": "John",
  "email": "not-an-email",
  "password": "MyPass123!",
  "role": "student"
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

---

## 1.2 — Login

**What it does:** Validates credentials and returns a JWT token.

```
POST https://skillbridge-704u.onrender.com/auth/login
```

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON) — login as Trainer:**
```json
{
  "email": "trainer1@skillbridge.dev",
  "password": "Password123!"
}
```

**Expected Response — 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> **Tip:** Copy this token. In the Tests tab of Postman you can auto-save it:
> ```js
> let json = pm.response.json();
> pm.environment.set("trainer_token", json.access_token);
> ```

**Repeat login for all roles and save their tokens:**

| Role | Email | Environment Variable |
|---|---|---|
| Student | student01@skillbridge.dev | `student_token` |
| Trainer | trainer1@skillbridge.dev | `trainer_token` |
| Institution | inst1@skillbridge.dev | `inst_token` |
| Programme Manager | pm@skillbridge.dev | `pm_token` |
| Monitoring Officer | monitor@skillbridge.dev | `mo_token` |

---

### Error Cases for Login

**Wrong password:**
```json
{
  "email": "trainer1@skillbridge.dev",
  "password": "wrongpassword"
}
```
Response — **401 Unauthorized:**
```json
{
  "detail": "Invalid credentials"
}
```

---

**Email not registered:**
```json
{
  "email": "nobody@nowhere.com",
  "password": "Password123!"
}
```
Response — **401 Unauthorized:**
```json
{
  "detail": "Invalid credentials"
}
```

---

**Empty body:**
```json
{}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": [
    { "type": "missing", "loc": ["body", "email"], "msg": "Field required" },
    { "type": "missing", "loc": ["body", "password"], "msg": "Field required" }
  ]
}
```

---

## 1.3 — Get Monitoring Token (Monitoring Officer only)

**What it does:** Exchanges a valid Monitoring Officer JWT + API key for a short-lived, read-only scoped token. This is the only token accepted by `/monitoring/attendance`.

```
POST https://skillbridge-704u.onrender.com/auth/monitoring-token
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{mo_token}}
```

**Body:**
```json
{
  "key": "monitor123"
}
```

**Expected Response — 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> Save this as `monitoring_token` in your Postman environment.

---

### Error Cases for Monitoring Token

**Wrong API key:**
```json
{
  "key": "wrongkey"
}
```
Response — **401 Unauthorized:**
```json
{
  "detail": "Invalid API key"
}
```

---

**Using a non-monitoring-officer login token (e.g. trainer token):**
```
Authorization: Bearer {{trainer_token}}
```
Response — **403 Forbidden:**
```json
{
  "detail": "Only monitoring_officer can obtain monitoring tokens"
}
```

---

**No Authorization header at all:**
Response — **403 Forbidden:**
```json
{
  "detail": "Not authenticated"
}
```

---

---

# SECTION 2 — Batches

---

## 2.1 — Create a Batch

**What it does:** Creates a new training batch under an institution. Trainers are auto-assigned to the batch they create.

```
POST https://skillbridge-704u.onrender.com/batches
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{trainer_token}}
```

**Body:**
```json
{
  "name": "Python Bootcamp 2025",
  "institution_id": 1
}
```

> Replace `institution_id` with the actual ID of an institution user (check seed output or use the login token's `sub` claim after decoding).

**Expected Response — 201 Created:**
```json
{
  "id": 4,
  "name": "Python Bootcamp 2025",
  "institution_id": 1,
  "created_at": "2025-04-30T10:23:11.045231"
}
```

> Save `id` as `batch_id` in your environment.

---

### Error Cases for Create Batch

**Wrong role (student tries to create batch):**
```
Authorization: Bearer {{student_token}}
```
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

**No token:**
Response — **403 Forbidden:**
```json
{
  "detail": "Not authenticated"
}
```

---

**Non-existent institution_id:**
```json
{
  "name": "Ghost Batch",
  "institution_id": 99999
}
```
Response — **404 Not Found:**
```json
{
  "detail": "Institution not found"
}
```

---

**Missing required field:**
```json
{
  "institution_id": 1
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": [
    { "type": "missing", "loc": ["body", "name"], "msg": "Field required" }
  ]
}
```

---

## 2.2 — Generate an Invite Link

**What it does:** Creates a single-use invite token that a student can use to join the batch.

```
POST https://skillbridge-704u.onrender.com/batches/{{batch_id}}/invite
```

**Headers:**
```
Authorization: Bearer {{trainer_token}}
```

**No body required.**

**Expected Response — 201 Created:**
```json
{
  "token": "aB3xK9mPqR7vWzYn2cDfGhJsLtUeOi5E",
  "expires_at": "2025-05-07T10:23:11.000000",
  "batch_id": 4
}
```

> Save the `token` value as `invite_token` in your Postman environment.

---

### Error Cases for Generate Invite

**Batch does not exist:**
```
POST /batches/99999/invite
```
Response — **404 Not Found:**
```json
{
  "detail": "Batch not found"
}
```

---

**Trainer not assigned to this batch:**
```
Authorization: Bearer {{trainer_token}}   ← a different trainer
```
Response — **403 Forbidden:**
```json
{
  "detail": "You are not assigned to this batch"
}
```

---

**Wrong role (institution tries to generate invite):**
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

## 2.3 — Join a Batch (Student)

**What it does:** Student uses the invite token to enroll in a batch.

```
POST https://skillbridge-704u.onrender.com/batches/join
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{student_token}}
```

**Body:**
```json
{
  "token": "aB3xK9mPqR7vWzYn2cDfGhJsLtUeOi5E"
}
```

**Expected Response — 200 OK:**
```json
{
  "message": "Joined batch successfully",
  "batch_id": 4
}
```

---

### Error Cases for Join Batch

**Invalid / non-existent token:**
```json
{
  "token": "thisTokenDoesNotExist"
}
```
Response — **404 Not Found:**
```json
{
  "detail": "Invite token not found"
}
```

---

**Token already used (try the same token a second time):**
Response — **410 Gone:**
```json
{
  "detail": "Invite token already used"
}
```

---

**Student already enrolled:**
```json
{
  "token": "anotherValidToken"
}
```
Response — **409 Conflict:**
```json
{
  "detail": "Already enrolled in this batch"
}
```

---

**Wrong role (trainer tries to join):**
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

## 2.4 — Batch Attendance Summary (Institution)

**What it does:** Returns aggregated attendance stats for all sessions in a batch.

```
GET https://skillbridge-704u.onrender.com/batches/{{batch_id}}/summary
```

**Headers:**
```
Authorization: Bearer {{inst_token}}
```

**Expected Response — 200 OK:**
```json
{
  "batch_id": 1,
  "batch_name": "Web Dev Batch A",
  "total_sessions": 3,
  "total_students": 7,
  "attendance_records": 21,
  "present": 15,
  "absent": 3,
  "late": 3
}
```

---

### Error Cases for Batch Summary

**Batch not found:**
```
GET /batches/99999/summary
```
Response — **404 Not Found:**
```json
{
  "detail": "Batch not found"
}
```

---

**Wrong role (student tries to access):**
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

---

# SECTION 3 — Sessions

---

## 3.1 — Create a Session

**What it does:** Trainer creates a training session under a batch they are assigned to.

```
POST https://skillbridge-704u.onrender.com/sessions
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{trainer_token}}
```

**Body:**
```json
{
  "title": "Introduction to Python",
  "date": "2025-05-15",
  "start_time": "09:00:00",
  "end_time": "11:00:00",
  "batch_id": 1
}
```

**Expected Response — 201 Created:**
```json
{
  "id": 9,
  "batch_id": 1,
  "trainer_id": 2,
  "title": "Introduction to Python",
  "date": "2025-05-15",
  "start_time": "09:00:00",
  "end_time": "11:00:00",
  "created_at": "2025-04-30T10:30:00.123456"
}
```

> Save `id` as `session_id` in your environment.

---

### Error Cases for Create Session

**Missing required fields:**
```json
{
  "title": "Python Class",
  "batch_id": 1
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": [
    { "type": "missing", "loc": ["body", "date"], "msg": "Field required" },
    { "type": "missing", "loc": ["body", "start_time"], "msg": "Field required" },
    { "type": "missing", "loc": ["body", "end_time"], "msg": "Field required" }
  ]
}
```

---

**Invalid date format:**
```json
{
  "title": "Python Class",
  "date": "15-05-2025",
  "start_time": "09:00:00",
  "end_time": "11:00:00",
  "batch_id": 1
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": [
    { "type": "date_from_datetime_parsing", "loc": ["body", "date"], "msg": "Input should be a valid date" }
  ]
}
```

---

**Non-existent batch_id:**
```json
{
  "title": "Python Class",
  "date": "2025-05-15",
  "start_time": "09:00:00",
  "end_time": "11:00:00",
  "batch_id": 99999
}
```
Response — **404 Not Found:**
```json
{
  "detail": "Batch not found"
}
```

---

**Trainer not assigned to this batch:**
Response — **403 Forbidden:**
```json
{
  "detail": "You are not assigned to this batch"
}
```

---

**Wrong role (student tries to create session):**
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

## 3.2 — View Session Attendance (Trainer)

**What it does:** Returns the full list of students and their attendance status for a specific session.

```
GET https://skillbridge-704u.onrender.com/sessions/{{session_id}}/attendance
```

**Headers:**
```
Authorization: Bearer {{trainer_token}}
```

**Expected Response — 200 OK:**
```json
[
  {
    "student_id": 3,
    "student_name": "Student 01",
    "status": "present",
    "marked_at": "2025-03-01T09:30:00"
  },
  {
    "student_id": 4,
    "student_name": "Student 02",
    "status": "absent",
    "marked_at": "2025-03-01T09:30:00"
  },
  {
    "student_id": 5,
    "student_name": "Student 03",
    "status": "late",
    "marked_at": "2025-03-01T09:30:00"
  }
]
```

> Returns empty `[]` if no attendance has been marked yet.

---

### Error Cases for Session Attendance

**Session not found:**
```
GET /sessions/99999/attendance
```
Response — **404 Not Found:**
```json
{
  "detail": "Session not found"
}
```

---

**No token provided:**
Response — **403 Forbidden:**
```json
{
  "detail": "Not authenticated"
}
```

---

**Expired or invalid token:**
```
Authorization: Bearer thisisnotavalidtoken
```
Response — **401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

---

---

# SECTION 4 — Attendance

---

## 4.1 — Mark Attendance (Student)

**What it does:** A student marks their own attendance for a session that is scheduled for today.

> **Important:** The session's `date` must equal today's date. Use the seeded data or create a new session with today's date.

```
POST https://skillbridge-704u.onrender.com/attendance/mark
```

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{student_token}}
```

**Body:**
```json
{
  "session_id": 1,
  "status": "present"
}
```

Valid status values: `present` | `absent` | `late`

**Expected Response — 201 Created:**
```json
{
  "id": 100,
  "session_id": 1,
  "student_id": 3,
  "status": "present",
  "marked_at": "2025-04-30T10:45:22.334512"
}
```

---

### Error Cases for Mark Attendance

**Invalid status value:**
```json
{
  "session_id": 1,
  "status": "here"
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": "status must be one of ['absent', 'late', 'present']"
}
```

---

**Session not found:**
```json
{
  "session_id": 99999,
  "status": "present"
}
```
Response — **404 Not Found:**
```json
{
  "detail": "Session not found"
}
```

---

**Session is not today (date mismatch):**
```json
{
  "session_id": 1,
  "status": "present"
}
```
*(session is scheduled for a past date)*

Response — **400 Bad Request:**
```json
{
  "detail": "Can only mark attendance for today's session"
}
```

---

**Student not enrolled in this batch:**
Response — **403 Forbidden:**
```json
{
  "detail": "You are not enrolled in this batch"
}
```

---

**Attendance already marked (duplicate attempt):**
Response — **409 Conflict:**
```json
{
  "detail": "Attendance already marked for this session"
}
```

---

**Wrong role (trainer tries to mark attendance):**
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

**Missing fields:**
```json
{
  "session_id": 1
}
```
Response — **422 Unprocessable Entity:**
```json
{
  "detail": [
    { "type": "missing", "loc": ["body", "status"], "msg": "Field required" }
  ]
}
```

---

---

# SECTION 5 — Institution & Programme Summaries

---

## 5.1 — Institution Summary (Programme Manager)

**What it does:** Returns attendance stats for every batch under a specific institution.

```
GET https://skillbridge-704u.onrender.com/institutions/1/summary
```

**Headers:**
```
Authorization: Bearer {{pm_token}}
```

**Expected Response — 200 OK:**
```json
{
  "institution_id": 1,
  "institution_name": "Sunrise Institute",
  "batches": [
    {
      "batch_id": 1,
      "batch_name": "Web Dev Batch A",
      "total_sessions": 3,
      "total_students": 7,
      "attendance_records": 21,
      "present": 15,
      "absent": 3,
      "late": 3
    },
    {
      "batch_id": 2,
      "batch_name": "Data Science Batch B",
      "total_sessions": 2,
      "total_students": 7,
      "attendance_records": 14,
      "present": 10,
      "absent": 2,
      "late": 2
    }
  ]
}
```

---

### Error Cases for Institution Summary

**Institution not found:**
```
GET /institutions/99999/summary
```
Response — **404 Not Found:**
```json
{
  "detail": "Institution not found"
}
```

---

**Wrong role (trainer tries to access):**
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

## 5.2 — Programme-Wide Summary (Programme Manager)

**What it does:** Returns a complete attendance breakdown across all institutions and all batches.

```
GET https://skillbridge-704u.onrender.com/programme/summary
```

**Headers:**
```
Authorization: Bearer {{pm_token}}
```

**Expected Response — 200 OK:**
```json
{
  "programme_summary": [
    {
      "institution_id": 1,
      "institution_name": "Sunrise Institute",
      "batches": [
        {
          "batch_id": 1,
          "batch_name": "Web Dev Batch A",
          "total_sessions": 3,
          "total_students": 7,
          "attendance_records": 21,
          "present": 15,
          "absent": 3,
          "late": 3
        }
      ]
    },
    {
      "institution_id": 2,
      "institution_name": "Horizon College",
      "batches": [
        {
          "batch_id": 3,
          "batch_name": "Cybersecurity Batch C",
          "total_sessions": 3,
          "total_students": 6,
          "attendance_records": 18,
          "present": 12,
          "absent": 3,
          "late": 3
        }
      ]
    }
  ]
}
```

---

### Error Cases for Programme Summary

**Wrong role (student tries to access):**
Response — **403 Forbidden:**
```json
{
  "detail": "Forbidden: insufficient role"
}
```

---

**No token:**
Response — **403 Forbidden:**
```json
{
  "detail": "Not authenticated"
}
```

---

---

# SECTION 6 — Monitoring Officer

---

## 6.1 — Full Attendance Read (Monitoring Officer — Scoped Token)

**What it does:** Returns every attendance record in the system across all institutions, batches, and sessions. Read-only. Requires the short-lived **monitoring-scoped token**, not the standard login token.

```
GET https://skillbridge-704u.onrender.com/monitoring/attendance
```

**Headers:**
```
Authorization: Bearer {{monitoring_token}}
```

**Expected Response — 200 OK:**
```json
[
  {
    "attendance_id": 1,
    "session_id": 1,
    "session_title": "HTML Basics",
    "batch_id": 1,
    "batch_name": "Web Dev Batch A",
    "student_id": 3,
    "student_name": "Student 01",
    "status": "present",
    "marked_at": "2025-03-01T09:30:00"
  },
  {
    "attendance_id": 2,
    "session_id": 1,
    "session_title": "HTML Basics",
    "batch_id": 1,
    "batch_name": "Web Dev Batch A",
    "student_id": 4,
    "student_name": "Student 02",
    "status": "absent",
    "marked_at": "2025-03-01T09:30:00"
  }
]
```

---

### Error Cases for Monitoring Attendance

**Using a standard login token instead of the scoped monitoring token:**
```
Authorization: Bearer {{mo_token}}    ← standard JWT, not monitoring-scoped
```
Response — **401 Unauthorized:**
```json
{
  "detail": "Token is not a monitoring-scoped token"
}
```

---

**Using another role's token (e.g. Programme Manager):**
Response — **401 Unauthorized:**
```json
{
  "detail": "Token is not a monitoring-scoped token"
}
```

---

**No token:**
Response — **403 Forbidden:**
```json
{
  "detail": "Not authenticated"
}
```

---

**Expired monitoring token (after 1 hour):**
Response — **401 Unauthorized:**
```json
{
  "detail": "Invalid or expired monitoring token"
}
```

---

## 6.2 — POST to /monitoring/attendance Returns 405

**What it does:** The monitoring endpoint is strictly read-only. Any write method is rejected.

```
POST https://skillbridge-704u.onrender.com/monitoring/attendance
```

*(No headers or body needed — it should be rejected before auth)*

**Expected Response — 405 Method Not Allowed:**
```json
{
  "detail": "Method Not Allowed"
}
```

> This also applies to PUT, PATCH, and DELETE on this endpoint.

---

---

# SECTION 7 — Cross-Role Access Tests

Use these to verify RBAC is enforced correctly end-to-end.

| Test | Token Used | Endpoint | Expected |
|---|---|---|---|
| Student creates batch | `student_token` | POST /batches | 403 |
| Student creates session | `student_token` | POST /sessions | 403 |
| Trainer marks attendance | `trainer_token` | POST /attendance/mark | 403 |
| Student views programme summary | `student_token` | GET /programme/summary | 403 |
| Trainer views programme summary | `trainer_token` | GET /programme/summary | 403 |
| PM gets monitoring attendance | `pm_token` | GET /monitoring/attendance | 401 |
| Standard MO JWT on monitoring | `mo_token` | GET /monitoring/attendance | 401 |
| No token on any protected route | *(none)* | Any protected endpoint | 403 |
| Garbage token on any route | `Bearer abc123` | Any protected endpoint | 401 |

---

---

# SECTION 8 — Full End-to-End Flow (Recommended Demo Order)

Follow this sequence to demo the full system to an interviewer:

```
1.  POST /auth/login          → login as trainer1, save trainer_token
2.  POST /auth/login          → login as student01, save student_token
3.  POST /auth/login          → login as inst1, save inst_token
4.  POST /auth/login          → login as pm, save pm_token
5.  POST /auth/login          → login as monitor, save mo_token

6.  POST /batches             → trainer creates batch (note batch_id)
7.  POST /batches/{id}/invite → trainer generates invite (note invite_token)
8.  POST /batches/join        → student joins using invite_token

9.  POST /sessions            → trainer creates session for TODAY's date (note session_id)
10. POST /attendance/mark     → student marks attendance on that session

11. GET  /sessions/{id}/attendance   → trainer views attendance list
12. GET  /batches/{id}/summary       → institution views batch summary
13. GET  /institutions/{id}/summary  → PM views institution summary
14. GET  /programme/summary          → PM views full programme summary

15. POST /auth/monitoring-token → mo exchanges JWT + API key for scoped token
16. GET  /monitoring/attendance  → monitoring officer reads all data (read-only)
17. POST /monitoring/attendance  → verify 405 is returned
```

---

---

# SECTION 9 — Health Check

```
GET https://skillbridge-704u.onrender.com/health
```

No authentication required.

**Expected Response — 200 OK:**
```json
{
  "status": "ok"
}
```

---

# SECTION 10 — Interactive API Docs

FastAPI generates automatic documentation. Open in browser:

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — try every endpoint interactively |
| `http://localhost:8000/redoc` | ReDoc — clean reference documentation |

You can use Swagger UI as an alternative to Postman for quick manual testing — click **Authorize**, paste your JWT token, and run requests directly in the browser.

---

*Guide covers all 13 endpoints — every success case, every error case, cross-role RBAC tests, and a recommended demo flow.*
