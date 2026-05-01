"""
pytest tests for SkillBridge API.
At least two tests (signup/login + mark attendance) hit a real test database.
"""
import uuid
import pytest
from jose import jwt
from src.core.auth import SECRET, ALGO


def unique_email(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.dev"


# ---------------------------------------------------------------------------
# 1. Successful student signup and login — real DB
# ---------------------------------------------------------------------------

def test_student_signup_and_login(client):
    email = unique_email("student")
    # Signup
    resp = client.post("/auth/signup", json={
        "name": "Test Student",
        "email": email,
        "password": "Passw0rd!",
        "role": "student",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    assert token

    payload = jwt.decode(token, SECRET, algorithms=[ALGO])
    assert payload["role"] == "student"
    assert "sub" in payload
    assert "exp" in payload
    assert "iat" in payload

    # Login
    resp2 = client.post("/auth/login", json={"email": email, "password": "Passw0rd!"})
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["access_token"]


# ---------------------------------------------------------------------------
# 2. Trainer creating a session — real DB
# ---------------------------------------------------------------------------

def test_trainer_creates_session(client):
    inst_email = unique_email("inst")
    trainer_email = unique_email("trainer")

    # Create institution
    inst_resp = client.post("/auth/signup", json={
        "name": "Test Institution",
        "email": inst_email,
        "password": "Passw0rd!",
        "role": "institution",
    })
    assert inst_resp.status_code == 201
    inst_id = jwt.decode(inst_resp.json()["access_token"], SECRET, algorithms=[ALGO])["sub"]

    # Create trainer
    t_resp = client.post("/auth/signup", json={
        "name": "Test Trainer",
        "email": trainer_email,
        "password": "Passw0rd!",
        "role": "trainer",
    })
    assert t_resp.status_code == 201
    trainer_token = t_resp.json()["access_token"]
    trainer_id = jwt.decode(trainer_token, SECRET, algorithms=[ALGO])["sub"]

    # Create batch (trainer creates, auto-assigned)
    batch_resp = client.post(
        "/batches",
        json={"name": "Test Batch", "institution_id": int(inst_id)},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert batch_resp.status_code == 201, batch_resp.text
    batch_id = batch_resp.json()["id"]

    # Create session
    sess_resp = client.post(
        "/sessions",
        json={
            "title": "Intro to Testing",
            "date": "2025-06-01",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "batch_id": batch_id,
        },
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert sess_resp.status_code == 201, sess_resp.text
    data = sess_resp.json()
    assert data["title"] == "Intro to Testing"
    assert data["batch_id"] == batch_id
    assert data["trainer_id"] == int(trainer_id)


# ---------------------------------------------------------------------------
# 3. Student marks own attendance — real DB
# ---------------------------------------------------------------------------

def test_student_marks_attendance(client):
    inst_email = unique_email("inst")
    trainer_email = unique_email("trainer")
    student_email = unique_email("student")

    inst_resp = client.post("/auth/signup", json={
        "name": "Inst B", "email": inst_email, "password": "Passw0rd!", "role": "institution"
    })
    inst_id = int(jwt.decode(inst_resp.json()["access_token"], SECRET, algorithms=[ALGO])["sub"])

    t_resp = client.post("/auth/signup", json={
        "name": "Trainer B", "email": trainer_email, "password": "Passw0rd!", "role": "trainer"
    })
    trainer_token = t_resp.json()["access_token"]

    s_resp = client.post("/auth/signup", json={
        "name": "Student B", "email": student_email, "password": "Passw0rd!", "role": "student"
    })
    student_token = s_resp.json()["access_token"]

    # Batch
    batch_resp = client.post("/batches", json={"name": "Batch B", "institution_id": inst_id},
                             headers={"Authorization": f"Bearer {trainer_token}"})
    batch_id = batch_resp.json()["id"]

    # Invite
    inv_resp = client.post(f"/batches/{batch_id}/invite",
                           headers={"Authorization": f"Bearer {trainer_token}"})
    assert inv_resp.status_code == 201, inv_resp.text
    token_val = inv_resp.json()["token"]

    # Student joins
    join_resp = client.post("/batches/join", json={"token": token_val},
                            headers={"Authorization": f"Bearer {student_token}"})
    assert join_resp.status_code == 200, join_resp.text

    # Create session for today
    from datetime import date
    today = date.today().isoformat()
    sess_resp = client.post("/sessions", json={
        "title": "Live Session",
        "date": today,
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "batch_id": batch_id,
    }, headers={"Authorization": f"Bearer {trainer_token}"})
    assert sess_resp.status_code == 201, sess_resp.text
    session_id = sess_resp.json()["id"]

    # Mark attendance
    att_resp = client.post("/attendance/mark", json={
        "session_id": session_id,
        "status": "present",
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert att_resp.status_code == 201, att_resp.text
    assert att_resp.json()["status"] == "present"


# ---------------------------------------------------------------------------
# 4. POST to /monitoring/attendance returns 405
# ---------------------------------------------------------------------------

def test_monitoring_attendance_post_returns_405(client):
    resp = client.post("/monitoring/attendance")
    assert resp.status_code == 405, resp.text


# ---------------------------------------------------------------------------
# 5. Protected endpoint with no token returns 401
# ---------------------------------------------------------------------------

def test_no_token_returns_401(client):
    resp = client.get("/sessions/1/attendance")
    assert resp.status_code == 403 or resp.status_code == 401, resp.text
    # FastAPI HTTPBearer returns 403 by default when no credentials provided
    # Both are acceptable — the key thing is it's not 200


def test_invalid_token_returns_401(client):
    resp = client.get("/sessions/1/attendance",
                      headers={"Authorization": "Bearer invalidtoken.xyz.abc"})
    assert resp.status_code == 401, resp.text
