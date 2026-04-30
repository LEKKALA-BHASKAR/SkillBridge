from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.batch import Batch, BatchTrainer, BatchStudent
from models.session import Session as SessionModel
from models.attendance import Attendance
from models.user import User
from schemas.session import SessionCreate, SessionOut, AttendanceRecord
from core.dependencies import require_roles
from typing import List

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer")),
):
    batch = db.query(Batch).filter(Batch.id == body.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    link = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == body.batch_id,
        BatchTrainer.trainer_id == current_user.id,
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="You are not assigned to this batch")

    session = SessionModel(
        batch_id=body.batch_id,
        trainer_id=current_user.id,
        title=body.title,
        date=body.date,
        start_time=body.start_time,
        end_time=body.end_time,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/attendance", response_model=List[AttendanceRecord])
def session_attendance(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer", "institution", "programme_manager")),
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = (
        db.query(Attendance, User)
        .join(User, Attendance.student_id == User.id)
        .filter(Attendance.session_id == session_id)
        .all()
    )

    return [
        AttendanceRecord(
            student_id=att.student_id,
            student_name=user.name,
            status=att.status,
            marked_at=att.marked_at,
        )
        for att, user in records
    ]
