from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db import get_db
from src.models.batch import Batch, BatchStudent
from src.models.session import Session as SessionModel
from src.models.attendance import Attendance
from src.models.user import User
from src.schemas.batch import BatchSummary
from src.core.dependencies import require_roles
from typing import List

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/{institution_id}/summary")
def institution_summary(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("programme_manager", "institution", "monitoring_officer")),
):
    inst = db.query(User).filter(User.id == institution_id, User.role == "institution").first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    batches = db.query(Batch).filter(Batch.institution_id == institution_id).all()
    result = []
    for batch in batches:
        total_sessions = db.query(SessionModel).filter(SessionModel.batch_id == batch.id).count()
        total_students = db.query(BatchStudent).filter(BatchStudent.batch_id == batch.id).count()
        session_ids = [s.id for s in db.query(SessionModel.id).filter(SessionModel.batch_id == batch.id)]
        records = db.query(Attendance).filter(Attendance.session_id.in_(session_ids)).all() if session_ids else []
        result.append(BatchSummary(
            batch_id=batch.id,
            batch_name=batch.name,
            total_sessions=total_sessions,
            total_students=total_students,
            attendance_records=len(records),
            present=sum(1 for r in records if r.status == "present"),
            absent=sum(1 for r in records if r.status == "absent"),
            late=sum(1 for r in records if r.status == "late"),
        ))

    return {"institution_id": institution_id, "institution_name": inst.name, "batches": result}
