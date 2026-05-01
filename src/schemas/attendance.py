from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AttendanceMark(BaseModel):
    session_id: int
    status: str  # present/absent/late


class AttendanceOut(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: str
    marked_at: datetime

    model_config = {"from_attributes": True}


class MonitoringAttendanceRecord(BaseModel):
    attendance_id: int
    session_id: int
    session_title: str
    batch_id: int
    batch_name: str
    student_id: int
    student_name: str
    status: str
    marked_at: datetime
