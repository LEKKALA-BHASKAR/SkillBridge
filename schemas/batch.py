from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BatchCreate(BaseModel):
    name: str
    institution_id: int


class BatchOut(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteOut(BaseModel):
    token: str
    expires_at: datetime
    batch_id: int


class JoinBatchRequest(BaseModel):
    token: str


class BatchSummary(BaseModel):
    batch_id: int
    batch_name: str
    total_sessions: int
    total_students: int
    attendance_records: int
    present: int
    absent: int
    late: int
