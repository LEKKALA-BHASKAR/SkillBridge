"""
Seed the database with test data.
Run: python seed.py
"""
import os
import sys
from datetime import date, time, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from db import SessionLocal, Base, engine
import models  # noqa — registers all models
from models.user import User
from models.batch import Batch, BatchTrainer, BatchStudent, BatchInvite
from models.session import Session
from models.attendance import Attendance
from core.auth import hash_password
import secrets

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def clear():
    db.query(Attendance).delete()
    db.query(Session).delete()
    db.query(BatchStudent).delete()
    db.query(BatchTrainer).delete()
    db.query(BatchInvite).delete()
    db.query(Batch).delete()
    db.query(User).delete()
    db.commit()


def seed():
    clear()

    pw = hash_password("Password123!")

    # --- Institutions ---
    inst1 = User(name="Sunrise Institute", email="inst1@skillbridge.dev", hashed_password=pw, role="institution")
    inst2 = User(name="Horizon College", email="inst2@skillbridge.dev", hashed_password=pw, role="institution")
    db.add_all([inst1, inst2])
    db.flush()

    # --- Trainers ---
    t1 = User(name="Trainer Alice", email="trainer1@skillbridge.dev", hashed_password=pw, role="trainer", institution_id=inst1.id)
    t2 = User(name="Trainer Bob", email="trainer2@skillbridge.dev", hashed_password=pw, role="trainer", institution_id=inst1.id)
    t3 = User(name="Trainer Carol", email="trainer3@skillbridge.dev", hashed_password=pw, role="trainer", institution_id=inst2.id)
    t4 = User(name="Trainer Dave", email="trainer4@skillbridge.dev", hashed_password=pw, role="trainer", institution_id=inst2.id)
    db.add_all([t1, t2, t3, t4])
    db.flush()

    # --- Programme Manager + Monitoring Officer ---
    pm = User(name="Programme Manager", email="pm@skillbridge.dev", hashed_password=pw, role="programme_manager")
    mo = User(name="Monitoring Officer", email="monitor@skillbridge.dev", hashed_password=pw, role="monitoring_officer")
    db.add_all([pm, mo])
    db.flush()

    # --- Students (15) ---
    students = []
    for i in range(1, 16):
        s = User(
            name=f"Student {i:02d}",
            email=f"student{i:02d}@skillbridge.dev",
            hashed_password=pw,
            role="student",
        )
        students.append(s)
    db.add_all(students)
    db.flush()

    # --- Batches (3) ---
    b1 = Batch(name="Web Dev Batch A", institution_id=inst1.id)
    b2 = Batch(name="Data Science Batch B", institution_id=inst1.id)
    b3 = Batch(name="Cybersecurity Batch C", institution_id=inst2.id)
    db.add_all([b1, b2, b3])
    db.flush()

    # --- Assign trainers ---
    db.add_all([
        BatchTrainer(batch_id=b1.id, trainer_id=t1.id),
        BatchTrainer(batch_id=b1.id, trainer_id=t2.id),
        BatchTrainer(batch_id=b2.id, trainer_id=t2.id),
        BatchTrainer(batch_id=b3.id, trainer_id=t3.id),
        BatchTrainer(batch_id=b3.id, trainer_id=t4.id),
    ])

    # --- Enroll students ---
    # Batch 1: students 1-7
    for s in students[:7]:
        db.add(BatchStudent(batch_id=b1.id, student_id=s.id))
    # Batch 2: students 5-11
    for s in students[4:11]:
        db.add(BatchStudent(batch_id=b2.id, student_id=s.id))
    # Batch 3: students 10-15
    for s in students[9:]:
        db.add(BatchStudent(batch_id=b3.id, student_id=s.id))
    db.flush()

    # --- Sessions (8) ---
    base_date = date(2025, 3, 1)
    sessions_data = [
        Session(batch_id=b1.id, trainer_id=t1.id, title="HTML Basics", date=base_date, start_time=time(9, 0), end_time=time(11, 0)),
        Session(batch_id=b1.id, trainer_id=t1.id, title="CSS Layouts", date=base_date + timedelta(days=2), start_time=time(9, 0), end_time=time(11, 0)),
        Session(batch_id=b1.id, trainer_id=t2.id, title="JavaScript Intro", date=base_date + timedelta(days=4), start_time=time(13, 0), end_time=time(15, 0)),
        Session(batch_id=b2.id, trainer_id=t2.id, title="Python Fundamentals", date=base_date, start_time=time(10, 0), end_time=time(12, 0)),
        Session(batch_id=b2.id, trainer_id=t2.id, title="Pandas & NumPy", date=base_date + timedelta(days=3), start_time=time(10, 0), end_time=time(12, 0)),
        Session(batch_id=b3.id, trainer_id=t3.id, title="Network Security", date=base_date, start_time=time(14, 0), end_time=time(16, 0)),
        Session(batch_id=b3.id, trainer_id=t4.id, title="Ethical Hacking", date=base_date + timedelta(days=2), start_time=time(14, 0), end_time=time(16, 0)),
        Session(batch_id=b3.id, trainer_id=t3.id, title="Cryptography", date=base_date + timedelta(days=5), start_time=time(14, 0), end_time=time(16, 0)),
    ]
    db.add_all(sessions_data)
    db.flush()

    # --- Attendance records ---
    statuses = ["present", "present", "present", "absent", "late", "present", "present"]
    # Batch 1 sessions: students 0-6
    for sess in sessions_data[:3]:
        enrolled = students[:7]
        for i, student in enumerate(enrolled):
            db.add(Attendance(
                session_id=sess.id,
                student_id=student.id,
                status=statuses[i % len(statuses)],
                marked_at=datetime(sess.date.year, sess.date.month, sess.date.day, 9, 30),
            ))
    # Batch 2 sessions: students 4-10
    for sess in sessions_data[3:5]:
        enrolled = students[4:11]
        for i, student in enumerate(enrolled):
            db.add(Attendance(
                session_id=sess.id,
                student_id=student.id,
                status=statuses[i % len(statuses)],
                marked_at=datetime(sess.date.year, sess.date.month, sess.date.day, 10, 30),
            ))
    # Batch 3 sessions: students 9-14
    for sess in sessions_data[5:]:
        enrolled = students[9:]
        for i, student in enumerate(enrolled):
            db.add(Attendance(
                session_id=sess.id,
                student_id=student.id,
                status=statuses[i % len(statuses)],
                marked_at=datetime(sess.date.year, sess.date.month, sess.date.day, 14, 30),
            ))

    db.commit()
    print("Seed complete.")
    print(f"  Institutions: {inst1.email}, {inst2.email}")
    print(f"  Trainers: trainer1-4@skillbridge.dev")
    print(f"  Students: student01-15@skillbridge.dev")
    print(f"  Programme Manager: {pm.email}")
    print(f"  Monitoring Officer: {mo.email}")
    print(f"  All passwords: Password123!")
    db.close()


if __name__ == "__main__":
    seed()
