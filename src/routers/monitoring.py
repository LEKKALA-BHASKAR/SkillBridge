from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.db import get_db
from src.models.attendance import Attendance
from src.models.session import Session as SessionModel
from src.models.batch import Batch
from src.models.user import User
from src.schemas.attendance import MonitoringAttendanceRecord
from src.core.dependencies import get_monitoring_user
from typing import List

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/attendance", response_model=List[MonitoringAttendanceRecord])
def monitoring_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_monitoring_user),
):
    rows = (
        db.query(Attendance, SessionModel, Batch, User)
        .join(SessionModel, Attendance.session_id == SessionModel.id)
        .join(Batch, SessionModel.batch_id == Batch.id)
        .join(User, Attendance.student_id == User.id)
        .all()
    )
    return [
        MonitoringAttendanceRecord(
            attendance_id=att.id,
            session_id=sess.id,
            session_title=sess.title,
            batch_id=batch.id,
            batch_name=batch.name,
            student_id=student.id,
            student_name=student.name,
            status=att.status,
            marked_at=att.marked_at,
        )
        for att, sess, batch, student in rows
    ]


# Return 405 for any non-GET method on /monitoring/attendance
@router.post("/attendance")
@router.put("/attendance")
@router.patch("/attendance")
@router.delete("/attendance")
async def monitoring_attendance_method_not_allowed():
    return JSONResponse(status_code=405, content={"detail": "Method Not Allowed"})
