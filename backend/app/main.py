import time
import uuid

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.logging_config import configure_logging
from app.models import Job, JobLog, JobStatus
from app.queue import enqueue_job
from app.schemas import JobCreate, JobRead, LogRead

configure_logging()
log = structlog.get_logger()

app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request: method, path, status, and how long it took."""
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 2)
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.get("/health")
def health():
    """Liveness check — returns 200 if the API process is up."""
    return {"status": "ok"}


@app.post("/jobs", response_model=JobRead, status_code=201)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    """Create a job as PENDING and enqueue it for a worker to pick up."""
    job = Job(
        command=job_in.command,
        status=JobStatus.PENDING.value,
        timeout_seconds=job_in.timeout_seconds,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    enqueue_job(job.id)
    log.info("job_created", job_id=str(job.id), command=job.command)
    return job


@app.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetch a job's current state."""
    job = db.get(Job, job_id)
    if job is None:
        log.warning("job_not_found", job_id=str(job_id))
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/jobs/{job_id}/logs", response_model=list[LogRead])
def get_job_logs(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetch a job's logs, oldest first — one entry per attempt's stdout/stderr."""
    job = db.get(Job, job_id)
    if job is None:
        log.warning("job_not_found", job_id=str(job_id))
        raise HTTPException(status_code=404, detail="job not found")
    return db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp).all()
