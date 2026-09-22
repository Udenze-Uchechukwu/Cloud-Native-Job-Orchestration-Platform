import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import JobStatus


class JobCreate(BaseModel):
    command: str


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    command: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class LogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    timestamp: datetime
    message: str
