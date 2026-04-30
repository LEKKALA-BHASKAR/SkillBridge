from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.batch import BatchStudent
from models.session import Session as SessionModel
from models.attendance import Attendance
from models.user import User
from schemas.attendance import AttendanceMark, AttendanceOut
from core.dependencies import require_roles
from datetime import date

router = APIRouter(prefix="/attendance", tags=["attendance"])

VALID_STATUSES = {"present", "absent", "late"}


@router.post("/mark", response_model=AttendanceOut, status_code=201)
def mark_attendance(
    body: AttendanceMark,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(VALID_STATUSES)}")

    session = db.query(SessionModel).filter(SessionModel.id == body.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check session is active (today's session)
    if session.date != date.today():
        raise HTTPException(status_code=400, detail="Can only mark attendance for today's session")

    # Check enrollment
    enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == session.batch_id,
        BatchStudent.student_id == current_user.id,
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this batch")

    # Prevent duplicate
    existing = db.query(Attendance).filter(
        Attendance.session_id == body.session_id,
        Attendance.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already marked for this session")

    record = Attendance(
        session_id=body.session_id,
        student_id=current_user.id,
        status=body.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
