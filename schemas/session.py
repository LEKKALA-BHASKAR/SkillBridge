from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional


class SessionCreate(BaseModel):
    title: str
    date: date
    start_time: time
    end_time: time
    batch_id: int


class SessionOut(BaseModel):
    id: int
    batch_id: int
    trainer_id: int
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceRecord(BaseModel):
    student_id: int
    student_name: str
    status: str
    marked_at: Optional[datetime]
