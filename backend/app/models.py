import enum
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class JobStatus(str, enum.Enum):
    """The four states a job can be in. PENDING covers both "never run yet"
    and "waiting to retry" — there's no separate "retrying" state."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"


class Job(Base):
    """A submitted unit of work: the command to run, its current state, and
    how many times it's been attempted."""

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    command = Column(String, nullable=False)
    status = Column(String, nullable=False, default=JobStatus.PENDING.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    attempts = Column(Integer, nullable=False, default=0, server_default=text("0"))
    timeout_seconds = Column(Integer, nullable=False, default=30, server_default=text("30"))


class LogStream(str, enum.Enum):
    """Which output stream a JobLog entry came from."""

    STDOUT = "stdout"
    STDERR = "stderr"


class JobLog(Base):
    """One stdout/stderr capture from a single attempt of a job."""

    __tablename__ = "job_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message = Column(Text, nullable=False)
    stream = Column(String, nullable=False, server_default=text("'stdout'"))
    attempt = Column(Integer, nullable=False, server_default=text("1"))
