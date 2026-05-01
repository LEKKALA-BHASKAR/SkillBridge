# SkillBridge API

REST API for a state-level skilling programme attendance management system with five user roles and JWT-based auth.

---

## 1. Live API Base URL

> **Deployment note:** The API is configured for Railway/Render/Fly.io deployment. The Neon PostgreSQL database is live and seeded. Set the `DATABASE_URL` environment variable from the `.env` file in the platform secrets panel.
>
> Replace `https://skillbridge-704u.onrender.com` with your actual deployed URL once deployed.

```
https://skillbridge-704u.onrender.com
```

### Working curl against live deployment

```bash
curl -s -X POST https://skillbridge-704u.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student01@skillbridge.dev","password":"Password123!"}' | jq .
```

---

## 2. Local Setup (from scratch)

```bash
# Clone / enter the project
cd skillbridge-api

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env            # edit DATABASE_URL, JWT_SECRET, MONITORING_API_KEY

# Seed the database
python -m src.seed

# Run the API
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## 3. Test Accounts (all seeded by `seed.py`)

| Role | Email | Password |
|---|---|---|
| Student | student01@skillbridge.dev | Password123! |
| Trainer | trainer1@skillbridge.dev | Password123! |
| Institution | inst1@skillbridge.dev | Password123! |
| Programme Manager | pm@skillbridge.dev | Password123! |
| Monitoring Officer | monitor@skillbridge.dev | Password123! |

Additional accounts: `student02–15`, `trainer2–4`, `inst2` — all with `Password123!`.

---

## 4. Sample curl Commands

### Auth

```bash
BASE=http://localhost:8000

# Signup (any role)
curl -s -X POST $BASE/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"New User","email":"new@test.dev","password":"Pass123!","role":"student"}' | jq .

# Login
curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student01@skillbridge.dev","password":"Password123!"}' | jq .

# Store token for reuse
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"trainer1@skillbridge.dev","password":"Password123!"}' | jq -r .access_token)

# --- Monitoring Officer two-step token ---
# Step 1: login to get standard JWT
MO_TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"monitor@skillbridge.dev","password":"Password123!"}' | jq -r .access_token)

# Step 2: exchange for scoped monitoring token
MONITORING_TOKEN=$(curl -s -X POST $BASE/auth/monitoring-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MO_TOKEN" \
  -d '{"key":"monitor123"}' | jq -r .access_token)
```

### Batches

```bash
TRAINER_TOKEN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"trainer1@skillbridge.dev","password":"Password123!"}' | jq -r .access_token)

INST_TOKEN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"inst1@skillbridge.dev","password":"Password123!"}' | jq -r .access_token)

# Get inst1 id first
INST_ID=<id of inst1>   # from seed output or GET users

# Create batch (trainer or institution)
curl -s -X POST $BASE/batches \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"New Batch","institution_id":'"$INST_ID"'}' | jq .

# Generate invite link (trainer only)
BATCH_ID=1
curl -s -X POST $BASE/batches/$BATCH_ID/invite \
  -H "Authorization: Bearer $TRAINER_TOKEN" | jq .

# Student joins via invite token
STUDENT_TOKEN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"student01@skillbridge.dev","password":"Password123!"}' | jq -r .access_token)

curl -s -X POST $BASE/batches/join \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"<invite-token-from-above>"}' | jq .

# Batch attendance summary (institution)
curl -s $BASE/batches/$BATCH_ID/summary \
  -H "Authorization: Bearer $INST_TOKEN" | jq .
```

### Sessions

```bash
# Create session (trainer)
curl -s -X POST $BASE/sessions \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"HTML Basics","date":"2025-06-01","start_time":"09:00:00","end_time":"11:00:00","batch_id":1}' | jq .

# Get session attendance list (trainer)
SESSION_ID=1
curl -s $BASE/sessions/$SESSION_ID/attendance \
  -H "Authorization: Bearer $TRAINER_TOKEN" | jq .
```

### Attendance

```bash
# Mark own attendance (student — session must be today)
curl -s -X POST $BASE/attendance/mark \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":1,"status":"present"}' | jq .
```

### Institution / Programme Summary

```bash
PM_TOKEN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"pm@skillbridge.dev","password":"Password123!"}' | jq -r .access_token)

# Institution summary (programme manager)
INST_ID=1
curl -s $BASE/institutions/$INST_ID/summary \
  -H "Authorization: Bearer $PM_TOKEN" | jq .

# Programme-wide summary
curl -s $BASE/programme/summary \
  -H "Authorization: Bearer $PM_TOKEN" | jq .
```

### Monitoring (requires scoped token)

```bash
# Read-only full attendance (monitoring officer scoped token required)
curl -s $BASE/monitoring/attendance \
  -H "Authorization: Bearer $MONITORING_TOKEN" | jq .

# POST returns 405
curl -s -X POST $BASE/monitoring/attendance  # → 405
```

---

## 5. Schema Decisions

### `batch_trainers` (many-to-many)
A batch can be co-taught by multiple trainers — composite primary key `(batch_id, trainer_id)`. When a trainer creates a batch, they are automatically enrolled as a `BatchTrainer`. Institution admins can also create batches and assign trainers separately.

### `batch_invites`
Invite tokens are randomly generated URL-safe strings (`secrets.token_urlsafe`). Each token is single-use (`used=True` after consumption) with a 7-day TTL. This prevents token replay and lets trainers issue time-bounded invitations without exposing batch IDs directly.

### Dual-token approach for Monitoring Officer
Standard JWT tokens (24 h) are issued on login for all roles. The Monitoring Officer must additionally call `POST /auth/monitoring-token` with both their standard JWT **and** a pre-shared API key (`MONITORING_API_KEY`). This returns a short-lived (1 h), scope-restricted token (`scope: "monitoring"`) accepted **only** by `/monitoring/*` endpoints. Standard tokens are rejected on those endpoints and vice versa — defence-in-depth preventing token reuse across endpoint classes.

---

## 6. JWT Payload Structure

### Standard token (all roles)
```json
{
  "sub": "42",
  "role": "trainer",
  "iat": 1710000000,
  "exp": 1710086400
}
```

### Monitoring-scoped token
```json
{
  "sub": "7",
  "role": "monitoring_officer",
  "scope": "monitoring",
  "iat": 1710000000,
  "exp": 1710003600
}
```

### Token rotation / revocation in a real deployment
- Store a `token_version` or `jti` (JWT ID) counter per user in the database.
- On revocation, increment the version; middleware rejects tokens with a lower version.
- Alternatively, maintain a Redis-backed deny-list of revoked `jti` values with TTL equal to the token's remaining lifetime.
- For the monitoring token, the API key can be rotated in environment config, instantly invalidating all existing monitoring tokens (because they'd have been issued against the old key checksum).

### Known security issue
The `MONITORING_API_KEY` is a static, long-lived shared secret stored in `.env`. If it leaks, any monitoring-officer-JWT holder can mint unlimited scoped tokens. **Fix with more time:** replace with TOTP / short-lived server-generated challenges, or scope the key per monitoring officer user and store it hashed in the database with a rotation workflow.

---

## 7. What Is Working / Partial / Skipped

| Area | Status |
|---|---|
| All 13 endpoints | ✅ Fully implemented |
| JWT auth (signup, login, 24 h token) | ✅ |
| Monitoring dual-token flow | ✅ |
| Role-based access control on every endpoint | ✅ |
| 422 validation on all POST bodies | ✅ |
| 404 on missing FK references | ✅ |
| 403 for unenrolled student attendance | ✅ |
| 405 on non-GET to /monitoring/attendance | ✅ |
| Seed script (2 inst, 4 trainers, 15 students, 3 batches, 8 sessions) | ✅ |
| 6 pytest tests (2 hitting real DB) | ✅ All pass |
| Deployment config | ✅ Neon DB live; Railway/Render deploy-ready |
| Password hashing (bcrypt via passlib) | ✅ |
| Alembic migrations | ⚠️ Using `Base.metadata.create_all` instead; alembic wired but migrations not authored |

### One thing I'd do differently with more time
Replace `Base.metadata.create_all` at startup with proper Alembic migrations — enabling schema evolution without dropping and recreating tables, safe zero-downtime deployments, and a full audit trail of schema changes.
# SkillBridge
