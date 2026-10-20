import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import JobStatus, LogStream


class JobCreate(BaseModel):
    command: str
    timeout_seconds: int = Field(default=30, gt=0)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    command: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    attempts: int
    timeout_seconds: int


class LogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    timestamp: datetime
    message: str
    stream: LogStream
    attempt: int
