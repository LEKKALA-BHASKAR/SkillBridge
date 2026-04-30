from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import get_db
from models.batch import Batch, BatchTrainer, BatchStudent, BatchInvite
from models.session import Session as SessionModel
from models.attendance import Attendance
from models.user import User
from schemas.batch import BatchCreate, BatchOut, InviteOut, JoinBatchRequest, BatchSummary
from core.dependencies import require_roles, get_current_user
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchOut, status_code=201)
def create_batch(
    body: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer", "institution")),
):
    # Verify institution exists
    inst = db.query(User).filter(User.id == body.institution_id, User.role == "institution").first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch = Batch(name=body.name, institution_id=body.institution_id)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Auto-assign trainer to batch if caller is a trainer
    if current_user.role == "trainer":
        link = BatchTrainer(batch_id=batch.id, trainer_id=current_user.id)
        db.add(link)
        db.commit()

    return batch


@router.post("/{batch_id}/invite", response_model=InviteOut, status_code=201)
def create_invite(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("trainer")),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Trainer must be assigned to batch
    link = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == batch_id,
        BatchTrainer.trainer_id == current_user.id,
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="You are not assigned to this batch")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    invite = BatchInvite(
        batch_id=batch_id,
        token=token,
        created_by=current_user.id,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return {"token": invite.token, "expires_at": invite.expires_at, "batch_id": invite.batch_id}


@router.post("/join", status_code=200)
def join_batch(
    body: JoinBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    invite = db.query(BatchInvite).filter(BatchInvite.token == body.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite token not found")
    if invite.used:
        raise HTTPException(status_code=410, detail="Invite token already used")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Invite token expired")

    existing = db.query(BatchStudent).filter(
        BatchStudent.batch_id == invite.batch_id,
        BatchStudent.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already enrolled in this batch")

    enrollment = BatchStudent(batch_id=invite.batch_id, student_id=current_user.id)
    db.add(enrollment)
    invite.used = True
    db.commit()
    return {"message": "Joined batch successfully", "batch_id": invite.batch_id}


@router.get("/{batch_id}/summary", response_model=BatchSummary)
def batch_summary(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("institution", "programme_manager", "monitoring_officer")),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    total_sessions = db.query(SessionModel).filter(SessionModel.batch_id == batch_id).count()
    total_students = db.query(BatchStudent).filter(BatchStudent.batch_id == batch_id).count()

    session_ids = [s.id for s in db.query(SessionModel.id).filter(SessionModel.batch_id == batch_id)]
    records = db.query(Attendance).filter(Attendance.session_id.in_(session_ids)).all() if session_ids else []

    present = sum(1 for r in records if r.status == "present")
    absent = sum(1 for r in records if r.status == "absent")
    late = sum(1 for r in records if r.status == "late")

    return BatchSummary(
        batch_id=batch_id,
        batch_name=batch.name,
        total_sessions=total_sessions,
        total_students=total_students,
        attendance_records=len(records),
        present=present,
        absent=absent,
        late=late,
    )
